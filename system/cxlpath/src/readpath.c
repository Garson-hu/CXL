/* Component C: read in place, count reads, promote by break-even (C1, C2). */
#define _GNU_SOURCE
#include "internal.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

uint32_t cxlp_k_compute(double t_copy, double t_cxl, double t_dram, double w, double pressure) {
    /* reading in place costs (t_cxl - t_dram) extra per read; promoting costs one copy, made more
     * expensive by the harm it does to other DRAM readers right now. Rent-or-buy: promote at the
     * read where the rent paid equals the price -> at most twice the optimal cost. */
    if (t_dram <= 0 || t_cxl - t_dram < 0.05 * t_dram) return 0;          /* < 5% penalty: never worth a copy */
    if (pressure < 0) pressure = 0;
    double k = ceil(t_copy * (1.0 + w * pressure) / (t_cxl - t_dram) - 1e-9);
    return k < 1 ? 1 : (k > 1e6 ? 1000000u : (uint32_t)k);
}

static void count_read(uint32_t e, cxlp_consumer_t who) {
    cxlp_ext_t *x = &cxlp_g.ext[e];
    uint32_t bms = atomic_load(&POL->read_bucket_ms); if (!bms) bms = 300000;
    uint32_t b = (uint32_t)(cxlp_now_ns() / 1000000ull / bms) + 1, cur = atomic_load(&x->rd_bucket);
    if (cur != b) {                                            /* roll the window (benign races: counts are hints) */
        atomic_store(&x->rd_prev, cur + 1 == b ? atomic_load(&x->rd_cur) : 0);
        atomic_store(&x->rd_cur, 0); atomic_store(&x->rd_bucket, b);
    }
    uint32_t reads = atomic_fetch_add(&x->rd_cur, 1) + 1 + atomic_load(&x->rd_prev);
    uint32_t k = atomic_load(&POL->k_read[who]);
    if (!k || reads < k || cxlp_g.meta->dev[x->dev].kind != CXLP_DEV_CXL) return;
    if (atomic_load(&cxlp_g.obj[x->obj].flags) & CXLP_OBJ_NOPROMOTE) return;
    uint32_t z = 0; if (!atomic_compare_exchange_strong(&x->queued, &z, 1)) return;
    uint32_t slot = atomic_fetch_add(&POL->promo_tail, 1) % CXLP_PROMO_RING;
    atomic_store(&POL->promo_ring[slot], e + 1);
}

int cxlp_obj_pin(cxlp_key_t key, cxlp_consumer_t who, uint64_t off, uint64_t len, cxlp_res_t *ext, int max, uint64_t *bytes, cxlp_pin_t *pin) {
    cxlp_obj_t *o = cxlp_obj_find(key); if (!o) return -1;
    atomic_fetch_add(&o->pins, 1);                             /* pin FIRST: a relocation now keeps the old copy alive for us */
    if (atomic_load(&o->state) != OBJ_COMMITTED || atomic_load(&o->key) != key) { atomic_fetch_sub(&o->pins, 1); return -1; }
    uint64_t end = len > UINT64_MAX - off ? UINT64_MAX : off + len; int n;
    uint32_t hit[64]; int nhit;
    for (;;) {
        uint32_t s0 = atomic_load(&o->seq); if (s0 & 1) continue;
        n = 0; nhit = 0; uint64_t pos = 0;
        for (uint32_t e = atomic_load(&o->head); e != CXLP_NIL; e = atomic_load(&cxlp_g.ext[e].next)) {
            cxlp_ext_t *x = &cxlp_g.ext[e]; uint64_t a = pos, b = pos + x->len; pos = b;
            if (b <= off || a >= end) continue;
            if (n < max) ext[n] = (cxlp_res_t){ (char *)cxlp_seg_ptr((int)x->dev, x->seg) + x->off, (int)x->dev, x->seg, x->off, x->len, 0 };
            if (nhit < 64) hit[nhit++] = e;
            n++;
        }
        if (atomic_load(&o->seq) == s0) break;
    }
    for (int i = 0; i < nhit; i++) count_read(hit[i], who);
    if (bytes) *bytes = atomic_load(&o->bytes);
    if (pin) { pin->slot = (uint32_t)(o - cxlp_g.obj); pin->gen = atomic_load(&o->gen); }
    return n;
}

int cxlp_obj_unpin(const cxlp_pin_t *pin) {
    if (!pin || pin->slot >= cxlp_g.meta->nobj) return -1;
    cxlp_obj_t *o = &cxlp_g.obj[pin->slot];                   /* the object that was pinned, even if its key was re-written since */
    if (atomic_load(&o->gen) != pin->gen || atomic_load(&o->pins) == 0) return -1;
    atomic_fetch_sub(&o->pins, 1); return 0;
}

/* old CXL copies wait here until no reader pins their object */
typedef struct limbo { cxlp_res_t old; uint32_t obj; struct limbo *next; } limbo_t;
static limbo_t *limbo;

static int dram_dev(void) { int best = -1; uint32_t bf = 0; for (uint32_t d = 0; d < cxlp_g.meta->ndev; d++) if (cxlp_g.meta->dev[d].kind == CXLP_DEV_DRAM && cxlp_dev_free((int)d) > bf) { bf = cxlp_dev_free((int)d); best = (int)d; } return best; }

int cxlp_promote_pending(int dram_ok) {
    int moved = 0;
    for (limbo_t **pp = &limbo; *pp;) {                         /* finish deferred releases */
        limbo_t *l = *pp;
        if (atomic_load(&cxlp_g.obj[l->obj].pins) == 0) { cxlp_release(&l->old); *pp = l->next; free(l); } else pp = &l->next;
    }
    for (uint32_t i = 0; i < CXLP_PROMO_RING; i++) {
        uint32_t v = atomic_load(&POL->promo_ring[i]); if (!v) continue;
        if (!dram_ok) break;                                   /* the copy is itself a DRAM write stream: wait for calm */
        int dd = dram_dev(); if (dd < 0) break;                /* DRAM quota (pool) exhausted */
        atomic_store(&POL->promo_ring[i], 0);
        cxlp_ext_t *x = &cxlp_g.ext[v - 1]; cxlp_obj_t *o = &cxlp_g.obj[x->obj];
        if (!atomic_load(&x->used) || atomic_load(&o->state) != OBJ_COMMITTED || cxlp_g.meta->dev[x->dev].kind != CXLP_DEV_CXL) { atomic_store(&x->queued, 0); continue; }
        cxlp_hints_t h = { o->klass, 4096, dd, 0, 0 }; cxlp_res_t nr;
        if (cxlp_reserve(x->len, &h, &nr)) { atomic_store(&x->queued, 0); continue; }
        cxlp_res_t old = { (char *)cxlp_seg_ptr((int)x->dev, x->seg) + x->off, (int)x->dev, x->seg, x->off, x->len, 0 };
        cxlp_copy_in(nr.ptr, old.ptr, x->len); cxlp_commit(&nr);
        atomic_fetch_add(&o->seq, 1);                          /* relocate under the seqlock */
        x->dev = (uint32_t)nr.dev; x->seg = nr.seg; x->off = nr.off;
        atomic_fetch_add(&o->seq, 1);
        limbo_t *l = malloc(sizeof *l); *l = (limbo_t){ old, x->obj, limbo }; limbo = l;
        atomic_fetch_add(&POL->promoted_bytes, x->len); atomic_fetch_add(&POL->promoted_extents, 1);
        atomic_store(&x->queued, 0); moved++;
    }
    cxlp_thread_seal();
    return moved;
}
