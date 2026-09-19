/* cxlp_readers <store> — C live gate helper: with a real daemon, put an object on CXL, read it k
 * times as a CPU consumer, wait for the daemon's promoter, verify placement and content. */
#define _GNU_SOURCE
#include "../../src/internal.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
int main(int argc, char **argv) {
    if (argc < 2 || cxlp_attach(argv[1])) return 2;
    size_t n = (48u << 20) + 5; unsigned char *src = malloc(n), *got = malloc(n); for (size_t i = 0; i < n; i++) src[i] = (unsigned char)(i * 2654435761u >> 11);
    uint32_t kc = atomic_load(&POL->k_read[CXLP_CONSUMER_CPU]), kg = atomic_load(&POL->k_read[CXLP_CONSUMER_GPU]);
    printf("published thresholds: k_cpu=%u k_gpu=%u (GPU reads: CXL %.2f vs DRAM %.2f GiB/s)\n", kc, kg, atomic_load(&POL->gpu_rd_cxl_bps) / 1073741824.0, atomic_load(&POL->gpu_rd_dram_bps) / 1073741824.0);
    if (!kc || cxlp_put(777, 0, src, n)) { puts("FAIL: no k or put failed"); return 1; }
    cxlp_res_t e[8]; uint64_t b; int nx = cxlp_obj_lookup(777, e, 8, &b), cxl0 = 0, dram1 = 0;
    for (int i = 0; i < nx; i++) cxl0 += cxlp_dev_kind(e[i].dev) == CXLP_DEV_CXL;
    for (uint32_t i = 0; i < kc; i++) { cxlp_pin_t pin; cxlp_obj_pin(777, CXLP_CONSUMER_CPU, 0, UINT64_MAX, e, 8, &b, &pin); cxlp_obj_unpin(&pin); }
    for (int t = 0; t < 40 && dram1 < nx; t++) { usleep(50000); dram1 = 0; int m = cxlp_obj_lookup(777, e, 8, &b); for (int i = 0; i < m; i++) dram1 += cxlp_dev_kind(e[i].dev) == CXLP_DEV_DRAM; }
    int ok = cxl0 == nx && dram1 == nx && cxlp_get(777, got, n) == (int64_t)n && !memcmp(src, got, n);
    printf("object of %d extents: %d on CXL before, %d on DRAM after %u reads; promoted %.0f MiB; content %s\n", nx, cxl0, dram1, kc, atomic_load(&POL->promoted_bytes) / 1048576.0, ok ? "byte-exact" : "WRONG");
    cxlp_obj_release(777); cxlp_thread_seal(); cxlp_close();
    puts(ok ? "PASS" : "FAIL"); return !ok;
}
