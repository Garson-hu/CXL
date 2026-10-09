/* topo — does traffic to CXL memory slow down DRAM readers that run on the SAME core group (CCD)? (2026-10-09)
 * Motivation: arXiv 2503.17864 (MIKU) reports DDR bandwidth losses when DDR and CXL traffic share a core complex;
 * every c28 experiment so far kept writers and readers on different CCDs. c28 = EPYC 9745, 8 CCDs x 16 cores
 * (CCD k = cpus 16k..16k+15, one L3 each), NPS1.
 * Foreground (fixed on CCD 4): 4 threads stream through their own 256 MiB DRAM slices (cpus 64-67) for 3 s, then one
 * thread follows a random chain of 64-byte lines through 1 GiB (cpu 64): bandwidth and single-load latency.
 * Background (T threads, started 0.5 s before and running throughout), kinds:
 *   cxl_nt    non-temporal stores of random data from a 2 MiB cache-resident source into CXL   (pure CXL writes)
 *   copy_cxl  DRAM -> CXL copy with non-temporal stores                                       (a checkpoint copy)
 *   cxl_st    ordinary stores into CXL from a 2 MiB source                                    (read-for-ownership + writeback)
 *   cxl_rd    streaming loads from CXL
 *   dram_nt   non-temporal stores from a 2 MiB source into DRAM                               (reference)
 *   copy_dram DRAM -> DRAM copy with non-temporal stores                                      (reference: staging today)
 * Placements of the background threads: same = cpus 72.. (CCD 4, beside the readers), near = cpus 80.. (CCD 5),
 * far = cpus 0.. (CCD 0). T = 1, 2, 4, 8.
 * A second foreground "cxl" (stream and chain on CXL) runs a smaller set (T = 8, three kinds).
 * CXL = /dev/dax0.0 (cards c1+e1) at offset 64 GiB, 16 GiB mapped; DRAM = anonymous memory with huge pages.
 * usage: topo [reps=5] [dramonly]  -> one line per measurement on stdout
 *   dramonly: no CXL mapping; only the DRAM reference kinds with the DRAM foreground (used while /dev/dax* was root-only)
 * environment overrides: TOPO_PLACES="name:firstcpu,..." (default same:72,near:80,far:0), TOPO_THREADS="1,2,4,8" */
#define _GNU_SOURCE
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
#include <time.h>
#include <unistd.h>

#define GiB (1ull << 30)
#define MiB (1ull << 20)
#define SRC_SMALL (2 * MiB)
#define STREAM_S 3.0   /* 2.0 in the DRAM-only pilot runs of 2026-10-09 (topo-dramonly*.txt) */
static uint64_t now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return (uint64_t)t.tv_sec * 1000000000ull + (uint64_t)t.tv_nsec; }
static void pin(int c) { cpu_set_t s; CPU_ZERO(&s); CPU_SET(c, &s); pthread_setaffinity_np(pthread_self(), sizeof s, &s); }

enum { K_NONE, K_CXL_NT, K_COPY_CXL, K_CXL_ST, K_CXL_RD, K_DRAM_NT, K_COPY_DRAM, K_N };
static const char *kname[K_N] = { "none", "cxl_nt", "copy_cxl", "cxl_st", "cxl_rd", "dram_nt", "copy_dram" };
static char pname[16][16] = { "same", "near", "far" };
static int pbase[16] = { 72, 80, 0 }, nplace = 3;
static const int rd_cpus[4] = { 64, 65, 66, 67 };

static char *fg_dram, *fg_cxl;                       /* [0,1 GiB) streaming slices, [1 GiB, 2 GiB) the chain */
static char *bg_cxl, *bg_dsrc, *bg_ddst, *bg_small;  /* 8 x 1 GiB each; small = 8 x 2 MiB */
static volatile int stop_rd, stop_bg;
static volatile long long sink;
static _Atomic uint64_t bg_bytes;

static char *huge(size_t n) {
    char *p = mmap(NULL, n, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (p == MAP_FAILED) { perror("mmap"); exit(1); }
    madvise(p, n, MADV_HUGEPAGE); return p;
}
static void fill_random(char *p, size_t n, uint64_t seed) {
    uint64_t x = seed | 1; for (size_t i = 0; i < n; i += 8) { x ^= x << 13; x ^= x >> 7; x ^= x << 17; *(uint64_t *)(p + i) = x; }
}

typedef struct { char *base; size_t len; int cpu; uint64_t bytes, ns; } rd_t;
static void *reader(void *a) {
    rd_t *r = a; pin(r->cpu); __m256i acc = _mm256_setzero_si256(); uint64_t t0 = now(), t_last = t0, b = 0;
    while (!stop_rd) {
        for (size_t i = 0; i < r->len; i += 64) {
            acc = _mm256_add_epi64(acc, _mm256_load_si256((const __m256i *)(r->base + i)));
            acc = _mm256_add_epi64(acc, _mm256_load_si256((const __m256i *)(r->base + i + 32)));
        }
        b += r->len; t_last = now();
    }
    sink += _mm256_extract_epi64(acc, 0) + _mm256_extract_epi64(acc, 3); r->bytes = b; r->ns = t_last - t0; return NULL;
}
static double stream(char *base, double secs) {
    pthread_t th[4]; rd_t r[4]; stop_rd = 0;
    for (int i = 0; i < 4; i++) { r[i] = (rd_t){ base + (size_t)i * 256 * MiB, 256 * MiB, rd_cpus[i], 0, 0 }; pthread_create(&th[i], NULL, reader, &r[i]); }
    usleep((useconds_t)(secs * 1e6)); stop_rd = 1;
    double tot = 0; for (int i = 0; i < 4; i++) { pthread_join(th[i], NULL); if (r[i].ns) tot += r[i].bytes / (r[i].ns / 1e9); }
    return tot / GiB;
}
static void build_chain(char *base, size_t len) {
    size_t n = len / 64; uint32_t *ord = malloc(n * sizeof *ord); uint64_t x = 0x9E3779B97F4A7C15ull;
    for (size_t i = 0; i < n; i++) ord[i] = (uint32_t)i;
    for (size_t i = n - 1; i > 0; i--) { x ^= x << 13; x ^= x >> 7; x ^= x << 17; size_t j = x % i; uint32_t t = ord[i]; ord[i] = ord[j]; ord[j] = t; }
    for (size_t i = 0; i < n; i++) *(char **)(base + (size_t)ord[i] * 64) = base + (size_t)ord[(i + 1) % n] * 64;
    free(ord);
}
typedef struct { char *start; uint64_t loads; double ns_per; } ch_t;
static void *chase_thread(void *a) {
    ch_t *c = a; pin(rd_cpus[0]); char *p = c->start;
    for (int i = 0; i < 200000; i++) p = *(char **)p;
    uint64_t t0 = now(); for (uint64_t i = 0; i < c->loads; i++) p = *(char **)p; uint64_t t1 = now();
    c->ns_per = (t1 - t0) / (double)c->loads + (p == NULL); return NULL;
}
static double chase(char *start, uint64_t loads) { pthread_t th; ch_t c = { start, loads, 0 }; pthread_create(&th, NULL, chase_thread, &c); pthread_join(th, NULL); return c.ns_per; }

typedef struct { int kind, cpu, id; } bg_t;
static void *bg_thread(void *a) {
    bg_t *w = a; pin(w->cpu); const size_t CH = 32 * MiB; size_t off = 0; __m256i acc = _mm256_setzero_si256();
    char *small = bg_small + (size_t)w->id * SRC_SMALL, *dsrc = bg_dsrc + (size_t)w->id * GiB;
    char *cdst = bg_cxl + (size_t)w->id * GiB, *ddst = bg_ddst + (size_t)w->id * GiB;
    while (!stop_bg) {
        switch (w->kind) {
        case K_CXL_NT:    for (size_t i = 0; i < CH; i += 32) _mm256_stream_si256((__m256i *)(cdst + off + i), _mm256_load_si256((const __m256i *)(small + ((off + i) & (SRC_SMALL - 1))))); break;
        case K_COPY_CXL:  for (size_t i = 0; i < CH; i += 32) _mm256_stream_si256((__m256i *)(cdst + off + i), _mm256_load_si256((const __m256i *)(dsrc + off + i))); break;
        case K_CXL_ST:    for (size_t i = 0; i < CH; i += 32) _mm256_store_si256((__m256i *)(cdst + off + i), _mm256_load_si256((const __m256i *)(small + ((off + i) & (SRC_SMALL - 1))))); break;
        case K_CXL_RD:    for (size_t i = 0; i < CH; i += 64) { acc = _mm256_add_epi64(acc, _mm256_load_si256((const __m256i *)(cdst + off + i))); acc = _mm256_add_epi64(acc, _mm256_load_si256((const __m256i *)(cdst + off + i + 32))); } break;
        case K_DRAM_NT:   for (size_t i = 0; i < CH; i += 32) _mm256_stream_si256((__m256i *)(ddst + off + i), _mm256_load_si256((const __m256i *)(small + ((off + i) & (SRC_SMALL - 1))))); break;
        case K_COPY_DRAM: for (size_t i = 0; i < CH; i += 32) _mm256_stream_si256((__m256i *)(ddst + off + i), _mm256_load_si256((const __m256i *)(dsrc + off + i))); break;
        }
        _mm_sfence(); atomic_fetch_add(&bg_bytes, CH); off = (off + CH) % GiB;
    }
    sink += _mm256_extract_epi64(acc, 1);
    return NULL;
}

/* one measurement: start T background threads of `kind` at placement p, then measure the foreground */
static void cell(int rep, const char *fg, char *fgbase, int kind, int p, int T) {
    pthread_t th[8]; bg_t w[8];
    stop_bg = 0; atomic_store(&bg_bytes, 0);
    for (int i = 0; i < T && kind != K_NONE; i++) { w[i] = (bg_t){ kind, pbase[p] + i, i }; pthread_create(&th[i], NULL, bg_thread, &w[i]); }
    usleep(500000);
    uint64_t t0 = now(), b0 = atomic_load(&bg_bytes);
    double bw = stream(fgbase, STREAM_S), lat = chase(fgbase + GiB, 2000000);
    double bg = (atomic_load(&bg_bytes) - b0) / ((now() - t0) / 1e9) / GiB;
    if (kind != K_NONE) { stop_bg = 1; for (int i = 0; i < T; i++) pthread_join(th[i], NULL); }
    printf("CELL rep=%d fg=%s kind=%s place=%s threads=%d reader_GiBs=%.2f chain_ns=%.1f bg_GiBs=%.2f\n",
           rep, fg, kname[kind], kind == K_NONE ? "-" : pname[p], kind == K_NONE ? 0 : T, bw, lat, kind == K_NONE ? 0.0 : bg);
    fflush(stdout);
}

int main(int argc, char **argv) {
    int reps = argc > 1 ? atoi(argv[1]) : 5, dramonly = argc > 2 && !strcmp(argv[2], "dramonly");
    char *cx;
    if (dramonly) cx = huge(16 * GiB);                     /* stands in for the CXL buffers; never measured */
    else {
        int fd = open("/dev/dax0.0", O_RDWR); if (fd < 0) { perror("/dev/dax0.0"); return 1; }
        cx = mmap(NULL, 16 * GiB, PROT_READ | PROT_WRITE, MAP_SHARED, fd, (off_t)(64 * GiB)); if (cx == MAP_FAILED) { perror("mmap dax"); return 1; }
    }
    fg_cxl = cx; bg_cxl = cx + 8 * GiB;                    /* fg: [64, 66) GiB of dax0.0; bg: [72, 80) GiB */
    fg_dram = huge(2 * GiB); bg_dsrc = huge(8 * GiB); bg_ddst = huge(8 * GiB); bg_small = huge(8 * SRC_SMALL);
    fill_random(fg_dram, GiB, 1); fill_random(fg_cxl, GiB, 2); fill_random(bg_dsrc, 8 * GiB, 3); fill_random(bg_small, 8 * SRC_SMALL, 4);
    fill_random(bg_cxl, 8 * GiB, 5); memset(bg_ddst, 1, 8 * GiB);
    build_chain(fg_dram + GiB, GiB); build_chain(fg_cxl + GiB, GiB);
    printf("# topo c28%s %s", dramonly ? " DRAM-ONLY" : "", ctime(&(time_t){ time(NULL) })); fflush(stdout);
    int Ts[8] = { 1, 2, 4, 8 }, nT = 4;
    if (getenv("TOPO_PLACES")) {
        char buf[512]; snprintf(buf, sizeof buf, "%s", getenv("TOPO_PLACES")); nplace = 0;
        for (char *tok = strtok(buf, ","); tok && nplace < 16; tok = strtok(NULL, ",")) {
            char *c = strchr(tok, ':'); if (!c) continue; *c = 0;
            snprintf(pname[nplace], sizeof pname[0], "%s", tok); pbase[nplace++] = atoi(c + 1);
        }
    }
    if (getenv("TOPO_THREADS")) {
        char buf[64]; snprintf(buf, sizeof buf, "%s", getenv("TOPO_THREADS")); nT = 0;
        for (char *tok = strtok(buf, ","); tok && nT < 8; tok = strtok(NULL, ",")) Ts[nT++] = atoi(tok);
    }
    const int fg_cxl_kinds[3] = { K_CXL_NT, K_COPY_CXL, K_DRAM_NT };
    for (int rep = 1; rep <= reps; rep++) {
        for (int p = 0; p < nplace; p++) {
            cell(rep, "dram", fg_dram, K_NONE, p, 0);                       /* a baseline before every placement group */
            for (int k = dramonly ? K_DRAM_NT : K_CXL_NT; k < K_N; k++) for (int t = 0; t < nT; t++) cell(rep, "dram", fg_dram, k, p, Ts[t]);
        }
        if (dramonly) continue;
        cell(rep, "cxl", fg_cxl, K_NONE, 0, 0);
        for (int p = 0; p < nplace; p++) for (int k = 0; k < 3; k++) cell(rep, "cxl", fg_cxl, fg_cxl_kinds[k], p, 8);
    }
    return 0;
}
