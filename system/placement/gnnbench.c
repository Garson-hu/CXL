/*
 * gnnbench — GNN-style feature-gather benchmark using ObjPlace.
 *
 * Models the dominant memory cost of GNN inference/training: gathering feature
 * rows for sampled neighbors from a large node-feature table. Node sampling is
 * degree-skewed (Zipf): low node ids = high-degree = frequently gathered = hot.
 *
 * Placement policies (the baselines for evaluation):
 *   dram        feature table on DRAM
 *   cxl         feature table on CXL
 *   interleave  table interleaved across DRAM + CXL
 *   skew        manual split: hot (low-id) nodes on DRAM, cold tail on CXL
 *   objplace    register the table with ObjPlace; planner decides (-> SPLIT)
 *
 * Reports per-step gather time (ms) and effective gather bandwidth (GiB/s).
 * Memory-bound: feature rows are large enough that gather misses cache.
 */
#define _GNU_SOURCE
#include "objplace.h"

#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <numa.h>

static uint64_t now_ns(void) {
    struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

/* Precompute a Zipf CDF over [0, n) with P(rank) ~ 1/(rank+1)^alpha. */
static double *zipf_cdf(size_t n, double alpha) {
    double *cdf = malloc(n * sizeof(double));
    double acc = 0;
    for (size_t i = 0; i < n; i++) { acc += 1.0 / pow((double)(i + 1), alpha); cdf[i] = acc; }
    for (size_t i = 0; i < n; i++) cdf[i] /= acc;
    return cdf;
}
static size_t zipf_sample(const double *cdf, size_t n, uint64_t *rng) {
    *rng = *rng * 6364136223846793005ULL + 1442695040888963407ULL;
    double u = (double)(*rng >> 11) / (double)(1ULL << 53);
    /* binary search */
    size_t lo = 0, hi = n - 1;
    while (lo < hi) { size_t m = (lo + hi) / 2; if (cdf[m] < u) lo = m + 1; else hi = m; }
    return lo;
}

int main(int argc, char **argv) {
    const char *policy = "objplace";
    size_t nodes = 2000000;     /* 2M nodes */
    int feat = 256;             /* 256 floats = 1 KiB rows */
    int batch = 8192;           /* neighbors gathered per step */
    int steps = 40;
    double alpha = 1.2, hotf = 0.10;
    int csv = 0; const char *tag = "run";

    for (int i = 1; i < argc; i++) {
        char *a = argv[i];
        if (!strncmp(a, "--policy=", 9)) policy = a + 9;
        else if (!strncmp(a, "--nodes=", 8)) nodes = strtoull(a + 8, NULL, 0);
        else if (!strncmp(a, "--feat=", 7)) feat = atoi(a + 7);
        else if (!strncmp(a, "--batch=", 8)) batch = atoi(a + 8);
        else if (!strncmp(a, "--steps=", 8)) steps = atoi(a + 8);
        else if (!strncmp(a, "--alpha=", 8)) alpha = atof(a + 8);
        else if (!strncmp(a, "--hot-frac=", 11)) hotf = atof(a + 11);
        else if (!strcmp(a, "--csv")) csv = 1;
        else if (!strncmp(a, "--tag=", 6)) tag = a + 6;
        else { fprintf(stderr, "gnnbench: unknown arg %s\n", a); return 2; }
    }
    if (numa_available() < 0) { fprintf(stderr, "no libnuma\n"); return 2; }

    size_t row_bytes = (size_t)feat * sizeof(float);
    size_t total = nodes * row_bytes;
    size_t hot_nodes = (size_t)(nodes * hotf);
    if (hot_nodes < 1) hot_nodes = 1;

    /* Allocate per policy. For split-style policies we keep two buffers and
       route by node id (< hot_nodes -> hot/DRAM). */
    float *table = NULL, *hot = NULL, *cold = NULL;
    obj_handle_t obj = NULL;
    int split = 0;

    if (!strcmp(policy, "dram")) {
        table = numa_alloc_onnode(total, 0);
    } else if (!strcmp(policy, "cxl")) {
        table = numa_alloc_onnode(total, 1);
    } else if (!strcmp(policy, "interleave")) {
        table = numa_alloc_interleaved(total);
    } else if (!strcmp(policy, "skew") || !strcmp(policy, "hotness")) {
        /* For a single skewed table, hotness-only and sensitivity agree: hot
           (low-id, high-degree) vertices -> DRAM, cold tail -> CXL. They diverge
           only across heterogeneous objects (see sensbench / mixbench). */
        hot = numa_alloc_onnode(hot_nodes * row_bytes, 0);
        cold = numa_alloc_onnode((nodes - hot_nodes) * row_bytes, 1);
        split = 1;
    } else if (!strcmp(policy, "objplace")) {
        /* Fast-tier budget sized to the hot partition: forces hot->DRAM,
           cold tail->CXL (a split), matching the manual skew baseline. */
        objplace_set_dram_budget((size_t)(total * hotf * 1.25));
        objplace_set_pressure(CXL_BW_CEILING_GIB);
        obj_attr_t fa = { OBJ_FEATURE, total, ACC_RANDOM, SENS_BANDWIDTH,
                          hotf, alpha, PHASE_GATHER };
        obj = obj_create(&fa);
        obj_rebalance();
        fprintf(stderr, "gnnbench objplace: feature table -> %s\n",
                placement_name(obj_placement(obj)));
        if (obj_placement(obj) == PLACE_SPLIT) {
            hot = obj_hot_ptr(obj); cold = obj_cold_ptr(obj);
            hot_nodes = obj_hot_bytes(obj) / row_bytes;
            split = 1;
        } else {
            table = obj_ptr(obj);
        }
    } else { fprintf(stderr, "gnnbench: unknown policy %s\n", policy); return 2; }

    /* Pre-touch. */
    if (split) { memset(hot, 1, hot_nodes * row_bytes);
                 memset(cold, 1, (nodes - hot_nodes) * row_bytes); }
    else       { memset(table, 1, total); }

    /* Precompute the gather index stream OUTSIDE the timed region so we measure
       memory (feature gather), not the Zipf sampler. */
    double *cdf = zipf_cdf(nodes, alpha);
    uint64_t rng = 0x1234567;
    size_t total_g = (size_t)steps * batch;
    uint32_t *idx = malloc(total_g * sizeof(uint32_t));
    for (size_t i = 0; i < total_g; i++) idx[i] = (uint32_t)zipf_sample(cdf, nodes, &rng);
    free(cdf);
    /* Realistic gather: materialize each neighbor's feature row into a contiguous
       output buffer (memcpy), as a GNN aggregation input would. This is
       memory-bandwidth-bound (no per-element float reduction to hide latency). */
    float *dst = numa_alloc_onnode(row_bytes, 0);

    /* warmup over a slice */
    for (size_t i = 0; i < (size_t)batch && i < total_g; i++) {
        size_t id = idx[i];
        const float *row = split ? ((id < hot_nodes) ? hot + id * feat
                                                      : cold + (id - hot_nodes) * feat)
                                 : table + id * feat;
        memcpy(dst, row, row_bytes);
    }

    uint64_t t0 = now_ns();
    uint64_t bytes = 0;
    size_t gi = 0;
    for (int s = 0; s < steps; s++) {
        for (int b = 0; b < batch; b++, gi++) {
            size_t id = idx[gi];
            const float *row = split ? ((id < hot_nodes) ? hot + id * feat
                                                         : cold + (id - hot_nodes) * feat)
                                     : table + id * feat;
            memcpy(dst, row, row_bytes);   /* materialize neighbor feature row */
        }
        bytes += (uint64_t)batch * row_bytes;
    }
    uint64_t t1 = now_ns();
    asm volatile("" :: "r"(dst));
    free(idx);
    numa_free(dst, row_bytes);

    double sec = (t1 - t0) / 1e9;
    double per_step_ms = sec / steps * 1000.0;
    double gibs = (bytes / sec) / (1ULL << 30);

    if (csv) printf("%s,%s,%.3f,%.3f,%.3f\n", tag, policy, sec, per_step_ms, gibs);
    else printf("policy=%-10s per_step=%.2f ms  gather_bw=%.2f GiB/s\n",
                policy, per_step_ms, gibs);

    if (obj) obj_destroy(obj);
    else if (split) { numa_free(hot, hot_nodes * row_bytes);
                      numa_free(cold, (nodes - hot_nodes) * row_bytes); }
    else numa_free(table, total);
    return 0;
}
