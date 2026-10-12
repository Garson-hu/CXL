/* ckpt_cxl — periodic checkpoint copies DRAM -> CXL beside a KV cache that reads CXL (experiment 3, 2026-10-12).
 * Every <period_s> a burst copies <S_GiB> of pseudo-random data from DRAM into /dev/dax0.0 [offset 0, S) with 8 threads
 * (cpus 32-39), non-temporal stores, 2 MiB pieces. Modes:
 *   full    as fast as it goes (uncoordinated)
 *   rate    all threads together at most <rate_GBps>
 *   kvprio  before every piece, wait while the flag byte in /dev/shm/kvprio_flag is non-zero (set by kvprio_gate.py
 *           while the GPU reads from the host, i.e. while KV blocks are being loaded)
 * Optionally one thread on cpu 64 follows a random chain through 1 GiB of /dev/dax0.0 above the checkpoint area (a
 * latency-sensitive CPU reader of CXL): "R <mono_ns> <ns per load>" every 10 ms. Per burst: "C <n> <start_ns> <end_ns>
 * <GiB> paused_ms <ms>". Runs until SIGTERM.
 * usage: ckpt_cxl <S_GiB> <period_s> <full|rate|kvprio> [rate_GBps] [reader 0|1] */
#define _GNU_SOURCE
#include <fcntl.h>
#include <immintrin.h>
#include <pthread.h>
#include <sched.h>
#include <signal.h>
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
#define PIECE (2 * MiB)
static uint64_t now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return (uint64_t)t.tv_sec * 1000000000ull + (uint64_t)t.tv_nsec; }
static void pin_cpu(int c) { cpu_set_t s; CPU_ZERO(&s); CPU_SET(c, &s); pthread_setaffinity_np(pthread_self(), sizeof s, &s); }
static void sleep_until(uint64_t t) { uint64_t n = now(); if (t > n) { struct timespec d = { (time_t)((t - n) / 1000000000ull), (long)((t - n) % 1000000000ull) }; nanosleep(&d, NULL); } }
static volatile int stop; static void on_term(int s) { (void)s; stop = 1; }
static char *src, *dst, *chain; static size_t bytes; static int mode; static double rate_Bps; static volatile uint8_t *flag;
static _Atomic uint64_t clk, paused_ns; static pthread_barrier_t bar;
static void *writer(void *a) {
    int id = (int)(intptr_t)a; pin_cpu(32 + id); size_t per = bytes / 8, lo = (size_t)id * per;
    for (;;) {
        pthread_barrier_wait(&bar); if (stop) return NULL;
        for (size_t off = 0; off < per && !stop; off += PIECE) {
            if (mode == 2 && flag) { uint64_t w0 = 0; while (*flag && !stop) { if (!w0) w0 = now(); struct timespec d = { 0, 50000 }; nanosleep(&d, NULL); } if (w0) atomic_fetch_add(&paused_ns, now() - w0); }
            if (mode == 1) { uint64_t dur = (uint64_t)(PIECE / rate_Bps * 1e9), t = now(), old = atomic_load(&clk), st;
                             do { st = old > t ? old : t; } while (!atomic_compare_exchange_weak(&clk, &old, st + dur)); sleep_until(st); }
            for (size_t i = 0; i < PIECE; i += 32) _mm256_stream_si256((__m256i *)(dst + lo + off + i), _mm256_load_si256((const __m256i *)(src + lo + off + i)));
            _mm_sfence();
        }
        pthread_barrier_wait(&bar);
    }
}
static void *reader(void *a) {
    (void)a; pin_cpu(64); char *p = chain;
    while (!stop) { uint64_t t0 = now(); long n = 0; while (now() - t0 < 10000000ull) { for (int i = 0; i < 1000; i++) p = *(char **)p; n += 1000; }
                    printf("R %lu %.1f\n", (unsigned long)now(), (now() - t0) / (double)n + (p == NULL)); }
    return NULL;
}
int main(int argc, char **argv) {
    if (argc < 4) { fprintf(stderr, "usage: ckpt_cxl <S_GiB> <period_s> <full|rate|kvprio> [rate_GBps] [reader 0|1]\n"); return 2; }
    bytes = (size_t)(atof(argv[1]) * GiB); double period = atof(argv[2]);
    mode = !strcmp(argv[3], "rate") ? 1 : !strcmp(argv[3], "kvprio") ? 2 : 0; rate_Bps = (argc > 4 ? atof(argv[4]) : 0) * 1e9; int want_reader = argc > 5 && atoi(argv[5]);
    signal(SIGTERM, on_term); signal(SIGINT, on_term); setvbuf(stdout, NULL, _IOLBF, 0);
    int fd = open("/dev/dax0.0", O_RDWR); if (fd < 0) { perror("/dev/dax0.0"); return 1; }
    dst = mmap(NULL, bytes + GiB, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0); if (dst == MAP_FAILED) { perror("mmap"); return 1; }
    src = mmap(NULL, bytes, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0); madvise(src, bytes, MADV_HUGEPAGE);
    uint64_t v = 0x9E3779B97F4A7C15ull; for (size_t i = 0; i < bytes; i += 8) { v ^= v << 13; v ^= v >> 7; v ^= v << 17; *(uint64_t *)(src + i) = v; }
    memcpy(dst, src, bytes);
    if (mode == 2) { int ff = open("/dev/shm/kvprio_flag", O_RDWR | O_CREAT, 0644); if (ftruncate(ff, 4096)) {} flag = mmap(NULL, 4096, PROT_READ, MAP_SHARED, ff, 0); }
    pthread_t rt; if (want_reader) {
        chain = dst + bytes; size_t nl = GiB / 64; uint32_t *ord = malloc(nl * 4);
        for (size_t i = 0; i < nl; i++) ord[i] = (uint32_t)i;
        for (size_t i = nl - 1; i > 0; i--) { v ^= v << 13; v ^= v >> 7; v ^= v << 17; size_t j = v % i; uint32_t t = ord[i]; ord[i] = ord[j]; ord[j] = t; }
        for (size_t i = 0; i < nl; i++) *(char **)(chain + (size_t)ord[i] * 64) = chain + (size_t)ord[(i + 1) % nl] * 64;
        chain += (size_t)ord[0] * 64; free(ord); pthread_create(&rt, NULL, reader, NULL);
    }
    printf("# ckpt_cxl %.1f GiB every %.1f s, mode %s%s, reader %d, start %lu\n", bytes / (double)GiB, period, argv[3], mode == 1 ? argv[4] : "", want_reader, (unsigned long)now());
    pthread_barrier_init(&bar, NULL, 9); pthread_t th[8]; for (int i = 0; i < 8; i++) pthread_create(&th[i], NULL, writer, (void *)(intptr_t)i);
    for (int b = 0; !stop; b++) {
        uint64_t t0 = now(); atomic_store(&paused_ns, 0);
        pthread_barrier_wait(&bar); pthread_barrier_wait(&bar);
        printf("C %d %lu %lu %.1f paused_ms %.1f\n", b, (unsigned long)t0, (unsigned long)now(), bytes / (double)GiB, atomic_load(&paused_ns) / 8e6);
        while (!stop && now() < t0 + (uint64_t)(period * 1e9)) usleep(10000);
    }
    pthread_barrier_wait(&bar); for (int i = 0; i < 8; i++) pthread_join(th[i], NULL);
    if (want_reader) pthread_join(rt, NULL);
    return 0;
}
