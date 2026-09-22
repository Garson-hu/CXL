// is the DRAM->CXL copy rate data-dependent beside a victim? pure NT writes of zeros/ones, pure reads of zeros/ones, copies to CXL and to DRAM
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
static char *srcz, *srco, *dax, *dram; static int mode; static __m256i fill;
static volatile long long sink;
static void *worker(void *a) {
    long id = (long)a; pin(cpus[id]); size_t per = S / 8, o0 = id * per; __m256i acc = _mm256_setzero_si256();
    switch (mode) {
    case 0: for (size_t i = o0; i < o0 + per; i += 32) _mm256_stream_si256((__m256i *)(dax + i), fill); _mm_sfence(); break;          /* pure NT write to CXL */
    case 1: for (size_t i = o0; i < o0 + per; i += 32) acc = _mm256_add_epi64(acc, _mm256_load_si256((const __m256i *)(srcz + i))); break;   /* pure read, zero source */
    case 2: for (size_t i = o0; i < o0 + per; i += 32) acc = _mm256_add_epi64(acc, _mm256_load_si256((const __m256i *)(srco + i))); break;   /* pure read, ones source */
    case 3: for (size_t i = o0; i < o0 + per; i += 32) _mm256_stream_si256((__m256i *)(dax + i), _mm256_load_si256((const __m256i *)(srcz + i))); _mm_sfence(); break;  /* copy zeros -> CXL */
    case 4: for (size_t i = o0; i < o0 + per; i += 32) _mm256_stream_si256((__m256i *)(dax + i), _mm256_load_si256((const __m256i *)(srco + i))); _mm_sfence(); break;  /* copy ones -> CXL */
    case 5: for (size_t i = o0; i < o0 + per; i += 32) _mm256_stream_si256((__m256i *)(dram + i), _mm256_load_si256((const __m256i *)(srcz + i))); _mm_sfence(); break; /* copy zeros -> DRAM */
    case 6: for (size_t i = o0; i < o0 + per; i += 32) _mm256_stream_si256((__m256i *)(dram + i), _mm256_load_si256((const __m256i *)(srco + i))); _mm_sfence(); break; /* copy ones -> DRAM */
    }
    sink += _mm256_extract_epi64(acc, 0); return NULL;
}
static double run(int m) { mode = m; uint64_t t0 = now(); pthread_t th[8]; for (long i = 0; i < 8; i++) pthread_create(&th[i], NULL, worker, (void *)i); for (int i = 0; i < 8; i++) pthread_join(th[i], NULL); return S / 1073741824.0 / ((now() - t0) / 1e9); }
static char *huge(size_t n) { char *p = mmap(NULL, n, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0); madvise(p, n, MADV_HUGEPAGE); return p; }
int main(int argc, char **argv) {
    S = (size_t)atoi(argv[1]) << 30; int fd = open("/dev/dax0.0", O_RDWR);
    dax = mmap(NULL, S, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 64ull << 30);
    srcz = huge(S); for (size_t i = 0; i < S; i += 4096) *(uint64_t *)(srcz + i) = i * 0x9E3779B97F4A7C15ull;
    srco = huge(S); memset(srco, 1, S);
    dram = huge(S); memset(dram, 2, S);
    const char *name[] = { "NT write const -> CXL", "read zero-ish source", "read ones source", "copy zero-ish -> CXL", "copy ones -> CXL", "copy zero-ish -> DRAM", "copy ones -> DRAM" };
    for (int rep = 0; rep < 2; rep++) {
        fill = _mm256_setzero_si256(); printf("rep %d: NT write ZEROS -> CXL %.1f GiB/s\n", rep, run(0));
        fill = _mm256_set1_epi8(1);     printf("rep %d: NT write ONES  -> CXL %.1f GiB/s\n", rep, run(0));
        for (int m = 1; m <= 6; m++) printf("rep %d: %-24s %.1f GiB/s\n", rep, name[m], run(m));
    }
    return 0;
}
