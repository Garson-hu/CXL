/* A1 + A2 gate: map devices, then a multi-process multi-thread claim/release stress test.
 * Invariants: a segment is never held by two claimers at once (each claimer stamps the
 * segment's first bytes and re-checks them before release); no segment leaks.
 * usage: test_segments [nproc nthread claims_per_thread]   (devices from env, see Makefile) */
#define _GNU_SOURCE
#include "cxlpath.h"
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>

static long claims_per_thread;
static void *worker(void *arg) {
    uint64_t tag = ((uint64_t)getpid() << 20) | (uint64_t)(long)arg;
    unsigned seed = (unsigned)tag; long errors = 0, got = 0;
    uint32_t held[4]; int heldd[4], nheld = 0;
    for (long i = 0; i < claims_per_thread; i++) {
        int dev = (int)(rand_r(&seed) % (unsigned)cxlp_ndev());
        uint32_t s = cxlp_seg_claim(dev, CXLP_SEG_OPEN);
        if (s != CXLP_NO_SEG) {
            got++;
            uint64_t *p = cxlp_seg_ptr(dev, s); p[0] = tag; p[1] = ~tag;
            held[nheld] = s; heldd[nheld] = dev; nheld++;
        }
        if (nheld == 4 || (s == CXLP_NO_SEG && nheld)) {
            for (int k = 0; k < nheld; k++) {
                uint64_t *p = cxlp_seg_ptr(heldd[k], held[k]);
                if (p[0] != tag || p[1] != ~tag || cxlp_seg_owner(heldd[k], held[k]) != (uint32_t)getpid()) errors++;
                cxlp_seg_release(heldd[k], held[k]);
            }
            nheld = 0;
        }
    }
    for (int k = 0; k < nheld; k++) cxlp_seg_release(heldd[k], held[k]);
    (void)got;
    return (void *)errors;
}

int main(int argc, char **argv) {
    int nproc = argc > 1 ? atoi(argv[1]) : 8, nthr = argc > 2 ? atoi(argv[2]) : 8;
    claims_per_thread = argc > 3 ? atol(argv[3]) : 15625;          /* 8*8*15625 = 1,000,000 */
    const char *d0 = getenv("CXLP_DEV0"), *d1 = getenv("CXLP_DEV1");
    uint64_t bytes = (uint64_t)atol(getenv("CXLP_DEV_MIB") ? getenv("CXLP_DEV_MIB") : "2048") << 20;
    cxlp_config_t cfg = { .name = "test_segments", .ndev = 2,
        .dev = { { d0, 0, bytes, CXLP_DEV_CXL }, { d1, 0, bytes, CXLP_DEV_CXL } } };
    cxlp_destroy(cfg.name);
    if (cxlp_open(&cfg) != 0) { fprintf(stderr, "open failed\n"); return 1; }
    uint32_t n0 = cxlp_dev_nseg(0), n1 = cxlp_dev_nseg(1);
    printf("A1: mapped %s (%u segs) and %s (%u segs)\n", d0, n0, d1, n1);
    /* every segment address is writable and distinct */
    for (uint32_t s = 0; s < n0; s++) *(uint32_t *)cxlp_seg_ptr(0, s) = s;
    for (uint32_t s = 0; s < n0; s++) if (*(uint32_t *)cxlp_seg_ptr(0, s) != s) { puts("A1 FAIL: segment aliasing"); return 1; }
    cxlp_close();

    for (int p = 0; p < nproc; p++) {
        if (fork() == 0) {
            if (cxlp_attach(cfg.name) != 0) _exit(2);
            pthread_t th[64]; long bad = 0;
            for (int t = 0; t < nthr; t++) pthread_create(&th[t], NULL, worker, (void *)(long)t);
            for (int t = 0; t < nthr; t++) { void *r; pthread_join(th[t], &r); bad += (long)r; }
            cxlp_close(); _exit(bad ? 3 : 0);
        }
    }
    int fail = 0, st;
    while (wait(&st) > 0) if (!WIFEXITED(st) || WEXITSTATUS(st)) fail++;
    cxlp_attach(cfg.name);
    uint32_t f0 = cxlp_dev_free(0), f1 = cxlp_dev_free(1), held = 0;
    for (int d = 0; d < 2; d++) for (uint32_t s = 0; s < cxlp_dev_nseg(d); s++) if (cxlp_seg_owner(d, s)) held++;
    printf("A2: %d procs x %d threads x %ld claims: failed procs=%d, free %u/%u + %u/%u, still owned=%u\n",
           nproc, nthr, claims_per_thread, fail, f0, n0, f1, n1, held);
    int ok = !fail && f0 == n0 && f1 == n1 && held == 0;
    cxlp_close(); cxlp_destroy(cfg.name);
    puts(ok ? "PASS" : "FAIL"); return !ok;
}
