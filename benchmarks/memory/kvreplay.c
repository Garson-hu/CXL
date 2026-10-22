/* kvreplay — physical replay of a KV-cache HOST-WRITE LOG on c28 (2026-10-21 hardware validation of the Phase 3 joint benefit analysis).
 *
 * Input: the write log of `kv_joint_sim.py --write-log` ("S <offer wall s> <D|C> <bytes> <scored> <id> <hash-share candidate> <credit>")
 * and a window [t0, t1) of log time. Every store becomes one job due at START + (offer - t0). A pinned worker thread takes the next job in
 * due order, sleeps until it is due, chooses the tier (from the log, or LIVE with a token bucket on the hash-share candidates = the
 * simulator's independent budget-gated split decided on the real clock), writes the block into the next slot of that tier's arena with
 * the chosen store primitive, paced at the per-stream link rate (as kvemu2 on 2026-10-11/12: one block stream = one GPU->host DMA link,
 * 9.5 GB/s), and records start / end. CXL-targeted stores go to the DAX device when it can be opened; otherwise they are COUNTED but NOT
 * ISSUED, and the output says so.
 *
 * This is a CPU REPLAY of the traffic shape — non-temporal stores from a cache-resident pseudo-random source (no DRAM reads, like a DMA
 * write) — not GPU DMA and not the LMCache runtime. `--store plain` (regular stores: read-for-ownership + write-back) and `--store none`
 * (the same thread activity into a 32 KiB L1-resident buffer: CPU overhead without memory traffic) are the controls.
 *
 * usage: kvreplay <writelog> <t0_s> <t1_s> <dram_GiB> [--workers 64] [--cpu0 96 | --cpus a-b,c-d,...] [--cxl-dev PATH] [--cxl-GiB 8]
 *        [--link-GBps 9.5] [--store nt|plain|none] [--budget GBps --depth blocks] [--wait-file PATH] [--log-ms 10] [--logger-cpu 95]
 * output: "# ..." header lines; "READY" (arenas mapped and pre-faulted; with --wait-file the run starts when that file appears);
 *         "START <mono_ns>"; every log-ms "W <mono_ns> <offered_GBps> <dram_GBps> <cxl_GBps> <skipped_GBps> <backlog_GB> <late_max_ms> <busy> <inflight>"
 *         (offered = bytes due in the bin; backlog = bytes due so far minus bytes completed or skipped); after the run one
 *         "R <offer_s> <due_ms> <start_ms> <end_ms> <bytes> <D|C> <issued> <cand> <scored>" per store (ms relative to START) and "S ..." summaries.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <immintrin.h>
#include <pthread.h>
#include <sched.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <time.h>
#include <unistd.h>

#define MiB (1ull << 20)
#define GiB (1ull << 30)
#define PIECE (2 * MiB)
static uint64_t now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return (uint64_t)t.tv_sec * 1000000000ull + (uint64_t)t.tv_nsec; }
static void pin_cpu(int c) { cpu_set_t s; CPU_ZERO(&s); CPU_SET(c, &s); pthread_setaffinity_np(pthread_self(), sizeof s, &s); }
static void sleep_until(uint64_t t) { uint64_t n = now(); if (t > n) { struct timespec d = { (time_t)((t - n) / 1000000000ull), (long)((t - n) % 1000000000ull) }; nanosleep(&d, NULL); } }

typedef struct { double offer; uint64_t due; uint32_t bytes; uint8_t tier_log, cand, scored, tier, issued; uint64_t start, end; } job_t;
static job_t *J; static size_t NJ; static _Atomic size_t next_job; static _Atomic uint32_t busy, inflight;
static _Atomic uint64_t done_bytes[2], skipped_bytes, late_max_ns, n_issued[2], n_skipped;
static char *base[2]; static uint64_t nslot[2], slot_bytes; static _Atomic uint64_t slot_next[2];
static char *src; static double link_Bps = 9.5e9; static int store_mode = 0;   /* 0 nt, 1 plain, 2 none */
static uint64_t t_start; static volatile int stop_all; static uint64_t log_ms = 10; static int logger_cpu = 95; static volatile uint64_t log_end;
static double bud_Bps = -1, bud_cap, credit; static uint64_t credit_t; static pthread_mutex_t bm = PTHREAD_MUTEX_INITIALIZER;
static _Atomic uint64_t n_cand, n_granted, n_refused;

static void write_block(char *dst, uint32_t bytes, int tier, uint64_t t0, char *mine) {
    for (size_t off = 0; off < bytes; off += PIECE) {
        size_t n = bytes - off < PIECE ? bytes - off : PIECE;
        if (store_mode == 0) { for (size_t i = 0; i < n; i += 32) _mm256_stream_si256((__m256i *)(dst + off + i), _mm256_load_si256((const __m256i *)(src + i))); _mm_sfence(); }
        else if (store_mode == 1) { for (size_t i = 0; i < n; i += 32) _mm256_store_si256((__m256i *)(dst + off + i), _mm256_load_si256((const __m256i *)(src + i))); }
        else { for (size_t i = 0; i < n; i += 32) _mm256_store_si256((__m256i *)(mine + (i & 32767)), _mm256_load_si256((const __m256i *)(src + i))); }
        atomic_fetch_add(&done_bytes[tier], n);                                  /* per 2 MiB piece, so the 10 ms rates are right */
        if (link_Bps > 0) sleep_until(t0 + (uint64_t)((off + n) / link_Bps * 1e9));
    }
}
static void *worker(void *a) {
    pin_cpu((int)(intptr_t)a); char *mine = aligned_alloc(64, 32768); memset(mine, 1, 32768);
    for (;;) {
        size_t k = atomic_fetch_add(&next_job, 1); if (k >= NJ || stop_all) break;
        job_t *j = &J[k]; atomic_fetch_add(&inflight, 1);
        sleep_until(j->due);
        uint64_t t0 = now(); atomic_fetch_add(&busy, 1);
        uint64_t late = t0 - j->due, m = atomic_load(&late_max_ns); while (late > m && !atomic_compare_exchange_weak(&late_max_ns, &m, late)) {}
        int tier = j->tier_log;
        if (bud_Bps >= 0) {                                                      /* LIVE bucket on the hash-share candidates, real clock */
            if (j->cand) {
                atomic_fetch_add(&n_cand, 1); pthread_mutex_lock(&bm);
                credit += bud_Bps * (double)(t0 - credit_t) / 1e9; if (credit > bud_cap) credit = bud_cap; credit_t = t0;
                if (credit >= j->bytes && nslot[0]) { credit -= j->bytes; tier = 0; atomic_fetch_add(&n_granted, 1); } else { tier = 1; atomic_fetch_add(&n_refused, 1); }
                pthread_mutex_unlock(&bm);
            } else tier = 1;
        }
        j->tier = (uint8_t)tier; j->start = t0;
        if (base[tier]) { uint64_t s = atomic_fetch_add(&slot_next[tier], 1) % nslot[tier]; write_block(base[tier] + s * slot_bytes, j->bytes, tier, t0, mine); j->issued = 1; atomic_fetch_add(&n_issued[tier], 1); }
        else { atomic_fetch_add(&skipped_bytes, j->bytes); atomic_fetch_add(&n_skipped, 1); j->issued = 0; }
        j->end = now(); atomic_fetch_sub(&busy, 1); atomic_fetch_sub(&inflight, 1);
    }
    return NULL;
}
static void *logger(void *a) {
    (void)a; pin_cpu(logger_cpu); size_t oi = 0; uint64_t off_cum = 0, loff = 0, ld0 = 0, ld1 = 0, lsk = 0; double dt = log_ms / 1e3;
    for (size_t bi = 1;; bi++) {
        uint64_t tw = t_start + bi * log_ms * 1000000ull; sleep_until(tw);
        while (oi < NJ && J[oi].due <= tw) { off_cum += J[oi].bytes; oi++; }
        uint64_t d0 = atomic_load(&done_bytes[0]), d1 = atomic_load(&done_bytes[1]), sk = atomic_load(&skipped_bytes);
        double backlog = ((double)off_cum - (double)(d0 + d1 + sk)) / 1e9;
        printf("W %lu %.3f %.3f %.3f %.3f %.3f %.2f %u %u\n", (unsigned long)tw, (off_cum - loff) / dt / 1e9, (d0 - ld0) / dt / 1e9, (d1 - ld1) / dt / 1e9, (sk - lsk) / dt / 1e9,
               backlog > 0 ? backlog : 0, atomic_exchange(&late_max_ns, 0) / 1e6, atomic_load(&busy), atomic_load(&inflight));
        loff = off_cum; ld0 = d0; ld1 = d1; lsk = sk;
        if (log_end && tw >= log_end) return NULL;
    }
}
static char *map_arena(const char *dev, size_t bytes, const char **why) {
    char *p;
    if (!dev) { p = mmap(NULL, bytes, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0); if (p == MAP_FAILED) { *why = strerror(errno); return NULL; } madvise(p, bytes, MADV_HUGEPAGE); }
    else { int fd = open(dev, O_RDWR); if (fd < 0) { *why = strerror(errno); return NULL; } p = mmap(NULL, bytes, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0); if (p == MAP_FAILED) { *why = strerror(errno); return NULL; } }
    for (size_t off = 0; off < bytes; off += PIECE) { for (size_t i = 0; i < PIECE; i += 32) _mm256_stream_si256((__m256i *)(p + off + i), _mm256_load_si256((const __m256i *)(src + i))); }
    _mm_sfence(); return p;
}
static int cmp_job(const void *a, const void *b) { double x = ((const job_t *)a)->offer, y = ((const job_t *)b)->offer; return x < y ? -1 : x > y; }
static int cmp_u64(const void *a, const void *b) { uint64_t x = *(const uint64_t *)a, y = *(const uint64_t *)b; return x < y ? -1 : x > y; }
static double qv(uint64_t *v, size_t n, double p) { if (!n) return 0; return v[(size_t)(p * (n - 1))] / 1e6; }

int main(int argc, char **argv) {
    if (argc < 5) { fprintf(stderr, "usage: see the header of kvreplay.c\n"); return 2; }
    const char *log = argv[1]; double t0 = atof(argv[2]), t1 = atof(argv[3]), dram_gib = atof(argv[4]);
    int W = 64, cpu0 = 96; const char *cpus = NULL, *cxl_dev = NULL, *wait_file = NULL; double cxl_gib = 8, depth = 1;
    for (int i = 5; i < argc; i++) {
        if (!strcmp(argv[i], "--workers")) W = atoi(argv[++i]); else if (!strcmp(argv[i], "--cpu0")) cpu0 = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--cpus")) cpus = argv[++i]; else if (!strcmp(argv[i], "--cxl-dev")) cxl_dev = argv[++i];
        else if (!strcmp(argv[i], "--cxl-GiB")) cxl_gib = atof(argv[++i]); else if (!strcmp(argv[i], "--link-GBps")) link_Bps = atof(argv[++i]) * 1e9;
        else if (!strcmp(argv[i], "--store")) { const char *m = argv[++i]; store_mode = !strcmp(m, "nt") ? 0 : !strcmp(m, "plain") ? 1 : 2; }
        else if (!strcmp(argv[i], "--budget")) bud_Bps = atof(argv[++i]) * 1e9; else if (!strcmp(argv[i], "--depth")) depth = atof(argv[++i]);
        else if (!strcmp(argv[i], "--wait-file")) wait_file = argv[++i]; else if (!strcmp(argv[i], "--log-ms")) log_ms = (uint64_t)atol(argv[++i]);
        else if (!strcmp(argv[i], "--logger-cpu")) logger_cpu = atoi(argv[++i]); else { fprintf(stderr, "unknown option %s\n", argv[i]); return 2; }
    }
    /* ---- the log ---- */
    FILE *f = fopen(log, "r"); if (!f) { perror(log); return 1; }
    char *line = NULL; size_t lcap = 0, cap = 0; uint32_t bmax = 0; size_t nD = 0, nC = 0, nS = 0, nall = 0;
    while (getline(&line, &lcap, f) > 0) {
        if (line[0] != 'S') continue;
        double off, fbytes; char tier; int sc, cand; char id[80]; double cr;
        if (sscanf(line + 2, "%lf %c %lf %d %79s %d %lf", &off, &tier, &fbytes, &sc, id, &cand, &cr) < 6) continue;   /* bytes may be printed as a float */
        uint32_t bytes = (uint32_t)(fbytes + 0.5); bytes -= bytes % 32;
        nall++; if (off < t0 || off >= t1) continue;
        if (NJ == cap) { cap = cap ? 2 * cap : 1 << 16; J = realloc(J, cap * sizeof *J); }
        J[NJ++] = (job_t){ off, 0, bytes, (uint8_t)(tier == 'D' ? 0 : 1), (uint8_t)cand, (uint8_t)sc, 0, 0, 0, 0 };
        if (bytes > bmax) bmax = bytes;
        if (tier == 'D') nD++; else nC++;
        if (sc) nS++;
    }
    fclose(f); qsort(J, NJ, sizeof *J, cmp_job);
    if (!NJ) { fprintf(stderr, "no stores in [%g, %g)\n", t0, t1); return 1; }
    slot_bytes = (bmax + PIECE - 1) / PIECE * PIECE;
    src = aligned_alloc(4096, PIECE); { uint64_t x = 0xD6E8FEB86659FD93ull; for (size_t i = 0; i < PIECE; i += 8) { x ^= x << 13; x ^= x >> 7; x ^= x << 17; *(uint64_t *)(src + i) = x; } }
    /* ---- arenas ---- */
    const char *why = NULL;
    if (store_mode == 2) dram_gib = 0.004;                                        /* control: nothing is written to the arena */
    nslot[0] = (uint64_t)(dram_gib * GiB / slot_bytes); if (nslot[0] < 1) nslot[0] = 1;
    base[0] = map_arena(NULL, nslot[0] * slot_bytes, &why); if (!base[0]) { fprintf(stderr, "DRAM arena: %s\n", why); return 1; }
    if (cxl_dev && store_mode != 2) {
        nslot[1] = (uint64_t)(cxl_gib * GiB / slot_bytes); if (nslot[1] < 1) nslot[1] = 1;
        base[1] = map_arena(cxl_dev, nslot[1] * slot_bytes, &why);
        if (!base[1]) printf("# cxl-dev %s: %s -> CXL-targeted stores are COUNTED but NOT ISSUED\n", cxl_dev, why);
    } else if (store_mode != 2) printf("# no --cxl-dev: CXL-targeted stores are COUNTED but NOT ISSUED\n");
    if (bud_Bps >= 0) { bud_cap = depth * bmax; credit = bud_cap; }
    /* ---- cpus ---- */
    int cpu_list[512], ncpu = 0;
    if (cpus) { char *c = strdup(cpus), *tok = strtok(c, ","); while (tok && ncpu < 512) { int a, b; if (sscanf(tok, "%d-%d", &a, &b) == 2) { for (int x = a; x <= b && ncpu < 512; x++) cpu_list[ncpu++] = x; } else cpu_list[ncpu++] = atoi(tok); tok = strtok(NULL, ","); } }
    else for (int i = 0; i < W; i++) cpu_list[ncpu++] = cpu0 + (i % 32) + 128 * ((i / 32) % 2);   /* kvemu2's pattern: CCDs 6-7 and their SMT siblings */
    printf("# kvreplay %s [%g, %g) s: %zu stores of %zu in the log (D %zu, C %zu, scored %zu), bytes/store %u, slot %lu MiB; DRAM arena %.1f GiB (%lu slots); CXL %s (%lu slots); "
           "%d workers on cpus %s (first %d); link %.2f GB/s per stream; store %s; bucket %s; log %lu ms\n",
           log, t0, t1, NJ, nall, nD, nC, nS, bmax, (unsigned long)(slot_bytes / MiB), dram_gib, (unsigned long)nslot[0], base[1] ? cxl_dev : "NOT ISSUED", (unsigned long)nslot[1],
           W, cpus ? cpus : "cpu0 pattern", cpu_list[0], link_Bps / 1e9, store_mode == 0 ? "nt" : store_mode == 1 ? "plain" : "none (CPU-only control)",
           bud_Bps >= 0 ? "live" : "from the log", (unsigned long)log_ms);
    if (bud_Bps >= 0) printf("# live bucket: %.2f GB/s, depth %.1f blocks (%.1f MB)\n", bud_Bps / 1e9, depth, bud_cap / 1e6);
    printf("READY\n"); fflush(stdout);
    if (wait_file) while (access(wait_file, F_OK) != 0) usleep(10000);
    t_start = now() + 100000000ull; for (size_t k = 0; k < NJ; k++) J[k].due = t_start + (uint64_t)((J[k].offer - t0) * 1e9);
    printf("START %lu\n", (unsigned long)t_start); fflush(stdout);
    credit_t = t_start;
    pthread_t th[512], lg;
    for (int i = 0; i < W && i < 512; i++) pthread_create(&th[i], NULL, worker, (void *)(intptr_t)cpu_list[i % ncpu]);
    pthread_create(&lg, NULL, logger, NULL);
    uint64_t last_due = J[NJ - 1].due;
    while (atomic_load(&next_job) < NJ || atomic_load(&inflight)) { usleep(10000); if (now() > last_due + 300000000000ull) { stop_all = 1; break; } }
    for (int i = 0; i < W && i < 512; i++) pthread_join(th[i], NULL);
    log_end = now(); pthread_join(lg, NULL);
    double wall = (log_end - t_start) / 1e9;
    /* ---- records and summary ---- */
    uint64_t *lat = malloc(NJ * 8), *lend = malloc(NJ * 8); size_t nl = 0; uint64_t off_tot[2] = { 0, 0 }, done_tot[2] = { 0, 0 }, skipped = 0, last_end = t_start;
    for (size_t k = 0; k < NJ; k++) {
        job_t *j = &J[k];
        if (!j->start) continue;
        printf("R %.6f %.1f %.1f %.1f %u %c %d %d %d\n", j->offer, (j->due - t_start) / 1e6, (j->start - t_start) / 1e6, (j->end - t_start) / 1e6, j->bytes, j->tier ? 'C' : 'D', j->issued, j->cand, j->scored);
        lat[nl] = j->start - j->due; lend[nl] = j->end - j->due; nl++;
        if (j->issued) { off_tot[j->tier] += j->bytes; done_tot[j->tier] += j->bytes; } else skipped += j->bytes;
        if (j->end > last_end) last_end = j->end;
    }
    qsort(lat, nl, 8, cmp_u64); qsort(lend, nl, 8, cmp_u64);
    struct rusage ru; getrusage(RUSAGE_SELF, &ru);
    printf("S stores %zu started %zu issued_dram %lu issued_cxl %lu skipped %lu bytes_dram_GB %.3f bytes_cxl_GB %.3f bytes_skipped_GB %.3f wall_s %.3f active_s %.3f\n",
           NJ, nl, (unsigned long)n_issued[0], (unsigned long)n_issued[1], (unsigned long)n_skipped, done_tot[0] / 1e9, done_tot[1] / 1e9, skipped / 1e9, wall, (last_end - t_start) / 1e9);
    printf("S start_delay_ms p50 %.2f p90 %.2f p99 %.2f max %.2f | completion_after_due_ms p50 %.2f p90 %.2f p99 %.2f max %.2f\n",
           qv(lat, nl, .5), qv(lat, nl, .9), qv(lat, nl, .99), qv(lat, nl, 1.0), qv(lend, nl, .5), qv(lend, nl, .9), qv(lend, nl, .99), qv(lend, nl, 1.0));
    printf("S bucket cand %lu granted %lu refused %lu\n", (unsigned long)n_cand, (unsigned long)n_granted, (unsigned long)n_refused);
    printf("S cpu_user_s %.2f cpu_sys_s %.2f stopped_early %d\n", ru.ru_utime.tv_sec + ru.ru_utime.tv_usec / 1e6, ru.ru_stime.tv_sec + ru.ru_stime.tv_usec / 1e6, stop_all);
    return 0;
}
