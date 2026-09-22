// beside a victim: the C producer's per-thread chunk loop vs cxlp_copy_in_par, same source (THP, touched), same dax destination
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
#include "cxlpath.h"
static uint64_t now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec * 1000000000ull + t.tv_nsec; }
static void pin(int c) { cpu_set_t s; CPU_ZERO(&s); CPU_SET(c, &s); pthread_setaffinity_np(pthread_self(), sizeof s, &s); }
static void nt_copy(char *d, const char *s, size_t n) { for (size_t i = 0; i < n; i += 32) _mm256_stream_si256((__m256i *)(d + i), _mm256_load_si256((const __m256i *)(s + i))); _mm_sfence(); }
static char *src, *dst; static size_t S; static int cpus[8] = { 96, 97, 98, 99, 112, 113, 114, 115 };
static void *worker(void *a) { long id = (long)a; pin(cpus[id]); size_t per = S / 8, off0 = id * per; for (size_t off = off0; off < off0 + per; off += 32 << 20) nt_copy(dst + off, src + off, 32 << 20); return NULL; }
int main(int argc, char **argv) {
    S = (size_t)atoi(argv[1]) << 30; int fd = open("/dev/dax0.0", O_RDWR);
    dst = mmap(NULL, S, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 64ull << 30);
    src = mmap(NULL, S, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0); madvise(src, S, MADV_HUGEPAGE); if (argc > 2 && !strcmp(argv[2], "sparse")) { for (size_t i = 0; i < S; i += 4096) *(uint64_t *)(src + i) = i * 0x9E3779B97F4A7C15ull; } else memset(src, 1, S);
    { FILE *f = fopen("/proc/self/smaps_rollup", "r"); char l[256]; while (fgets(l, sizeof l, f)) if (!strncmp(l, "AnonHugePages", 13)) fputs(l, stdout); fclose(f); }
    if (dst == MAP_FAILED) { perror("dax"); return 1; }
    for (int rep = 0; rep < 3; rep++) {
        uint64_t t0 = now(); pthread_t th[8]; for (long i = 0; i < 8; i++) pthread_create(&th[i], NULL, worker, (void *)i); for (int i = 0; i < 8; i++) pthread_join(th[i], NULL);
        uint64_t t1 = now(); cxlp_copy_in_par(dst, src, S, 8, cpus); uint64_t t2 = now();
        printf("rep %d: producer-style %.1f GiB/s   cxlp_copy_in_par %.1f GiB/s\n", rep, S / 1073741824.0 / ((t1 - t0) / 1e9), S / 1073741824.0 / ((t2 - t1) / 1e9));
    }
    return 0;
}
