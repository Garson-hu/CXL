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
    uint32_t k = atomic_load(&POL->k_read[who]), flags = atomic_load(&cxlp_g.obj[x->obj].flags);
    if (!k) return;                                            /* DRAM is not faster for this consumer (GPU on c28): never */
    if (flags & CXLP_OBJ_LATENCY) { uint32_t kl = atomic_load(&POL->k_read_latency); if (kl && kl < k) k = kl; }   /* serving hits: the next hit matters more than the copy */
    if (reads < k || cxlp_g.meta->dev[x->dev].kind != CXLP_DEV_CXL || atomic_load(&x->sh_seg) != CXLP_NIL) return;
    if (flags & CXLP_OBJ_NOPROMOTE) return;
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
            uint32_t ss = atomic_load(&x->sh_seg);
            if (ss != CXLP_NIL) {                                /* served from the DRAM shadow */
                if (n < max) ext[n] = (cxlp_res_t){ (char *)cxlp_seg_ptr((int)x->sh_dev, ss) + x->sh_off, (int)x->sh_dev, ss, x->sh_off, x->len, 0 };
                atomic_store(&x->sh_last_ms, cxlp_now_ns() / 1000000ull); atomic_fetch_add(&x->sh_hits, 1); atomic_fetch_add(&POL->shadow_hits, 1);
            } else {
                if (n < max) ext[n] = (cxlp_res_t){ (char *)cxlp_seg_ptr((int)x->dev, x->seg) + x->off, (int)x->dev, x->seg, x->off, x->len, 0 };
                if (nhit < 64) hit[nhit++] = e;
            }
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

static int dram_dev(void) { int best = -1; uint32_t bf = 0; for (uint32_t d = 0; d < cxlp_g.meta->ndev; d++) if (cxlp_g.meta->dev[d].kind == CXLP_DEV_DRAM && cxlp_dev_free((int)d) > bf) { bf = cxlp_dev_free((int)d); best = (int)d; } return best; }

static uint64_t shadow_cap(void) {
    uint64_t cap = atomic_load(&POL->shadow_cap);
    if (cap) return cap;
    uint64_t pool = 0; for (uint32_t d = 0; d < cxlp_g.meta->ndev; d++) if (cxlp_g.meta->dev[d].kind == CXLP_DEV_DRAM) pool += (uint64_t)cxlp_g.meta->dev[d].nseg * CXLP_SEG_BYTES;
    return pool / 2;                                           /* default: half the DRAM pool; the loan keeps the other half */
}

/* Drop one object's shadows (caller checked pins == 0). Zero writes: the CXL originals are intact. */
static uint64_t drop_shadows(cxlp_obj_t *o) {
    uint64_t dropped = 0;
    atomic_fetch_add(&o->seq, 1);
    for (uint32_t e = atomic_load(&o->head); e != CXLP_NIL; e = atomic_load(&cxlp_g.ext[e].next)) {
        cxlp_ext_t *x = &cxlp_g.ext[e]; uint32_t ss = atomic_exchange(&x->sh_seg, CXLP_NIL);
        if (ss == CXLP_NIL) continue;
        cxlp_res_t r = { NULL, (int)x->sh_dev, ss, x->sh_off, x->len, 0 }; cxlp_release(&r);
        atomic_store(&x->rd_cur, 0); atomic_store(&x->rd_prev, 0);   /* a dropped shadow needs fresh evidence before it is copied again */
        atomic_fetch_sub(&POL->shadow_bytes, x->len); atomic_fetch_add(&POL->shadow_drops, 1); dropped += x->len;
        if (atomic_load(&x->sh_hits) == 0) atomic_fetch_add(&POL->shadow_drops_unhit, 1);
    }
    atomic_fetch_add(&o->seq, 1);
    return dropped;
}

/* LRU over objects (an object's age = its most recently hit shadow); an object with a group takes its whole group
 * along, because a KV prefix chain is read together and half a chain in DRAM is worth nothing. */
uint64_t cxlp_shadow_trim(uint64_t target) {
    uint64_t dropped = 0;
    while (atomic_load(&POL->shadow_bytes) > target) {
        cxlp_obj_t *victim = NULL; uint64_t oldest = UINT64_MAX;
        for (uint32_t i = 0; i < cxlp_g.meta->nobj; i++) {
            cxlp_obj_t *o = &cxlp_g.obj[i];
            if (atomic_load(&o->state) != OBJ_COMMITTED || atomic_load(&o->pins)) continue;
            uint64_t last = 0; int any = 0;
            for (uint32_t e = atomic_load(&o->head); e != CXLP_NIL; e = atomic_load(&cxlp_g.ext[e].next)) {
                cxlp_ext_t *x = &cxlp_g.ext[e]; if (atomic_load(&x->sh_seg) == CXLP_NIL) continue;
                any = 1; uint64_t t = atomic_load(&x->sh_last_ms); if (t > last) last = t;
            }
            if (any && last < oldest) { oldest = last; victim = o; }
        }
        if (!victim) break;
        uint32_t g = victim->group; dropped += drop_shadows(victim);
        if (g) for (uint32_t i = 0; i < cxlp_g.meta->nobj; i++) {
            cxlp_obj_t *o = &cxlp_g.obj[i];
            if (o != victim && atomic_load(&o->state) == OBJ_COMMITTED && o->group == g && !atomic_load(&o->pins)) dropped += drop_shadows(o);
        }
    }
    return dropped;
}

int cxlp_obj_prefetch(cxlp_key_t key) {
    cxlp_obj_t *o = cxlp_obj_find(key); if (!o || atomic_load(&o->state) != OBJ_COMMITTED) return -1;
    if (atomic_load(&o->flags) & CXLP_OBJ_NOPROMOTE) return 0;
    int n = 0;
    for (uint32_t e = atomic_load(&o->head); e != CXLP_NIL; e = atomic_load(&cxlp_g.ext[e].next)) {
        cxlp_ext_t *x = &cxlp_g.ext[e];
        if (cxlp_g.meta->dev[x->dev].kind != CXLP_DEV_CXL || atomic_load(&x->sh_seg) != CXLP_NIL) continue;
        uint32_t z = 0; if (!atomic_compare_exchange_strong(&x->queued, &z, 1)) continue;
        uint32_t slot = atomic_fetch_add(&POL->promo_tail, 1) % CXLP_PROMO_RING; atomic_store(&POL->promo_ring[slot], e + 1); n++;
    }
    return n;
}

/* Promotion = a DRAM COPY beside the CXL original; readers are switched to it under the object's seqlock. */
int cxlp_promote_pending(int dram_ok) {
    int moved = 0; uint64_t cap = shadow_cap();
    for (uint32_t i = 0; i < CXLP_PROMO_RING; i++) {
        uint32_t v = atomic_load(&POL->promo_ring[i]); if (!v) continue;
        if (!dram_ok) break;                                   /* the copy is itself a DRAM write stream: wait for calm */
        cxlp_ext_t *x = &cxlp_g.ext[v - 1]; cxlp_obj_t *o = &cxlp_g.obj[x->obj];
        if (!atomic_load(&x->used) || atomic_load(&o->state) != OBJ_COMMITTED || cxlp_g.meta->dev[x->dev].kind != CXLP_DEV_CXL || atomic_load(&x->sh_seg) != CXLP_NIL) { atomic_store(&POL->promo_ring[i], 0); atomic_store(&x->queued, 0); continue; }
        if (atomic_load(&POL->shadow_bytes) + x->len > cap && cxlp_shadow_trim(cap > x->len ? cap - x->len : 0) == 0 && atomic_load(&POL->shadow_bytes) + x->len > cap) break;   /* nothing evictable: wait */
        int dd = dram_dev(); if (dd < 0) break;                /* DRAM pool exhausted (the loan has it): wait */
        atomic_store(&POL->promo_ring[i], 0);
        cxlp_hints_t h = { o->klass, 4096, dd, 0, 0 }; cxlp_res_t nr;
        if (cxlp_reserve(x->len, &h, &nr)) { atomic_store(&x->queued, 0); continue; }
        cxlp_copy_in(nr.ptr, (char *)cxlp_seg_ptr((int)x->dev, x->seg) + x->off, x->len); cxlp_commit(&nr);
        atomic_fetch_add(&o->seq, 1);                          /* switch readers under the seqlock */
        x->sh_dev = (uint32_t)nr.dev; x->sh_off = nr.off; atomic_store(&x->sh_hits, 0); atomic_store(&x->sh_last_ms, cxlp_now_ns() / 1000000ull); atomic_store(&x->sh_seg, nr.seg);
        atomic_fetch_add(&o->seq, 1);
        atomic_fetch_add(&POL->shadow_bytes, x->len); atomic_fetch_add(&POL->promoted_bytes, x->len); atomic_fetch_add(&POL->promoted_extents, 1);
        atomic_store(&x->queued, 0); moved++;
    }
    cxlp_thread_seal();
    return moved;
}
