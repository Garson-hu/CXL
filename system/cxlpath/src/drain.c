/* Component D: DRAM-free drain to NVMe (D1), pacing (D2). Runs in the background process. */
#define _GNU_SOURCE
#include "internal.h"
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#define ALIGN 4096u

int cxlp_obj_set_drain(uint32_t h, const char *path, uint64_t file_off) {
    if (strlen(path) >= sizeof(((cxlp_drain_t *)0)->path)) return -1;
    for (uint32_t i = 0; i < CXLP_NDRAIN; i++) {
        cxlp_drain_t *d = &cxlp_g.meta->drain[i]; uint32_t z = 0;
        if (atomic_load(&d->used) == 0 && atomic_compare_exchange_strong(&d->used, &z, 1)) {
            d->obj = h; d->file_off = file_off; snprintf(d->path, sizeof d->path, "%s", path);
            atomic_store(&cxlp_g.obj[h].drain_idx, i); atomic_store(&d->used, 2);      /* 2 = ready for the drainer */
            return 0;
        }
    }
    return -1;
}

int cxlp_obj_drained(cxlp_key_t key) {
    cxlp_obj_t *o = cxlp_obj_find(key); if (!o || atomic_load(&o->drain_idx) == CXLP_NIL) return -1;
    return (int)atomic_load(&o->drained);
}

static int bs_slot(cxlp_key_t client) { for (int i = 0; i < CXLP_MAX_BUFSETS; i++) if (atomic_load(&cxlp_g.meta->bufset[i].client) == client) return i; return -1; }

int cxlp_bufset_commit_drain(cxlp_key_t client, int which, const char *path) {
    int sl = bs_slot(client); if (sl < 0 || strlen(path) >= 240) return -1;
    cxlp_bufset_t *b = &cxlp_g.meta->bufset[sl];
    snprintf(b->drain_path[which], 240, "%s", path);
    atomic_store(&b->drain_next[which], 0); atomic_store(&b->drain_done[which], 0);
    if (cxlp_bufset_commit(client, which)) return -1;
    atomic_store(&b->drain_armed[which], 1);
    return 0;
}
int cxlp_bufset_set_used(cxlp_key_t client, int which, uint64_t bytes) {
    int sl = bs_slot(client); if (sl < 0 || bytes > cxlp_g.meta->bufset[sl].bytes[which]) return -1;
    cxlp_g.meta->bufset[sl].used[which] = bytes; return 0;
}
int cxlp_bufset_drained(cxlp_key_t client, int which) { int sl = bs_slot(client); return sl < 0 ? -1 : (int)atomic_load(&cxlp_g.meta->bufset[sl].drained[which]); }

/* ---- per-thread descriptor cache: one O_DIRECT and one buffered descriptor per file ---- */
typedef struct { char path[240]; int fd_direct, fd_buf; uint64_t used; } fdc_t;
static __thread fdc_t fdc[8]; static __thread uint64_t fdc_tick;
static fdc_t *get_fd(const char *path) {
    fdc_t *v = &fdc[0];
    for (int i = 0; i < 8; i++) { if (fdc[i].used && !strcmp(fdc[i].path, path)) { fdc[i].used = ++fdc_tick; return &fdc[i]; } if (fdc[i].used < v->used) v = &fdc[i]; }
    if (v->used) { if (v->fd_direct >= 0) close(v->fd_direct); close(v->fd_buf); }
    v->fd_buf = open(path, O_WRONLY | O_CREAT, 0644); if (v->fd_buf < 0) { v->used = 0; return NULL; }
    v->fd_direct = open(path, O_WRONLY | O_DIRECT);            /* tmpfs and some file systems refuse it: fall back to buffered */
    snprintf(v->path, sizeof v->path, "%s", path); v->used = ++fdc_tick;
    return v;
}

/* write [p, p+len) at file offset off: the 4 KiB-aligned body with O_DIRECT straight from the
 * device mapping, unaligned edges (and everything, if alignment is impossible) buffered */
static int write_range(fdc_t *f, const char *p, uint64_t len, uint64_t off) {
    uint64_t body = 0;
    if (f->fd_direct >= 0 && ((uintptr_t)p % ALIGN) == 0 && off % ALIGN == 0) body = len & ~(uint64_t)(ALIGN - 1);
    for (uint64_t done = 0; done < body;) { ssize_t w = pwrite(f->fd_direct, p + done, body - done, (off_t)(off + done)); if (w <= 0) { if (errno == EINTR) continue; return -1; } done += (uint64_t)w; }
    for (uint64_t done = body; done < len;) { ssize_t w = pwrite(f->fd_buf, p + done, len - done, (off_t)(off + done)); if (w <= 0) { if (errno == EINTR) continue; return -1; } done += (uint64_t)w; }
    return 0;
}

static int should_yield(void) {
    static __thread uint64_t last_bytes, last_change_ns;
    uint64_t b = atomic_load(&POL->gpu_direct.bytes) + atomic_load(&POL->gpu_staged.bytes), now = cxlp_now_ns();
    uint32_t free_cxl = 0, tot_cxl = 0;
    for (uint32_t d = 0; d < cxlp_g.meta->ndev; d++) if (cxlp_g.meta->dev[d].kind == CXLP_DEV_CXL) { b += atomic_load(&POL->led[d].bytes); free_cxl += atomic_load(&cxlp_g.meta->dev[d].nfree); tot_cxl += cxlp_g.meta->dev[d].nseg; }
    if (b != last_bytes) { last_bytes = b; last_change_ns = now; }
    int writers_active = last_change_ns && now - last_change_ns < 100000000ull;
    int space_low = tot_cxl && free_cxl * 100u < tot_cxl * atomic_load(&cxlp_g.meta->drain_lowspace_pct);
    return writers_active && !space_low;
}

static __thread int need_reclaim;
static int64_t drain_object(cxlp_drain_t *d) {
    cxlp_obj_t *o = &cxlp_g.obj[d->obj];
    uint32_t st = atomic_load(&o->state); if (st != OBJ_CREATING && st != OBJ_COMMITTED) return 0;
    if (atomic_load(&o->drained)) return 0;
    atomic_fetch_add(&o->pins, 1);                             /* a release now waits for us */
    int64_t wrote = 0; int all_done = 1;
    for (uint32_t e = atomic_load(&o->head); e != CXLP_NIL; e = atomic_load(&cxlp_g.ext[e].next)) {
        cxlp_ext_t *x = &cxlp_g.ext[e]; uint32_t ds = atomic_load(&x->drain_state);
        if (ds == 2) continue;
        all_done = 0;
        uint32_t z = 0; if (ds != 0 || !atomic_compare_exchange_strong(&x->drain_state, &z, 1)) continue;
        fdc_t *f = get_fd(d->path);
        const char *p = (const char *)cxlp_seg_ptr((int)x->dev, x->seg) + x->off;
        if (f && write_range(f, p, x->len, d->file_off + x->obj_off) == 0) { atomic_store(&x->drain_state, 2); wrote = x->len; atomic_fetch_add(&cxlp_g.meta->drained_bytes, x->len); }
        else atomic_store(&x->drain_state, 0);
        break;                                                 /* one extent per step */
    }
    if (all_done && atomic_load(&o->state) == OBJ_COMMITTED) {  /* nothing pending and no more extents can come */
        uint32_t z = 0; if (atomic_compare_exchange_strong(&o->drained, &z, 2)) { fdc_t *f = get_fd(d->path); if (f) { fsync(f->fd_buf); } atomic_store(&o->drained, 1); need_reclaim = 1; }
    }
    atomic_fetch_sub(&o->pins, 1);
    return wrote;
}

static int64_t drain_bufset(cxlp_bufset_t *b, int slot, int w) {
    uint64_t total = b->used[w] ? b->used[w] : b->bytes[w];
    uint32_t n = (uint32_t)((total + CXLP_SEG_BYTES - 1) / CXLP_SEG_BYTES), i = atomic_fetch_add(&b->drain_next[w], 1);
    if (i >= n) { atomic_fetch_sub(&b->drain_next[w], 1); return 0; }
    uint32_t *t = (uint32_t *)((char *)cxlp_g.meta + cxlp_g.meta->bs_segtab_off) + ((size_t)slot * 2 + (size_t)w) * CXLP_BS_MAXSEG;
    uint64_t off = (uint64_t)i * CXLP_SEG_BYTES, len = total - off < CXLP_SEG_BYTES ? total - off : CXLP_SEG_BYTES;
    fdc_t *f = get_fd(b->drain_path[w]);
    if (!f || write_range(f, cxlp_seg_ptr((int)b->dev[w], t[i]), len, off)) return -1;
    atomic_fetch_add(&cxlp_g.meta->drained_bytes, len);
    if (atomic_fetch_add(&b->drain_done[w], 1) + 1 == n) {     /* last segment: exact size, durable, then the set may be overwritten */
        if (ftruncate(f->fd_buf, (off_t)total) == 0 && fsync(f->fd_buf) == 0) { atomic_store(&b->drain_armed[w], 0); atomic_store(&b->drained[w], 1); }
    }
    return (int64_t)len;
}

/* Reclaim checkpoint versions: on NVMe, and a newer version of the same chain is committed. */
static int reclaim_chains(void) {
    enum { NC = 64 }; uint64_t chain[NC], newest[NC]; int nc = 0, freed = 0;
    for (uint32_t k = 0; k < CXLP_NDRAIN; k++) {
        cxlp_drain_t *d = &cxlp_g.meta->drain[k]; if (atomic_load(&d->used) != 2) continue;
        cxlp_obj_t *o = &cxlp_g.obj[d->obj]; if (!o->chain || atomic_load(&o->state) != OBJ_COMMITTED) continue;
        int i = 0; while (i < nc && chain[i] != o->chain) i++;
        if (i == nc) { if (nc == NC) continue; chain[nc] = o->chain; newest[nc] = o->version; nc++; } else if (o->version > newest[i]) newest[i] = o->version;
    }
    for (uint32_t k = 0; k < CXLP_NDRAIN; k++) {
        cxlp_drain_t *d = &cxlp_g.meta->drain[k]; if (atomic_load(&d->used) != 2) continue;
        cxlp_obj_t *o = &cxlp_g.obj[d->obj]; if (!o->chain || atomic_load(&o->state) != OBJ_COMMITTED || atomic_load(&o->drained) != 1) continue;
        for (int i = 0; i < nc; i++) if (chain[i] == o->chain && o->version < newest[i] && cxlp_obj_release(atomic_load(&o->key)) == 0) freed++;
    }
    if (freed) cxlp_thread_seal();
    return freed;
}

static int have_work(void) {
    for (int s = 0; s < CXLP_MAX_BUFSETS; s++) { cxlp_bufset_t *b = &cxlp_g.meta->bufset[s]; if (!atomic_load(&b->client)) continue;
        for (int w = 0; w < 2; w++) if (atomic_load(&b->drain_armed[w])) return 1; }
    for (uint32_t k = 0; k < CXLP_NDRAIN; k++) { cxlp_drain_t *d = &cxlp_g.meta->drain[k]; if (atomic_load(&d->used) != 2) continue;
        cxlp_obj_t *o = &cxlp_g.obj[d->obj]; if (!atomic_load(&o->drained) && atomic_load(&o->head) != CXLP_NIL) return 1; }
    return 0;
}

int64_t cxlp_drain_step(int yield) {
    static __thread uint32_t idle_steps; static __thread uint64_t pending_since;
    if (idle_steps++ % 25 == 0) reclaim_chains();              /* also covers versions whose successor committed after their drain */
    /* Pacing: give way to active writers — but never indefinitely. The first all-clients run (F1)
     * showed the flaw of "yield while anybody writes": with a KV layer writing all the time the drain
     * never ran, and a checkpoint writer waited a minute for a buffer set. The drain stops yielding
     * when (a) free CXL space is short, (b) a writer is blocked until a drain completes, or
     * (c) work has been pending longer than drain_lag_ms (bounds how long data stays non-durable). */
    if (yield && should_yield()) {
        uint64_t now = cxlp_now_ns();
        if (!have_work()) { pending_since = 0; return 0; }
        if (!pending_since) pending_since = now;
        int urgent = now - atomic_load(&cxlp_g.meta->drain_wanted_ns) < 200000000ull;
        int overdue = now - pending_since > (uint64_t)atomic_load(&cxlp_g.meta->drain_lag_ms) * 1000000ull;
        if (!urgent && !overdue) return 0;
    }
    for (int s = 0; s < CXLP_MAX_BUFSETS; s++) {               /* checkpoints in buffer sets first: they gate the writer */
        cxlp_bufset_t *b = &cxlp_g.meta->bufset[s]; if (!atomic_load(&b->client)) continue;
        for (int w = 0; w < 2; w++) if (atomic_load(&b->drain_armed[w]) && (uint64_t)atomic_load(&b->drain_next[w]) * CXLP_SEG_BYTES < (b->used[w] ? b->used[w] : b->bytes[w])) { int64_t r = drain_bufset(b, s, w); if (r) return r; }
    }
    static __thread uint32_t rr;
    for (uint32_t k = 0; k < CXLP_NDRAIN; k++) {
        cxlp_drain_t *d = &cxlp_g.meta->drain[(rr + k) % CXLP_NDRAIN];
        if (atomic_load(&d->used) != 2) continue;
        int64_t r = drain_object(d);
        if (need_reclaim) { need_reclaim = 0; reclaim_chains(); }
        if (r) { rr = (rr + k) % CXLP_NDRAIN; return r; }
    }
    if (!have_work()) pending_since = 0;
    return 0;
}
