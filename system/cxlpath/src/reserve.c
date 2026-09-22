/* Component A, part 2: reserve / commit / release on per-thread append-only log segments (A3).
 * Placement of each NEW segment comes from the published policy (Component B, policy.c). */
#define _GNU_SOURCE
#include "internal.h"
#include <immintrin.h>
#include <pthread.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/syscall.h>

typedef struct { uint32_t seg, off; } open_t;
typedef struct { open_t o[CXLP_MAX_DEVS][CXLP_NKLASS]; uint32_t nclaim; int init; } tls_t;
static __thread tls_t tls;
static pthread_key_t key; static pthread_once_t once = PTHREAD_ONCE_INIT;

static cxlp_seg_t *segp(int dev, uint32_t seg) { return cxlp_g.seg + cxlp_g.meta->dev[dev].first + seg; }
uint64_t cxlp_seg_live(int dev, uint32_t seg) { return atomic_load(&segp(dev, seg)->live); }

static void seal(int dev, open_t *o) {
    if (o->seg == CXLP_NO_SEG) return;
    cxlp_seg_t *s = segp(dev, o->seg);
    uint32_t cur = atomic_load(&s->st);
    if (ST_STATE(cur) == CXLP_SEG_OPEN) atomic_compare_exchange_strong(&s->st, &cur, ST_MAKE(ST_GEN(cur), CXLP_SEG_SEALED));
    cxlp_seg_to_free(dev, o->seg, 1);      /* sealed and already empty: back to the pool */
    o->seg = CXLP_NO_SEG; o->off = 0;
}

/* Crash cleanup: the owner is gone; set the true live byte count and seal. */
void cxlp_seg_force_seal(int dev, uint32_t seg, uint64_t live) {
    cxlp_seg_t *s = segp(dev, seg);
    atomic_store(&s->live, live);
    uint32_t cur = atomic_load(&s->st);
    if (ST_STATE(cur) == CXLP_SEG_OPEN) atomic_compare_exchange_strong(&s->st, &cur, ST_MAKE(ST_GEN(cur), CXLP_SEG_SEALED));
    cxlp_seg_to_free(dev, seg, 1);
}

void cxlp_thread_seal(void) {
    if (!tls.init || !cxlp_g.meta) return;
    for (uint32_t d = 0; d < cxlp_g.meta->ndev; d++) for (int k = 0; k < CXLP_NKLASS; k++) seal((int)d, &tls.o[d][k]);
}
static void tls_dtor(void *p) { (void)p; cxlp_thread_seal(); }
static void mkkey(void) { pthread_key_create(&key, tls_dtor); }
static void tls_init(void) {
    pthread_once(&once, mkkey); pthread_setspecific(key, &tls);
    for (int d = 0; d < CXLP_MAX_DEVS; d++) for (int k = 0; k < CXLP_NKLASS; k++) tls.o[d][k] = (open_t){ CXLP_NO_SEG, 0 };
    tls.nclaim = (uint32_t)syscall(SYS_gettid) * 2654435761u >> 28;   /* threads start at different points of the 16-cycle */
    tls.init = 1;
}

int cxlp_reserve(size_t len, const cxlp_hints_t *h, cxlp_res_t *out) {
    static const cxlp_hints_t dflt = { 0, 0, -1, 0, 0 };
    if (!h) h = &dflt;
    if (len == 0 || len > CXLP_SEG_BYTES || h->klass >= CXLP_NKLASS) return -1;
    if (!tls.init) tls_init();
    uint32_t align = h->align ? h->align : 64;
    uint64_t deadline = h->wait_ms ? cxlp_now_ns() + (uint64_t)h->wait_ms * 1000000ull : 0;
    atomic_fetch_add(&POL->reserve_seq, 1);
    if (atomic_load(&POL->pace_on[h->stream % CXLP_NSTREAM])) cxlp_policy_pace_wait(h->stream, len);   /* last resort: paced stream */
    for (;;) {
        uint32_t ev = atomic_load(&POL->free_event);
        /* Placement is consulted when this thread needs a NEW segment; inside an open segment
         * the thread keeps appending. A forced device (hints.dev >= 0) bypasses the policy. */
        int dev = h->dev;
        if (dev < 0)
            for (uint32_t d = 0; d < cxlp_g.meta->ndev && dev < 0; d++) {
                open_t *o = &tls.o[d][h->klass];
                if (o->seg != CXLP_NO_SEG && ((o->off + align - 1) & ~(align - 1)) + len <= CXLP_SEG_BYTES) dev = (int)d;
            }
        if (dev < 0) dev = cxlp_policy_pick(h->stream, tls.nclaim);
        if (dev >= 0) {
            open_t *o = &tls.o[dev][h->klass];
            uint32_t off = (o->off + align - 1) & ~(align - 1);
            int have = (o->seg != CXLP_NO_SEG && off + len <= CXLP_SEG_BYTES);
            if (!have) {
                seal(dev, o);
                uint32_t s = cxlp_seg_claim(dev, CXLP_SEG_OPEN);
                if (s != CXLP_NO_SEG) { o->seg = s; off = 0; tls.nclaim++; have = 1; }
            }
            if (have) {
                /* reserved bytes count as live at once, so a sealed segment is never freed under a writer */
                atomic_fetch_add(&segp(dev, o->seg)->live, len);
                *out = (cxlp_res_t){ (char *)cxlp_seg_ptr(dev, o->seg) + off, dev, o->seg, off, (uint32_t)len, h->stream % CXLP_NSTREAM };
                o->off = off + (uint32_t)len;
                return 0;
            }
        }
        /* no space anywhere the policy allows: back-pressure */
        if (!deadline) return -1;
        uint64_t now = cxlp_now_ns(); if (now >= deadline) return -1;
        uint64_t left_ms = (deadline - now) / 1000000ull + 1;
        cxlp_policy_wait_free(ev, (int)(left_ms < 50 ? left_ms : 50));
    }
}

void cxlp_commit(const cxlp_res_t *r) { (void)r; _mm_sfence(); }

void cxlp_shrink(cxlp_res_t *r, uint32_t new_len) {
    if (new_len >= r->len) return;
    atomic_fetch_sub(&segp(r->dev, r->seg)->live, r->len - new_len);
    for (int k = 0; k < CXLP_NKLASS; k++) {                    /* still the tail of this thread's open segment: reuse the space */
        open_t *o = &tls.o[r->dev][k];
        if (tls.init && o->seg == r->seg && o->off == r->off + r->len) o->off = r->off + new_len;
    }
    r->len = new_len;
}

static void drop(const cxlp_res_t *r) {
    atomic_fetch_sub(&segp(r->dev, r->seg)->live, r->len);
    cxlp_seg_to_free(r->dev, r->seg, 1);
}
void cxlp_abort(const cxlp_res_t *r)   { drop(r); }
void cxlp_release(const cxlp_res_t *r) { drop(r); }

/* NT-store copy: plain stores to CXL would first READ the destination lines over the link. */
void cxlp_copy_in(void *dst, const void *src, size_t n) {
    char *d = dst; const char *s = src;
    size_t head = (32 - ((uintptr_t)d & 31)) & 31;
    if (head > n) head = n;
    memcpy(d, s, head); d += head; s += head; n -= head;
    for (; n >= 32; n -= 32, d += 32, s += 32)
        _mm256_stream_si256((__m256i *)d, _mm256_loadu_si256((const __m256i *)s));
    memcpy(d, s, n);
    _mm_sfence();
}
