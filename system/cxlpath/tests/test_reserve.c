/* A3 gate: functional checks, a multi-thread hammer with data verification and full reclaim,
 * and write throughput through reserve/copy_in/commit versus a raw NT memcpy to the same device. */
#define _GNU_SOURCE
#include "cxlpath.h"
#include <immintrin.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }
static int fails;
#define SAMESEG(x, y) ((x).dev == (y).dev && (x).seg == (y).seg)   /* a segment is (device, index) */
#define CHECK(c, msg) do { if (!(c)) { printf("  FAIL: %s\n", msg); fails++; } } while (0)

static void *hammer(void *arg) {
    unsigned seed = (unsigned)(long)arg * 7919u + 1; long bad = 0;
    enum { N = 64 }; cxlp_res_t r[N]; int n = 0;
    for (int it = 0; it < 4000; it++) {
        size_t len = 4096 + rand_r(&seed) % (6u << 20);
        cxlp_hints_t h = { rand_r(&seed) % CXLP_NKLASS, 0, -1, 0, 0 };
        if (cxlp_reserve(len, &h, &r[n]) == 0) {
            memset(r[n].ptr, (int)(r[n].off ^ r[n].seg ^ (unsigned)(long)arg), 64);
            ((unsigned char *)r[n].ptr)[len - 1] = 0x5a; cxlp_commit(&r[n]); n++;
        }
        if (n == N || it % 97 == 0) {
            for (int k = n - 1; k >= 0; k -= 1 + (int)(rand_r(&seed) % 2)) { /* release a random subset */
                unsigned char *p = r[k].ptr;
                if (p[0] != (unsigned char)(r[k].off ^ r[k].seg ^ (unsigned)(long)arg) || p[r[k].len - 1] != 0x5a) bad++;
                cxlp_release(&r[k]); r[k] = r[n - 1]; n--;
            }
        }
    }
    for (int k = 0; k < n; k++) cxlp_release(&r[k]);
    cxlp_thread_seal();
    return (void *)bad;
}

int main(void) {
    const char *d0 = getenv("CXLP_DEV0"), *d1 = getenv("CXLP_DEV1");
    uint64_t bytes = (uint64_t)atol(getenv("CXLP_DEV_MIB") ? getenv("CXLP_DEV_MIB") : "2048") << 20;
    cxlp_config_t cfg = { .name = "test_reserve", .ndev = 2, .dev = { { d0, 0, bytes, CXLP_DEV_CXL }, { d1, 0, bytes, CXLP_DEV_CXL } } };
    cxlp_destroy(cfg.name);
    if (cxlp_open(&cfg)) { puts("open failed"); return 1; }
    uint32_t total = cxlp_dev_nseg(0) + cxlp_dev_nseg(1);

    puts("A3.1 functional");
    cxlp_res_t a, b, c;
    CHECK(cxlp_reserve(CXLP_SEG_BYTES + 1, NULL, &a) == -1, "oversize reservation must fail");
    CHECK(cxlp_reserve(1000, NULL, &a) == 0 && cxlp_reserve(1000, NULL, &b) == 0, "two small reservations");
    CHECK(SAMESEG(a, b) && b.off == 1024 && ((uintptr_t)b.ptr & 63) == 0, "append in one segment, 64 B aligned");
    cxlp_hints_t h4k = { 1, 4096, -1, 0, 0 };
    CHECK(cxlp_reserve(5000, &h4k, &c) == 0 && !SAMESEG(c, a) && (c.off & 4095) == 0, "other class -> other segment, 4 KiB aligned");
    cxlp_commit(&a); cxlp_commit(&b); cxlp_commit(&c);
    CHECK(cxlp_seg_live(a.dev, a.seg) == 2000, "live bytes = reserved bytes");
    cxlp_release(&a);
    CHECK(cxlp_dev_free(0) + cxlp_dev_free(1) == total - 2, "open segment is kept while its thread appends");
    cxlp_release(&b); cxlp_release(&c); cxlp_thread_seal();
    CHECK(cxlp_dev_free(0) + cxlp_dev_free(1) == total, "sealed + empty segments return to the pool");
    cxlp_res_t big[3];                                   /* sealed while data is live, freed on release */
    for (int i = 0; i < 3; i++) { CHECK(cxlp_reserve(20u << 20, NULL, &big[i]) == 0, "20 MiB reservation"); cxlp_commit(&big[i]); }
    CHECK(!SAMESEG(big[0], big[1]) && !SAMESEG(big[1], big[2]) && !SAMESEG(big[0], big[2]), "20 MiB x3 need three segments");
    CHECK(cxlp_dev_free(0) + cxlp_dev_free(1) == total - 3, "three segments in use");
    cxlp_release(&big[0]);
    CHECK(cxlp_dev_free(0) + cxlp_dev_free(1) == total - 2, "sealed segment freed when its last byte dies");
    cxlp_release(&big[1]); cxlp_release(&big[2]); cxlp_thread_seal();
    cxlp_hints_t force1 = { 0, 0, 1, 0, 0 };
    CHECK(cxlp_reserve(100, &force1, &a) == 0 && a.dev == 1, "forced device"); cxlp_abort(&a); cxlp_thread_seal();
    CHECK(cxlp_dev_free(0) + cxlp_dev_free(1) == total, "abort returns the space");

    puts("A3.2 hammer: 16 threads x 4000 reservations, random release order, data verified");
    pthread_t th[16]; long bad = 0;
    for (long t = 0; t < 16; t++) pthread_create(&th[t], NULL, hammer, (void *)(t + 1));
    for (int t = 0; t < 16; t++) { void *r; pthread_join(th[t], &r); bad += (long)r; }
    CHECK(bad == 0, "data intact under concurrency");
    CHECK(cxlp_dev_free(0) + cxlp_dev_free(1) == total, "everything reclaimed after the hammer");

    puts("A3.3 throughput: reserve/copy_in/commit vs raw NT memcpy (single thread, device 0)");
    size_t chunk = CXLP_SEG_BYTES, tot = bytes < (8ull << 30) ? bytes / 2 : (4ull << 30); int n = (int)(tot / chunk);
    char *src = aligned_alloc(4096, chunk); memset(src, 0x3c, chunk);
    double best_raw = 0, best_lib = 0;
    for (int rep = 0; rep < 9; rep++) {                      /* best of 9 each, alternating: single runs at the device limit vary by ~8% */
        char *raw = cxlp_seg_ptr(0, 0); double t = now();
        for (int i = 0; i < n; i++) cxlp_copy_in(raw + (size_t)i * chunk, src, chunk);
        double r1 = tot / (now() - t) / 1073741824.0; if (r1 > best_raw) best_raw = r1;
        cxlp_hints_t f0 = { 0, 0, 0, 0, 0 }; cxlp_res_t *rs = malloc(n * sizeof *rs); t = now();
        for (int i = 0; i < n; i++) { if (cxlp_reserve(chunk, &f0, &rs[i])) { puts("  reserve failed"); return 1; } cxlp_copy_in(rs[i].ptr, src, chunk); cxlp_commit(&rs[i]); }
        double r2 = tot / (now() - t) / 1073741824.0; if (r2 > best_lib) best_lib = r2;
        for (int i = 0; i < n; i++) cxlp_release(&rs[i]);
        cxlp_thread_seal(); free(rs);
    }
    printf("  raw NT memcpy %.2f GiB/s, through cxlpath %.2f GiB/s (%.1f%% of raw; gate >= 95%%)\n", best_raw, best_lib, 100 * best_lib / best_raw);
    CHECK(best_lib >= 0.95 * best_raw, "throughput within 5% of raw");
    cxlp_close(); cxlp_destroy(cfg.name);
    puts(fails ? "FAIL" : "PASS"); return fails != 0;
}
