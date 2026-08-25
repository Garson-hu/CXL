/*
 * test_objplace — sanity checks for the ObjPlace runtime.
 *   1. compat obj_alloc_hint: each hint lands on the right node (move_pages).
 *   2. planner: bandwidth-sensitive -> DRAM, capacity -> CXL, skewed -> SPLIT,
 *      and "hotness-only" confusability case is resolved by sensitivity.
 *   3. materialized split object: hot on DRAM, cold on CXL.
 */
#define _GNU_SOURCE
#include "objplace.h"

#include <stdio.h>
#include <string.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <numa.h>

static int node_of(void *p) {
    int status = -1;
    void *pages[1] = { p };
    if (syscall(SYS_move_pages, 0, 1, pages, NULL, &status, 0) < 0) return -2;
    return status;
}

static int expect(const char *what, int got, int want) {
    int ok = (got == want);
    printf("  %-40s got=%d want=%d  %s\n", what, got, want, ok ? "PASS" : "FAIL");
    return ok ? 0 : 1;
}

int main(void) {
    if (numa_available() < 0) { fprintf(stderr, "no libnuma\n"); return 2; }
    int dram = obj_hint_node(HINT_BW_SENSITIVE);
    int cxl  = obj_hint_node(HINT_COLD_CAPACITY);
    printf("ObjPlace test (DRAM node %d, CXL node %d)\n", dram, cxl);
    int fails = 0;

    /* 1. compat hints land on the right node. */
    printf("[compat obj_alloc_hint]\n");
    size_t sz = 8 << 20;
    void *a = obj_alloc_hint(sz, HINT_BW_SENSITIVE); memset(a, 1, sz);
    void *b = obj_alloc_hint(sz, HINT_COLD_CAPACITY); memset(b, 1, sz);
    fails += expect("BW_SENSITIVE -> DRAM", node_of(a), dram);
    fails += expect("COLD_CAPACITY -> CXL", node_of(b), cxl);
    obj_free_hint(a, sz); obj_free_hint(b, sz);

    /* 2. planner decisions. DRAM budget models a constrained fast tier (smaller
       than the total working set) — that is the regime where placement matters.
       128 MiB fits the bandwidth object + the skewed hot partition, but not the
       cold tail or the capacity object. */
    printf("[planner decisions]\n");
    objplace_set_dram_budget(128UL << 20);  /* 128 MiB fast tier */
    objplace_set_pressure(CXL_BW_CEILING_GIB);  /* saturated */

    obj_attr_t bw = { OBJ_BUFFER, 64<<20, ACC_STREAMING, SENS_BANDWIDTH, 0,0, PHASE_ACTIVE };
    obj_attr_t cap = { OBJ_GENERIC, 64<<20, ACC_RANDOM, SENS_CAPACITY, 0,0, PHASE_INACTIVE };
    obj_attr_t skew = { OBJ_EMBEDDING, 512<<20, ACC_RANDOM, SENS_BANDWIDTH, 0.1, 1.2, PHASE_GATHER };
    obj_handle_t hbw = obj_create(&bw);
    obj_handle_t hcap = obj_create(&cap);
    obj_handle_t hskew = obj_create(&skew);
    obj_rebalance();

    printf("    bw-sensitive  -> %s (bpb=%.3f)\n", placement_name(obj_placement(hbw)), obj_benefit_per_byte(hbw));
    printf("    capacity      -> %s (bpb=%.3f)\n", placement_name(obj_placement(hcap)), obj_benefit_per_byte(hcap));
    printf("    skewed embed  -> %s (bpb=%.3f)\n", placement_name(obj_placement(hskew)), obj_benefit_per_byte(hskew));
    fails += expect("bw-sensitive placement==DRAM", obj_placement(hbw)==PLACE_DRAM, 1);
    fails += expect("capacity placement==CXL", obj_placement(hcap)==PLACE_CXL, 1);
    fails += expect("skewed placement==SPLIT", obj_placement(hskew)==PLACE_SPLIT, 1);

    /* 3. split object materializes hot->DRAM, cold->CXL. */
    printf("[split materialization]\n");
    if (obj_placement(hskew) == PLACE_SPLIT) {
        void *hot = obj_hot_ptr(hskew); memset(hot, 1, 4096);
        void *cold = obj_cold_ptr(hskew); memset(cold, 1, 4096);
        fails += expect("skew hot -> DRAM", node_of(hot), dram);
        fails += expect("skew cold -> CXL", node_of(cold), cxl);
    } else {
        printf("  (skew not SPLIT; skipping partition node check)\n");
    }

    /* 4. hotness-only confusability: two objects same hot_fraction, different
       sensitivity. ObjPlace ranks the bandwidth one higher. */
    printf("[sensitivity vs hotness-only]\n");
    obj_attr_t hot_lat = { OBJ_GENERIC, 64<<20, ACC_RANDOM, SENS_LATENCY, 0,0, PHASE_ACTIVE };
    obj_attr_t hot_bw  = { OBJ_BUFFER, 64<<20, ACC_STREAMING, SENS_BANDWIDTH, 0,0, PHASE_ACTIVE };
    obj_handle_t hl = obj_create(&hot_lat);
    obj_handle_t hb = obj_create(&hot_bw);
    double bl = obj_benefit_per_byte(hl), bb = obj_benefit_per_byte(hb);
    printf("    latency-bound bpb=%.3f  bandwidth-bound bpb=%.3f\n", bl, bb);
    fails += expect("bandwidth bpb > latency bpb", bb > bl, 1);

    obj_destroy(hbw); obj_destroy(hcap); obj_destroy(hskew);
    obj_destroy(hl); obj_destroy(hb);

    printf("%s (%d failure(s))\n", fails==0 ? "ALL PASS" : "SOME FAIL", fails);
    return fails==0 ? 0 : 1;
}
