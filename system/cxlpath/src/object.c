/* Component A, part 3: shared object index, lookup, crash cleanup (A4). */
#define _GNU_SOURCE
#include "internal.h"
#include <pthread.h>
#include <sched.h>
#include <errno.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>

static uint64_t mix(uint64_t x) { x ^= x >> 33; x *= 0xff51afd7ed558ccdull; x ^= x >> 33; x *= 0xc4ceb9fe1a85ec53ull; return x ^ (x >> 33); }

static uint32_t ext_alloc(void) {
    uint32_t n = cxlp_g.meta->next_cap, start = atomic_fetch_add(&cxlp_g.meta->ext_hint, 1) % n;
    for (uint32_t k = 0; k < n; k++) {
        uint32_t i = start + k; if (i >= n) i -= n;
        uint32_t z = 0;
        if (atomic_load(&cxlp_g.ext[i].used) == 0 && atomic_compare_exchange_strong(&cxlp_g.ext[i].used, &z, 1)) return i;
    }
    return CXLP_NIL;
}

int cxlp_obj_begin(cxlp_key_t key, uint32_t klass, uint32_t *handle) {
    if (key == 0 || key == CXLP_KEY_TOMB) return -1;
    uint32_t mask = cxlp_g.meta->nobj - 1, i = (uint32_t)mix(key) & mask;
    for (uint32_t probe = 0; probe <= mask; probe++, i = (i + 1) & mask) {
        cxlp_obj_t *o = &cxlp_g.obj[i];
        uint32_t st = atomic_load(&o->state);
        if (st == OBJ_EMPTY || st == OBJ_TOMB) {
            if (!atomic_compare_exchange_strong(&o->state, &st, OBJ_CREATING)) { probe--; i = (i - 1) & mask; continue; }
            o->owner = cxlp_g.pid; o->klass = klass;
            atomic_store(&o->head, CXLP_NIL); atomic_store(&o->tail, CXLP_NIL); atomic_store(&o->bytes, 0);
            atomic_store(&o->flags, 0); atomic_store(&o->pins, 0); atomic_store(&o->seq, 0);
            atomic_store(&o->drain_idx, CXLP_NIL); atomic_store(&o->drained, 0); o->chain = 0; o->version = 0;
            atomic_store(&o->gen, 0); atomic_store(&o->superseded, 0); o->drain_whole = 0; o->group = 0;
            atomic_store(&o->key, key);
            /* a new writer of an existing key: the old object's drain stops now (we own the target file) */
            for (uint32_t p2 = 0, j = (uint32_t)mix(key) & mask; p2 <= mask; p2++, j = (j + 1) & mask) {
                cxlp_obj_t *q = &cxlp_g.obj[j]; uint32_t qs = atomic_load(&q->state);
                if (qs == OBJ_EMPTY) break;
                if (j != i && qs == OBJ_COMMITTED && atomic_load(&q->key) == key) atomic_store(&q->superseded, 1);
            }
            *handle = i; return 0;
        }
    }
    return -1;
}

int cxlp_obj_append(uint32_t h, const cxlp_res_t *r) {
    cxlp_obj_t *o = &cxlp_g.obj[h];
    uint32_t e = ext_alloc(); if (e == CXLP_NIL) return -1;
    cxlp_ext_t *x = &cxlp_g.ext[e];
    x->dev = (uint32_t)r->dev; x->seg = r->seg; x->off = r->off; x->len = r->len; atomic_store(&x->next, CXLP_NIL);
    x->obj = h; x->obj_off = atomic_load(&o->bytes); atomic_store(&x->drain_state, 0); atomic_store(&x->rd_cur, 0); atomic_store(&x->rd_prev, 0); atomic_store(&x->rd_bucket, 0); atomic_store(&x->queued, 0);
    atomic_store(&x->sh_seg, CXLP_NIL); atomic_store(&x->sh_hits, 0); atomic_store(&x->sh_last_ms, 0);
    uint32_t tail = atomic_load(&o->tail);
    if (tail == CXLP_NIL) atomic_store(&o->head, e); else atomic_store(&cxlp_g.ext[tail].next, e);
    atomic_store(&o->tail, e); atomic_fetch_add(&o->bytes, r->len);
    return 0;
}

int cxlp_obj_set_flags(uint32_t h, uint32_t flags) { atomic_store(&cxlp_g.obj[h].flags, flags); return 0; }
int cxlp_obj_set_group(uint32_t h, uint32_t group) { cxlp_g.obj[h].group = group; return 0; }

int cxlp_obj_commit(uint32_t h) {
    cxlp_obj_t *o = &cxlp_g.obj[h]; cxlp_key_t key = atomic_load(&o->key);
    atomic_store(&o->gen, atomic_fetch_add(&cxlp_g.meta->obj_gen, 1) + 1);       /* before it becomes visible */
    uint32_t st = OBJ_CREATING;
    if (!atomic_compare_exchange_strong(&o->state, &st, OBJ_COMMITTED)) return -1;
    /* this is THE object of its key now: older committed objects under the same key go away
     * (pinned ones stay flagged and are reaped once their readers are gone) */
    uint32_t mask = cxlp_g.meta->nobj - 1;
    for (uint32_t p = 0, j = (uint32_t)mix(key) & mask; p <= mask; p++, j = (j + 1) & mask) {
        cxlp_obj_t *q = &cxlp_g.obj[j]; uint32_t qs = atomic_load(&q->state);
        if (qs == OBJ_EMPTY) break;
        if (j != h && qs == OBJ_COMMITTED && atomic_load(&q->key) == key && atomic_load(&q->gen) < atomic_load(&o->gen)) { atomic_store(&q->superseded, 1); cxlp_obj_release_slot(q); }
    }
    return 0;
}

static cxlp_obj_t *find(cxlp_key_t key) {
    uint32_t mask = cxlp_g.meta->nobj - 1, i = (uint32_t)mix(key) & mask; cxlp_obj_t *best = NULL; uint64_t bg = 0;
    for (uint32_t probe = 0; probe <= mask; probe++, i = (i + 1) & mask) {
        cxlp_obj_t *o = &cxlp_g.obj[i];
        uint32_t st = atomic_load(&o->state);
        if (st == OBJ_EMPTY) break;                           /* never used: end of the probe chain */
        if (st == OBJ_COMMITTED && atomic_load(&o->key) == key) { uint64_t g = atomic_load(&o->gen); if (!best || g > bg) { best = o; bg = g; } }
    }
    return best;                                              /* the newest committed object under this key */
}

int cxlp_obj_lookup(cxlp_key_t key, cxlp_res_t *ext, int max, uint64_t *bytes) {
    cxlp_obj_t *o = find(key); if (!o) return -1;
    int n = 0;
    for (uint32_t e = atomic_load(&o->head); e != CXLP_NIL; e = atomic_load(&cxlp_g.ext[e].next), n++) {
        if (n < max) { cxlp_ext_t *x = &cxlp_g.ext[e]; uint32_t ss = atomic_load(&x->sh_seg);
            ext[n] = ss != CXLP_NIL ? (cxlp_res_t){ (char *)cxlp_seg_ptr((int)x->sh_dev, ss) + x->sh_off, (int)x->sh_dev, ss, x->sh_off, x->len, 0 }
                                    : (cxlp_res_t){ (char *)cxlp_seg_ptr((int)x->dev, x->seg) + x->off, (int)x->dev, x->seg, x->off, x->len, 0 }; }
    }
    if (bytes) *bytes = atomic_load(&o->bytes);
    return n;
}

static void drop_extents(cxlp_obj_t *o, int fix_live) {
    for (uint32_t e = atomic_load(&o->head); e != CXLP_NIL;) {
        cxlp_ext_t *x = &cxlp_g.ext[e]; uint32_t nx = atomic_load(&x->next);
        if (fix_live) { cxlp_res_t r = { NULL, (int)x->dev, x->seg, x->off, x->len, 0 }; cxlp_release(&r); }
        uint32_t ss = atomic_exchange(&x->sh_seg, CXLP_NIL);
        if (ss != CXLP_NIL) { if (fix_live) { cxlp_res_t r = { NULL, (int)x->sh_dev, ss, x->sh_off, x->len, 0 }; cxlp_release(&r); } atomic_fetch_sub(&POL->shadow_bytes, x->len); }
        atomic_store(&x->used, 0); e = nx;
    }
    atomic_store(&o->head, CXLP_NIL); atomic_store(&o->tail, CXLP_NIL);
    uint32_t di = atomic_exchange(&o->drain_idx, CXLP_NIL);
    if (di != CXLP_NIL) atomic_store(&cxlp_g.meta->drain[di].used, 0);
}

int cxlp_obj_release_slot(cxlp_obj_t *o) {
    if (atomic_load(&o->pins)) return -2;                     /* readers still hold pointers: retry later */
    uint32_t st = OBJ_COMMITTED;
    if (!atomic_compare_exchange_strong(&o->state, &st, OBJ_CREATING)) return -1;   /* one releaser wins */
    drop_extents(o, 1);
    atomic_store(&o->key, CXLP_KEY_TOMB); atomic_store(&o->state, OBJ_TOMB);
    return 0;
}

int cxlp_obj_release(cxlp_key_t key) {
    cxlp_obj_t *o = find(key); if (!o) return -1;
    return cxlp_obj_release_slot(o);
}

/* Superseded objects that were pinned when their successor committed. Also un-supersede an object
 * whose successor never arrived (its writer died): the old object is THE object again. */
int cxlp_obj_reap_superseded(void) {
    int n = 0; uint32_t mask = cxlp_g.meta->nobj - 1;
    for (uint32_t i = 0; i <= mask; i++) {
        cxlp_obj_t *o = &cxlp_g.obj[i];
        if (atomic_load(&o->state) != OBJ_COMMITTED || !atomic_load(&o->superseded)) continue;
        cxlp_key_t key = atomic_load(&o->key); int newer = 0, writer = 0;
        for (uint32_t p = 0, j = (uint32_t)mix(key) & mask; p <= mask; p++, j = (j + 1) & mask) {
            cxlp_obj_t *q = &cxlp_g.obj[j]; uint32_t qs = atomic_load(&q->state);
            if (qs == OBJ_EMPTY) break;
            if (q == o || atomic_load(&q->key) != key) continue;
            if (qs == OBJ_COMMITTED && atomic_load(&q->gen) > atomic_load(&o->gen)) newer = 1;
            if (qs == OBJ_CREATING) writer = 1;
        }
        if (newer) { if (cxlp_obj_release_slot(o) == 0) n++; }
        else if (!writer) atomic_store(&o->superseded, 0);
    }
    return n;
}

int cxlp_put(cxlp_key_t key, uint32_t klass, const void *buf, size_t len) { return cxlp_put_version(key, klass, buf, len, NULL, 0, 0, 0); }
int cxlp_put_drain(cxlp_key_t key, uint32_t klass, const void *buf, size_t len, const char *path, uint32_t wait_ms) { return cxlp_put_version(key, klass, buf, len, path, wait_ms, 0, 0); }
int cxlp_obj_set_version(uint32_t h, uint64_t chain, uint64_t version) { cxlp_g.obj[h].chain = chain; cxlp_g.obj[h].version = version; return 0; }

int cxlp_put_version(cxlp_key_t key, uint32_t klass, const void *buf, size_t len, const char *path, uint32_t wait_ms, uint64_t chain, uint64_t version) {
    uint32_t h; if (cxlp_obj_begin(key, klass, &h)) return -1;
    cxlp_obj_set_version(h, chain, version); if (chain) cxlp_obj_set_flags(h, CXLP_OBJ_NOPROMOTE);   /* checkpoints are never promoted */
    if (path && cxlp_obj_set_drain_whole(h, path)) { atomic_store(&cxlp_g.obj[h].key, CXLP_KEY_TOMB); atomic_store(&cxlp_g.obj[h].state, OBJ_TOMB); return -1; }
    cxlp_hints_t hint = { klass, path ? 4096u : 0u, -1, 0, wait_ms };
    for (size_t done = 0; done < len;) {
        size_t n = len - done < CXLP_SEG_BYTES ? len - done : CXLP_SEG_BYTES; cxlp_res_t r;
        if (cxlp_reserve(n, &hint, &r)) goto fail;
        cxlp_copy_to(&r, 0, (const char *)buf + done, n); cxlp_commit(&r);
        if (cxlp_obj_append(h, &r)) { cxlp_abort(&r); goto fail; }
        done += n;
    }
    return cxlp_obj_commit(h);
fail:
    drop_extents(&cxlp_g.obj[h], 1);
    atomic_store(&cxlp_g.obj[h].key, CXLP_KEY_TOMB); atomic_store(&cxlp_g.obj[h].state, OBJ_TOMB);
    return -1;
}

int64_t cxlp_get(cxlp_key_t key, void *buf, size_t cap) {
    cxlp_res_t ext[64]; uint64_t bytes; cxlp_pin_t pin; int n = cxlp_obj_pin(key, CXLP_CONSUMER_CPU, 0, UINT64_MAX, ext, 64, &bytes, &pin);
    if (n < 0) return -1;
    if (n > 64 || bytes > cap) { cxlp_obj_unpin(&pin); return -1; }
    size_t off = 0; for (int i = 0; i < n; i++) { memcpy((char *)buf + off, ext[i].ptr, ext[i].len); off += ext[i].len; }
    cxlp_obj_unpin(&pin);
    return (int64_t)bytes;
}

cxlp_obj_t *cxlp_obj_find(cxlp_key_t key) { return find(key); }

static int dead(uint32_t pid) { return pid && pid != cxlp_g.pid && kill((pid_t)pid, 0) == -1 && errno == ESRCH; }

int cxlp_cleanup_dead(void) {
    cxlp_meta_t *m = cxlp_g.meta; int dropped = 0;
    /* 1. objects a dead writer never committed are garbage */
    for (uint32_t i = 0; i < m->nobj; i++) {
        cxlp_obj_t *o = &cxlp_g.obj[i];
        if (atomic_load(&o->state) == OBJ_CREATING && dead(o->owner)) {
            drop_extents(o, 0);                              /* live bytes are recomputed below */
            atomic_store(&o->key, CXLP_KEY_TOMB); atomic_store(&o->state, OBJ_TOMB); dropped++;
        }
    }
    cxlp_obj_reap_superseded();                                /* an object superseded by a writer that died is THE object again */
    /* 2. segments of dead writers: true live bytes = extents of committed objects inside them;
     *    everything else (reserved, never committed) disappears with the recount */
    uint64_t *live = calloc(m->nseg_total, sizeof *live); int any = 0;
    for (uint32_t d = 0; d < m->ndev; d++) for (uint32_t s = 0; s < m->dev[d].nseg; s++) {
        uint32_t st = atomic_load(&cxlp_g.seg[m->dev[d].first + s].st);
        if ((ST_STATE(st) == CXLP_SEG_OPEN || ST_STATE(st) == CXLP_SEG_SEALED) && dead(cxlp_seg_owner((int)d, s))) any = 1;
    }
    if (any) {
        for (uint32_t i = 0; i < m->nobj; i++) {
            cxlp_obj_t *o = &cxlp_g.obj[i]; if (atomic_load(&o->state) != OBJ_COMMITTED) continue;
            for (uint32_t e = atomic_load(&o->head); e != CXLP_NIL; e = atomic_load(&cxlp_g.ext[e].next))
                live[m->dev[cxlp_g.ext[e].dev].first + cxlp_g.ext[e].seg] += cxlp_g.ext[e].len;
        }
        for (uint32_t d = 0; d < m->ndev; d++) for (uint32_t s = 0; s < m->dev[d].nseg; s++) {
            uint32_t st = atomic_load(&cxlp_g.seg[m->dev[d].first + s].st);
            if ((ST_STATE(st) == CXLP_SEG_OPEN || ST_STATE(st) == CXLP_SEG_SEALED) && dead(cxlp_seg_owner((int)d, s)))
                cxlp_seg_force_seal((int)d, s, live[m->dev[d].first + s]);
        }
    }
    free(live);
    return dropped;
}

/* Parallel put for large CPU buffers (the PyTorch plugin's CPU tensors, 2026-10-06): the buffer is cut into segment-sized
 * chunks, `nthreads` pinned threads reserve / NT-copy / commit their chunks (placement per chunk: the loan applies), the
 * extents are appended in order, and the object drains into `path` at `file_off` (NULL path = never drained). */
typedef struct { const char *buf; size_t len; uint32_t klass, stream, align; int cpu, id, nthreads, err; cxlp_res_t *res; size_t nchunks; } putpar_t;
static void *putpar_thread(void *a) {
    putpar_t *w = a;
    if (w->cpu >= 0) { cpu_set_t cs; CPU_ZERO(&cs); CPU_SET(w->cpu, &cs); pthread_setaffinity_np(pthread_self(), sizeof cs, &cs); }
    cxlp_hints_t h = { w->klass, w->align, -1, w->stream, 20000 };
    for (size_t c = (size_t)w->id; c < w->nchunks; c += (size_t)w->nthreads) {
        size_t off = c * CXLP_SEG_BYTES, n = w->len - off < CXLP_SEG_BYTES ? w->len - off : CXLP_SEG_BYTES;
        if (cxlp_reserve(n, &h, &w->res[c])) { w->err = 1; break; }
        cxlp_copy_to(&w->res[c], 0, w->buf + off, n); cxlp_commit(&w->res[c]);
    }
    cxlp_thread_seal(); return NULL;
}
int cxlp_put_par(cxlp_key_t key, uint32_t klass, const void *buf, size_t len, const char *path, uint64_t file_off, uint32_t stream, uint64_t chain, uint64_t version, int nthreads, const int *cpus) {
    if (nthreads < 1) nthreads = 1; if (nthreads > 64) nthreads = 64;
    uint32_t h; if (cxlp_obj_begin(key, klass, &h)) return -1;
    cxlp_obj_set_version(h, chain, version); if (chain) cxlp_obj_set_flags(h, CXLP_OBJ_NOPROMOTE);
    if (path && cxlp_obj_set_drain(h, path, file_off)) { atomic_store(&cxlp_g.obj[h].key, CXLP_KEY_TOMB); atomic_store(&cxlp_g.obj[h].state, OBJ_TOMB); return -1; }
    size_t nchunks = (len + CXLP_SEG_BYTES - 1) / CXLP_SEG_BYTES; if (!nchunks) nchunks = 0;
    cxlp_res_t *res = calloc(nchunks ? nchunks : 1, sizeof *res); putpar_t w[64]; pthread_t th[64]; int err = 0;
    for (int i = 0; i < nthreads; i++) { w[i] = (putpar_t){ buf, len, klass, stream, path ? 4096u : 0u, cpus ? cpus[i] : -1, i, nthreads, 0, res, nchunks }; pthread_create(&th[i], NULL, putpar_thread, &w[i]); }
    for (int i = 0; i < nthreads; i++) { pthread_join(th[i], NULL); err |= w[i].err; }
    for (size_t c = 0; c < nchunks && !err; c++) if (cxlp_obj_append(h, &res[c])) err = 1;
    if (err) { for (size_t c = 0; c < nchunks; c++) if (res[c].len) cxlp_release(&res[c]); free(res); drop_extents(&cxlp_g.obj[h], 0); atomic_store(&cxlp_g.obj[h].key, CXLP_KEY_TOMB); atomic_store(&cxlp_g.obj[h].state, OBJ_TOMB); return -1; }
    free(res); return cxlp_obj_commit(h);
}
