/* Test pattern shared by cxl_cpu.c (CPU only) and gpu_cxl.cu (GPU): 64-bit word i of a range filled with seed s holds
 * pat(s, i), a splitmix64 hash -- random-looking data, no all-zero cache lines. pat(s, i) == pat(t, i) only if s == t
 * (the mix is a bijection), so checking a range against a seed that was NOT written flags every word. */
#pragma once
#include <stdint.h>
#ifdef __CUDACC__
#define PAT_FN __host__ __device__ static inline
#else
#define PAT_FN static inline
#endif
PAT_FN uint64_t pat(uint64_t seed, uint64_t i) {
    uint64_t z = i + (seed + 1) * 0x9E3779B97F4A7C15ull;
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ull;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBull;
    return z ^ (z >> 31);
}
