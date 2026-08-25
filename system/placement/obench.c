/*
 * obench — ObjPlace overhead microbenchmark.
 * Measures: obj_create cost, obj_rebalance cost, per-object metadata memory,
 * and steady-state access overhead (objplace whole-DRAM object vs a plain
 * numa_alloc_onnode buffer streamed identically).
 */
#define _GNU_SOURCE
#include "objplace.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <numa.h>

static uint64_t now_ns(void){ struct timespec t; clock_gettime(CLOCK_MONOTONIC,&t);
    return (uint64_t)t.tv_sec*1000000000ULL+t.tv_nsec; }

static double stream_gibs(volatile uint64_t *p, size_t qw, double dur){
    uint64_t deadline=now_ns()+(uint64_t)(dur*1e9), bytes=0, acc=0;
    uint64_t t0=now_ns();
    while(now_ns()<deadline){ for(size_t i=0;i+8<=qw;i+=8) acc+=p[i]+p[i+1]+p[i+2]+p[i+3]+p[i+4]+p[i+5]+p[i+6]+p[i+7]; bytes+=qw*8; }
    uint64_t t1=now_ns(); asm volatile(""::"r"(acc));
    return (bytes/((t1-t0)/1e9))/(1ULL<<30);
}

int main(int argc,char**argv){
    int N=2000; (void)argc;(void)argv;
    if(numa_available()<0){ fprintf(stderr,"no libnuma\n"); return 2; }
    objplace_init(0,1);
    objplace_set_dram_budget((size_t)64<<30);   /* ample: not the focus here */

    /* --- obj_create cost (no materialization) --- */
    obj_attr_t a={OBJ_GENERIC, 1<<20, ACC_RANDOM, SENS_BANDWIDTH, 0.1, 1.0, PHASE_ACTIVE};
    obj_handle_t *hs=malloc(N*sizeof(*hs));
    uint64_t t0=now_ns();
    for(int i=0;i<N;i++) hs[i]=obj_create(&a);
    uint64_t t1=now_ns();
    double create_us=(t1-t0)/1e3/N;

    /* --- obj_rebalance cost (global plan over N objects) --- */
    t0=now_ns(); obj_rebalance(); t1=now_ns();
    double rebal_us=(t1-t0)/1e3;

    /* --- metadata memory --- */
    size_t rec=objplace_record_bytes();
    int live=objplace_live_count();

    for(int i=0;i<N;i++) obj_destroy(hs[i]);
    free(hs);

    /* --- steady-state access overhead: objplace DRAM object vs plain numa buf.
       Alternate runs and take the median to remove first-run / ordering bias. --- */
    size_t sz=(size_t)512<<20, qw=sz/8;
    obj_attr_t da={OBJ_BUFFER,sz,ACC_STREAMING,SENS_BANDWIDTH,0,0,PHASE_ACTIVE};
    obj_handle_t h=obj_create(&da);
    void *op=obj_ptr(h); memset(op,1,sz);
    void *mn=numa_alloc_onnode(sz,0); memset(mn,1,sz);
    double bo[5], bm[5];
    for(int i=0;i<5;i++){ bo[i]=stream_gibs(op,qw,1.0); bm[i]=stream_gibs(mn,qw,1.0); }
    for(int i=0;i<5;i++)for(int j=i+1;j<5;j++){ if(bo[j]<bo[i]){double t=bo[i];bo[i]=bo[j];bo[j]=t;}
        if(bm[j]<bm[i]){double t=bm[i];bm[i]=bm[j];bm[j]=t;} }
    double bw_obj=bo[2], bw_man=bm[2];   /* medians */
    double access_overhead=(bw_man-bw_obj)/bw_man*100.0;
    obj_destroy(h); numa_free(mn,sz);

    printf("obj_create        : %.3f us/op  (N=%d)\n", create_us, N);
    printf("obj_rebalance     : %.1f us for %d objects (%.3f us/obj)\n", rebal_us, N, rebal_us/N);
    printf("metadata/object   : %zu bytes  (registry live=%d)\n", rec, live);
    printf("metadata for 10k  : %.2f MiB\n", rec*10000.0/(1<<20));
    printf("steady-state bw   : objplace=%.2f manual=%.2f GiB/s  overhead=%.2f%%\n",
           bw_obj, bw_man, access_overhead);
    if(getenv("OBENCH_CSV"))
        printf("CSV,create_us,%.4f,rebalance_us_total,%.2f,rec_bytes,%zu,access_overhead_pct,%.3f\n",
               create_us, rebal_us, rec, access_overhead);
    return 0;
}
