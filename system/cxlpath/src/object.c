/* Component A, part 3: shared object index, lookup, crash cleanup (A4). */
#define _GNU_SOURCE
#include "internal.h"
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
            atomic_store(&o->key, key);
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
    x->obj = h; atomic_store(&x->rd_cur, 0); atomic_store(&x->rd_prev, 0); atomic_store(&x->rd_bucket, 0); atomic_store(&x->queued, 0);
    uint32_t tail = atomic_load(&o->tail);
    if (tail == CXLP_NIL) atomic_store(&o->head, e); else atomic_store(&cxlp_g.ext[tail].next, e);
    atomic_store(&o->tail, e); atomic_fetch_add(&o->bytes, r->len);
    return 0;
}

int cxlp_obj_set_flags(uint32_t h, uint32_t flags) { atomic_store(&cxlp_g.obj[h].flags, flags); return 0; }

int cxlp_obj_commit(uint32_t h) {
    uint32_t st = OBJ_CREATING;
    return atomic_compare_exchange_strong(&cxlp_g.obj[h].state, &st, OBJ_COMMITTED) ? 0 : -1;
}

static cxlp_obj_t *find(cxlp_key_t key) {
    uint32_t mask = cxlp_g.meta->nobj - 1, i = (uint32_t)mix(key) & mask;
    for (uint32_t probe = 0; probe <= mask; probe++, i = (i + 1) & mask) {
        cxlp_obj_t *o = &cxlp_g.obj[i];
        uint32_t st = atomic_load(&o->state);
        if (st == OBJ_EMPTY) return NULL;                     /* never used: end of the probe chain */
        if (st == OBJ_COMMITTED && atomic_load(&o->key) == key) return o;
    }
    return NULL;
}

int cxlp_obj_lookup(cxlp_key_t key, cxlp_res_t *ext, int max, uint64_t *bytes) {
    cxlp_obj_t *o = find(key); if (!o) return -1;
    int n = 0;
    for (uint32_t e = atomic_load(&o->head); e != CXLP_NIL; e = atomic_load(&cxlp_g.ext[e].next), n++) {
        if (n < max) { cxlp_ext_t *x = &cxlp_g.ext[e];
            ext[n] = (cxlp_res_t){ (char *)cxlp_seg_ptr((int)x->dev, x->seg) + x->off, (int)x->dev, x->seg, x->off, x->len, 0 }; }
    }
    if (bytes) *bytes = atomic_load(&o->bytes);
    return n;
}

static void drop_extents(cxlp_obj_t *o, int fix_live) {
    for (uint32_t e = atomic_load(&o->head); e != CXLP_NIL;) {
        cxlp_ext_t *x = &cxlp_g.ext[e]; uint32_t nx = atomic_load(&x->next);
        if (fix_live) { cxlp_res_t r = { NULL, (int)x->dev, x->seg, x->off, x->len, 0 }; cxlp_release(&r); }
        atomic_store(&x->used, 0); e = nx;
    }
    atomic_store(&o->head, CXLP_NIL); atomic_store(&o->tail, CXLP_NIL);
}

int cxlp_obj_release(cxlp_key_t key) {
    cxlp_obj_t *o = find(key); if (!o) return -1;
    if (atomic_load(&o->pins)) return -2;                     /* readers still hold pointers: retry later */
    uint32_t st = OBJ_COMMITTED;
    if (!atomic_compare_exchange_strong(&o->state, &st, OBJ_CREATING)) return -1;   /* one releaser wins */
    drop_extents(o, 1);
    atomic_store(&o->key, CXLP_KEY_TOMB); atomic_store(&o->state, OBJ_TOMB);
    return 0;
}

int cxlp_put(cxlp_key_t key, uint32_t klass, const void *buf, size_t len) {
    uint32_t h; if (cxlp_obj_begin(key, klass, &h)) return -1;
    cxlp_hints_t hint = { klass, 0, -1, 0, 0 };
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
    cxlp_res_t ext[64]; uint64_t bytes; int n = cxlp_obj_pin(key, CXLP_CONSUMER_CPU, 0, UINT64_MAX, ext, 64, &bytes);
    if (n < 0) return -1;
    if (n > 64 || bytes > cap) { cxlp_obj_unpin(key); return -1; }
    size_t off = 0; for (int i = 0; i < n; i++) { memcpy((char *)buf + off, ext[i].ptr, ext[i].len); off += ext[i].len; }
    cxlp_obj_unpin(key);
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
