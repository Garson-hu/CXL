/* gpuread — how fast does the GPU read 1 GiB from DRAM (pinned) and from CXL (/dev/dax0.0 at offset 64 GiB, registered
 * with CUDA)? Host-to-device copies, 10 repetitions each, alternating. (2026-10-07; the GPU is an RTX 4060 Ti on a
 * PCIe 4.0 x8 link) */
#define _GNU_SOURCE
#include <cuda_runtime.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <time.h>
#include <unistd.h>
static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }
int main(void) {
    size_t len = 1ull << 30; int fd = open("/dev/dax0.0", O_RDWR); if (fd < 0) { perror("dax"); return 1; }
    unsigned char *cx = mmap(NULL, len, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 64ull << 30); if (cx == MAP_FAILED) { perror("mmap"); return 1; }
    unsigned char *dr; if (cudaMallocHost((void **)&dr, len)) { puts("cudaMallocHost failed"); return 1; }
    uint64_t x = 7; for (size_t i = 0; i < len; i += 8) { x ^= x << 13; x ^= x >> 7; x ^= x << 17; *(uint64_t *)(dr + i) = x; }
    memcpy(cx, dr, len);
    if (cudaHostRegister(cx, len, cudaHostRegisterDefault)) { puts("cudaHostRegister(dax) failed"); return 1; }
    unsigned char *d; if (cudaMalloc((void **)&d, len)) { puts("cudaMalloc failed"); return 1; }
    cudaMemcpy(d, dr, len, cudaMemcpyHostToDevice); cudaMemcpy(d, cx, len, cudaMemcpyHostToDevice); cudaDeviceSynchronize();
    for (int r = 1; r <= 10; r++) {
        double t0 = now(); cudaMemcpy(d, dr, len, cudaMemcpyHostToDevice); cudaDeviceSynchronize(); double t1 = now();
        cudaMemcpy(d, cx, len, cudaMemcpyHostToDevice); cudaDeviceSynchronize(); double t2 = now();
        printf("GPUREAD rep=%d from_dram_GiBs=%.2f from_cxl_GiBs=%.2f\n", r, 1 / (t1 - t0), 1 / (t2 - t1));
    }
    cudaHostUnregister(cx); return 0;
}
