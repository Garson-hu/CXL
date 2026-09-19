/* cxlpath, GPU sources (step B5). Optional module: needs the CUDA runtime.
 * A GPU checkpoint rests on CXL whatever happens (buffer sets, A5); what the policy chooses per
 * 32 MiB chunk is the PATH:
 *   direct : the GPU writes the chunk straight into the CUDA-registered CXL buffer. No DRAM
 *            traffic. On c28: 3.9 GiB/s (checks V3/V6).
 *   staged : the GPU writes into a small reused pinned DRAM buffer, and a copy thread OWNED BY THE
 *            RUNTIME (pinned to a CPU we choose) NT-copies it to CXL. 12 GiB/s on c28, at the price
 *            of a full DRAM write stream.
 * The share of staged chunks is the per-stream value `staged16` published by cxlpathd: it grows
 * while DRAM is calm and is halved within 20-50 ms when the DRAM probe leaves its bound. */
#ifndef CXLPATH_GPU_H
#define CXLPATH_GPU_H
#include "cxlpath.h"
typedef struct { uint64_t direct_bytes, staged_bytes; double seconds; } cxlp_gpu_stats_t;
int  cxlp_gpu_init(int copy_threads, int first_cpu);      /* bounce pool, copy threads, link-speed calibration */
int  cxlp_gpu_register(void *buf, size_t len);            /* cudaHostRegister on a buffer-set mapping */
int  cxlp_gpu_unregister(void *buf);
/* Copy `len` bytes of GPU memory to `dst` (inside a registered CXL buffer). Blocks until all
 * chunks, including staged ones, have reached CXL. */
int  cxlp_gpu_copy_in(void *dst, const void *src_dev, size_t len, uint32_t stream, cxlp_gpu_stats_t *st);
void cxlp_gpu_shutdown(void);
#endif
