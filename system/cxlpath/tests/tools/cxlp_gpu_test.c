/* B5 gate. Mode "paths": with a hand-written policy page, copy 1 GiB GPU -> CXL buffer set all-direct,
 * all-staged and half/half; verify every byte. Mode "live <seconds>": with a real cxlpathd, copy
 * 1 GiB in a loop and print one line per copy (time, staged share, speed) so the orchestrator can
 * see the path follow an injected DRAM aggressor.
 * usage: cxlp_gpu_test <store> paths | live <seconds> */
#define _GNU_SOURCE
#include "../../src/internal.h"
#include "cxlpath_gpu.h"
#include <cuda_runtime.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
int main(int argc, char **argv) {
    if (argc < 3 || cxlp_attach(argv[1])) { fprintf(stderr, "usage/attach\n"); return 2; }
    const cxlp_key_t C = 9000; size_t len = 1ul << 30; int fails = 0;
    if (cxlp_bufset_create(C, 0, 0, len)) { puts("bufset_create failed"); return 1; }
    size_t got; unsigned char *buf = cxlp_bufset_map(C, 0, &got);
    if (!buf || cxlp_gpu_init(1, 100) || cxlp_gpu_register(buf, len)) { puts("gpu init/register failed"); return 1; }
    unsigned char *pat = malloc(len); for (size_t i = 0; i < len; i++) pat[i] = (unsigned char)((i * 2654435761u) >> 9);
    void *d; cudaMalloc(&d, len); cudaMemcpy(d, pat, len, cudaMemcpyHostToDevice);
    printf("GPU link (D2H into pinned DRAM): %.2f GiB/s\n", atomic_load(&POL->gpu_link_bps) / 1073741824.0);
    if (!strcmp(argv[2], "paths")) {
        uint32_t shares[] = { 0, 16, 8, 3 };
        for (int t = 0; t < 4; t++) {
            atomic_store(&POL->daemon_pid, (uint32_t)getpid()); atomic_store(&POL->heartbeat_ns, cxlp_now_ns());
            for (int s = 0; s < CXLP_NSTREAM; s++) atomic_store(&POL->staged16[s], shares[t]);
            memset(buf, 0, len); cxlp_gpu_stats_t st;
            int rc = cxlp_gpu_copy_in(buf, d, len, 0, &st); int ok = rc == 0 && memcmp(buf, pat, len) == 0;
            printf("staged %2u/16: direct %4llu MiB, staged %4llu MiB, %.2f GiB/s, data %s\n", shares[t], (unsigned long long)(st.direct_bytes >> 20), (unsigned long long)(st.staged_bytes >> 20), len / st.seconds / 1073741824.0, ok ? "verified" : "MISMATCH");
            if (!ok || st.staged_bytes != (uint64_t)(len / 16) * shares[t]) fails++;
        }
        atomic_store(&POL->daemon_pid, 0);
    } else {
        double secs = argc > 3 ? atof(argv[3]) : 10; uint64_t t0 = cxlp_now_ns(); int n = 0, bad = 0;
        printf("T0 %llu\n", (unsigned long long)t0);
        while ((cxlp_now_ns() - t0) / 1e9 < secs) {
            cxlp_gpu_stats_t st; if (n % 8 == 0) memset(buf, 0, 4096);
            if (cxlp_gpu_copy_in(buf, d, len, 0, &st)) { bad++; break; }
            if (n % 8 == 0 && memcmp(buf, pat, len)) bad++;
            printf("COPY %.0f %.3f %.2f\n", (cxlp_now_ns() - t0) / 1e6, (double)st.staged_bytes / len, len / st.seconds / 1073741824.0); fflush(stdout); n++;
        }
        fails += bad; printf("copies=%d data_errors=%d\n", n, bad);
    }
    cxlp_gpu_unregister(buf); cxlp_gpu_shutdown(); cxlp_bufset_destroy(C); cxlp_close();
    puts(fails ? "FAIL" : "PASS"); return fails != 0;
}
