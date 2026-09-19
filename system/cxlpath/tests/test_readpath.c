/* C1 + C2 gate: break-even k, read counting in a two-bucket window, promotion under the bound,
 * readers keep valid pointers across a relocation, checkpoints are never promoted. */
#define _GNU_SOURCE
#include "../src/internal.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
static int fails;
#define CHECK(c, msg) do { if (!(c)) { printf("  FAIL: %s\n", msg); fails++; } } while (0)
static void fill(unsigned char *b, size_t n, uint64_t k) { uint64_t x = k; for (size_t i = 0; i < n; i++) { x = x * 6364136223846793005ull + 1442695040888963407ull; b[i] = (unsigned char)(x >> 56); } }
static int on_kind(cxlp_key_t key, cxlp_devkind_t kind) { cxlp_res_t e[8]; uint64_t b; int n = cxlp_obj_lookup(key, e, 8, &b), c = 0; for (int i = 0; i < n && i < 8; i++) c += cxlp_dev_kind(e[i].dev) == kind; return c; }

int main(void) {
    const char *d0 = getenv("CXLP_DEV0"), *d1 = getenv("CXLP_DEV1");
    uint64_t bytes = (uint64_t)atol(getenv("CXLP_DEV_MIB") ? getenv("CXLP_DEV_MIB") : "2048") << 20;
    cxlp_config_t cfg = { .name = "test_readpath", .ndev = 3, .dev = { { d0, 0, bytes, CXLP_DEV_CXL }, { d1, 0, bytes, CXLP_DEV_CXL }, { "/dev/shm/cxlpath.fakedram_rp", 0, 1024ull << 20, CXLP_DEV_DRAM } } };
    cxlp_destroy(cfg.name); if (cxlp_open(&cfg)) { puts("open failed"); return 1; }
    uint32_t total_cxl = cxlp_dev_nseg(0) + cxlp_dev_nseg(1), total_dram = cxlp_dev_nseg(2);

    puts("C1.1 break-even threshold");
    CHECK(cxlp_k_compute(1.0, 1.2, 1.0, 10, 0) == 5, "CXL read 1.2x DRAM, copy = 1.0: k = 5 (the numbers of the stencil proxy)");
    CHECK(cxlp_k_compute(1.0, 1.2, 1.0, 10, 0.10) == 10, "DRAM probe 10% above its reference, w = 10: k doubles to 10");
    CHECK(cxlp_k_compute(1.0, 1.5, 1.0, 10, 0) == 2, "latency-bound small object, 1.5x: k = 2");
    CHECK(cxlp_k_compute(1.0, 1.016, 1.0, 10, 0) == 0, "GPU consumer on c28 (12.3 vs 12.5 GiB/s): penalty < 5% -> never");

    puts("C1.2 read counting, two-bucket window");
    size_t n = (40u << 20) + 777; unsigned char *src = malloc(n), *got = malloc(n); fill(src, n, 42);
    CHECK(cxlp_put(1001, 0, src, n) == 0 && on_kind(1001, CXLP_DEV_CXL) == 2, "object of 40 MiB = two extents, on CXL");
    atomic_store(&POL->k_read[CXLP_CONSUMER_CPU], 5); atomic_store(&POL->k_read[CXLP_CONSUMER_GPU], 0); atomic_store(&POL->read_bucket_ms, 200);
    cxlp_res_t e[8]; uint64_t b;
    for (int i = 0; i < 3; i++) { cxlp_obj_pin(1001, CXLP_CONSUMER_CPU, 0, UINT64_MAX, e, 8, &b); cxlp_obj_unpin(1001); }
    CHECK(cxlp_promote_pending(1) == 0, "3 reads < k = 5: nothing queued");
    usleep(450000);                                           /* both buckets expire */
    for (int i = 0; i < 4; i++) { cxlp_obj_pin(1001, CXLP_CONSUMER_CPU, 0, UINT64_MAX, e, 8, &b); cxlp_obj_unpin(1001); }
    CHECK(cxlp_promote_pending(1) == 0, "old reads left the window: 4 fresh reads are still < 5");
    for (int i = 0; i < 50; i++) { cxlp_obj_pin(1001, CXLP_CONSUMER_GPU, 0, UINT64_MAX, e, 8, &b); cxlp_obj_unpin(1001); }
    CHECK(cxlp_promote_pending(1) == 0, "50 reads by a GPU consumer whose k is 0 (never): nothing queued");

    puts("C2 promotion");
    CHECK(cxlp_put(1002, 0, src, n) == 0, "second object");
    for (int i = 0; i < 5; i++) { cxlp_obj_pin(1002, CXLP_CONSUMER_CPU, 0, 1000, e, 8, &b); cxlp_obj_unpin(1002); }   /* only the first extent is read */
    CHECK(cxlp_promote_pending(0) == 0 && on_kind(1002, CXLP_DEV_DRAM) == 0, "k reached but DRAM is over its bound: no promotion");
    int np = cxlp_obj_pin(1002, CXLP_CONSUMER_CPU, 0, 1000, e, 8, &b); unsigned char *oldp = e[0].ptr; uint32_t free_before = cxlp_dev_free(0) + cxlp_dev_free(1);
    CHECK(np == 1 && cxlp_promote_pending(1) == 1, "DRAM calm: exactly the extent that was read is promoted");
    CHECK(on_kind(1002, CXLP_DEV_DRAM) == 1 && on_kind(1002, CXLP_DEV_CXL) == 1, "first extent now on DRAM, the unread second extent stays on CXL");
    CHECK(memcmp(oldp, src, 1000) == 0 && cxlp_dev_free(0) + cxlp_dev_free(1) == free_before, "a reader pinned before the move still reads valid data; the old CXL copy is kept for it");
    CHECK(cxlp_obj_release(1002) == -2, "release is refused while a reader pins the object");
    cxlp_obj_unpin(1002); cxlp_promote_pending(1);
    CHECK(cxlp_get(1002, got, n) == (int64_t)n && memcmp(got, src, n) == 0, "object byte-exact after the move (DRAM + CXL extents)");
    CHECK(cxlp_put(1003, 0, src, n) == 0, "checkpoint-like object"); { uint32_t h; cxlp_obj_begin(1004, 0, &h); cxlp_obj_set_flags(h, CXLP_OBJ_NOPROMOTE); cxlp_res_t r; cxlp_reserve(4096, NULL, &r); cxlp_copy_to(&r, 0, src, 4096); cxlp_commit(&r); cxlp_obj_append(h, &r); cxlp_obj_commit(h); }
    for (int i = 0; i < 20; i++) { cxlp_obj_pin(1004, CXLP_CONSUMER_CPU, 0, UINT64_MAX, e, 8, &b); cxlp_obj_unpin(1004); }
    CHECK(cxlp_promote_pending(1) == 0 && on_kind(1004, CXLP_DEV_DRAM) == 0, "NOPROMOTE object (checkpoint): never promoted, however often it is read");
    for (cxlp_key_t k = 1001; k <= 1004; k++) CHECK(cxlp_obj_release(k) == 0, "release");
    cxlp_promote_pending(1); cxlp_thread_seal();
    CHECK(cxlp_dev_free(0) + cxlp_dev_free(1) == total_cxl && cxlp_dev_free(2) == total_dram, "all CXL and DRAM segments free at the end (old copies were released)");
    cxlp_close(); cxlp_destroy(cfg.name); unlink("/dev/shm/cxlpath.fakedram_rp");
    puts(fails ? "FAIL" : "PASS"); return fails != 0;
}
