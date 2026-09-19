/* Component A, part 4: buffer sets for GPU checkpoint clients (A5). */
#define _GNU_SOURCE
#include "internal.h"
#include <string.h>
#include <sys/mman.h>

static uint32_t *segtab(int slot, int which) {
    return (uint32_t *)((char *)cxlp_g.meta + cxlp_g.meta->bs_segtab_off) + ((size_t)slot * 2 + (size_t)which) * CXLP_BS_MAXSEG;
}
static int slot_of(cxlp_key_t client, int create) {
    for (int i = 0; i < CXLP_MAX_BUFSETS; i++) if (atomic_load(&cxlp_g.meta->bufset[i].client) == client) return i;
    if (!create) return -1;
    for (int i = 0; i < CXLP_MAX_BUFSETS; i++) { uint64_t z = 0;
        if (atomic_compare_exchange_strong(&cxlp_g.meta->bufset[i].client, &z, client)) return i; }
    return -1;
}

int cxlp_bufset_create(cxlp_key_t client, int which, int dev, size_t bytes) {
    if (!client || which < 0 || which > 1) return -1;
    int sl = slot_of(client, 1); if (sl < 0) return -1;
    cxlp_bufset_t *b = &cxlp_g.meta->bufset[sl];
    if (b->nseg[which]) return b->bytes[which] == bytes ? 0 : -1;          /* already there */
    uint32_t n = (uint32_t)((bytes + CXLP_SEG_BYTES - 1) / CXLP_SEG_BYTES);
    if (n == 0 || n > CXLP_BS_MAXSEG) return -1;
    uint32_t *t = segtab(sl, which);
    for (uint32_t i = 0; i < n; i++) {
        t[i] = cxlp_seg_claim(dev, CXLP_SEG_BUFSET);
        if (t[i] == CXLP_NO_SEG) { while (i--) cxlp_seg_release(dev, t[i]); return -1; }
    }
    b->dev[which] = (uint32_t)dev; b->bytes[which] = bytes; b->nseg[which] = n;
    return 0;
}

void *cxlp_bufset_map(cxlp_key_t client, int which, size_t *bytes) {
    int sl = slot_of(client, 0); if (sl < 0) return NULL;
    cxlp_bufset_t *b = &cxlp_g.meta->bufset[sl]; uint32_t n = b->nseg[which]; if (!n) return NULL;
    size_t len = (size_t)n * CXLP_SEG_BYTES;
    char *base = mmap(NULL, len, PROT_NONE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (base == MAP_FAILED) return NULL;
    uint32_t *t = segtab(sl, which); int dev = (int)b->dev[which];
    for (uint32_t i = 0; i < n; i++) {
        off_t off = (off_t)(cxlp_g.meta->dev[dev].offset + (uint64_t)t[i] * CXLP_SEG_BYTES);
        if (mmap(base + (size_t)i * CXLP_SEG_BYTES, CXLP_SEG_BYTES, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_FIXED, cxlp_g.fd[dev], off) == MAP_FAILED) { munmap(base, len); return NULL; }
    }
    if (bytes) *bytes = b->bytes[which];
    return base;
}

int cxlp_bufset_begin(cxlp_key_t client, uint64_t version) {
    int sl = slot_of(client, 0); if (sl < 0) return -1;
    cxlp_bufset_t *b = &cxlp_g.meta->bufset[sl];
    for (int pass = 0; pass < 2; pass++) for (int w = 0; w < 2; w++) {
        if (!b->nseg[w]) continue;
        uint32_t st = atomic_load(&b->state[w]); int other = 1 - w;
        int ok;
        if (pass == 0) ok = (st == CXLP_BS_EMPTY);                          /* an unused set first */
        else ok = (st == CXLP_BS_COMMITTED && atomic_load(&b->drained[w]) &&            /* overwrite rule */
                   atomic_load(&b->state[other]) == CXLP_BS_COMMITTED &&
                   atomic_load(&b->version[other]) > atomic_load(&b->version[w]));
        if (ok && atomic_compare_exchange_strong(&b->state[w], &st, CXLP_BS_WRITING)) {
            atomic_store(&b->drained[w], 0); atomic_store(&b->drain_armed[w], 0); b->used[w] = 0; atomic_store(&b->version[w], version); return w; }
    }
    return -1;
}

int cxlp_bufset_commit(cxlp_key_t client, int which) {
    int sl = slot_of(client, 0); if (sl < 0) return -1;
    uint32_t st = CXLP_BS_WRITING;
    return atomic_compare_exchange_strong(&cxlp_g.meta->bufset[sl].state[which], &st, CXLP_BS_COMMITTED) ? 0 : -1;
}
int cxlp_bufset_mark_drained(cxlp_key_t client, int which) {
    int sl = slot_of(client, 0); if (sl < 0) return -1;
    if (atomic_load(&cxlp_g.meta->bufset[sl].state[which]) != CXLP_BS_COMMITTED) return -1;
    atomic_store(&cxlp_g.meta->bufset[sl].drained[which], 1); return 0;
}
int cxlp_bufset_newest(cxlp_key_t client, uint64_t *version) {
    int sl = slot_of(client, 0); if (sl < 0) return -1;
    cxlp_bufset_t *b = &cxlp_g.meta->bufset[sl]; int best = -1; uint64_t bv = 0;
    for (int w = 0; w < 2; w++) if (atomic_load(&b->state[w]) == CXLP_BS_COMMITTED && (best < 0 || atomic_load(&b->version[w]) > bv)) { best = w; bv = atomic_load(&b->version[w]); }
    if (best >= 0 && version) *version = bv;
    return best;
}
/* committed version held by set `which`, -1 if the set holds none */
int64_t cxlp_bufset_version(cxlp_key_t client, int which) {
    int sl = slot_of(client, 0); if (sl < 0 || which < 0 || which > 1) return -1;
    cxlp_bufset_t *b = &cxlp_g.meta->bufset[sl];
    return atomic_load(&b->state[which]) == CXLP_BS_COMMITTED ? (int64_t)atomic_load(&b->version[which]) : -1;
}

int cxlp_bufset_destroy(cxlp_key_t client) {
    int sl = slot_of(client, 0); if (sl < 0) return -1;
    cxlp_bufset_t *b = &cxlp_g.meta->bufset[sl];
    for (int w = 0; w < 2; w++) { uint32_t *t = segtab(sl, w); for (uint32_t i = 0; i < b->nseg[w]; i++) cxlp_seg_release((int)b->dev[w], t[i]); }
    memset((char *)b + sizeof(b->client), 0, sizeof *b - sizeof(b->client));
    atomic_store(&b->client, 0); return 0;
}
