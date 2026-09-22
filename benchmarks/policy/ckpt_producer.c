/* ckpt_producer — a periodic checkpoint copy beside a running victim, under one of the simple policies
 * or through cxlpath. A snapshot of S GiB lives in DRAM (as a training state does); every period it is
 * copied, in 32 MiB chunks by T threads, to:
 *   dram          a DRAM staging buffer, NT stores, full speed          (today's practice)
 *   dram-plain    the same with plain stores (RFO + writeback)           (what a memcpy/tensor.copy_ does)
 *   dram-limited  DRAM staging, NT stores, paced at --rate GiB/s          (throttled writer)
 *   cxl           /dev/dax0.0 at offset 64 GiB, NT stores, full speed     (everything to CXL)
 *   cxlpath       reserve / copy_to / commit through the runtime; the daemon decides per chunk
 * Prints one line per period: COPY <i> START <mono ns> END <mono ns> bytes=<> GiBs=<> dram_share=<0..1>
 * Threads are placed 4 per CCD starting at <first_cpu> (cpus c, c+1, c+2, c+3, c+16, ...).
 * usage: ckpt_producer <policy> <snapshot_GiB> <threads> <first_cpu> <period_s> <periods> [--rate G] [--store NAME] [--dax-offset-gib 64] */
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
#include <time.h>
#include <unistd.h>
#include <sys/mman.h>
#include "cxlpath.h"
#define CH (32ul << 20)
static uint64_t now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return (uint64_t)t.tv_sec * 1000000000ull + (uint64_t)t.tv_nsec; }
static void pin(int c) { cpu_set_t s; CPU_ZERO(&s); CPU_SET(c, &s); pthread_setaffinity_np(pthread_self(), sizeof s, &s); }
static void *anon(size_t n) { void *p = mmap(NULL, n, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0); if (p == MAP_FAILED) { perror("mmap"); exit(1); } madvise(p, n, MADV_HUGEPAGE); return p; }
static void nt_copy(char *d, const char *s, size_t n) { for (size_t i = 0; i < n; i += 32) _mm256_stream_si256((__m256i *)(d + i), _mm256_load_si256((const __m256i *)(s + i))); _mm_sfence(); }
static void plain_copy(char *d, const char *s, size_t n) { for (size_t i = 0; i < n; i += 32) _mm256_store_si256((__m256i *)(d + i), _mm256_load_si256((const __m256i *)(s + i))); }

enum { P_DRAM, P_PLAIN, P_LIMITED, P_CXL, P_CXLPATH };
static void *fill_thread(void *a);
static int policy, nthr, cpu0; static size_t S; static double rate_bps; static char *src, *dst;
static pthread_barrier_t bar; static volatile int quit;
static _Atomic uint64_t dram_bytes, cxl_bytes; static _Atomic int done_threads;
static cxlp_res_t *held; static _Atomic uint32_t nheld;      /* cxlpath reservations of the current period */
static uint64_t t_period_start;

static void *fill_thread(void *a) {
    long id = (long)a; pin(cpu0 + (int)(id % 4) + 16 * (int)(id / 4)); size_t per = S / 8; uint64_t x = 0x9E3779B97F4A7C15ull * (uint64_t)(id + 1);
    for (size_t i = (size_t)id * per; i < (size_t)(id + 1) * per; i += 8) { x ^= x << 13; x ^= x >> 7; x ^= x << 17; *(uint64_t *)(src + i) = x; }
    return NULL;
}
static void *worker(void *a) {
    long id = (long)a; pin(cpu0 + (int)(id % 4) + 16 * (int)(id / 4)); size_t per = S / (size_t)nthr, off0 = (size_t)id * per;   /* 4 threads per CCD: one CCD's port caps NT writes at ~65-77 GiB/s */
    cxlp_hints_t h = { 0, 0, -1, 2, 20000 };
    for (;;) {
        pthread_barrier_wait(&bar); if (quit) break;
        uint64_t sent = 0;
        for (size_t off = off0; off < off0 + per; off += CH) {
            if (policy == P_CXLPATH) {
                cxlp_res_t r; if (cxlp_reserve(CH, &h, &r)) { fprintf(stderr, "reserve failed\n"); exit(2); }
                cxlp_copy_to(&r, 0, src + off, CH); cxlp_commit(&r);
                held[atomic_fetch_add(&nheld, 1)] = r;
                if (cxlp_dev_kind(r.dev) == CXLP_DEV_DRAM) atomic_fetch_add(&dram_bytes, CH); else atomic_fetch_add(&cxl_bytes, CH);
            } else if (policy == P_PLAIN) plain_copy(dst + off, src + off, CH);
            else nt_copy(dst + off, src + off, CH);
            sent += CH;
            if (policy == P_LIMITED) { uint64_t due = t_period_start + (uint64_t)((double)sent / (rate_bps / nthr) * 1e9); while (now() < due) _mm_pause(); }
        }
        atomic_fetch_add(&done_threads, 1); pthread_barrier_wait(&bar);
    }
    return NULL;
}
int main(int argc, char **argv) {
    if (argc < 7) { fprintf(stderr, "usage\n"); return 2; }
    const char *pol = argv[1]; S = (size_t)atol(argv[2]) << 30; nthr = atoi(argv[3]); cpu0 = atoi(argv[4]); double period = atof(argv[5]); int periods = atoi(argv[6]); const char *store = "policy";
    uint64_t dax_off = 64ul << 30;
    for (int i = 7; i + 1 < argc; i++) { if (!strcmp(argv[i], "--rate")) rate_bps = atof(argv[i + 1]) * 1073741824.0; if (!strcmp(argv[i], "--store")) store = argv[i + 1]; if (!strcmp(argv[i], "--dax-offset-gib")) dax_off = (uint64_t)atol(argv[i + 1]) << 30; }
    policy = !strcmp(pol, "dram") ? P_DRAM : !strcmp(pol, "dram-plain") ? P_PLAIN : !strcmp(pol, "dram-limited") ? P_LIMITED : !strcmp(pol, "cxl") ? P_CXL : !strcmp(pol, "cxlpath") ? P_CXLPATH : -1;
    if (policy < 0 || (policy == P_LIMITED && rate_bps <= 0)) { fprintf(stderr, "bad policy\n"); return 2; }
    pin(cpu0);
    /* The training state: pseudo-random fp-like data, filled by the copy threads' cpus. NOT a sparse touch: on c28 a
     * cache line that is all zeros is written at near-full speed beside a co-running program while any non-zero
     * line is not (2026-09-22-zero-line-writes.md), so a mostly-zero snapshot measures the wrong thing. */
    src = anon(S); { pthread_t ft[8]; for (long i = 0; i < 8; i++) pthread_create(&ft[i], NULL, fill_thread, (void *)i); for (int i = 0; i < 8; i++) pthread_join(ft[i], NULL); }
    if (policy == P_CXL) { int fd = open("/dev/dax0.0", O_RDWR); if (fd < 0) { perror("dax"); return 1; } dst = mmap(NULL, S, PROT_READ | PROT_WRITE, MAP_SHARED, fd, (off_t)dax_off); if (dst == MAP_FAILED) { perror("mmap dax"); return 1; } }
    else if (policy == P_CXLPATH) { if (cxlp_attach(store)) { fprintf(stderr, "no store %s\n", store); return 1; } held = calloc(S / CH + 16, sizeof *held); }
    else { dst = anon(S); for (size_t i = 0; i < S; i += 4096) *(uint64_t *)(dst + i) = 1; }                     /* staging buffer, touched once */
    pthread_barrier_init(&bar, NULL, (unsigned)nthr + 1); pthread_t th[256]; for (long i = 0; i < nthr; i++) pthread_create(&th[i], NULL, worker, (void *)i);
    printf("READY %llu policy=%s snapshot_GiB=%zu threads=%d\n", (unsigned long long)now(), pol, S >> 30, nthr); fflush(stdout);
    uint64_t next = now();
    for (int p = 0; p < periods; p++) {
        while (now() < next) usleep(1000);
        if (policy == P_CXLPATH) { for (uint32_t i = 0; i < atomic_load(&nheld); i++) cxlp_release(&held[i]); atomic_store(&nheld, 0); cxlp_thread_seal(); }   /* previous version is dead */
        atomic_store(&dram_bytes, 0); atomic_store(&cxl_bytes, 0); atomic_store(&done_threads, 0);
        t_period_start = now(); pthread_barrier_wait(&bar); pthread_barrier_wait(&bar); uint64_t t1 = now();
        double share = policy == P_CXLPATH ? (double)atomic_load(&dram_bytes) / (double)(atomic_load(&dram_bytes) + atomic_load(&cxl_bytes)) : (policy == P_CXL ? 0.0 : 1.0);
        printf("COPY %d START %llu END %llu bytes=%zu GiBs=%.2f dram_share=%.3f\n", p, (unsigned long long)t_period_start, (unsigned long long)t1, S, (double)S / ((t1 - t_period_start) / 1e9) / 1073741824.0, share); fflush(stdout);
        next += (uint64_t)(period * 1e9);
    }
    quit = 1; pthread_barrier_wait(&bar); for (int i = 0; i < nthr; i++) pthread_join(th[i], NULL);
    if (policy == P_CXLPATH) { for (uint32_t i = 0; i < atomic_load(&nheld); i++) cxlp_release(&held[i]); cxlp_thread_seal(); cxlp_close(); }
    printf("DONE %llu\n", (unsigned long long)now()); return 0;
}
