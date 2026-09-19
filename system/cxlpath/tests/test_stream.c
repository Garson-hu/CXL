/* E1 gate, library half: a file written as many write() calls of odd sizes comes back byte-exact
 * from CXL (random-offset reads) and from NVMe; extents are whole segments except the last; the
 * newest version of a chain is found; an aborted stream leaves nothing behind. */
#define _GNU_SOURCE
#include "../src/internal.h"
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
static int fails;
#define CHECK(c, msg) do { if (!(c)) { printf("  FAIL: %s\n", msg); fails++; } } while (0)
int main(void) {
    const char *d0 = getenv("CXLP_DEV0"), *d1 = getenv("CXLP_DEV1");
    uint64_t bytes = (uint64_t)atol(getenv("CXLP_DEV_MIB") ? getenv("CXLP_DEV_MIB") : "2048") << 20;
    char dir[256]; snprintf(dir, sizeof dir, "%s", access("/mnt/local/ghu4", W_OK) == 0 ? "/mnt/local/ghu4/cxlpath_test" : "/tmp/cxlpath_test"); mkdir(dir, 0755);
    cxlp_config_t cfg = { .name = "test_stream", .ndev = 2, .dev = { { d0, 0, bytes, CXLP_DEV_CXL }, { d1, 0, bytes, CXLP_DEV_CXL } } };
    cxlp_destroy(cfg.name); if (cxlp_open(&cfg)) { puts("open failed"); return 1; }
    uint32_t total = cxlp_dev_nseg(0) + cxlp_dev_nseg(1);
    size_t n = (150u << 20) + 4321; unsigned char *ref = malloc(n), *got = malloc(n); uint64_t x = 99; for (size_t i = 0; i < n; i++) { x = x * 6364136223846793005ull + 1; ref[i] = (unsigned char)(x >> 56); }
    const uint64_t chain = cxlp_key_of("lulesh:0"); char path[300];
    for (uint64_t v = 1; v <= 2; v++) {
        snprintf(path, sizeof path, "%s/stream_v%llu.dat", dir, (unsigned long long)v); unlink(path); char kt[64]; snprintf(kt, sizeof kt, "lulesh:0:%llu", (unsigned long long)v);
        cxlp_stream_t *s = cxlp_stream_create(cxlp_key_of(kt), 0, 3, 0, path, chain, v); CHECK(s != NULL, "stream created");
        unsigned seed = (unsigned)v; size_t off = 0; int rc = 0;
        while (off < n) { size_t m = 1 + rand_r(&seed) % (9u << 20); if (rand_r(&seed) % 3 == 0) m = 1 + rand_r(&seed) % 300; if (m > n - off) m = n - off; ref[0] = (unsigned char)v; rc |= cxlp_stream_write(s, ref + off, m); off += m; }
        CHECK(rc == 0 && cxlp_stream_close(s) == 0, "written as random-sized pieces (1 B .. 9 MiB) and committed");
    }
    cxlp_key_t nk; uint64_t nv; CHECK(cxlp_chain_newest(chain, &nk, &nv) == 0 && nv == 2 && nk == cxlp_key_of("lulesh:0:2"), "newest version of the chain found on CXL");
    cxlp_res_t e[16]; uint64_t b; int ne = cxlp_obj_lookup(nk, e, 16, &b); int whole = 1; for (int i = 0; i + 1 < ne; i++) whole &= e[i].len == CXLP_SEG_BYTES;
    CHECK(b == n && ne == 5 && whole && e[4].len == n - 4ull * CXLP_SEG_BYTES, "150 MiB + 4321 B = four whole 32 MiB extents + one short extent");
    ref[0] = 2; unsigned seed = 7; int bad = 0;
    for (int i = 0; i < 200; i++) { size_t off = rand_r(&seed) % n, m = 1 + rand_r(&seed) % (3u << 20); if (m > n - off) m = n - off; if (cxlp_read(nk, off, got, m) != (int64_t)m || memcmp(got, ref + off, m)) bad++; }
    CHECK(bad == 0 && cxlp_read(nk, n - 10, got, 100) == 10, "200 random-offset reads from CXL byte-exact; reads are clipped at the end");
    for (int i = 0; i < 100000 && cxlp_obj_drained(nk) != 1; i++) if (cxlp_drain_step(0) <= 0) usleep(1000);
    int fd = open(path, O_RDONLY); struct stat sb; fstat(fd, &sb); ssize_t r = read(fd, got, n); close(fd);
    CHECK(r == (ssize_t)n && (size_t)sb.st_size == n && memcmp(got, ref, n) == 0, "drained file byte-identical and exactly as long");
    CHECK(cxlp_obj_drained(cxlp_key_of("lulesh:0:1")) == -1, "version 1 was reclaimed by the runtime once version 2 was committed and v1 was on NVMe");
    cxlp_stream_t *a = cxlp_stream_create(cxlp_key_of("junk"), 0, 0, 0, NULL, 0, 0); cxlp_stream_write(a, ref, 40u << 20); cxlp_stream_abort(a);
    cxlp_obj_release(nk); cxlp_thread_seal();
    CHECK(cxlp_dev_free(0) + cxlp_dev_free(1) == total, "nothing left behind (aborted stream, shrunk tail extents, released object)");
    cxlp_close(); cxlp_destroy(cfg.name); puts(fails ? "FAIL" : "PASS"); return fails != 0;
}
