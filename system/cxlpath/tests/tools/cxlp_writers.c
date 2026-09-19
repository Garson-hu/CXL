/* cxlp_writers <store> <threads> <first_cpu> <seconds> [MiB_per_s_per_thread (0 = unlimited)] [stream]
 * Each thread: reserve one segment -> timed NT copy from a private 32 MiB source -> commit -> release. */
#define _GNU_SOURCE
#include "cxlpath.h"
#include <pthread.h>
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }
static double t_end, rate; static uint32_t stream; static pthread_barrier_t bar;
typedef struct { int cpu; uint64_t cxl, dram, fail; } w_t;
static void *run(void *a) {
    w_t *w = a; cpu_set_t s; CPU_ZERO(&s); CPU_SET(w->cpu, &s); pthread_setaffinity_np(pthread_self(), sizeof s, &s);
    char *src = aligned_alloc(4096, CXLP_SEG_BYTES); memset(src, w->cpu, CXLP_SEG_BYTES);
    cxlp_hints_t h = { 0, 0, -1, stream, 200 }; pthread_barrier_wait(&bar);
    double next = now();
    while (now() < t_end) {
        cxlp_res_t r; if (cxlp_reserve(CXLP_SEG_BYTES, &h, &r)) { w->fail++; continue; }
        cxlp_copy_to(&r, 0, src, CXLP_SEG_BYTES); cxlp_commit(&r);
        if (cxlp_dev_kind(r.dev) == CXLP_DEV_DRAM) w->dram += CXLP_SEG_BYTES; else w->cxl += CXLP_SEG_BYTES;
        cxlp_release(&r);
        if (rate > 0) { next += 32.0 / rate; double d = next - now(); if (d > 0) { struct timespec ts = { (time_t)d, (long)((d - (time_t)d) * 1e9) }; nanosleep(&ts, NULL); } else if (d < -0.5) next = now(); }
    }
    cxlp_thread_seal(); free(src); return NULL;
}
int main(int argc, char **argv) {
    if (argc < 5) return 2;
    int n = atoi(argv[2]), cpu0 = atoi(argv[3]); double secs = atof(argv[4]); rate = argc > 5 ? atof(argv[5]) : 0; stream = argc > 6 ? (uint32_t)atoi(argv[6]) : 0;
    if (cxlp_attach(argv[1])) { fprintf(stderr, "no store\n"); return 1; }
    pthread_t th[256]; w_t w[256]; pthread_barrier_init(&bar, NULL, (unsigned)n + 1);
    for (int i = 0; i < n; i++) { w[i] = (w_t){ cpu0 + i, 0, 0, 0 }; }
    t_end = now() + secs + 3600;                                     /* threads wait at the barrier first */
    for (int i = 0; i < n; i++) pthread_create(&th[i], NULL, run, &w[i]);
    usleep(300000); double t0 = now(); t_end = t0 + secs;
    struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts); printf("START %llu\n", (unsigned long long)ts.tv_sec * 1000000000ull + ts.tv_nsec); fflush(stdout);
    pthread_barrier_wait(&bar);
    uint64_t c = 0, d = 0, f = 0; for (int i = 0; i < n; i++) { pthread_join(th[i], NULL); c += w[i].cxl; d += w[i].dram; f += w[i].fail; }
    double dt = now() - t0;
    printf("WRITERS threads=%d secs=%.1f total_GiBs=%.2f cxl_GiBs=%.2f dram_GiBs=%.2f dram_share=%.3f reserve_timeouts=%llu\n", n, dt, (c + d) / dt / 1073741824.0, c / dt / 1073741824.0, d / dt / 1073741824.0, (c + d) ? (double)d / (c + d) : 0, (unsigned long long)f);
    cxlp_close(); return 0;
}
