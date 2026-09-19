/* Component B, signal 3: DRAM latency probe (B2). Code shape from check V5: a non-inlined
 * function with integer clock math (the first V5 attempt mis-timed an inlined loop). */
#define _GNU_SOURCE
#include "cxlpath_daemon.h"
#include <stdint.h>
#include <stdlib.h>
#include <time.h>
#include <sys/mman.h>

typedef struct { uint32_t next; char pad[60]; } node_t;          /* one cache line per node */
struct cxlp_probe { node_t *g; uint32_t n, cur; size_t bytes; };

cxlp_probe_t *cxlp_probe_create(size_t bytes) {
    cxlp_probe_t *p = calloc(1, sizeof *p); if (!p) return NULL;
    p->n = (uint32_t)(bytes / sizeof(node_t)); p->bytes = (size_t)p->n * sizeof(node_t);
    p->g = mmap(NULL, p->bytes, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (p->g == MAP_FAILED) { free(p); return NULL; }
    madvise(p->g, p->bytes, MADV_HUGEPAGE);
    uint32_t *perm = malloc((size_t)p->n * sizeof *perm); if (!perm) { munmap(p->g, p->bytes); free(p); return NULL; }
    for (uint32_t i = 0; i < p->n; i++) perm[i] = i;
    uint64_t x = 88172645463325252ull;
    for (uint32_t i = p->n - 1; i > 0; i--) { x ^= x << 13; x ^= x >> 7; x ^= x << 17; uint32_t j = (uint32_t)(x % (i + 1)), t = perm[i]; perm[i] = perm[j]; perm[j] = t; }
    for (uint32_t i = 0; i < p->n; i++) p->g[perm[i]].next = perm[(i + 1) % p->n];   /* one random cycle */
    free(perm); p->cur = 12345 % p->n;
    return p;
}

__attribute__((noinline)) double cxlp_probe_once(cxlp_probe_t *p, int loads) {
    struct timespec a, b; uint32_t c = p->cur; node_t *g = p->g;
    clock_gettime(CLOCK_MONOTONIC, &a);
    for (int i = 0; i < loads; i++) { c = g[c].next; __asm__ volatile("" ::: "memory"); }
    clock_gettime(CLOCK_MONOTONIC, &b);
    p->cur = (uint32_t)(((uint64_t)c * 2654435761u) % p->n);     /* next probe starts elsewhere */
    return ((double)(b.tv_sec - a.tv_sec) * 1e9 + (double)(b.tv_nsec - a.tv_nsec)) / loads;
}

void cxlp_probe_destroy(cxlp_probe_t *p) { if (p) { munmap(p->g, p->bytes); free(p); } }
