/* D1 + D3 gate: objects and buffer-set versions reach NVMe byte-exactly (sizes that are not
 * multiples of 4 KiB or of a segment, a shared file with an offset, extents drained before the
 * object is complete); recovery from CXL after the writer is killed, from NVMe after the store is gone. */
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
static int fails; static char dir[200];
#define CHECK(c, msg) do { if (!(c)) { printf("  FAIL: %s\n", msg); fails++; } } while (0)
static void fill(unsigned char *b, size_t n, uint64_t k) { uint64_t x = k * 0x9E3779B97F4A7C15ull + 1; for (size_t i = 0; i < n; i++) { x = x * 6364136223846793005ull + 1442695040888963407ull; b[i] = (unsigned char)(x >> 56); } }
static int file_equals(const char *path, uint64_t off, const unsigned char *exp, size_t n, int check_size) {
    int fd = open(path, O_RDONLY); if (fd < 0) return 0; struct stat sb; fstat(fd, &sb);
    unsigned char *g = malloc(n ? n : 1); ssize_t r = pread(fd, g, n, (off_t)off); close(fd);
    int ok = r == (ssize_t)n && memcmp(g, exp, n) == 0 && (!check_size || (uint64_t)sb.st_size == off + n); free(g); return ok;
}
static int drain_until(cxlp_key_t key) { for (int i = 0; i < 100000; i++) { if (cxlp_obj_drained(key) == 1) return 1; if (cxlp_drain_step(0) <= 0) usleep(1000); } return 0; }
static const char *P(const char *name) { static char b[8][512]; static int i; i = (i + 1) % 8; snprintf(b[i], 512, "%.200s/%.200s", dir, name); return b[i]; }

int main(void) {
    const char *d0 = getenv("CXLP_DEV0"), *d1 = getenv("CXLP_DEV1"), *dd = getenv("CXLP_DRAIN_DIR");
    uint64_t bytes = (uint64_t)atol(getenv("CXLP_DEV_MIB") ? getenv("CXLP_DEV_MIB") : "2048") << 20;
    snprintf(dir, sizeof dir, "%s", dd ? dd : (access("/mnt/local/ghu4", W_OK) == 0 ? "/mnt/local/ghu4/cxlpath_test" : "/tmp/cxlpath_test"));
    mkdir(dir, 0755);
    cxlp_config_t cfg = { .name = "test_drain", .ndev = 2, .dev = { { d0, 0, bytes, CXLP_DEV_CXL }, { d1, 0, bytes, CXLP_DEV_CXL } } };
    cxlp_destroy(cfg.name); if (cxlp_open(&cfg)) { puts("open failed"); return 1; }
    uint32_t total = cxlp_dev_nseg(0) + cxlp_dev_nseg(1);
    printf("drain target directory: %s\n", dir);

    puts("D1.1 objects of awkward sizes");
    size_t sizes[] = { 1, 4095, 4096, 4097, (5u << 20) + 3, 32u << 20, (40u << 20) + 777, (100u << 20) + 1 };
    for (int i = 0; i < 8; i++) {
        size_t n = sizes[i]; unsigned char *b = malloc(n); fill(b, n, 100 + (uint64_t)i); char name[64]; snprintf(name, sizeof name, "obj_%d.bin", i); unlink(P(name));
        int ok = cxlp_put_drain(100 + (uint64_t)i, 0, b, n, P(name), 0) == 0 && drain_until(100 + (uint64_t)i) && file_equals(P(name), 0, b, n, 1);
        if (!ok) printf("  size %zu\n", n);
        CHECK(ok, "file byte-identical and exactly as long as the object"); cxlp_obj_release(100 + (uint64_t)i); free(b);
    }
    puts("D1.2 two objects in one file (second at offset 8192), and an extent drained before its object is complete");
    { unsigned char *a = malloc(8192), *b = malloc((70u << 20) + 5); fill(a, 8192, 7); fill(b, (70u << 20) + 5, 8); unlink(P("shared.bin"));
      CHECK(cxlp_put_drain(201, 0, a, 8192, P("shared.bin"), 0) == 0, "first object");
      uint32_t h; cxlp_obj_begin(202, 0, &h); cxlp_obj_set_drain(h, P("shared.bin"), 8192); cxlp_hints_t hi = { 0, 4096, -1, 0, 0 }; cxlp_res_t r;
      cxlp_reserve(CXLP_SEG_BYTES, &hi, &r); cxlp_copy_to(&r, 0, b, CXLP_SEG_BYTES); cxlp_commit(&r); cxlp_obj_append(h, &r);
      uint64_t before = atomic_load(&cxlp_g.meta->drained_bytes); for (int i = 0; i < 50; i++) cxlp_drain_step(0);
      CHECK(atomic_load(&cxlp_g.meta->drained_bytes) - before >= CXLP_SEG_BYTES && cxlp_obj_drained(202) != 1, "first 32 MiB already on NVMe while the object is still being written");
      size_t rest = (70u << 20) + 5 - CXLP_SEG_BYTES; for (size_t o = 0; o < rest;) { size_t n = rest - o < CXLP_SEG_BYTES ? rest - o : CXLP_SEG_BYTES; cxlp_reserve(n, &hi, &r); cxlp_copy_to(&r, 0, b + CXLP_SEG_BYTES + o, n); cxlp_commit(&r); cxlp_obj_append(h, &r); o += n; }
      cxlp_obj_commit(h);
      CHECK(drain_until(201) && drain_until(202) && file_equals(P("shared.bin"), 0, a, 8192, 0) && file_equals(P("shared.bin"), 8192, b, (70u << 20) + 5, 1), "both objects byte-identical inside the shared file");
      cxlp_obj_release(201); cxlp_obj_release(202); free(a); free(b); }
    cxlp_thread_seal(); CHECK(cxlp_dev_free(0) + cxlp_dev_free(1) == total, "all segments free after release");

    puts("D1.3 buffer-set versions: the overwrite rule is driven by the real drain");
    const cxlp_key_t C = 88; size_t sz = (300u << 20) + 12345; unsigned char *ref = malloc(sz);
    cxlp_bufset_create(C, 0, 0, sz); cxlp_bufset_create(C, 1, 1, sz); unsigned char *m[2] = { cxlp_bufset_map(C, 0, NULL), cxlp_bufset_map(C, 1, NULL) };
    int w1 = cxlp_bufset_begin(C, 1); fill(m[w1], sz, 1); unlink(P("ckpt_v1.bin")); cxlp_bufset_commit_drain(C, w1, P("ckpt_v1.bin"));
    int w2 = cxlp_bufset_begin(C, 2); fill(m[w2], sz, 2); unlink(P("ckpt_v2.bin")); cxlp_bufset_commit_drain(C, w2, P("ckpt_v2.bin"));
    CHECK(cxlp_bufset_begin(C, 3) == -1, "v3 must wait: v1 is not on NVMe yet");
    for (int i = 0; i < 100000 && !(cxlp_bufset_drained(C, w1) == 1 && cxlp_bufset_drained(C, w2) == 1); i++) if (cxlp_drain_step(0) <= 0) usleep(1000);
    fill(ref, sz, 1); CHECK(file_equals(P("ckpt_v1.bin"), 0, ref, sz, 1), "v1 file byte-identical, exact size (300 MiB + 12345)");
    fill(ref, sz, 2); CHECK(file_equals(P("ckpt_v2.bin"), 0, ref, sz, 1), "v2 file byte-identical");
    CHECK(cxlp_bufset_begin(C, 3) == w1, "v1 drained and v2 committed: v3 may overwrite v1's set");
    cxlp_bufset_destroy(C);

    puts("D3 recovery");
    size_t n = (90u << 20) + 11; unsigned char *ck = malloc(n); fill(ck, n, 5001); unlink(P("app_v7.ckpt"));
    pid_t w = fork();
    if (w == 0) { cxlp_attach(cfg.name); if (cxlp_put_drain(5001, 0, ck, n, P("app_v7.ckpt"), 0)) _exit(9); raise(SIGKILL); }
    int st; waitpid(w, &st, 0); CHECK(WIFSIGNALED(st), "application killed right after commit, before any drain"); cxlp_cleanup_dead();
    pid_t r = fork();
    if (r == 0) { cxlp_attach(cfg.name); unsigned char *g = malloc(n); int ok = cxlp_get(5001, g, n) == (int64_t)n && !memcmp(g, ck, n); _exit(!ok); }
    waitpid(r, &st, 0); CHECK(WIFEXITED(st) && WEXITSTATUS(st) == 0, "a new process restores the checkpoint from CXL, byte-exact");
    CHECK(drain_until(5001), "the node-level store drains the dead writer's checkpoint");
    cxlp_close(); cxlp_destroy(cfg.name); if (cxlp_open(&cfg)) return 1;          /* node reboot: the CXL content and the index are gone */
    unsigned char tmp[8]; CHECK(cxlp_get(5001, tmp, sizeof tmp) == -1, "after the store is gone the object is not on CXL ...");
    CHECK(file_equals(P("app_v7.ckpt"), 0, ck, n, 1), "... and is restored from NVMe, byte-exact");
    cxlp_close(); cxlp_destroy(cfg.name);
    puts(fails ? "FAIL" : "PASS"); return fails != 0;
}
