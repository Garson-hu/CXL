/* cxlp_ckpt_loop <store> <versions> <MiB per version> <dir> [backlog-only]
 * A checkpointing application in miniature: every version is one object of a version chain with a
 * drain target. The application never releases anything itself: the runtime reclaims a version once
 * it is on NVMe and a newer one is committed. The producer is far faster than the NVMe, so it is held
 * back by reserve() back-pressure. */
#define _GNU_SOURCE
#include "../../src/internal.h"
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
static void fill(uint64_t *b, size_t words, uint64_t v) { for (size_t i = 0; i < words; i++) b[i] = (i + 1) * 0x9E3779B97F4A7C15ull ^ (v << 48); }
int main(int argc, char **argv) {
    if (argc < 5 || cxlp_attach(argv[1])) return 2;
    int nv = atoi(argv[2]); size_t n = (size_t)atol(argv[3]) << 20; const char *dir = argv[4]; int backlog_only = argc > 5;
    uint64_t *buf = aligned_alloc(4096, n); char path[300]; int released[256] = { 0 }; uint32_t min_free = UINT32_MAX; int fails = 0;
    uint32_t tot = 0; for (int d = 0; d < cxlp_ndev(); d++) if (cxlp_dev_kind(d) == CXLP_DEV_CXL) tot += cxlp_dev_nseg(d);
    for (int v = 1; v <= nv; v++) {
        fill(buf, n / 8, (uint64_t)v); snprintf(path, sizeof path, "%s/loop_v%d.bin", dir, v); unlink(path);
        uint64_t t0 = cxlp_now_ns(); int rc = cxlp_put_version(7000 + (uint64_t)v, 0, buf, n, path, 300000, 1, (uint64_t)v); double dt = (cxlp_now_ns() - t0) / 1e9;
        uint32_t fr = 0; for (int d = 0; d < cxlp_ndev(); d++) if (cxlp_dev_kind(d) == CXLP_DEV_CXL) fr += cxlp_dev_free(d);
        if (fr < min_free) min_free = fr;
        printf("VERSION %d rc=%d put %.2f s (%.2f GiB/s incl. waiting) free CXL segments %u/%u\n", v, rc, dt, n / dt / 1073741824.0, fr, tot); fflush(stdout);
        if (rc) { fails++; break; }
    }
    if (backlog_only) { puts("BACKLOG-READY"); fflush(stdout); }
    (void)released;
    for (int i = 0; i < 600000 && cxlp_obj_drained(7000 + (uint64_t)nv) == 0; i++) usleep(1000);    /* older versions: reclaimed by the runtime */
    int older_left = 0; for (int v = 1; v < nv; v++) { for (int i = 0; i < 5000 && cxlp_obj_drained(7000 + (uint64_t)v) != -1; i++) usleep(1000); older_left += cxlp_obj_drained(7000 + (uint64_t)v) != -1; }
    printf("older versions still on CXL after the drain: %d (the runtime reclaims them)\n", older_left); if (older_left) fails++;
    while (cxlp_obj_release(7000 + (uint64_t)nv) == -2) usleep(1000);
    uint64_t *chk = aligned_alloc(4096, 64u << 20);
    for (int v = 1; v <= nv; v++) { fill(buf, n / 8, (uint64_t)v); snprintf(path, sizeof path, "%s/loop_v%d.bin", dir, v); int fd = open(path, O_RDONLY), bad = fd < 0;
        for (size_t o = 0; o < n && !bad; o += 64u << 20) { size_t m = n - o < (64u << 20) ? n - o : (64u << 20); if (pread(fd, chk, m, (off_t)o) != (ssize_t)m || memcmp(chk, (char *)buf + o, m)) bad = 1; }
        if (fd >= 0) close(fd);
        if (bad) { printf("VERSION %d file MISMATCH\n", v); fails++; }
        unlink(path); }
    cxlp_thread_seal(); uint32_t fr = 0; for (int d = 0; d < cxlp_ndev(); d++) if (cxlp_dev_kind(d) == CXLP_DEV_CXL) fr += cxlp_dev_free(d);
    printf("LOOP versions=%d files_ok=%d min_free_segments=%u final_free=%u/%u\n", nv, fails == 0, min_free, fr, tot);
    cxlp_close(); puts(fails ? "FAIL" : "PASS"); return fails != 0;
}
