/*
 * bwbench — bandwidth-sensitive synthetic workload using obj_alloc_hint.
 *
 * Models a workload with two memory regions:
 *   - a HOT, bandwidth-sensitive working set streamed by all worker threads
 *   - a COLD, capacity region (allocated, lightly touched — represents data that
 *     must live somewhere but is not on the hot path)
 *
 * Placement policy controls where each region goes:
 *   allcxl      both regions on CXL
 *   interleave  both regions interleaved across DRAM + CXL
 *   hint        HOT via HINT_BW_SENSITIVE (DRAM), COLD via HINT_COLD_CAPACITY (CXL)
 *   objplace    HOT/COLD registered with the ObjPlace runtime, planner decides
 *
 * The reported metric is aggregate streaming bandwidth over the HOT region.
 * Run it with and without a CXL aggressor (launched externally on disjoint
 * cores) to see how much the hint policy protects the bandwidth-sensitive work.
 *
 * Threads pin to cores 0..threads-1, so an aggressor at --cpu-offset 64 (membench)
 * contends only on memory, not CPUs.
 */
#define _GNU_SOURCE
#include "objplace.h"

#include <pthread.h>
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <numa.h>

static uint64_t now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

struct targ {
    int cpu;
    volatile uint64_t *buf;
    size_t qwords;
    uint64_t deadline;
    pthread_barrier_t *bar;
    uint64_t bytes;
};

static void pin(int cpu) {
    cpu_set_t s; CPU_ZERO(&s); CPU_SET(cpu, &s);
    sched_setaffinity(0, sizeof(s), &s);
}

static void *worker(void *a) {
    struct targ *t = (struct targ *)a;
    pin(t->cpu);
    pthread_barrier_wait(t->bar);
    uint64_t acc = 0, bytes = 0;
    const volatile uint64_t *p = t->buf;
    size_t n = t->qwords;
    while (now_ns() < t->deadline) {
        for (size_t i = 0; i + 8 <= n; i += 8) {
            acc += p[i] + p[i+1] + p[i+2] + p[i+3]
                 + p[i+4] + p[i+5] + p[i+6] + p[i+7];
        }
        bytes += n * sizeof(uint64_t);
    }
    asm volatile("" :: "r"(acc));
    t->bytes = bytes;
    return NULL;
}

int main(int argc, char **argv) {
    const char *policy = "hint";
    int threads = 4;
    size_t hot = (size_t)1 << 30;    /* 1 GiB hot working set */
    size_t cold = (size_t)4 << 30;   /* 4 GiB cold capacity */
    double dur = 3.0;
    int csv = 0;
    const char *tag = "run";

    for (int i = 1; i < argc; i++) {
        char *a = argv[i];
        if (!strncmp(a, "--policy=", 9)) policy = a + 9;
        else if (!strncmp(a, "--threads=", 10)) threads = atoi(a + 10);
        else if (!strncmp(a, "--hot=", 6)) hot = strtoull(a + 6, NULL, 0);
        else if (!strncmp(a, "--cold=", 7)) cold = strtoull(a + 7, NULL, 0);
        else if (!strncmp(a, "--duration=", 11)) dur = atof(a + 11);
        else if (!strcmp(a, "--csv")) csv = 1;
        else if (!strncmp(a, "--tag=", 6)) tag = a + 6;
        else { fprintf(stderr, "bwbench: unknown arg %s\n", a); return 2; }
    }
    if (numa_available() < 0) { fprintf(stderr, "no libnuma\n"); return 2; }

    void *hotbuf = NULL, *coldbuf = NULL;
    obj_handle_t oh = NULL, oc = NULL;   /* objplace handles, if used */
    if (!strcmp(policy, "allcxl")) {
        hotbuf = obj_alloc_hint(hot, HINT_COLD_CAPACITY);   /* force CXL */
        coldbuf = obj_alloc_hint(cold, HINT_COLD_CAPACITY);
    } else if (!strcmp(policy, "interleave")) {
        hotbuf = numa_alloc_interleaved(hot);
        coldbuf = numa_alloc_interleaved(cold);
    } else if (!strcmp(policy, "hint")) {
        hotbuf = obj_alloc_hint(hot, HINT_BW_SENSITIVE);    /* DRAM */
        coldbuf = obj_alloc_hint(cold, HINT_COLD_CAPACITY); /* CXL */
    } else if (!strcmp(policy, "objplace")) {
        /* Register both regions; let the planner decide under CXL pressure.
           DRAM budget models a constrained fast tier: enough for the hot
           bandwidth-sensitive region, not the cold capacity region. */
        objplace_set_dram_budget(hot + hot / 4);
        objplace_set_pressure(CXL_BW_CEILING_GIB);          /* assume saturated */
        obj_attr_t ha = { OBJ_BUFFER, hot, ACC_STREAMING, SENS_BANDWIDTH, 0, 0, PHASE_ACTIVE };
        obj_attr_t ca = { OBJ_GENERIC, cold, ACC_RANDOM, SENS_CAPACITY, 0, 0, PHASE_INACTIVE };
        oh = obj_create(&ha);
        oc = obj_create(&ca);
        obj_rebalance();
        fprintf(stderr, "bwbench objplace: hot->%s cold->%s\n",
                placement_name(obj_placement(oh)), placement_name(obj_placement(oc)));
        hotbuf = obj_ptr(oh);
        coldbuf = obj_ptr(oc);
    } else {
        fprintf(stderr, "bwbench: unknown policy %s\n", policy); return 2;
    }
    if (!hotbuf || !coldbuf) { fprintf(stderr, "alloc failed\n"); return 5; }
    memset(hotbuf, 1, hot);
    memset(coldbuf, 1, cold);   /* touch cold once so it's backed */

    pthread_barrier_t bar;
    pthread_barrier_init(&bar, NULL, threads);
    pthread_t th[256];
    struct targ ta[256];
    uint64_t deadline = now_ns() + (uint64_t)(dur * 1e9) + 200000000ULL;
    size_t per = (hot / sizeof(uint64_t)) / threads;
    for (int i = 0; i < threads; i++) {
        ta[i].cpu = i;
        ta[i].buf = (uint64_t *)hotbuf + (size_t)i * per;
        ta[i].qwords = per;
        ta[i].deadline = deadline;
        ta[i].bar = &bar;
        ta[i].bytes = 0;
    }
    uint64_t t0 = now_ns();
    for (int i = 0; i < threads; i++) pthread_create(&th[i], NULL, worker, &ta[i]);
    for (int i = 0; i < threads; i++) pthread_join(th[i], NULL);
    uint64_t t1 = now_ns();
    pthread_barrier_destroy(&bar);

    uint64_t total = 0;
    for (int i = 0; i < threads; i++) total += ta[i].bytes;
    double sec = (t1 - t0) / 1e9;
    double gibs = (total / sec) / (1ULL << 30);

    if (csv)
        printf("%s,%s,%d,%.3f,%.3f\n", tag, policy, threads, sec, gibs);
    else
        printf("policy=%s threads=%d hot=%zuMiB bw=%.2f GiB/s\n",
               policy, threads, hot >> 20, gibs);

    if (oh || oc) {
        obj_destroy(oh);          /* objplace owns the buffers */
        obj_destroy(oc);
    } else {
        obj_free_hint(hotbuf, hot);   /* numa_free works for interleaved too */
        obj_free_hint(coldbuf, cold);
    }
    return 0;
}
