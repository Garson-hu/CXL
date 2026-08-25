/*
 * sensbench — shows why bandwidth-SENSITIVITY beats HOTNESS-ONLY for placement.
 *
 * Two equally-"hot" objects of equal size compete for a DRAM fast tier that
 * fits only ONE of them:
 *   - obj_stream: bandwidth-bound (streaming reads)   -> suffers a lot on CXL
 *   - obj_chase : latency-bound (pointer chase)       -> tolerates CXL
 *
 * A hotness-only planner cannot tell them apart (same hot_fraction) and, lacking
 * the sensitivity signal, protects the wrong one. ObjPlace ranks obj_stream
 * higher (sensitivity x CXL-penalty) and protects it.
 *
 * Policies (metric = bandwidth/stream object's throughput, the SLO-relevant one):
 *   cxl         stream object -> CXL          (naive)
 *   interleave  stream object -> interleaved
 *   hotness     emulates hotness-only: equal hotness, no sensitivity signal, so
 *               it protects the latency object (chase->DRAM) and strands
 *               stream->CXL  (coincides with `cxl` for the stream object)
 *   manual      oracle: stream -> DRAM
 *   objplace    planner: stream -> DRAM, chase -> CXL
 *
 * Both objects run concurrently under a CXL stream aggressor (started externally
 * on disjoint cores).
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

static uint64_t now_ns(void){ struct timespec t; clock_gettime(CLOCK_MONOTONIC,&t);
    return (uint64_t)t.tv_sec*1000000000ULL+t.tv_nsec; }
static void pin(int c){ cpu_set_t s; CPU_ZERO(&s); CPU_SET(c,&s);
    sched_setaffinity(0,sizeof(s),&s); }

struct sarg { int cpu; volatile uint64_t *buf; size_t qwords; uint64_t deadline;
              pthread_barrier_t *bar; uint64_t bytes; };

static void *stream_worker(void *a){
    struct sarg *t=a; pin(t->cpu); pthread_barrier_wait(t->bar);
    uint64_t acc=0,bytes=0; const volatile uint64_t *p=t->buf; size_t n=t->qwords;
    while(now_ns()<t->deadline){
        for(size_t i=0;i+8<=n;i+=8){ acc+=p[i]+p[i+1]+p[i+2]+p[i+3]+p[i+4]+p[i+5]+p[i+6]+p[i+7]; }
        bytes+=n*sizeof(uint64_t);
    }
    asm volatile(""::"r"(acc)); t->bytes=bytes; return NULL;
}
/* pointer-chase worker just keeps the latency object busy; its throughput is
   not the reported metric. */
static void *chase_worker(void *a){
    struct sarg *t=a; pin(t->cpu); pthread_barrier_wait(t->bar);
    uint64_t **p=(uint64_t**)t->buf;
    while(now_ns()<t->deadline){ for(int i=0;i<10000;i++) p=(uint64_t**)*p; }
    asm volatile(""::"r"(p)); return NULL;
}
static void build_chase(void *buf,size_t bytes){
    size_t n=bytes/64; uint64_t **s=(uint64_t**)buf;
    for(size_t i=0;i<n;i++) s[i*8]=(uint64_t*)&s[((i+1)%n)*8];
}

int main(int argc,char**argv){
    const char *policy="objplace"; double dur=3.0; int csv=0; const char*tag="run";
    size_t objsz=(size_t)1<<30;   /* 1 GiB each */
    for(int i=1;i<argc;i++){ char*a=argv[i];
        if(!strncmp(a,"--policy=",9))policy=a+9;
        else if(!strncmp(a,"--duration=",11))dur=atof(a+11);
        else if(!strncmp(a,"--size=",7))objsz=strtoull(a+7,NULL,0);
        else if(!strcmp(a,"--csv"))csv=1;
        else if(!strncmp(a,"--tag=",6))tag=a+6;
        else { fprintf(stderr,"sensbench: unknown arg %s\n",a); return 2; }
    }
    if(numa_available()<0){ fprintf(stderr,"no libnuma\n"); return 2; }

    void *stream_buf=NULL,*chase_buf=NULL;
    if(!strcmp(policy,"cxl")){
        stream_buf = numa_alloc_onnode(objsz,1);   /* CXL  */
        chase_buf  = numa_alloc_onnode(objsz,0);   /* DRAM */
    } else if(!strcmp(policy,"interleave")){
        stream_buf = numa_alloc_interleaved(objsz);
        chase_buf  = numa_alloc_interleaved(objsz);
    } else if(!strcmp(policy,"hotness")){
        /* hotness-only: equal hotness -> no sensitivity signal -> protects the
           latency object (chase on DRAM, stream on CXL). */
        chase_buf  = numa_alloc_onnode(objsz,0);   /* DRAM */
        stream_buf = numa_alloc_onnode(objsz,1);   /* CXL  */
    } else if(!strcmp(policy,"manual")){
        stream_buf = numa_alloc_onnode(objsz,0);   /* DRAM (oracle) */
        chase_buf  = numa_alloc_onnode(objsz,1);   /* CXL  */
    } else if(!strcmp(policy,"objplace")){
        objplace_set_dram_budget(objsz + objsz/4);  /* fits exactly one object */
        objplace_set_pressure(CXL_BW_CEILING_GIB);
        obj_attr_t sa={OBJ_BUFFER,objsz,ACC_STREAMING,SENS_BANDWIDTH,0,0,PHASE_ACTIVE};
        obj_attr_t ca={OBJ_GENERIC,objsz,ACC_RANDOM,SENS_LATENCY,0,0,PHASE_ACTIVE};
        obj_handle_t hs=obj_create(&sa), hc=obj_create(&ca);
        obj_rebalance();
        fprintf(stderr,"sensbench objplace: stream->%s chase->%s\n",
                placement_name(obj_placement(hs)),placement_name(obj_placement(hc)));
        stream_buf=obj_ptr(hs); chase_buf=obj_ptr(hc);
    } else { fprintf(stderr,"sensbench: unknown policy %s\n",policy); return 2; }
    if(!stream_buf||!chase_buf){ fprintf(stderr,"alloc failed\n"); return 5; }
    memset(stream_buf,1,objsz); memset(chase_buf,0,objsz); build_chase(chase_buf,objsz);

    pthread_barrier_t bar; pthread_barrier_init(&bar,NULL,2);
    uint64_t deadline=now_ns()+(uint64_t)(dur*1e9)+200000000ULL;
    struct sarg s={0,(uint64_t*)stream_buf,objsz/sizeof(uint64_t),deadline,&bar,0};
    struct sarg c={1,(uint64_t*)chase_buf,objsz/sizeof(uint64_t),deadline,&bar,0};
    pthread_t ts,tc;
    uint64_t t0=now_ns();
    pthread_create(&ts,NULL,stream_worker,&s);
    pthread_create(&tc,NULL,chase_worker,&c);
    pthread_join(ts,NULL); pthread_join(tc,NULL);
    uint64_t t1=now_ns();
    double sec=(t1-t0)/1e9, gibs=(s.bytes/sec)/(1ULL<<30);

    if(csv) printf("%s,%s,%.3f,%.3f\n",tag,policy,sec,gibs);
    else printf("policy=%-9s bandwidth_object_throughput=%.2f GiB/s\n",policy,gibs);
    return 0;   /* let process exit free everything */
}
