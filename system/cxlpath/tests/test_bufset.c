/* A5 gate: stitched buffer sets and the overwrite rule; a version survives its writer. */
#define _GNU_SOURCE
#include "cxlpath.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
static int fails;
#define CHECK(c, msg) do { if (!(c)) { printf("  FAIL: %s\n", msg); fails++; } } while (0)
static void fill(unsigned char *b, size_t n, uint64_t v) { for (size_t i = 0; i < n; i += 8) { uint64_t x = (i + 1) * 0x9E3779B97F4A7C15ull ^ v; memcpy(b + i, &x, n - i < 8 ? n - i : 8); } }
static int same(unsigned char *b, size_t n, uint64_t v) { for (size_t i = 0; i < n; i += 8) { uint64_t x = (i + 1) * 0x9E3779B97F4A7C15ull ^ v; if (memcmp(b + i, &x, n - i < 8 ? n - i : 8)) return 0; } return 1; }

int main(void) {
    const char *d0 = getenv("CXLP_DEV0"), *d1 = getenv("CXLP_DEV1");
    uint64_t bytes = (uint64_t)atol(getenv("CXLP_DEV_MIB") ? getenv("CXLP_DEV_MIB") : "2048") << 20;
    cxlp_config_t cfg = { .name = "test_bufset", .ndev = 2, .dev = { { d0, 0, bytes, CXLP_DEV_CXL }, { d1, 0, bytes, CXLP_DEV_CXL } } };
    cxlp_destroy(cfg.name); if (cxlp_open(&cfg)) { puts("open failed"); return 1; }
    uint32_t total = cxlp_dev_nseg(0) + cxlp_dev_nseg(1);
    const cxlp_key_t C = 77; size_t sz = (300u << 20) + 12345;              /* 10 segments, not a multiple */
    /* fragment the device first so the sets are built from SCATTERED segments */
    uint32_t hole[24]; for (int i = 0; i < 24; i++) hole[i] = cxlp_seg_claim(0, CXLP_SEG_OPEN);
    for (int i = 0; i < 24; i += 2) cxlp_seg_release(0, hole[i]);
    CHECK(cxlp_bufset_create(C, 0, 0, sz) == 0 && cxlp_bufset_create(C, 1, 0, sz) == 0, "create two sets");
    CHECK(cxlp_bufset_create(C, 0, 0, sz) == 0, "create is idempotent");
    for (int i = 1; i < 24; i += 2) cxlp_seg_release(0, hole[i]);
    CHECK(cxlp_dev_free(0) + cxlp_dev_free(1) == total - 20, "two sets hold 20 segments");
    size_t got; unsigned char *b0 = cxlp_bufset_map(C, 0, &got), *b1 = cxlp_bufset_map(C, 1, NULL);
    CHECK(b0 && b1 && got == sz, "stitched mappings");

    puts("A5.1 overwrite rule");
    int w1 = cxlp_bufset_begin(C, 1); CHECK(w1 == 0 || w1 == 1, "version 1 gets a set");
    fill(w1 ? b1 : b0, sz, 1); CHECK(cxlp_bufset_commit(C, w1) == 0, "commit v1");
    int w2 = cxlp_bufset_begin(C, 2); CHECK(w2 == 1 - w1, "version 2 goes to the OTHER set");
    CHECK(cxlp_bufset_begin(C, 99) == -1, "no third writer while v2 is being written");
    fill(w2 ? b1 : b0, sz, 2); cxlp_bufset_commit(C, w2);
    CHECK(cxlp_bufset_begin(C, 3) == -1, "v3 refused: v1 is not drained yet (back-pressure)");
    cxlp_bufset_mark_drained(C, w2);
    CHECK(cxlp_bufset_begin(C, 3) == -1, "v3 still refused: draining the NEWER version does not free the older set");
    cxlp_bufset_mark_drained(C, w1);
    int w3 = cxlp_bufset_begin(C, 3); CHECK(w3 == w1, "v3 overwrites v1's set once v1 is drained and v2 is committed");
    uint64_t nv; CHECK(cxlp_bufset_newest(C, &nv) == w2 && nv == 2, "while v3 is being written the newest complete version is v2");
    CHECK(same(w2 ? b1 : b0, sz, 2), "v2 intact while v3 is being written");

    puts("A5.2 a new process recovers the newest complete version after the writer dies mid-v3");
    pid_t p = fork();
    if (p == 0) { cxlp_attach(cfg.name); uint64_t v; int w = cxlp_bufset_newest(C, &v); size_t n; unsigned char *m = cxlp_bufset_map(C, w, &n);
        _exit(!(w == w2 && v == 2 && n == sz && m && same(m, n, 2))); }
    int st; waitpid(p, &st, 0); CHECK(WIFEXITED(st) && WEXITSTATUS(st) == 0, "recovery process reads v2 byte-exactly through its own stitched mapping");
    CHECK(cxlp_bufset_destroy(C) == 0 && cxlp_dev_free(0) + cxlp_dev_free(1) == total, "destroy returns all segments");
    cxlp_close(); cxlp_destroy(cfg.name);
    puts(fails ? "FAIL" : "PASS"); return fails != 0;
}
