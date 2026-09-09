/*
 * pond — large-footprint leapfrog (wave/pond) stencil for CXL write-tier study.
 *   new[i] = 2*cur[i] - old[i] + c*(cur[i-1] - 2*cur[i] + cur[i+1])   (1-D, 5-pt variant)
 * Per timestep: read old + cur, compute, write new. Three physical buffers,
 * each placeable on dram | node1 | daxA (/dev/dax0.0) | daxB (/dev/dax2.0).
 * Policies:
 *   rotate   pointer rotation old<-cur<-new (CXL buffer becomes a READ source)
 *   copyback fixed roles: new written to its buffer, then copied into the DRAM
 *            'cur' buffer (reads always DRAM); --alt alternates the write
 *            target between buffer 2 and buffer 3 (two devices)
 *   migrate  like copyback but the copy trails the compute chunk-by-chunk
 *            (copier threads on a separate CCD) so it overlaps with compute
 * Outputs per step: wall time, GiB read/written per tier, effective GiB/s.
 * Build: gcc -O3 -march=native -fopenmp -o pond pond.c -lnuma -lpthread
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <fcntl.h>
#include <unistd.h>
#include <sched.h>
#include <pthread.h>
#include <sys/mman.h>
#include <numa.h>
#include <omp.h>
#include <x86intrin.h>
#include <time.h>

static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec*1e-9;}
static void pin(int cpu){cpu_set_t s;CPU_ZERO(&s);CPU_SET(cpu,&s);sched_setaffinity(0,sizeof s,&s);}

enum place { P_DRAM, P_NODE1, P_DAXA, P_DAXB };
static const char *PN[] = {"dram","node1","daxA","daxB"};
static const char *DAXPATH[] = {NULL,NULL,"/dev/dax0.0","/dev/dax2.0"};
static int parse_place(const char *s){for(int i=0;i<4;i++)if(!strcmp(s,PN[i]))return i;fprintf(stderr,"bad placement %s\n",s);exit(2);}

static double *alloc_buf(enum place p, size_t bytes, size_t dax_off, int nt_init){
    double *b;
    if(p==P_DRAM||p==P_NODE1){
        b=numa_alloc_onnode(bytes,p==P_DRAM?0:1); if(!b){perror("numa_alloc");exit(1);}
    } else {
        int fd=open(DAXPATH[p],O_RDWR); if(fd<0){perror(DAXPATH[p]);exit(1);}
        b=mmap(NULL,bytes,PROT_READ|PROT_WRITE,MAP_SHARED,fd,dax_off);
        if(b==MAP_FAILED){perror("mmap dax");exit(1);} close(fd);
    }
    (void)nt_init; memset(b,0,bytes);   /* pre-touch */
    return b;
}

static size_t N; static int T, copyT, cpu0, cpu_copy; static int use_nt; static double C=0.1;

/* compute chunk [a,b) of new from cur,old; NT or normal stores */
static void step_chunk(double *restrict nw,const double *restrict cur,const double *restrict old,size_t a,size_t b){
    if(a==0)a=1; if(b==N)b=N-1;
    if(use_nt){
        for(size_t i=a;i<b;i++){
            double v=2*cur[i]-old[i]+C*(cur[i-1]-2*cur[i]+cur[i+1]);
            _mm_stream_si64((long long*)&nw[i],*(long long*)&v);
        }
        _mm_sfence();
    } else {
        for(size_t i=a;i<b;i++) nw[i]=2*cur[i]-old[i]+C*(cur[i-1]-2*cur[i]+cur[i+1]);
    }
}

/* migrate policy: copier threads trail compute progress (chunk counter) */
static volatile size_t chunks_done; static size_t NCHUNK; static double *mig_src,*mig_dst;
static void *copier(void *arg){
    long id=(long)arg; pin(cpu_copy+id);
    size_t per=N/NCHUNK;
    for(size_t c=id;c<NCHUNK;c+=copyT){
        while(chunks_done<=c) { _mm_pause(); }
        size_t a=c*per,b=(c==NCHUNK-1)?N:(c+1)*per;
        memcpy(mig_dst+a,mig_src+a,(b-a)*sizeof(double));
    }
    return NULL;
}

int main(int argc,char**argv){
    size_t gib=8; int steps=10; enum place pl[3]={P_DRAM,P_DRAM,P_DRAM}; const char *policy="rotate";
    int alt=0; size_t daxoff[3]={0,0,0}; T=8; copyT=8; cpu0=0; cpu_copy=64; use_nt=0; const char *tag="run";
    for(int i=1;i<argc;i++){
        char*a=argv[i];
        if(!strncmp(a,"--gib=",6))gib=atol(a+6);
        else if(!strncmp(a,"--steps=",8))steps=atoi(a+8);
        else if(!strncmp(a,"--threads=",10))T=atoi(a+10);
        else if(!strncmp(a,"--copy-threads=",15))copyT=atoi(a+15);
        else if(!strncmp(a,"--cpu0=",7))cpu0=atoi(a+7);
        else if(!strncmp(a,"--cpu-copy=",11))cpu_copy=atoi(a+11);
        else if(!strncmp(a,"--place=",8)){char*s=strdup(a+8);char*t=strtok(s,",");for(int k=0;k<3&&t;k++,t=strtok(NULL,","))pl[k]=parse_place(t);}
        else if(!strncmp(a,"--daxoff=",9)){char*s=strdup(a+9);char*t=strtok(s,",");for(int k=0;k<3&&t;k++,t=strtok(NULL,","))daxoff[k]=(size_t)atof(t)*(1ULL<<30);}
        else if(!strncmp(a,"--policy=",9))policy=a+9;
        else if(!strcmp(a,"--alt"))alt=1;
        else if(!strcmp(a,"--nt"))use_nt=1;
        else if(!strncmp(a,"--tag=",6))tag=a+6;
        else {fprintf(stderr,"usage: pond --gib=G --steps=S --threads=T --place=p0,p1,p2 (dram|node1|daxA|daxB)\n"
             "  --daxoff=g0,g1,g2 (GiB offsets for dax buffers) --policy=rotate|copyback|migrate [--alt] [--nt]\n"
             "  --copy-threads=N --cpu0=C --cpu-copy=C --tag=NAME\n");return 2;}
    }
    N=(gib<<30)/sizeof(double); size_t bytes=N*sizeof(double);
    int is_mig=!strcmp(policy,"migrate");
    double *B[4]; for(int k=0;k<3;k++) B[k]=alloc_buf(pl[k],bytes,daxoff[k],use_nt);
    double *stage=NULL; if(is_mig){ stage=alloc_buf(P_DRAM,bytes,0,0); }   /* migrate: 4th buffer, DRAM staging */
    /* init: a bump in the middle */
    #pragma omp parallel for num_threads(T)
    for(size_t i=0;i<N;i++){double x=(double)i/N; B[0][i]=B[1][i]=(x>0.49&&x<0.51)?1.0:0.0;}
    double *old=B[0],*cur=B[1],*nw=B[2]; int nw_idx=2, cur_idx=1, old_idx=0;
    NCHUNK=(size_t)T*8; size_t per=N/NCHUNK;
    printf("tag,step,policy,place_old,place_cur,place_new,threads,nt,step_s,read_gib,write_gib,copy_gib,eff_read_gibs,eff_write_gibs\n");
    for(int s=0;s<steps;s++){
        double t0=now(); double copy_gib=0;
        pthread_t *cth=NULL; chunks_done=0;
        int do_mig=is_mig; double *dst=NULL; int dst_idx=-1;
        if(!strcmp(policy,"copyback")){ for(int k=0;k<3;k++) if(k!=nw_idx&&k!=cur_idx) dst_idx=k; dst=B[dst_idx]; }
        if(do_mig){ mig_src=nw; mig_dst=stage; cth=calloc(copyT,sizeof*cth);
            for(long i=0;i<copyT;i++) pthread_create(&cth[i],NULL,copier,(void*)i); }
        #pragma omp parallel num_threads(T)
        {
            int tid=omp_get_thread_num(); pin(cpu0+tid);
            #pragma omp for schedule(static)
            for(size_t c=0;c<NCHUNK;c++){
                size_t a=c*per,b=(c==NCHUNK-1)?N:(c+1)*per;
                step_chunk(nw,cur,old,a,b);
                #pragma omp atomic
                chunks_done++;
            }
        }
        double t_compute=now()-t0;
        if(!strcmp(policy,"copyback")){
            #pragma omp parallel for num_threads(T) schedule(static)
            for(size_t c=0;c<NCHUNK;c++){size_t a=c*per,b=(c==NCHUNK-1)?N:(c+1)*per; memcpy(dst+a,nw+a,(b-a)*sizeof(double));}
            copy_gib=(double)bytes/(1<<30);
            old=cur; old_idx=cur_idx; cur=dst; cur_idx=dst_idx;           /* reads stay on DRAM */
            if(alt){ int other=-1; for(int k=0;k<3;k++) if(k!=cur_idx&&k!=old_idx) other=k; nw=B[other]; nw_idx=other; }
        } else if(do_mig){
            for(int i=0;i<copyT;i++) pthread_join(cth[i],NULL); free(cth); cth=NULL;
            copy_gib=(double)bytes/(1<<30);
            /* old <- cur, cur <- staged DRAM copy of new, old's DRAM buffer becomes next staging; new stays on its device */
            double *freed=old; old=cur; cur=stage; stage=freed;
            old_idx=cur_idx; cur_idx=0;   /* staged copy lives in DRAM (reported as placement of B[0]) */
        } else { /* rotate */
            double *tmp=old; old=cur; cur=nw; nw=tmp; int ti=old_idx; old_idx=cur_idx; cur_idx=nw_idx; nw_idx=ti;
        }
        if(cth) free(cth);
        double dt=now()-t0; double rd=2.0*bytes/(1<<30), wr=(double)bytes/(1<<30);
        printf("%s,%d,%s,%s,%s,%s,%d,%d,%.4f,%.1f,%.1f,%.1f,%.1f,%.1f\n",tag,s,policy,PN[pl[old_idx]],PN[pl[cur_idx]],PN[pl[nw_idx]],T,use_nt,dt,rd,wr,copy_gib,rd/t_compute,wr/t_compute);
        fflush(stdout);
    }
    return 0;
}
