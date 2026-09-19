/* Clients: file-style shim (E1) — a byte stream packed into whole-segment extents. */
#define _GNU_SOURCE
#include "internal.h"
#include <stdlib.h>
#include <string.h>

struct cxlp_stream { uint32_t h; cxlp_hints_t hints; cxlp_res_t cur; uint32_t fill; int have; int failed; };

cxlp_key_t cxlp_key_of(const char *t) {
    uint64_t x = 1469598103934665603ull; for (; *t; t++) { x ^= (unsigned char)*t; x *= 1099511628211ull; }
    return (x == 0 || x == UINT64_MAX) ? 0x5eedull : x;
}

cxlp_stream_t *cxlp_stream_create(cxlp_key_t key, uint32_t klass, uint32_t stream_id, uint32_t wait_ms, const char *path, uint64_t chain, uint64_t version) {
    cxlp_stream_t *s = calloc(1, sizeof *s); if (!s) return NULL;
    if (cxlp_obj_begin(key, klass, &s->h)) { free(s); return NULL; }
    cxlp_obj_set_version(s->h, chain, version); if (chain) cxlp_obj_set_flags(s->h, CXLP_OBJ_NOPROMOTE);
    if (path && cxlp_obj_set_drain_whole(s->h, path)) { cxlp_stream_abort(s); return NULL; }
    s->hints = (cxlp_hints_t){ klass, 4096, -1, stream_id, wait_ms };
    return s;
}

static int seal_extent(cxlp_stream_t *s) {
    if (!s->have) return 0;
    if (s->fill == 0) { cxlp_abort(&s->cur); s->have = 0; return 0; }
    cxlp_shrink(&s->cur, s->fill); cxlp_commit(&s->cur);
    s->have = 0;
    if (cxlp_obj_append(s->h, &s->cur)) { cxlp_abort(&s->cur); return -1; }
    return 0;
}

int cxlp_stream_write(cxlp_stream_t *s, const void *buf, size_t n) {
    const char *p = buf;
    while (n && !s->failed) {
        if (!s->have) { if (cxlp_reserve(CXLP_SEG_BYTES, &s->hints, &s->cur)) { s->failed = 1; break; } s->have = 1; s->fill = 0; }
        size_t room = CXLP_SEG_BYTES - s->fill, m = n < room ? n : room;
        cxlp_copy_to(&s->cur, s->fill, p, m); s->fill += (uint32_t)m; p += m; n -= m;
        if (s->fill == CXLP_SEG_BYTES && seal_extent(s)) s->failed = 1;
    }
    return s->failed ? -1 : 0;
}

int cxlp_stream_close(cxlp_stream_t *s) {
    int rc = s->failed || seal_extent(s) ? -1 : cxlp_obj_commit(s->h);
    if (rc) { s->failed = 1; cxlp_stream_abort(s); return -1; }
    free(s); return 0;
}

void cxlp_stream_abort(cxlp_stream_t *s) {
    if (s->have) cxlp_abort(&s->cur);
    cxlp_obj_t *o = &cxlp_g.obj[s->h];
    for (uint32_t e = atomic_load(&o->head); e != CXLP_NIL;) { cxlp_ext_t *x = &cxlp_g.ext[e]; uint32_t nx = atomic_load(&x->next);
        cxlp_res_t r = { NULL, (int)x->dev, x->seg, x->off, x->len, 0 }; cxlp_release(&r); atomic_store(&x->used, 0); e = nx; }
    atomic_store(&o->head, CXLP_NIL); atomic_store(&o->tail, CXLP_NIL);
    uint32_t di = atomic_exchange(&o->drain_idx, CXLP_NIL); if (di != CXLP_NIL) atomic_store(&cxlp_g.meta->drain[di].used, 0);
    atomic_store(&o->key, CXLP_KEY_TOMB); atomic_store(&o->state, OBJ_TOMB);
    free(s);
}

int64_t cxlp_read(cxlp_key_t key, uint64_t off, void *buf, size_t n) {
    cxlp_res_t ext[64]; uint64_t bytes; cxlp_pin_t pin; int ne = cxlp_obj_pin(key, CXLP_CONSUMER_CPU, 0, UINT64_MAX, ext, 64, &bytes, &pin);
    if (ne < 0) return -1;
    if (ne > 64 || off > bytes) { cxlp_obj_unpin(&pin); return -1; }
    if (n > bytes - off) n = (size_t)(bytes - off);
    uint64_t pos = 0; size_t done = 0;
    for (int i = 0; i < ne && done < n; i++) {
        uint64_t a = pos, b = pos + ext[i].len; pos = b;
        if (b <= off + done) continue;
        uint64_t in = off + done - a; size_t m = (size_t)(ext[i].len - in); if (m > n - done) m = n - done;
        memcpy((char *)buf + done, (char *)ext[i].ptr + in, m); done += m;
    }
    cxlp_obj_unpin(&pin);
    return (int64_t)done;
}

int cxlp_chain_newest(uint64_t chain, cxlp_key_t *key, uint64_t *version) {
    int found = -1; uint64_t best = 0;
    for (uint32_t k = 0; k < CXLP_NDRAIN; k++) {
        cxlp_drain_t *d = &cxlp_g.meta->drain[k]; if (atomic_load(&d->used) != 2) continue;
        cxlp_obj_t *o = &cxlp_g.obj[d->obj];
        if (o->chain != chain || atomic_load(&o->state) != OBJ_COMMITTED) continue;
        if (found < 0 || o->version > best) { found = 0; best = o->version; if (key) *key = atomic_load(&o->key); }
    }
    if (found == 0 && version) *version = best;
    return found;
}
