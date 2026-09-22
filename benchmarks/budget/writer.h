/* Rate-limited bulk writer shared by budget_synth (one process, overlap by construction) and
 * dram_writer (separate process beside a real application).
 *   mode PURE : NT-stores of a constant — the writer reads nothing from DRAM
 *   mode COPY : NT-copy from a private 256 MiB DRAM source — what a checkpoint copy does
 *   target    : anonymous DRAM, or a devdax CXL device (control)
 * Pacing is a spin-wait on the clock after every 1 MiB, so the stream is smooth at sub-millisecond
 * scale (sleeping cannot pace 1 MiB chunks at >10 GiB/s). rate 0 = unlimited. */
#ifndef BUDGET_WRITER_H
#define BUDGET_WRITER_H
#define _GNU_SOURCE
#include <fcntl.h>
#include <immintrin.h>
#include <pthread.h>
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/mman.h>
#define WBUF (256ul << 20)
#define WCHUNK (1ul << 20)
enum { W_PURE = 0, W_COPY = 1 };
typedef struct { int cpu, mode; double rate_bps; char *dst, *src; volatile uint64_t done; } wr_t;
static volatile int w_stop; static pthread_barrier_t w_bar;
static inline uint64_t w_now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return (uint64_t)t.tv_sec * 1000000000ull + (uint64_t)t.tv_nsec; }
static void w_pin(int c) { cpu_set_t s; CPU_ZERO(&s); CPU_SET(c, &s); pthread_setaffinity_np(pthread_self(), sizeof s, &s); }
static void *w_thread(void *a) {
    wr_t *w = a; w_pin(w->cpu); pthread_barrier_wait(&w_bar);
    const __m256i k = _mm256_set1_epi64x(0x5a5a5a5a5a5a5a5all); size_t off = 0; uint64_t t0 = w_now(), sent = 0;
    while (!w_stop) {
        char *d = w->dst + off;
        if (w->mode == W_PURE) for (size_t i = 0; i < WCHUNK; i += 32) _mm256_stream_si256((__m256i *)(d + i), k);
        else { const char *s = w->src + off; for (size_t i = 0; i < WCHUNK; i += 32) _mm256_stream_si256((__m256i *)(d + i), _mm256_load_si256((const __m256i *)(s + i))); }
        _mm_sfence(); off += WCHUNK; if (off >= WBUF) off = 0; sent += WCHUNK; w->done = sent;
        if (w->rate_bps > 0) { uint64_t due = t0 + (uint64_t)((double)sent / w->rate_bps * 1e9); while (w_now() < due && !w_stop) _mm_pause(); }
    }
    return NULL;
}
static void *w_anon(void) { void *p = mmap(NULL, WBUF, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0); madvise(p, WBUF, MADV_HUGEPAGE); memset(p, 1, WBUF); return p; }
/* buffers are touched serially by the caller, so set-up adds no burst of DRAM traffic */
static int w_setup(wr_t *w, int n, const int *cpus, int mode, const char *target, double total_gibs) {
    int fd = -1; if (strcmp(target, "dram")) { fd = open(target, O_RDWR); if (fd < 0) { perror(target); return -1; } }
    for (int i = 0; i < n; i++) {
        w[i] = (wr_t){ cpus[i], mode, total_gibs > 0 ? total_gibs * 1073741824.0 / n : 0, NULL, NULL, 0 };
        if (fd < 0) w[i].dst = w_anon();
        else { w[i].dst = mmap(NULL, WBUF, PROT_READ | PROT_WRITE, MAP_SHARED, fd, (off_t)((64ul << 30) + (uint64_t)i * WBUF)); if (w[i].dst == MAP_FAILED) { perror("mmap dax"); return -1; } }
        if (mode == W_COPY) w[i].src = w_anon();
    }
    return 0;
}
#endif
