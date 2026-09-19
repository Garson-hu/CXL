/* Component A, part 2: reserve / commit / release on per-thread append-only log segments (A3). */
#define _GNU_SOURCE
#include "internal.h"
#include <immintrin.h>
#include <pthread.h>
#include <stdlib.h>
#include <string.h>

typedef struct { uint32_t seg, off; } open_t;
typedef struct { open_t o[CXLP_MAX_DEVS][CXLP_NKLASS]; int init; } tls_t;
static __thread tls_t tls;
static pthread_key_t key; static pthread_once_t once = PTHREAD_ONCE_INIT;
static cxlp_pick_fn pick_fn;

static cxlp_seg_t *segp(int dev, uint32_t seg) { return cxlp_g.seg + cxlp_g.meta->dev[dev].first + seg; }
uint64_t cxlp_seg_live(int dev, uint32_t seg) { return atomic_load(&segp(dev, seg)->live); }

/* A SEALED segment with no live bytes goes back to the pool. Sealer and releaser may race here;
 * the compare-and-swap on the state lets exactly one of them free it. */
static void try_free(int dev, uint32_t seg) {
    cxlp_seg_t *s = segp(dev, seg);
    uint32_t cur = atomic_load(&s->st);
    if (ST_STATE(cur) != CXLP_SEG_SEALED || atomic_load(&s->live) != 0) return;
    atomic_store(&s->owner, 0);
    if (atomic_compare_exchange_strong(&s->st, &cur, ST_MAKE(ST_GEN(cur), CXLP_SEG_FREE)))
        atomic_fetch_add(&cxlp_g.meta->dev[dev].nfree, 1);
}

static void seal(int dev, open_t *o) {
    if (o->seg == CXLP_NO_SEG) return;
    cxlp_seg_t *s = segp(dev, o->seg);
    uint32_t cur = atomic_load(&s->st);
    if (ST_STATE(cur) == CXLP_SEG_OPEN) atomic_compare_exchange_strong(&s->st, &cur, ST_MAKE(ST_GEN(cur), CXLP_SEG_SEALED));
    try_free(dev, o->seg);
    o->seg = CXLP_NO_SEG; o->off = 0;
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
    tls.init = 1;
}

static int default_pick(uint32_t klass) {
    (void)klass;
    int fallback = -1;
    for (uint32_t d = 0; d < cxlp_g.meta->ndev; d++) {
        if (cxlp_dev_free((int)d) == 0) continue;
        if (cxlp_g.meta->dev[d].kind == CXLP_DEV_CXL) return (int)d;
        if (fallback < 0) fallback = (int)d;
    }
    return fallback;
}
void cxlp_set_pick(cxlp_pick_fn fn) { pick_fn = fn; }

int cxlp_reserve(size_t len, const cxlp_hints_t *h, cxlp_res_t *out) {
    static const cxlp_hints_t dflt = { 0, 0, -1 };
    if (!h) h = &dflt;
    if (len == 0 || len > CXLP_SEG_BYTES || h->klass >= CXLP_NKLASS) return -1;
    if (!tls.init) tls_init();
    uint32_t align = h->align ? h->align : 64;
    /* Placement is consulted when this thread needs a NEW segment; inside an open segment the
     * thread keeps appending. A forced device (hints.dev >= 0) bypasses the policy. */
    int dev = h->dev;
    if (dev < 0) {
        /* continue in an open segment that still has room, whatever device it is on */
        for (uint32_t d = 0; d < cxlp_g.meta->ndev && dev < 0; d++) {
            open_t *o = &tls.o[d][h->klass];
            if (o->seg != CXLP_NO_SEG && ((o->off + align - 1) & ~(align - 1)) + len <= CXLP_SEG_BYTES) dev = (int)d;
        }
        if (dev < 0) dev = pick_fn ? pick_fn(h->klass) : default_pick(h->klass);
        if (dev < 0) return -1;
    }
    open_t *o = &tls.o[dev][h->klass];
    uint32_t off = (o->off + align - 1) & ~(align - 1);
    if (o->seg == CXLP_NO_SEG || off + len > CXLP_SEG_BYTES) {
        seal(dev, o);
        uint32_t s = cxlp_seg_claim(dev, CXLP_SEG_OPEN);
        if (s == CXLP_NO_SEG) return -1;
        o->seg = s; off = 0;
    }
    /* reserved bytes count as live at once, so a sealed segment is never freed under a writer */
    atomic_fetch_add(&segp(dev, o->seg)->live, len);
    *out = (cxlp_res_t){ (char *)cxlp_seg_ptr(dev, o->seg) + off, dev, o->seg, off, (uint32_t)len };
    o->off = off + (uint32_t)len;
    return 0;
}

void cxlp_commit(const cxlp_res_t *r) { (void)r; _mm_sfence(); }

static void drop(const cxlp_res_t *r) {
    atomic_fetch_sub(&segp(r->dev, r->seg)->live, r->len);
    try_free(r->dev, r->seg);
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
