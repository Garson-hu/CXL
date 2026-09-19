/* cxlp_kv_replay <store> <trace.jsonl> <block_KiB> <max_requests> [capacity_GiB]
 * E3: a KV-cache layer in miniature, driven by a Mooncake trace (one request per line, hash_ids =
 * the prefix chain of 512-token blocks). It talks to cxlpath exactly the way an LMCache-like layer
 * would: get (pin/unpin) for every block of the longest matching prefix, allocate + fill + commit
 * for the rest, and ITS OWN eviction policy (LRU by last use) when its capacity is reached. Block
 * content is a function of the block hash, so EVERY hit is verified. Runs as fast as it can. */
#define _GNU_SOURCE
#include "../../src/internal.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct ent { uint64_t hash; struct ent *prev, *next, *hnext; } ent_t;
#define HB (1u << 18)
static ent_t *bucket[HB], *lru_head, *lru_tail; static size_t nlive;
static ent_t *find(uint64_t h) { for (ent_t *e = bucket[(h * 0x9E3779B97F4A7C15ull) >> 46]; e; e = e->hnext) if (e->hash == h) return e; return NULL; }
static void lru_unlink(ent_t *e) { if (e->prev) e->prev->next = e->next; else lru_head = e->next; if (e->next) e->next->prev = e->prev; else lru_tail = e->prev; }
static void lru_push(ent_t *e) { e->prev = lru_tail; e->next = NULL; if (lru_tail) lru_tail->next = e; else lru_head = e; lru_tail = e; }
static void hdel(ent_t *e) { ent_t **pp = &bucket[(e->hash * 0x9E3779B97F4A7C15ull) >> 46]; while (*pp != e) pp = &(*pp)->hnext; *pp = e->hnext; }
static cxlp_key_t key_of(uint64_t h) { return (h + 1) * 0x9E3779B97F4A7C15ull | 1; }
static void fill(uint64_t *b, size_t words, uint64_t h) { uint64_t x = h * 0xD6E8FEB86659FD93ull + 1; for (size_t i = 0; i < words; i++) { x ^= x << 13; x ^= x >> 7; x ^= x << 17; b[i] = x; } }

int main(int argc, char **argv) {
    if (argc < 5 || cxlp_attach(argv[1])) { fprintf(stderr, "usage / attach\n"); return 2; }
    FILE *f = fopen(argv[2], "r"); if (!f) { perror("trace"); return 2; }
    size_t bsz = (size_t)atol(argv[3]) << 10, words = bsz / 8; long maxreq = atol(argv[4]);
    double cap_gib = argc > 5 ? atof(argv[5]) : 0; size_t cap_blocks = cap_gib > 0 ? (size_t)(cap_gib * 1073741824.0 / bsz) : (size_t)-1;
    uint64_t *buf = aligned_alloc(4096, bsz), *exp = aligned_alloc(4096, bsz); char *line = malloc(1 << 22);
    uint64_t nreq = 0, nblk = 0, hits = 0, hit_dram = 0, misses = 0, writes = 0, evict = 0, bad = 0, putfail = 0; uint64_t t0 = cxlp_now_ns();
    cxlp_hints_t hi = { 1, 0, -1, 4, 0 };
    while (nreq < (uint64_t)maxreq && fgets(line, 1 << 22, f)) {
        char *p = strstr(line, "\"hash_ids\""); if (!p) continue; p = strchr(p, '['); if (!p) continue; p++;
        int matching = 1; nreq++;
        for (;;) {
            while (*p == ' ' || *p == ',') p++;
            if (*p == ']' || !*p) break;
            uint64_t h = strtoull(p, &p, 10); nblk++;
            ent_t *e = find(h);
            if (matching && e) {                                   /* prefix hit: read the block in place and check every word */
                cxlp_res_t x[4]; uint64_t bytes; int n = cxlp_obj_pin(key_of(h), CXLP_CONSUMER_CPU, 0, UINT64_MAX, x, 4, &bytes);
                if (n < 1 || bytes != bsz) { bad++; if (n >= 0) cxlp_obj_unpin(key_of(h)); }
                else { fill(exp, words, h); size_t o = 0; int ok = 1; for (int i = 0; i < n; i++) { if (memcmp((char *)exp + o, x[i].ptr, x[i].len)) ok = 0; o += x[i].len; hit_dram += cxlp_dev_kind(x[i].dev) == CXLP_DEV_DRAM && i == 0; }
                       if (!ok) { bad++; }
                       cxlp_obj_unpin(key_of(h)); hits++; }
                lru_unlink(e); lru_push(e);
                continue;
            }
            matching = 0; misses++;
            if (e) { lru_unlink(e); lru_push(e); continue; }      /* present, but the prefix is broken: recomputed anyway, nothing to store */
            fill(buf, words, h);
            for (int attempt = 0; ; attempt++) {                   /* the KV layer's own policy: evict least recently used blocks */
                while (nlive >= cap_blocks || attempt) { ent_t *v = lru_head; if (!v) break; lru_unlink(v); hdel(v); while (cxlp_obj_release(key_of(v->hash)) == -2) ; free(v); nlive--; evict++; if (attempt && evict % 8 == 0) break; if (!attempt) continue; }
                uint32_t oh; cxlp_res_t r; int ok = 0;
                if (cxlp_obj_begin(key_of(h), 1, &oh) == 0) {
                    if (cxlp_reserve(bsz, &hi, &r) == 0) { cxlp_copy_to(&r, 0, buf, bsz); cxlp_commit(&r); ok = cxlp_obj_append(oh, &r) == 0 && cxlp_obj_commit(oh) == 0; if (!ok) cxlp_abort(&r); }
                    if (!ok) { atomic_store(&cxlp_g.obj[oh].key, CXLP_KEY_TOMB); atomic_store(&cxlp_g.obj[oh].state, OBJ_TOMB); }
                }
                if (ok) { ent_t *ne = calloc(1, sizeof *ne); ne->hash = h; size_t bk = (h * 0x9E3779B97F4A7C15ull) >> 46; ne->hnext = bucket[bk]; bucket[bk] = ne; lru_push(ne); nlive++; writes++; break; }
                if (attempt > 64 || !lru_head) { putfail++; break; }
            }
        }
    }
    double dt = (cxlp_now_ns() - t0) / 1e9;
    printf("KV requests=%llu blocks=%llu hits=%llu (%.1f%%; %llu served from the DRAM pool after promotion) misses=%llu stored=%llu evicted=%llu put_failures=%llu VERIFY_ERRORS=%llu\n",
           (unsigned long long)nreq, (unsigned long long)nblk, (unsigned long long)hits, 100.0 * hits / (nblk ? nblk : 1), (unsigned long long)hit_dram, (unsigned long long)misses, (unsigned long long)writes, (unsigned long long)evict, (unsigned long long)putfail, (unsigned long long)bad);
    printf("KV stored %.1f GiB and read back %.1f GiB in %.1f s; promoted so far: %.0f MiB in %llu extents\n", writes * (double)bsz / 1073741824.0, hits * (double)bsz / 1073741824.0, dt,
           atomic_load(&POL->promoted_bytes) / 1048576.0, (unsigned long long)atomic_load(&POL->promoted_extents));
    while (lru_head) { ent_t *v = lru_head; lru_unlink(v); while (cxlp_obj_release(key_of(v->hash)) == -2) ; free(v); }
    cxlp_thread_seal();
    uint32_t fr = 0, tot = 0; for (int d = 0; d < cxlp_ndev(); d++) { fr += cxlp_dev_free(d); tot += cxlp_dev_nseg(d); }
    printf("KV after releasing everything: %u/%u segments free (the promoter may still hold old copies for a moment)\n", fr, tot);
    int ok = bad == 0 && putfail == 0 && hits > 0;
    cxlp_close(); puts(ok ? "PASS" : "FAIL"); return !ok;
}
