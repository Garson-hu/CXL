/* B1 gate: reserve() follows the ratio published in shared memory; overflow and back-pressure
 * rules; a real cxlpathd publishes a changed ratio within one epoch. `--datapath` runs only the
 * reserve/copy/commit/release loop between two markers for the strace check. */
#define _GNU_SOURCE
#include "../src/internal.h"
#include <pthread.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
static int fails;
#define CHECK(c, msg) do { if (!(c)) { printf("  FAIL: %s\n", msg); fails++; } } while (0)
static void fake_daemon(uint32_t spill, uint32_t dram_ok) {
    atomic_store(&POL->daemon_pid, (uint32_t)getpid()); atomic_store(&POL->heartbeat_ns, cxlp_now_ns());
    for (int s = 0; s < CXLP_NSTREAM; s++) atomic_store(&POL->spill16[s], spill);
    atomic_store(&POL->dram_ok, dram_ok);
}
static int dram_share(int n) {                      /* n whole-segment reservations -> how many on DRAM */
    int dram = 0; cxlp_res_t r;
    for (int i = 0; i < n; i++) { if (cxlp_reserve(CXLP_SEG_BYTES, NULL, &r)) { printf("  reserve failed at %d\n", i); return -1; }
        if (cxlp_dev_kind(r.dev) == CXLP_DEV_DRAM) { dram++; }
        cxlp_commit(&r); cxlp_release(&r); }
    cxlp_thread_seal(); return dram;
}
static void *late_release(void *arg) { usleep(300000); cxlp_res_t *r = arg; cxlp_release(r); return NULL; }

int main(int argc, char **argv) {
    const char *d0 = getenv("CXLP_DEV0"), *d1 = getenv("CXLP_DEV1"), *dd = getenv("CXLP_DRAM");
    uint64_t bytes = (uint64_t)atol(getenv("CXLP_DEV_MIB") ? getenv("CXLP_DEV_MIB") : "2048") << 20;
    if (!dd) dd = "/dev/shm/cxlpath.fakedram";
    cxlp_config_t cfg = { .name = "test_policy", .ndev = 3, .dev = { { d0, 0, bytes, CXLP_DEV_CXL }, { d1, 0, bytes, CXLP_DEV_CXL }, { dd, 0, 2048ull << 20, CXLP_DEV_DRAM } } };
    cxlp_destroy(cfg.name); if (cxlp_open(&cfg)) { puts("open failed"); return 1; }

    if (argc > 1 && !strcmp(argv[1], "--datapath")) {
        char *src = aligned_alloc(4096, 8u << 20); memset(src, 7, 8u << 20); cxlp_res_t r[8];
        fake_daemon(8, 1);
        for (int i = 0; i < 8; i++) { cxlp_reserve(8u << 20, NULL, &r[i]); cxlp_copy_to(&r[i], 0, src, 8u << 20); cxlp_commit(&r[i]); }   /* warm-up: TLS, page tables */
        for (int i = 0; i < 8; i++) cxlp_release(&r[i]);
        if (write(2, "DATAPATH-BEGIN\n", 15) < 0) return 1;
        for (int round = 0; round < 40; round++) {        /* 320 reservations, ~80 new segments on CXL and DRAM */
            for (int i = 0; i < 8; i++) { if (cxlp_reserve(8u << 20, NULL, &r[i])) return 3; cxlp_copy_to(&r[i], 0, src, 8u << 20); cxlp_commit(&r[i]); }
            for (int i = 0; i < 8; i++) cxlp_release(&r[i]);
        }
        if (write(2, "DATAPATH-END\n", 13) < 0) return 1;
        cxlp_close(); cxlp_destroy(cfg.name); unlink(dd); return 0;
    }

    puts("B1.1 reserve() follows the published ratio (no daemon = everything on CXL)");
    CHECK(dram_share(48) == 0, "no daemon: 0 of 48 segments on DRAM");
    fake_daemon(8, 1);  CHECK(dram_share(160) == 80,  "spill 8/16: 80 of 160");
    fake_daemon(4, 1);  CHECK(dram_share(160) == 40,  "spill 4/16: 40 of 160");
    fake_daemon(1, 1);  CHECK(dram_share(160) == 10,  "spill 1/16: 10 of 160");
    fake_daemon(16, 1); CHECK(dram_share(32) == 32,   "spill 16/16: all on DRAM");
    fake_daemon(0, 1);  CHECK(dram_share(32) == 0,    "spill 0: none");
    atomic_store(&POL->heartbeat_ns, cxlp_now_ns() - 5000000000ull); atomic_store(&POL->spill16[0], 16);
    CHECK(dram_share(16) == 0, "stale heartbeat (daemon gone): the published ratio is ignored");

    puts("B1.2 overflow and back-pressure");
    uint32_t n0 = cxlp_dev_nseg(0), n1 = cxlp_dev_nseg(1), n2 = cxlp_dev_nseg(2);
    for (uint32_t i = 0; i < n0; i++) cxlp_seg_claim(0, CXLP_SEG_BUFSET);
    for (uint32_t i = 0; i < n1; i++) cxlp_seg_claim(1, CXLP_SEG_BUFSET);
    cxlp_res_t r, held;
    fake_daemon(0, 0); CHECK(cxlp_reserve(1000, NULL, &r) == -1, "CXL has no space and DRAM is over the bound: reserve fails (caller waits)");
    fake_daemon(0, 1); CHECK(cxlp_reserve(1000, NULL, &r) == 0 && cxlp_dev_kind(r.dev) == CXLP_DEV_DRAM, "CXL has no space and DRAM is calm: overflow to DRAM");
    cxlp_release(&r); cxlp_thread_seal();
    for (uint32_t i = 0; i + 1 < n2; i++) cxlp_seg_claim(2, CXLP_SEG_BUFSET);
    CHECK(cxlp_reserve(CXLP_SEG_BYTES, NULL, &held) == 0, "last free segment"); cxlp_commit(&held); cxlp_thread_seal();
    cxlp_hints_t w = { 0, 0, -1, 0, 100 }; uint64_t t0 = cxlp_now_ns();
    CHECK(cxlp_reserve(1000, &w, &r) == -1 && cxlp_now_ns() - t0 >= 95000000ull, "everything full: reserve blocks for wait_ms, then fails");
    pthread_t th; pthread_create(&th, NULL, late_release, &held);
    w.wait_ms = 3000; t0 = cxlp_now_ns(); int rc = cxlp_reserve(1000, &w, &r); double waited = (cxlp_now_ns() - t0) / 1e6;
    pthread_join(th, NULL);
    printf("  blocked reserve woke after %.0f ms (segment was released at 300 ms)\n", waited);
    CHECK(rc == 0 && waited >= 290 && waited < 400, "blocked reserve is woken by the release");
    for (int d = 0; d < 3; d++) for (uint32_t i = 0; i < cxlp_dev_nseg(d); i++) cxlp_seg_release(d, i);
    atomic_store(&POL->daemon_pid, 0);

    puts("B1.3 a real cxlpathd publishes a changed ratio within one epoch");
    pid_t dpid = fork();
    if (dpid == 0) { execl("build/cxlpathd", "cxlpathd", cfg.name, "--no-calibrate", (char *)NULL); _exit(127); }
    int up = 0; for (int i = 0; i < 100 && !up; i++) { usleep(50000); up = cxlp_policy_daemon_alive(); }
    CHECK(up, "daemon is alive (heartbeat in shared memory)");
    cxlp_policy_view_t v; cxlp_policy_view(0, &v);
    printf("  daemon: base %.1f ns per load, bound %.2f\n", v.base_ns, v.bound);
    CHECK(v.spill16 == 0 && dram_share(16) == 0, "idle daemon publishes spill 0");
    cxlp_policy_force(8); t0 = cxlp_now_ns(); while (atomic_load(&POL->spill16[0]) != 8 && cxlp_now_ns() - t0 < 2000000000ull) usleep(1000);
    double lat = (cxlp_now_ns() - t0) / 1e6; printf("  ratio change visible to reserve() after %.0f ms (idle epoch = 200 ms)\n", lat);
    CHECK(lat <= 250, "published within one epoch"); CHECK(dram_share(160) == 80, "reserve() follows the daemon's ratio");
    cxlp_policy_force(-1); kill(dpid, SIGTERM); int st; waitpid(dpid, &st, 0);
    CHECK(WIFEXITED(st) && WEXITSTATUS(st) == 0 && atomic_load(&POL->daemon_pid) == 0, "daemon exits cleanly on SIGTERM");
    cxlp_close(); cxlp_destroy(cfg.name); unlink(dd);
    puts(fails ? "FAIL" : "PASS"); return fails != 0;
}
