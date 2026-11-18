/* gpu_cxl.cu -- can the GPU of c28 read and write CXL memory, and through which API?  (2026-11-12)
 *
 * On c28 the CXL memory is not a NUMA node. It is exposed only as device-DAX character devices; /dev/dax0.0 is a 242.5 GiB
 * window onto the CZ120 cards c1:00.0 + e1:00.0. A process reaches it with open() + mmap(MAP_SHARED) of the device: the page
 * tables then point at the CXL physical addresses themselves (device-DAX has no page cache and makes no DRAM copy).
 *
 * The API under test hands that mapping to CUDA:
 *
 *     cudaHostRegister(p, len, cudaHostRegisterMapped);   // pin the CXL pages and DMA-map them for the GPU
 *     cudaHostGetDevicePointer(&dp, p, 0);                 // the address of the same CXL bytes inside GPU kernels
 *
 * After it, (a) GPU kernels load/store the CXL bytes through dp ("zero-copy": each access is a PCIe read/write issued by the
 * GPU), and (b) cudaMemcpy() between VRAM and p is a DMA by the GPU's copy engine straight to/from CXL. The path is
 * GPU -> PCIe -> CPU root complex / I/O die -> CXL link -> CZ120: no CPU core copies anything and no DRAM buffer is used.
 * It is NOT peer-to-peer: the GPU is a plain PCIe device, not a CXL device, and the CPU's I/O die is on the path exactly as
 * it is when the GPU reads pinned DRAM.
 *
 * Checks. The data is checked by a SEPARATE process, cxl_cpu, which never touches CUDA and flushes its CPU caches, so a PASS
 * means the bytes really are in, or came from, the CXL device:
 *   1  GPU kernel reads CXL    cxl_cpu writes pattern A into the range; a GPU kernel reads it through dp and compares
 *   2  GPU kernel writes CXL   a GPU kernel writes pattern B through dp; cxl_cpu reads the range and compares
 *   3  GPU DMA reads CXL       cxl_cpu writes pattern C; cudaMemcpy(VRAM <- p); a GPU kernel compares the VRAM copy
 *   4  GPU DMA writes CXL      a GPU kernel writes pattern D into VRAM; cudaMemcpy(p <- VRAM); cxl_cpu compares
 *   controls                   each checker is also run against a pattern that is NOT there and must flag every word
 *   5  speed                   the same four transfers against pinned DRAM (cudaHostAlloc), for comparison
 * With --noreg, cudaHostRegister is not called: cudaMemcpy still works, but only because the CUDA driver copies through its
 * own pinned DRAM staging buffer with the CPU (the indirect path), and a GPU kernel that dereferences p must fail.
 *
 * usage: gpu_cxl <dax device> <offset MiB> <length MiB> [--noreg]     (cxl_cpu must sit next to this binary)
 *   The test OVERWRITES that range of the device. Run it with the GPU otherwise idle.
 * build: nvcc -O2 -arch=sm_89 -o gpu_cxl gpu_cxl.cu */
#include <cuda_runtime.h>
#include <fcntl.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <unistd.h>
#include <algorithm>
#include "pattern.h"

#define CK(call) do { cudaError_t e_ = (call); if (e_ != cudaSuccess) {                         \
        printf("FAIL  %s  ->  %s\n", #call, cudaGetErrorString(e_)); exit(1); } } while (0)

enum : uint64_t { SA = 0xA1, SB = 0xB2, SC = 0xC3, SD = 0xD4 };          // the four test patterns
static const char *dev; static size_t off_mib, len_mib; static char helper[PATH_MAX + 16];
static unsigned long long *d_bad; static int fails;

__global__ void k_check(const uint64_t *p, uint64_t n, uint64_t seed, unsigned long long *bad) {   // GPU LOADS from p
    unsigned long long b = 0;
    for (uint64_t i = blockIdx.x * (uint64_t)blockDim.x + threadIdx.x; i < n; i += (uint64_t)gridDim.x * blockDim.x)
        b += (p[i] != pat(seed, i));
    if (b) atomicAdd(bad, b);
}
__global__ void k_fill(uint64_t *p, uint64_t n, uint64_t seed) {                                    // GPU STORES to p
    for (uint64_t i = blockIdx.x * (uint64_t)blockDim.x + threadIdx.x; i < n; i += (uint64_t)gridDim.x * blockDim.x)
        p[i] = pat(seed, i);
}
static void gpu_fill(void *p, uint64_t n, uint64_t seed) {
    k_fill<<<1024, 256>>>((uint64_t *)p, n, seed); CK(cudaGetLastError()); CK(cudaDeviceSynchronize());
}
static unsigned long long gpu_mismatches(const void *p, uint64_t n, uint64_t seed) {
    unsigned long long h = 0;
    CK(cudaMemset(d_bad, 0, sizeof h));
    k_check<<<1024, 256>>>((const uint64_t *)p, n, seed, d_bad); CK(cudaGetLastError()); CK(cudaDeviceSynchronize());
    CK(cudaMemcpy(&h, d_bad, sizeof h, cudaMemcpyDeviceToHost));
    return h;
}
// run cxl_cpu (CPU only, no CUDA) as a separate process; 0 = fill done / check found no mismatch, 1 = check found mismatches
static int cxl_cpu(const char *op, uint64_t seed) {
    char cmd[PATH_MAX + 512];
    snprintf(cmd, sizeof cmd, "%s %s %s %zu %zu %llu", helper, op, dev, off_mib, len_mib, (unsigned long long)seed);
    fflush(stdout);
    int st = system(cmd);
    return WIFEXITED(st) ? WEXITSTATUS(st) : 99;
}
static void verdict(int ok, const char *what) { printf("%s  %s\n", ok ? "PASS" : "FAIL", what); fails += !ok; }
static void show_maps(const void *p) {                       // the line of /proc/self/maps that contains p
    FILE *f = fopen("/proc/self/maps", "r"); char l[512]; unsigned long a, b;
    while (f && fgets(l, sizeof l, f))
        if (sscanf(l, "%lx-%lx", &a, &b) == 2 && (unsigned long)p >= a && (unsigned long)p < b) printf("    %s", l);
    if (f) fclose(f);
}
static void show_ptr(const char *label, const void *p) {     // what CUDA itself thinks the pointer is
    cudaPointerAttributes a; CK(cudaPointerGetAttributes(&a, p));
    const char *t = a.type == cudaMemoryTypeHost ? "cudaMemoryTypeHost (registered/pinned host memory)"
                  : a.type == cudaMemoryTypeUnregistered ? "cudaMemoryTypeUnregistered (CUDA does not know this memory)"
                  : a.type == cudaMemoryTypeDevice ? "cudaMemoryTypeDevice" : "cudaMemoryTypeManaged";
    printf("    cudaPointerGetAttributes(%s %p): %s, devicePointer=%p\n", label, p, t, a.devicePointer);
}
template <class F> static double gibs(F op, size_t bytes) {  // median of 5 timed runs after one warm-up, GiB/s
    cudaEvent_t a, b; CK(cudaEventCreate(&a)); CK(cudaEventCreate(&b)); float ms[5];
    op(); CK(cudaDeviceSynchronize());
    for (int r = 0; r < 5; r++) {
        CK(cudaEventRecord(a)); op(); CK(cudaEventRecord(b)); CK(cudaEventSynchronize(b)); CK(cudaEventElapsedTime(&ms[r], a, b));
    }
    std::sort(ms, ms + 5); cudaEventDestroy(a); cudaEventDestroy(b);
    return bytes / (ms[2] * 1e-3) / (1u << 30);
}

int main(int argc, char **argv) {
    if (argc < 4) { fprintf(stderr, "usage: %s <dax device> <offset MiB> <length MiB> [--noreg]\n", argv[0]); return 2; }
    dev = argv[1]; off_mib = strtoull(argv[2], 0, 0); len_mib = strtoull(argv[3], 0, 0);
    int noreg = argc > 4 && !strcmp(argv[4], "--noreg");
    size_t off = off_mib << 20, len = len_mib << 20; uint64_t n = len / 8;
    char exe[PATH_MAX]; ssize_t k = readlink("/proc/self/exe", exe, sizeof exe - 1); exe[k > 0 ? k : 0] = 0;
    *strrchr(exe, '/') = 0; snprintf(helper, sizeof helper, "%s/cxl_cpu", exe);

    // device-DAX checks the bounds only when a page is first touched, so check the range against the device size here
    char path[256]; unsigned long long devsize = 0; snprintf(path, sizeof path, "/sys/bus/dax/devices/%s/size", strrchr(dev, '/') + 1);
    FILE *f = fopen(path, "r"); if (!f || fscanf(f, "%llu", &devsize) != 1 || off + len > devsize) {
        printf("range [%zu MiB, +%zu MiB) is not inside %s (%llu MiB)\n", off_mib, len_mib, dev, devsize >> 20); return 2; }
    fclose(f);

    printf("== 0  facts\n");
    cudaDeviceProp pr; CK(cudaGetDeviceProperties(&pr, 0)); char bus[32]; CK(cudaDeviceGetPCIBusId(bus, sizeof bus, 0));
    int pageable = -1, regsup = -1; int drv = 0, rt = 0;
    CK(cudaDeviceGetAttribute(&pageable, cudaDevAttrPageableMemoryAccess, 0));
    CK(cudaDeviceGetAttribute(&regsup, cudaDevAttrHostRegisterSupported, 0));
    CK(cudaDriverGetVersion(&drv)); CK(cudaRuntimeGetVersion(&rt));
    printf("    GPU %s at %s, CUDA driver %d runtime %d\n", pr.name, bus, drv, rt);
    printf("    pageableMemoryAccess=%d  (0: the GPU cannot touch host memory that CUDA has not registered or allocated)\n", pageable);
    printf("    hostRegisterSupported=%d\n", regsup);
    int fd = open(dev, O_RDWR); if (fd < 0) { perror(dev); return 2; }
    void *p = mmap(NULL, len, PROT_READ | PROT_WRITE, MAP_SHARED, fd, off);
    if (p == MAP_FAILED) { perror("mmap"); return 2; }
    printf("    p = mmap(%s, offset %zu MiB, %zu MiB, MAP_SHARED) = %p, backed by:\n", dev, off_mib, len_mib, p);
    show_maps(p);
    void *vram; CK(cudaMalloc(&vram, len)); CK(cudaMalloc(&d_bad, sizeof *d_bad));

    if (noreg) {
        printf("\n== --noreg: cudaHostRegister is NOT called\n");
        show_ptr("p", p);
        printf("\n== 3'  cudaMemcpy(vram, p, H2D) on the unregistered CXL pointer\n");
        if (cxl_cpu("fill", SC)) return 2;
        CK(cudaMemset(vram, 0, len)); CK(cudaMemcpy(vram, p, len, cudaMemcpyHostToDevice));
        verdict(gpu_mismatches(vram, n, SC) == 0, "data arrives -- through the driver's pinned DRAM staging buffer, copied by the CPU");
        printf("\n== 4'  cudaMemcpy(p, vram, D2H) on the unregistered CXL pointer\n");
        gpu_fill(vram, n, SD); CK(cudaMemcpy(p, vram, len, cudaMemcpyDeviceToHost));
        verdict(cxl_cpu("check", SD) == 0, "data arrives -- through the driver's pinned DRAM staging buffer, copied by the CPU");
        printf("\n== 5'  speed of the staged path, %zu MiB per transfer, median of 5\n", len_mib);
        printf("    cudaMemcpy H2D (CXL -> CPU copy -> DRAM -> GPU)  %6.2f GiB/s\n",
               gibs([&] { CK(cudaMemcpy(vram, p, len, cudaMemcpyHostToDevice)); }, len));
        printf("    cudaMemcpy D2H (GPU -> DRAM -> CPU copy -> CXL)  %6.2f GiB/s\n",
               gibs([&] { CK(cudaMemcpy(p, vram, len, cudaMemcpyDeviceToHost)); }, len));
        printf("\n== 1'  GPU kernel dereferences the unregistered CXL pointer p (expected to fail; the CUDA context is unusable after it)\n");
        CK(cudaMemset(d_bad, 0, sizeof *d_bad));
        k_check<<<1024, 256>>>((const uint64_t *)p, n, SD, d_bad);
        cudaError_t e = cudaDeviceSynchronize();
        printf("    cudaDeviceSynchronize() -> %s\n", cudaGetErrorString(e));
        verdict(e != cudaSuccess, "without cudaHostRegister the GPU cannot address the CXL mapping");
        printf("\n%s (%d failed checks)\n", fails ? "SOME CHECKS FAILED" : "ALL CHECKS PASSED", fails);
        return fails ? 1 : 0;
    }

    printf("\n== the API: cudaHostRegister + cudaHostGetDevicePointer\n");
    show_ptr("p, before", p);
    CK(cudaHostRegister(p, len, cudaHostRegisterMapped));
    void *dp; CK(cudaHostGetDevicePointer(&dp, p, 0));
    printf("    cudaHostRegister(p, %zu MiB, cudaHostRegisterMapped) = cudaSuccess\n", len_mib);
    printf("    cudaHostGetDevicePointer(&dp, p, 0)               = cudaSuccess, dp = %p\n", dp);
    show_ptr("p, after ", p);

    printf("\n== 1  GPU kernel READS CXL (zero-copy loads through dp)\n");
    if (cxl_cpu("fill", SA)) return 2;
    unsigned long long m = gpu_mismatches(dp, n, SA);
    printf("    GPU kernel: %llu of %llu words differ from pattern %#llx\n", m, (unsigned long long)n, (unsigned long long)SA);
    verdict(m == 0, "the GPU kernel read the bytes a CPU-only process had written into CXL");
    verdict(gpu_mismatches(dp, n, SB) == n, "control: the same kernel flags every word when checked against pattern B (not written)");

    printf("\n== 2  GPU kernel WRITES CXL (zero-copy stores through dp)\n");
    verdict(cxl_cpu("check", SB) == 1, "control: before the GPU writes, cxl_cpu does not find pattern B in CXL");
    gpu_fill(dp, n, SB);
    verdict(cxl_cpu("check", SB) == 0, "a CPU-only process reads from CXL the bytes the GPU kernel stored");

    printf("\n== 3  GPU copy engine READS CXL: cudaMemcpy(vram, p, H2D)\n");
    if (cxl_cpu("fill", SC)) return 2;
    CK(cudaMemset(vram, 0, len)); CK(cudaMemcpy(vram, p, len, cudaMemcpyHostToDevice));
    verdict(gpu_mismatches(vram, n, SC) == 0, "VRAM holds the bytes a CPU-only process had written into CXL");

    printf("\n== 4  GPU copy engine WRITES CXL: cudaMemcpy(p, vram, D2H)\n");
    gpu_fill(vram, n, SD);
    verdict(cxl_cpu("check", SD) == 1, "control: before the copy, cxl_cpu does not find pattern D in CXL");
    CK(cudaMemcpy(p, vram, len, cudaMemcpyDeviceToHost));
    verdict(cxl_cpu("check", SD) == 0, "a CPU-only process reads from CXL the bytes the copy engine wrote");

    printf("\n== 5  speed, %zu MiB per transfer, median of 5            CXL (dax, registered)   DRAM (cudaHostAlloc)\n", len_mib);
    void *h, *hd; CK(cudaHostAlloc(&h, len, cudaHostAllocMapped)); CK(cudaHostGetDevicePointer(&hd, h, 0));
    gpu_fill(hd, n, SA);
    printf("    cudaMemcpy H2D   (copy engine reads host)         %8.2f GiB/s          %8.2f GiB/s\n",
           gibs([&] { CK(cudaMemcpy(vram, p, len, cudaMemcpyHostToDevice)); }, len),
           gibs([&] { CK(cudaMemcpy(vram, h, len, cudaMemcpyHostToDevice)); }, len));
    printf("    cudaMemcpy D2H   (copy engine writes host)        %8.2f GiB/s          %8.2f GiB/s\n",
           gibs([&] { CK(cudaMemcpy(p, vram, len, cudaMemcpyDeviceToHost)); }, len),
           gibs([&] { CK(cudaMemcpy(h, vram, len, cudaMemcpyDeviceToHost)); }, len));
    printf("    kernel loads     (SMs read host, zero-copy)       %8.2f GiB/s          %8.2f GiB/s\n",
           gibs([&] { k_check<<<1024, 256>>>((const uint64_t *)dp, n, SA, d_bad); }, len),
           gibs([&] { k_check<<<1024, 256>>>((const uint64_t *)hd, n, SA, d_bad); }, len));
    printf("    kernel stores    (SMs write host, zero-copy)      %8.2f GiB/s          %8.2f GiB/s\n",
           gibs([&] { k_fill<<<1024, 256>>>((uint64_t *)dp, n, SB); }, len),
           gibs([&] { k_fill<<<1024, 256>>>((uint64_t *)hd, n, SB); }, len));

    CK(cudaHostUnregister(p)); CK(cudaFreeHost(h)); munmap(p, len); close(fd);
    printf("\n%s (%d failed checks)\n", fails ? "SOME CHECKS FAILED" : "ALL CHECKS PASSED", fails);
    return fails ? 1 : 0;
}
