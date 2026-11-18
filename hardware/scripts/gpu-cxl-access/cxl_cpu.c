/* cxl_cpu.c -- CPU-only access to a range of a CXL device-DAX device (2026-11-12).
 * It does not include or link CUDA and runs as its own process, so what it reads is what the CXL device holds and what it
 * writes goes to the CXL device. Every cache line of the range is flushed from the CPU caches (clflush) after a fill and
 * before a check, so neither step is served by a CPU cache.
 *   cxl_cpu fill  <device> <offset MiB> <length MiB> <seed>   word i := pat(seed, i), then flush       exit 0
 *   cxl_cpu check <device> <offset MiB> <length MiB> <seed>   flush, then count words != pat(seed, i)  exit 0 if none, 1 if any
 * build: gcc -O2 -Wall -o cxl_cpu cxl_cpu.c */
#define _GNU_SOURCE
#include <fcntl.h>
#include <immintrin.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
#include "pattern.h"

static void flush(const char *p, size_t len) {
    for (size_t i = 0; i < len; i += 64) _mm_clflush(p + i);
    _mm_mfence();
}

int main(int argc, char **argv) {
    if (argc != 6 || (strcmp(argv[1], "fill") && strcmp(argv[1], "check"))) {
        fprintf(stderr, "usage: %s fill|check <device> <offset MiB> <length MiB> <seed>\n", argv[0]); return 2;
    }
    const char *dev = argv[2];
    size_t off = strtoull(argv[3], 0, 0) << 20, len = strtoull(argv[4], 0, 0) << 20, n = len / 8;
    uint64_t seed = strtoull(argv[5], 0, 0);
    int fd = open(dev, O_RDWR);
    if (fd < 0) { perror(dev); return 2; }
    uint64_t *p = mmap(NULL, len, PROT_READ | PROT_WRITE, MAP_SHARED, fd, off);       /* the CXL bytes themselves */
    if (p == MAP_FAILED) { perror("mmap"); return 2; }

    if (!strcmp(argv[1], "fill")) {
        for (size_t i = 0; i < n; i++) p[i] = pat(seed, i);
        flush((const char *)p, len);
        printf("      [cxl_cpu pid %d, no CUDA] wrote pattern %#llx into %s [%zu MiB, +%zu MiB), flushed CPU caches\n",
               getpid(), (unsigned long long)seed, dev, off >> 20, len >> 20);
        return 0;
    }
    flush((const char *)p, len);
    size_t bad = 0;
    for (size_t i = 0; i < n; i++) bad += (p[i] != pat(seed, i));
    printf("      [cxl_cpu pid %d, no CUDA] flushed CPU caches, read %s [%zu MiB, +%zu MiB): %zu of %zu words differ from pattern %#llx\n",
           getpid(), dev, off >> 20, len >> 20, bad, n, (unsigned long long)seed);
    return bad != 0;
}
