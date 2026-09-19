// V5: does a cheap DRAM latency probe track the slowdown of a real DRAM reader?
// One process, overlap guaranteed by construction:
//   victim   : 8 streaming readers, cpus 0-7   (CCD0), 1 GiB each -> bandwidth
//   probe    : 1 thread, cpu 16 (CCD1): every 10 ms, 1000 dependent random loads over a
//              256 MiB pointer-chase region -> ns per load
//   aggressor: W NT-store writers on cpus 32.. (CCD2-7), 256 MiB each, run for the whole window
// Usage: v5 <writers> <seconds>
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <pthread.h>
#include <sched.h>
#include <time.h>
#include <unistd.h>
#include <sys/mman.h>
#include <immintrin.h>
static volatile int go=0, stop=0;
static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec*1e-9;}
static void pin(int c){cpu_set_t s;CPU_ZERO(&s);CPU_SET(c,&s);pthread_setaffinity_np(pthread_self(),sizeof s,&s);}
static void*huge(size_t n){void*p=mmap(0,n,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);madvise(p,n,MADV_HUGEPAGE);return p;}
typedef struct{int cpu;size_t bytes;uint64_t done;}targ;
static void*writer(void*a){targ*t=a;pin(t->cpu);size_t n=t->bytes/8;long long*b=huge(t->bytes);memset(b,1,t->bytes);
  __sync_fetch_and_add(&go,1); while(go>=0&&!stop&&go<1000000) { if(go<0)break; if(go>=100000)break; usleep(1000);} 
  while(!stop){for(size_t i=0;i<n;i++)_mm_stream_si64(b+i,(long long)i);_mm_sfence();t->done+=t->bytes;}return 0;}
static void*reader(void*a){targ*t=a;pin(t->cpu);size_t n=t->bytes/8;uint64_t*b=huge(t->bytes);for(size_t i=0;i<n;i++)b[i]=i;
  __sync_fetch_and_add(&go,1); while(go<100000&&!stop)usleep(1000);
  uint64_t s=0;while(!stop){for(size_t i=0;i<n;i++)s+=b[i];t->done+=t->bytes;} if(s==42)puts("");return 0;}
#define NODES (4u<<20)            /* 4M nodes x 64 B = 256 MiB */
typedef struct{uint32_t next;char pad[60];}node;
/* one probe: k dependent loads; returns ns per load (integer clock math, not inlined) */
static __attribute__((noinline)) double chase(node*g,uint32_t*pcur,int k){struct timespec a,b;uint32_t c=*pcur;
  clock_gettime(CLOCK_MONOTONIC,&a);for(int i=0;i<k;i++){c=g[c].next;__asm__ volatile("" ::: "memory");}clock_gettime(CLOCK_MONOTONIC,&b);
  *pcur=c;return ((b.tv_sec-a.tv_sec)*1e9+(b.tv_nsec-a.tv_nsec))/k;}
static int cmpd(const void*a,const void*b){double x=*(double*)a,y=*(double*)b;return x<y?-1:x>y;}
int main(int argc,char**argv){int W=atoi(argv[1]);double secs=atof(argv[2]);
  pin(16); node*g=huge((size_t)NODES*64); uint32_t*perm=malloc(NODES*4);
  for(uint32_t i=0;i<NODES;i++)perm[i]=i; uint64_t x=88172645463325252ull;
  for(uint32_t i=NODES-1;i>0;i--){x^=x<<13;x^=x>>7;x^=x<<17;uint32_t j=x%(i+1),t=perm[i];perm[i]=perm[j];perm[j]=t;}
  for(uint32_t i=0;i<NODES;i++)g[perm[i]].next=perm[(i+1)%NODES]; free(perm);
  int nt=W+8; pthread_t*th=malloc(nt*sizeof*th); targ*ta=calloc(nt,sizeof*ta);
  for(int i=0;i<8;i++){ta[i]=(targ){i,1ul<<30,0};pthread_create(&th[i],0,reader,&ta[i]);}
  for(int i=0;i<W;i++){ta[8+i]=(targ){32+i,256ul<<20,0};pthread_create(&th[8+i],0,writer,&ta[8+i]);}
  while(go<nt)usleep(1000);            // everyone pre-touched
  go=100000; sleep(3);                 // start all, settle 3 s
  uint64_t r0=0,w0=0;for(int i=0;i<8;i++)r0+=ta[i].done;for(int i=0;i<W;i++)w0+=ta[8+i].done;
  double t0=now(); int cap=(int)(secs*100)+8,ns=0; double*lat=malloc(cap*sizeof(double)); uint32_t cur=12345;
  while(now()-t0<secs&&ns<cap){lat[ns++]=chase(g,&cur,1000); cur=(cur*2654435761u)%NODES; usleep(10000);}
  double dt=now()-t0; uint64_t r1=0,w1=0;for(int i=0;i<8;i++)r1+=ta[i].done;for(int i=0;i<W;i++)w1+=ta[8+i].done;
  stop=1; for(int i=0;i<nt;i++)pthread_join(th[i],0);
  qsort(lat,ns,sizeof(double),cmpd); double m=0;for(int i=0;i<ns;i++)m+=lat[i];m/=ns;
  printf("writers=%3d  write=%7.1f GiB/s  victim_read=%6.1f GiB/s  probe ns/load: mean=%7.1f p50=%7.1f p90=%7.1f p99=%7.1f  (n=%d)\n",
    W,(w1-w0)/dt/1073741824.0,(r1-r0)/dt/1073741824.0,m,lat[ns/2],lat[ns*9/10],lat[ns*99/100],ns);
  return 0;}
