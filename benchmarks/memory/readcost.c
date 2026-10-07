/* readcost — how much slower is a read from CXL memory than from DRAM on c28? (2026-10-07)
 *   lat   : one thread follows a random chain of 64-byte lines through 1 GiB (every read waits for the previous one)
 *   bw    : T threads stream through their own 256 MiB slices, T = 1, 2, 4, 8, 16, 2 s each
 *   burst : the same readers (4 streaming threads, then 1 chain thread) while 8 other threads copy pseudo-random data
 *           from DRAM into DRAM or into CXL (a checkpoint copy running at the same time)
 * DRAM = anonymous memory with huge pages; CXL = /dev/dax0.0 at offset 64 GiB (2 MiB pages, no store there).
 * Readers on four core groups (cpus 64.., 80.., 96.., 112..), writers on two others (cpus 0-3, 16-19).
 * usage: readcost [reps=3]  -> one line per measurement on stdout */
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
static uint64_t now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return (uint64_t)t.tv_sec * 1000000000ull + (uint64_t)t.tv_nsec; }
static void pin(int c) { cpu_set_t s; CPU_ZERO(&s); CPU_SET(c, &s); pthread_setaffinity_np(pthread_self(), sizeof s, &s); }
static const int rd_cpus[16] = { 64, 80, 96, 112, 65, 81, 97, 113, 66, 82, 98, 114, 67, 83, 99, 115 };
static const int wr_cpus[8] = { 0, 1, 2, 3, 16, 17, 18, 19 };

static char *dram, *cxl, *wsrc, *wdst_dram, *wdst_cxl;   /* dram / cxl: [0,4 GiB) streaming slices, [4,5 GiB) the chain */
static volatile int stop_rd, stop_wr;
static volatile long long sink;                        /* keeps the streaming loads alive */
static _Atomic uint64_t wr_bytes;

static char *huge(size_t n) {
    char *p = mmap(NULL, n, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (p == MAP_FAILED) { perror("mmap"); exit(1); }
    madvise(p, n, MADV_HUGEPAGE); return p;
}
static void fill_random(char *p, size_t n, uint64_t seed) {            /* data-carrying lines: never a zero page */
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
static double stream(char *base, int T, double secs) {
    pthread_t th[16]; rd_t r[16]; stop_rd = 0;
    for (int i = 0; i < T; i++) { r[i] = (rd_t){ base + (size_t)i * 256 * MiB, 256 * MiB, rd_cpus[i], 0, 0 }; pthread_create(&th[i], NULL, reader, &r[i]); }
    usleep((useconds_t)(secs * 1e6)); stop_rd = 1;
    double tot = 0; for (int i = 0; i < T; i++) { pthread_join(th[i], NULL); if (r[i].ns) tot += r[i].bytes / (r[i].ns / 1e9); }
    return tot / GiB;
}

/* one random cycle through the 64-byte lines of [base, base + len) */
static void build_chain(char *base, size_t len) {
    size_t n = len / 64; uint32_t *ord = malloc(n * sizeof *ord); uint64_t x = 0x9E3779B97F4A7C15ull;
    for (size_t i = 0; i < n; i++) ord[i] = (uint32_t)i;
    for (size_t i = n - 1; i > 0; i--) { x ^= x << 13; x ^= x >> 7; x ^= x << 17; size_t j = x % i; uint32_t t = ord[i]; ord[i] = ord[j]; ord[j] = t; }   /* Sattolo: one cycle */
    for (size_t i = 0; i < n; i++) *(char **)(base + (size_t)ord[i] * 64) = base + (size_t)ord[(i + 1) % n] * 64;
    free(ord);
}
typedef struct { char *start; uint64_t loads; int cpu; double ns_per; } ch_t;
static void *chase_thread(void *a) {
    ch_t *c = a; pin(c->cpu); char *p = c->start;
    for (int i = 0; i < 200000; i++) p = *(char **)p;                                 /* warm the TLB */
    uint64_t t0 = now(); for (uint64_t i = 0; i < c->loads; i++) p = *(char **)p; uint64_t t1 = now();
    c->ns_per = (t1 - t0) / (double)c->loads + (p == NULL); return NULL;
}
static double chase(char *start, uint64_t loads) { pthread_t th; ch_t c = { start, loads, rd_cpus[0], 0 }; pthread_create(&th, NULL, chase_thread, &c); pthread_join(th, NULL); return c.ns_per; }

typedef struct { char *dst; int cpu, id; } wr_t;
static void *writer(void *a) {
    wr_t *w = a; pin(w->cpu); size_t off = 0, CH = 32 * MiB; char *src = wsrc + (size_t)w->id * GiB, *dst = w->dst + (size_t)w->id * GiB;
    while (!stop_wr) {
        for (size_t i = 0; i < CH; i += 32) _mm256_stream_si256((__m256i *)(dst + off + i), _mm256_load_si256((const __m256i *)(src + off + i)));
        _mm_sfence(); atomic_fetch_add(&wr_bytes, CH); off = (off + CH) % GiB;
    }
    return NULL;
}

int main(int argc, char **argv) {
    int reps = argc > 1 ? atoi(argv[1]) : 3;
    int fd = open("/dev/dax0.0", O_RDWR); if (fd < 0) { perror("/dev/dax0.0"); return 1; }
    char *cx = mmap(NULL, 16 * GiB, PROT_READ | PROT_WRITE, MAP_SHARED, fd, (off_t)(64 * GiB)); if (cx == MAP_FAILED) { perror("mmap dax"); return 1; }
    cxl = cx; wdst_cxl = cx + 8 * GiB;
    dram = huge(5 * GiB); wsrc = huge(8 * GiB); wdst_dram = huge(8 * GiB);
    fill_random(dram, 4 * GiB, 1); fill_random(cxl, 4 * GiB, 2); fill_random(wsrc, 8 * GiB, 3);
    memset(wdst_dram, 1, 8 * GiB); fill_random(wdst_cxl, 8 * GiB, 4);
    build_chain(dram + 4 * GiB, GiB); build_chain(cxl + 4 * GiB, GiB);
    printf("# readcost c28 %s", ctime(&(time_t){ time(NULL) })); fflush(stdout);
    for (int rep = 1; rep <= reps; rep++) {
        printf("LAT rep=%d dram_ns=%.1f cxl_ns=%.1f\n", rep, chase(dram + 4 * GiB, 5000000), chase(cxl + 4 * GiB, 5000000)); fflush(stdout);
        for (int T = 1; T <= 16; T *= 2) { double a = stream(dram, T, 2.0), b = stream(cxl, T, 2.0); printf("BW rep=%d threads=%d dram_GiBs=%.2f cxl_GiBs=%.2f\n", rep, T, a, b); fflush(stdout); }
        const char *names[3] = { "none", "dram", "cxl" }; char *dsts[3] = { NULL, wdst_dram, wdst_cxl };
        for (int where = 0; where < 2; where++) for (int burst = 0; burst < 3; burst++) {
            char *base = where ? cxl : dram; pthread_t th[8]; wr_t w[8];
            stop_wr = 0; atomic_store(&wr_bytes, 0);
            if (burst) for (int i = 0; i < 8; i++) { w[i] = (wr_t){ dsts[burst], wr_cpus[i], i }; pthread_create(&th[i], NULL, writer, &w[i]); }
            usleep(500000); uint64_t t0 = now(), b0 = atomic_load(&wr_bytes);
            double bw = stream(base, 4, 2.0); double lat = chase(base + 4 * GiB, 2000000);
            double wr = (atomic_load(&wr_bytes) - b0) / ((now() - t0) / 1e9) / GiB;
            if (burst) { stop_wr = 1; for (int i = 0; i < 8; i++) pthread_join(th[i], NULL); }
            printf("BURST rep=%d read_from=%s copy_into=%s reader4_GiBs=%.2f chain_ns=%.1f writers_GiBs=%.2f\n", rep, where ? "cxl" : "dram", names[burst], bw, lat, burst ? wr : 0.0); fflush(stdout);
        }
    }
    return 0;
}
