/* A4 gate: objects outlive their writer. A writer process commits 3 objects, starts a 4th,
 * leaves a raw uncommitted reservation, and is killed with SIGKILL. Then: cleanup, a NEW process
 * reads the 3 objects byte-exactly, the 4th does not exist, the uncommitted space is reclaimed,
 * and after releasing the 3 objects every segment is free again. Plus a concurrent put/get/release
 * run across processes. */
#define _GNU_SOURCE
#include "cxlpath.h"
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
static int fails;
#define CHECK(c, msg) do { if (!(c)) { printf("  FAIL: %s\n", msg); fails++; } } while (0)
static void fill(unsigned char *b, size_t n, uint64_t key) { uint64_t x = key * 0x9E3779B97F4A7C15ull; for (size_t i = 0; i < n; i++) { x = x * 6364136223846793005ull + 1442695040888963407ull; b[i] = (unsigned char)(x >> 56); } }
static size_t size_of(uint64_t key) { return (size_t)(5u << 20) + (size_t)(key % 7) * (13u << 20) + key % 4099; }  /* 5..83 MiB, not segment multiples */

int main(void) {
    const char *d0 = getenv("CXLP_DEV0"), *d1 = getenv("CXLP_DEV1");
    uint64_t bytes = (uint64_t)atol(getenv("CXLP_DEV_MIB") ? getenv("CXLP_DEV_MIB") : "2048") << 20;
    cxlp_config_t cfg = { .name = "test_objects", .ndev = 2, .dev = { { d0, 0, bytes, CXLP_DEV_CXL }, { d1, 0, bytes, CXLP_DEV_CXL } } };
    cxlp_destroy(cfg.name);
    if (cxlp_open(&cfg)) { puts("open failed"); return 1; }
    uint32_t total = cxlp_dev_nseg(0) + cxlp_dev_nseg(1);

    puts("A4.1 writer is killed mid-write");
    pid_t w = fork();
    if (w == 0) {
        cxlp_attach(cfg.name);
        for (uint64_t k = 101; k <= 103; k++) { size_t n = size_of(k); unsigned char *b = malloc(n); fill(b, n, k); if (cxlp_put(k, 0, b, n)) _exit(9); free(b); }
        uint32_t h; cxlp_obj_begin(104, 0, &h);
        for (int i = 0; i < 2; i++) { cxlp_res_t r; cxlp_reserve(20u << 20, NULL, &r); memset(r.ptr, 1, 4096); cxlp_commit(&r); cxlp_obj_append(h, &r); }
        cxlp_res_t stray; cxlp_reserve(9u << 20, NULL, &stray);         /* reserved, never committed */
        raise(SIGKILL);
    }
    int st; waitpid(w, &st, 0);
    CHECK(WIFSIGNALED(st), "writer died by signal");
    uint32_t before = cxlp_dev_free(0) + cxlp_dev_free(1);
    int dropped = cxlp_cleanup_dead();
    uint32_t after = cxlp_dev_free(0) + cxlp_dev_free(1);
    printf("  cleanup dropped %d uncommitted object(s); free segments %u -> %u of %u\n", dropped, before, after, total);
    CHECK(dropped == 1, "exactly the uncommitted object is dropped");

    puts("A4.2 a NEW process finds and verifies the committed objects");
    pid_t r = fork();
    if (r == 0) {
        cxlp_attach(cfg.name); int bad = 0;
        for (uint64_t k = 101; k <= 103; k++) { size_t n = size_of(k); unsigned char *exp = malloc(n), *got = malloc(n); fill(exp, n, k);
            if (cxlp_get(k, got, n) != (int64_t)n || memcmp(exp, got, n)) { bad++; }
            free(exp); free(got); }
        unsigned char tmp[8]; if (cxlp_get(104, tmp, sizeof tmp) != -1) bad += 10;
        cxlp_res_t e[8]; uint64_t b; if (cxlp_obj_lookup(104, e, 8, &b) != -1) bad += 10;
        _exit(bad);
    }
    waitpid(r, &st, 0);
    CHECK(WIFEXITED(st) && WEXITSTATUS(st) == 0, "committed objects byte-exact in a new process; uncommitted object absent");
    uint64_t need = 0; for (uint64_t k = 101; k <= 103; k++) need += size_of(k);
    CHECK(total - after <= (uint32_t)(need / CXLP_SEG_BYTES) + 4, "only the committed objects still hold segments");
    for (uint64_t k = 101; k <= 103; k++) CHECK(cxlp_obj_release(k) == 0, "release committed object from another process");
    CHECK(cxlp_obj_release(101) == -1, "double release is refused");
    CHECK(cxlp_dev_free(0) + cxlp_dev_free(1) == total, "all segments free after release (uncommitted space reclaimed)");

    puts("A4.3 4 processes: put / get+verify / release, 300 objects each");
    for (int p = 0; p < 4; p++) if (fork() == 0) {
        cxlp_attach(cfg.name); int bad = 0; size_t cap = 90u << 20; unsigned char *b = malloc(cap), *g = malloc(cap);
        for (uint64_t i = 0; i < 300; i++) { uint64_t k = 1000000ull * (uint64_t)(p + 1) + i; size_t n = size_of(k) / 8 + 1;
            fill(b, n, k); if (cxlp_put(k, (uint32_t)(i % 4), b, n)) { bad++; continue; }
            if (cxlp_get(k, g, cap) != (int64_t)n || memcmp(b, g, n)) bad++;
            if (i >= 3) { if (cxlp_obj_release(k - 3)) bad++; } }
        for (uint64_t i = 297; i < 300; i++) if (cxlp_obj_release(1000000ull * (uint64_t)(p + 1) + i)) bad++;
        cxlp_thread_seal(); _exit(bad ? 1 : 0);
    }
    int pf = 0; while (wait(&st) > 0) if (!WIFEXITED(st) || WEXITSTATUS(st)) pf++;
    CHECK(pf == 0, "concurrent put/get/release across processes");
    CHECK(cxlp_dev_free(0) + cxlp_dev_free(1) == total, "no leak after the concurrent run");
    cxlp_close(); cxlp_destroy(cfg.name);
    puts(fails ? "FAIL" : "PASS"); return fails != 0;
}
