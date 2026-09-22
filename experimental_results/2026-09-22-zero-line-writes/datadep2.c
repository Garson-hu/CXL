// which data is "cheap"? NT writes beside a victim: zeros, ones, random, one-nonzero-byte-per-line, one-nonzero-line-per-4KiB; to CXL and to DRAM
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <pthread.h>
#include <sched.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <immintrin.h>
#include <time.h>
static uint64_t now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec * 1000000000ull + t.tv_nsec; }
static void pin(int c) { cpu_set_t s; CPU_ZERO(&s); CPU_SET(c, &s); pthread_setaffinity_np(pthread_self(), sizeof s, &s); }
static int cpus[8] = { 96, 97, 98, 99, 112, 113, 114, 115 }; static size_t S;
static char *src, *dst;
static void *worker(void *a) { long id = (long)a; pin(cpus[id]); size_t per = S / 8, o0 = id * per; for (size_t i = o0; i < o0 + per; i += 32) _mm256_stream_si256((__m256i *)(dst + i), _mm256_load_si256((const __m256i *)(src + i))); _mm_sfence(); return NULL; }
static double run(void) { uint64_t t0 = now(); pthread_t th[8]; for (long i = 0; i < 8; i++) pthread_create(&th[i], NULL, worker, (void *)i); for (int i = 0; i < 8; i++) pthread_join(th[i], NULL); return S / 1073741824.0 / ((now() - t0) / 1e9); }
static char *huge(size_t n) { char *p = mmap(NULL, n, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0); madvise(p, n, MADV_HUGEPAGE); return p; }
int main(int argc, char **argv) {
    S = (size_t)atoi(argv[1]) << 30; int fd = open("/dev/dax0.0", O_RDWR);
    char *dax = mmap(NULL, S, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 64ull << 30); char *dram = huge(S); memset(dram, 2, S);
    src = huge(S);
    const char *pat[] = { "zeros", "ones", "random", "one byte per 64 B line", "one 8 B word per 4 KiB", "one zero line per two" };
    for (int p = 0; p < 6; p++) {
        if (p == 0) memset(src, 0, S); else if (p == 1) memset(src, 1, S);
        else if (p == 2) { uint64_t x = 88172645463325252ull; for (size_t i = 0; i < S; i += 8) { x ^= x << 13; x ^= x >> 7; x ^= x << 17; *(uint64_t *)(src + i) = x; } }
        else if (p == 3) { memset(src, 0, S); for (size_t i = 0; i < S; i += 64) src[i] = 1; }
        else if (p == 4) { memset(src, 0, S); for (size_t i = 0; i < S; i += 4096) *(uint64_t *)(src + i) = i * 0x9E3779B97F4A7C15ull; }
        else { memset(src, 0, S); for (size_t i = 0; i < S; i += 128) memset(src + i, 1, 64); }
        dst = dax; double a = run(), b = run(); dst = dram; double c = run(), d = run();
        printf("%-24s -> CXL %.1f %.1f GiB/s   -> DRAM %.1f %.1f GiB/s\n", pat[p], a, b, c, d); fflush(stdout);
    }
    return 0;
}
