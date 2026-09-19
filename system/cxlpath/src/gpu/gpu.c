/* Component B, GPU sources (B5): per-chunk choice between the direct and the staged path. */
#define _GNU_SOURCE
#include "../internal.h"
#include "cxlpath_gpu.h"
#include <cuda_runtime.h>
#include <pthread.h>
#include <sched.h>
#include <stdlib.h>
#include <string.h>

#define NBOUNCE 4
typedef struct { void *buf; _Atomic int busy; } bounce_t;
typedef struct job { void *dst; bounce_t *b; size_t n; struct job *next; } job_t;

static bounce_t bounce[NBOUNCE];
static cudaStream_t cs;
static pthread_t *threads; static int nthreads, first_cpu_g; static volatile int stopping;
static pthread_mutex_t mu = PTHREAD_MUTEX_INITIALIZER; static pthread_cond_t cv_job = PTHREAD_COND_INITIALIZER, cv_done = PTHREAD_COND_INITIALIZER;
static job_t *q_head, *q_tail; static int inflight;

static uint32_t br4(uint32_t k) { k &= 15; return ((k & 1) << 3) | ((k & 2) << 1) | ((k & 4) >> 1) | ((k & 8) >> 3); }

static void *copy_thread(void *arg) {
    int cpu = first_cpu_g + (int)(long)arg; cpu_set_t s; CPU_ZERO(&s); CPU_SET(cpu, &s); pthread_setaffinity_np(pthread_self(), sizeof s, &s);
    for (;;) {
        pthread_mutex_lock(&mu);
        while (!q_head && !stopping) pthread_cond_wait(&cv_job, &mu);
        if (!q_head && stopping) { pthread_mutex_unlock(&mu); return NULL; }
        job_t *j = q_head; q_head = j->next; if (!q_head) q_tail = NULL;
        pthread_mutex_unlock(&mu);
        cxlp_copy_in(j->dst, j->b->buf, j->n);                 /* DRAM bounce -> CXL, NT stores */
        atomic_store(&j->b->busy, 0);
        pthread_mutex_lock(&mu); inflight--; pthread_cond_broadcast(&cv_done); pthread_mutex_unlock(&mu);
        free(j);
    }
}

int cxlp_gpu_init(int copy_threads, int first_cpu) {
    if (cudaStreamCreate(&cs) != cudaSuccess) return -1;
    for (int i = 0; i < NBOUNCE; i++) { if (cudaMallocHost(&bounce[i].buf, CXLP_SEG_BYTES) != cudaSuccess) return -1; memset(bounce[i].buf, 0, CXLP_SEG_BYTES); }
    /* what the GPU link can push: D2H into pinned DRAM */
    void *d; if (cudaMalloc(&d, CXLP_SEG_BYTES) != cudaSuccess) return -1;
    cudaMemcpy(bounce[0].buf, d, CXLP_SEG_BYTES, cudaMemcpyDeviceToHost);
    uint64_t t0 = cxlp_now_ns(); for (int r = 0; r < 8; r++) cudaMemcpy(bounce[r % NBOUNCE].buf, d, CXLP_SEG_BYTES, cudaMemcpyDeviceToHost);
    uint64_t dt = cxlp_now_ns() - t0; cudaFree(d);
    if (cxlp_g.meta) atomic_store(&POL->gpu_link_bps, (uint64_t)(8.0 * CXLP_SEG_BYTES * 1e9 / (double)dt));
    /* Component C, GPU consumer: how fast the GPU reads host memory, DRAM vs a registered CXL segment */
    if (cxlp_g.meta) {
        int cd = -1; for (uint32_t dv = 0; dv < cxlp_g.meta->ndev; dv++) if (cxlp_g.meta->dev[dv].kind == CXLP_DEV_CXL && cxlp_dev_free((int)dv)) { cd = (int)dv; break; }
        uint32_t sg = cd >= 0 ? cxlp_seg_claim(cd, CXLP_SEG_OPEN) : CXLP_NO_SEG; void *dv2;
        if (sg != CXLP_NO_SEG && cudaMalloc(&dv2, CXLP_SEG_BYTES) == cudaSuccess) {
            void *cp = cxlp_seg_ptr(cd, sg);
            if (cudaHostRegister(cp, CXLP_SEG_BYTES, cudaHostRegisterDefault) == cudaSuccess) {
                uint64_t best_c = ~0ull, best_d = ~0ull;
                for (int r = 0; r < 4; r++) {
                    uint64_t a = cxlp_now_ns(); cudaMemcpy(dv2, cp, CXLP_SEG_BYTES, cudaMemcpyHostToDevice); uint64_t b = cxlp_now_ns();
                    cudaMemcpy(dv2, bounce[0].buf, CXLP_SEG_BYTES, cudaMemcpyHostToDevice); uint64_t c = cxlp_now_ns();
                    if (b - a < best_c) best_c = b - a;
                    if (c - b < best_d) best_d = c - b;
                }
                atomic_store(&POL->gpu_rd_cxl_bps, (uint64_t)(CXLP_SEG_BYTES * 1e9 / (double)best_c));
                atomic_store(&POL->gpu_rd_dram_bps, (uint64_t)(CXLP_SEG_BYTES * 1e9 / (double)best_d));
                cudaHostUnregister(cp);
            }
            cudaFree(dv2);
        }
        if (sg != CXLP_NO_SEG) cxlp_seg_release(cd, sg);
    }
    nthreads = copy_threads > 0 ? copy_threads : 1; first_cpu_g = first_cpu; stopping = 0;
    threads = calloc((size_t)nthreads, sizeof *threads);
    for (long i = 0; i < nthreads; i++) pthread_create(&threads[i], NULL, copy_thread, (void *)i);
    return 0;
}

int cxlp_gpu_register(void *buf, size_t len) { return cudaHostRegister(buf, len, cudaHostRegisterDefault) == cudaSuccess ? 0 : -1; }
int cxlp_gpu_unregister(void *buf) { return cudaHostUnregister(buf) == cudaSuccess ? 0 : -1; }

static bounce_t *get_bounce(void) {
    for (;;) {
        for (int i = 0; i < NBOUNCE; i++) { int z = 0; if (atomic_compare_exchange_strong(&bounce[i].busy, &z, 1)) return &bounce[i]; }
        pthread_mutex_lock(&mu); if (inflight) pthread_cond_wait(&cv_done, &mu); pthread_mutex_unlock(&mu);
    }
}

int cxlp_gpu_copy_in(void *dst, const void *src, size_t len, uint32_t stream, cxlp_gpu_stats_t *st) {
    uint64_t t_begin = cxlp_now_ns(), db = 0, sb = 0; uint32_t k = 0; int rc = 0;
    for (size_t off = 0; off < len; off += CXLP_SEG_BYTES, k++) {
        size_t n = len - off < CXLP_SEG_BYTES ? len - off : CXLP_SEG_BYTES;
        uint32_t staged16 = cxlp_policy_daemon_alive() ? atomic_load(&POL->staged16[stream % CXLP_NSTREAM]) : 0;
        uint64_t t0 = cxlp_now_ns();
        if (br4(k) < staged16) {                              /* staged: GPU -> pinned DRAM, then a runtime thread -> CXL */
            bounce_t *b = get_bounce();
            if (cudaMemcpyAsync(b->buf, (const char *)src + off, n, cudaMemcpyDeviceToHost, cs) != cudaSuccess || cudaStreamSynchronize(cs) != cudaSuccess) { atomic_store(&b->busy, 0); rc = -1; break; }
            uint64_t dt = cxlp_now_ns() - t0;
            atomic_fetch_add(&POL->gpu_staged.bytes, n); atomic_fetch_add(&POL->gpu_staged.ns, dt); sb += n;
            job_t *j = malloc(sizeof *j); *j = (job_t){ (char *)dst + off, b, n, NULL };
            pthread_mutex_lock(&mu); if (q_tail) q_tail->next = j; else q_head = j; q_tail = j; inflight++; pthread_cond_signal(&cv_job); pthread_mutex_unlock(&mu);
        } else {                                              /* direct: GPU -> registered CXL buffer, no DRAM traffic */
            if (cudaMemcpyAsync((char *)dst + off, (const char *)src + off, n, cudaMemcpyDeviceToHost, cs) != cudaSuccess || cudaStreamSynchronize(cs) != cudaSuccess) { rc = -1; break; }
            uint64_t dt = cxlp_now_ns() - t0;
            atomic_fetch_add(&POL->gpu_direct.bytes, n); atomic_fetch_add(&POL->gpu_direct.ns, dt); db += n;
        }
        atomic_fetch_add(&POL->sled[stream % CXLP_NSTREAM].bytes, n);       /* the stream is active */
        atomic_fetch_add(&POL->reserve_seq, 1);
    }
    pthread_mutex_lock(&mu); while (inflight) pthread_cond_wait(&cv_done, &mu); pthread_mutex_unlock(&mu);
    if (st) { st->direct_bytes = db; st->staged_bytes = sb; st->seconds = (cxlp_now_ns() - t_begin) / 1e9; }
    return rc;
}

void cxlp_gpu_shutdown(void) {
    pthread_mutex_lock(&mu); stopping = 1; pthread_cond_broadcast(&cv_job); pthread_mutex_unlock(&mu);
    for (int i = 0; i < nthreads; i++) pthread_join(threads[i], NULL);
    free(threads); threads = NULL;
    for (int i = 0; i < NBOUNCE; i++) if (bounce[i].buf) { cudaFreeHost(bounce[i].buf); bounce[i].buf = NULL; }
    cudaStreamDestroy(cs);
}
