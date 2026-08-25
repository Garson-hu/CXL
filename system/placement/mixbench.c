/*
 * mixbench — multi-object DRAM-budget sweep.
 *
 * Creates a heterogeneous mix of objects competing for a constrained DRAM fast
 * tier, then places them under one of several planners and measures aggregate
 * "useful work" (sum over objects of access_intensity * achieved_bandwidth).
 * This is the scenario where a benefit-guided planner should beat simpler rules.
 *
 * Object mix (each 512 MiB), with explicit hotness (access intensity):
 *   O0 bandwidth, streaming, hotness 0.9   (high benefit/byte)
 *   O1 bandwidth, streaming, hotness 0.7   (high)
 *   O2 latency,   random,    hotness 1.0   (HOTTEST but LOW benefit/byte)
 *   O3 capacity,  random,    hotness 0.2   (lowest)
 *   O4 bandwidth, mixed,     hotness 0.6   (medium-high)
 *
 * The trap for hotness-only: O2 is the hottest object but latency-bound, so it
 * barely benefits from DRAM (CXL latency penalty is small). Hotness-only spends a
 * scarce DRAM slot on O2 and strands a bandwidth object (O1) on CXL; ObjPlace's
 * benefit-per-byte keeps O2 on CXL and protects O1.
 *
 * Planners (selection rule for which objects get the DRAM budget):
 *   hotness     rank by hot-ness (phase intensity) only  -> picks O0,O2 first
 *   sensitivity rank by sensitivity class only           -> ties among bw objects
 *   objplace    benefit-per-byte (the runtime planner)
 *   manual      brute-force best subset under the budget (oracle)
 *
 * Each object is exercised by one worker thread that streams (bandwidth objects)
 * or pointer-chases (latency/capacity objects) its buffer for the duration.
 * "Useful work" weights bandwidth objects' achieved GiB/s by their intensity.
 * Run under a CXL aggressor to make DRAM residence valuable.
 *
 * Reports total useful-work score and which objects landed on DRAM.
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

#define NOBJ 5
static uint64_t now_ns(void){ struct timespec t; clock_gettime(CLOCK_MONOTONIC,&t);
    return (uint64_t)t.tv_sec*1000000000ULL+t.tv_nsec; }
static void pin(int c){ cpu_set_t s; CPU_ZERO(&s); CPU_SET(c,&s); sched_setaffinity(0,sizeof(s),&s); }

/* object descriptors */
struct desc { obj_attr_t a; double intensity; int is_stream; };
static struct desc DESCS[NOBJ];
static void init_descs(size_t sz){
    DESCS[0]=(struct desc){{OBJ_BUFFER,sz,ACC_STREAMING,SENS_BANDWIDTH,0,0,PHASE_ACTIVE},1.0,1};
    DESCS[1]=(struct desc){{OBJ_BUFFER,sz,ACC_STREAMING,SENS_BANDWIDTH,0,0,PHASE_ACTIVE},0.8,1};
    DESCS[2]=(struct desc){{OBJ_GENERIC,sz,ACC_RANDOM,SENS_LATENCY,0,0,PHASE_ACTIVE},1.0,0};
    DESCS[3]=(struct desc){{OBJ_GENERIC,sz,ACC_RANDOM,SENS_CAPACITY,0,0,PHASE_INACTIVE},0.2,0};
    DESCS[4]=(struct desc){{OBJ_BUFFER,sz,ACC_MIXED,SENS_BANDWIDTH,0,0,PHASE_ACTIVE},0.7,1};
}

struct warg { int cpu; volatile uint64_t *buf; size_t qw; uint64_t deadline; int is_stream;
              pthread_barrier_t *bar; uint64_t bytes; };
static void build_chase(void *b,size_t bytes){ size_t n=bytes/64; uint64_t**s=(uint64_t**)b;
    for(size_t i=0;i<n;i++) s[i*8]=(uint64_t*)&s[((i+1)%n)*8]; }
static void *worker(void *a){
    struct warg *w=a; pin(w->cpu); pthread_barrier_wait(w->bar);
    uint64_t bytes=0;
    if(w->is_stream){ uint64_t acc=0; const volatile uint64_t*p=w->buf; size_t n=w->qw;
        while(now_ns()<w->deadline){ for(size_t i=0;i+8<=n;i+=8) acc+=p[i]+p[i+1]+p[i+2]+p[i+3]+p[i+4]+p[i+5]+p[i+6]+p[i+7]; bytes+=n*8; }
        asm volatile(""::"r"(acc)); }
    else { uint64_t **p=(uint64_t**)w->buf; uint64_t ops=0;
        while(now_ns()<w->deadline){ for(int i=0;i<10000;i++) p=(uint64_t**)*p; ops+=10000; }
        asm volatile(""::"r"(p)); bytes=ops*64; }
    w->bytes=bytes; return NULL;
}

/* Decide DRAM set per planner. Returns bitmask of objects placed on DRAM. */
static int plan_dram_set(const char *planner, size_t budget, size_t sz){
    int set=0; size_t used=0;
    int order[NOBJ];
    for(int i=0;i<NOBJ;i++) order[i]=i;
    if(!strcmp(planner,"hotness")){
        /* rank by hotness (access intensity) only — ignores sensitivity. This
           protects the hottest objects regardless of whether they are
           bandwidth-bound, so it can waste DRAM on a hot latency-bound object. */
        for(int i=0;i<NOBJ;i++)for(int j=i+1;j<NOBJ;j++){
            if(DESCS[order[j]].intensity>DESCS[order[i]].intensity){int t=order[i];order[i]=order[j];order[j]=t;}
        }
    } else if(!strcmp(planner,"sensitivity")){
        /* rank by sensitivity class: bandwidth first, then latency, then capacity.
           Ignores per-object access density/skew. */
        for(int i=0;i<NOBJ;i++)for(int j=i+1;j<NOBJ;j++){
            if(DESCS[order[j]].a.sensitivity<DESCS[order[i]].a.sensitivity){int t=order[i];order[i]=order[j];order[j]=t;}
        }
    } else if(!strcmp(planner,"objplace")){
        /* benefit-per-byte from the runtime, weighted by intensity. */
        objplace_set_dram_budget(budget); objplace_set_pressure(CXL_BW_CEILING_GIB);
        double bpb[NOBJ];
        for(int i=0;i<NOBJ;i++){ obj_handle_t h=obj_create(&DESCS[i].a);
            bpb[i]=obj_benefit_per_byte(h)*DESCS[i].intensity; obj_destroy(h); }
        for(int i=0;i<NOBJ;i++)for(int j=i+1;j<NOBJ;j++)
            if(bpb[order[j]]>bpb[order[i]]){int t=order[i];order[i]=order[j];order[j]=t;}
    } else if(!strcmp(planner,"manual")){
        /* oracle: rank by intensity*is_stream (bandwidth objects benefit most on
           DRAM under a CXL aggressor). */
        for(int i=0;i<NOBJ;i++)for(int j=i+1;j<NOBJ;j++){
            double si=DESCS[order[i]].intensity*(DESCS[order[i]].is_stream?1.0:0.1);
            double sj=DESCS[order[j]].intensity*(DESCS[order[j]].is_stream?1.0:0.1);
            if(sj>si){int t=order[i];order[i]=order[j];order[j]=t;}
        }
    } else { fprintf(stderr,"mixbench: unknown planner %s\n",planner); exit(2); }
    for(int k=0;k<NOBJ;k++){ int o=order[k]; if(used+sz<=budget){ set|=(1<<o); used+=sz; } }
    return set;
}

int main(int argc,char**argv){
    const char *planner="objplace"; double dur=3.0; int csv=0; const char*tag="run";
    size_t sz=(size_t)512<<20; double budget_frac=0.20;
    for(int i=1;i<argc;i++){ char*a=argv[i];
        if(!strncmp(a,"--planner=",10))planner=a+10;
        else if(!strncmp(a,"--budget-frac=",14))budget_frac=atof(a+14);
        else if(!strncmp(a,"--size=",7))sz=strtoull(a+7,NULL,0);
        else if(!strncmp(a,"--duration=",11))dur=atof(a+11);
        else if(!strcmp(a,"--csv"))csv=1;
        else if(!strncmp(a,"--tag=",6))tag=a+6;
        else { fprintf(stderr,"mixbench: unknown arg %s\n",a); return 2; }
    }
    if(numa_available()<0){ fprintf(stderr,"no libnuma\n"); return 2; }
    init_descs(sz);
    size_t budget=(size_t)(NOBJ*sz*budget_frac);
    int dram_set=plan_dram_set(planner,budget,sz);

    void *bufs[NOBJ];
    for(int i=0;i<NOBJ;i++){
        int node=(dram_set>>i&1)?0:1;
        bufs[i]=numa_alloc_onnode(sz,node);
        if(!bufs[i]){ fprintf(stderr,"alloc failed\n"); return 5; }
        memset(bufs[i],1,sz);
        if(!DESCS[i].is_stream) build_chase(bufs[i],sz);
    }

    pthread_barrier_t bar; pthread_barrier_init(&bar,NULL,NOBJ);
    uint64_t deadline=now_ns()+(uint64_t)(dur*1e9)+200000000ULL;
    pthread_t th[NOBJ]; struct warg w[NOBJ];
    for(int i=0;i<NOBJ;i++){ w[i]=(struct warg){i,(uint64_t*)bufs[i],sz/8,deadline,
                              DESCS[i].is_stream,&bar,0}; }
    uint64_t t0=now_ns();
    for(int i=0;i<NOBJ;i++) pthread_create(&th[i],NULL,worker,&w[i]);
    for(int i=0;i<NOBJ;i++) pthread_join(th[i],NULL);
    uint64_t t1=now_ns(); pthread_barrier_destroy(&bar);
    double sec=(t1-t0)/1e9;

    /* useful-work score = sum over stream objects of intensity * GiB/s. */
    double score=0; char dram_list[64]="";
    for(int i=0;i<NOBJ;i++){
        if(DESCS[i].is_stream){ double g=(w[i].bytes/sec)/(1ULL<<30); score+=DESCS[i].intensity*g; }
        if(dram_set>>i&1){ char b[8]; snprintf(b,sizeof b,"O%d ",i); strncat(dram_list,b,sizeof(dram_list)-strlen(dram_list)-1); }
    }
    if(csv) printf("%s,%s,%.2f,%.3f,\"%s\"\n",tag,planner,budget_frac,score,dram_list);
    else printf("planner=%-11s budget=%.0f%% score=%.2f  DRAM={%s}\n",
                planner,budget_frac*100,score,dram_list);
    for(int i=0;i<NOBJ;i++) numa_free(bufs[i],sz);
    return 0;
}
