/* A key names ONE object: writing a key again supersedes the old object. The bug this guards
 * against was found by the all-clients run F1: every rerun of a checkpointing application left one
 * more "version 3" on CXL, never reclaimed, until the store was full — and a lookup could have
 * returned the stale copy. */
#define _GNU_SOURCE
#include "../src/internal.h"
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/wait.h>
static int fails;
#define CHECK(c, msg) do { if (!(c)) { printf("  FAIL: %s\n", msg); fails++; } } while (0)
static void fill(unsigned char *b, size_t n, uint64_t k) { uint64_t x = k * 0x9E3779B97F4A7C15ull + 1; for (size_t i = 0; i < n; i++) { x = x * 6364136223846793005ull + 1442695040888963407ull; b[i] = (unsigned char)(x >> 56); } }
static uint32_t nfree(void) { return cxlp_dev_free(0) + cxlp_dev_free(1); }
static int file_is(const char *path, const unsigned char *exp, size_t n) { int fd = open(path, O_RDONLY); if (fd < 0) return 0; struct stat sb; fstat(fd, &sb); unsigned char *g = malloc(n); ssize_t r = read(fd, g, n); close(fd); int ok = r == (ssize_t)n && (size_t)sb.st_size == n && !memcmp(g, exp, n); free(g); return ok; }
static void drain_all(void) { for (int i = 0, idle = 0; i < 200000 && idle < 50; i++) { if (cxlp_drain_step(0) > 0) idle = 0; else { idle++; usleep(1000); } } }

int main(void) {
    const char *d0 = getenv("CXLP_DEV0"), *d1 = getenv("CXLP_DEV1");
    uint64_t bytes = (uint64_t)atol(getenv("CXLP_DEV_MIB") ? getenv("CXLP_DEV_MIB") : "2048") << 20;
    char dir[256], path[300]; snprintf(dir, sizeof dir, "%s", access("/mnt/local/ghu4", W_OK) == 0 ? "/mnt/local/ghu4/cxlpath_test" : "/tmp/cxlpath_test"); mkdir(dir, 0755);
    cxlp_config_t cfg = { .name = "test_replace", .ndev = 2, .dev = { { d0, 0, bytes, CXLP_DEV_CXL }, { d1, 0, bytes, CXLP_DEV_CXL } } };
    cxlp_destroy(cfg.name); if (cxlp_open(&cfg)) { puts("open failed"); return 1; }
    uint32_t total = nfree(); size_t na = (40u << 20) + 5, nb = (10u << 20) + 9;
    unsigned char *A = malloc(na), *B = malloc(nb), *g = malloc(na); fill(A, na, 1); fill(B, nb, 2);

    puts("R1 writing a key again replaces the object");
    CHECK(cxlp_put(500, 0, A, na) == 0 && cxlp_put(500, 0, B, nb) == 0, "same key written twice");
    CHECK(cxlp_get(500, g, na) == (int64_t)nb && !memcmp(g, B, nb), "lookup returns the NEW content");
    cxlp_thread_seal(); CHECK(total - nfree() <= 2, "the old object's segments are already free");
    CHECK(cxlp_obj_release(500) == 0 && cxlp_obj_release(500) == -1, "one release removes the key completely (no stale copy behind it)");
    cxlp_thread_seal(); CHECK(nfree() == total, "all segments free");

    puts("R2 with a drain target: the file ends up as the new object, exactly as long");
    snprintf(path, sizeof path, "%s/replace.bin", dir); unlink(path);
    CHECK(cxlp_put_drain(501, 0, A, na, path, 0) == 0, "first version"); drain_all(); CHECK(file_is(path, A, na), "file = first content (40 MiB + 5)");
    CHECK(cxlp_put_drain(501, 0, B, nb, path, 0) == 0, "second, SHORTER version under the same key and path"); drain_all();
    CHECK(file_is(path, B, nb), "file = second content and truncated to 10 MiB + 9"); CHECK(cxlp_obj_drained(501) == 1, "the new object reports drained");
    cxlp_obj_release(501); cxlp_thread_seal(); CHECK(nfree() == total, "all segments free");

    puts("R3 a reader that pinned the old object keeps valid data; the old copy goes when it unpins");
    CHECK(cxlp_put(502, 0, A, na) == 0, "object"); cxlp_res_t e[8]; uint64_t b; cxlp_pin_t pin; int n = cxlp_obj_pin(502, CXLP_CONSUMER_CPU, 0, UINT64_MAX, e, 8, &b, &pin);
    CHECK(n == 2 && cxlp_put(502, 0, B, nb) == 0, "superseded while pinned");
    CHECK(!memcmp(e[0].ptr, A, e[0].len) && cxlp_get(502, g, na) == (int64_t)nb && !memcmp(g, B, nb), "old pointers still show the old content, a new lookup gets the new content");
    CHECK(cxlp_obj_reap_superseded() == 0, "while the reader pins it the old copy is NOT reaped");
    uint32_t before = nfree(); CHECK(cxlp_obj_unpin(&pin) == 0, "the pin names the OLD object although the key now belongs to the new one");
    CHECK(cxlp_obj_reap_superseded() == 1, "the superseded copy is reaped once nobody pins it"); cxlp_thread_seal();
    CHECK(nfree() > before, "its segments are free again"); cxlp_obj_release(502); cxlp_thread_seal(); CHECK(nfree() == total, "all segments free");

    puts("R4 the superseding writer dies before it commits: the old object is THE object again");
    snprintf(path, sizeof path, "%s/replace4.bin", dir); unlink(path);
    CHECK(cxlp_put_drain(503, 0, A, na, path, 0) == 0, "old version, not drained yet");
    pid_t w = fork();
    if (w == 0) { cxlp_attach(cfg.name); cxlp_stream_t *s = cxlp_stream_create(503, 0, 0, 0, path, 0, 0); cxlp_stream_write(s, B, nb); raise(SIGKILL); }
    int st; waitpid(w, &st, 0);
    CHECK(cxlp_drain_step(0) == 0, "while superseded the old object is not drained (the new writer owns the file)");
    CHECK(cxlp_cleanup_dead() == 1, "cleanup drops the dead writer's unfinished object");
    drain_all(); CHECK(cxlp_get(503, g, na) == (int64_t)na && !memcmp(g, A, na) && file_is(path, A, na), "old object readable, its drain resumed, file = old content");
    cxlp_obj_release(503); cxlp_thread_seal(); CHECK(nfree() == total, "all segments free");

    puts("R5 an application rerun writes checkpoint versions 1..3 again, five times");
    const uint64_t chain = cxlp_key_of("app:0");
    for (int run = 0; run < 5; run++) for (uint64_t v = 1; v <= 3; v++) {
        char kt[64]; snprintf(kt, sizeof kt, "app:0:%llu", (unsigned long long)v); snprintf(path, sizeof path, "%s/app_v%llu.dat", dir, (unsigned long long)v);
        fill(A, na, 100 * (uint64_t)run + v); CHECK(cxlp_put_version(cxlp_key_of(kt), 0, A, na, path, 0, chain, v) == 0, "put version"); drain_all();
    }
    unsigned live = 0; for (uint32_t i = 0; i < cxlp_g.meta->nobj; i++) live += atomic_load(&cxlp_g.obj[i].state) == OBJ_COMMITTED;
    printf("  live objects after 5 runs x 3 versions: %u (the newest version of the chain)\n", live);
    CHECK(live == 1, "exactly one object left: no pile-up of re-written versions");
    fill(A, na, 403); snprintf(path, sizeof path, "%s/app_v3.dat", dir);
    CHECK(cxlp_get(cxlp_key_of("app:0:3"), g, na) == (int64_t)na && !memcmp(g, A, na) && file_is(path, A, na), "version 3 on CXL and on NVMe is the one written by the LAST run");
    cxlp_obj_release(cxlp_key_of("app:0:3")); cxlp_thread_seal(); CHECK(nfree() == total, "all segments free");
    cxlp_close(); cxlp_destroy(cfg.name); puts(fails ? "FAIL" : "PASS"); return fails != 0;
}
