// V2: build a virtually contiguous buffer from SCATTERED 32 MB devdax segments
//     (mmap MAP_FIXED at adjacent addresses), verify CPU reads/writes across the seams.
// V3: cudaHostRegister on (a) the stitched buffer, (b) large plain ranges; time and limits;
//     GPU copy into the stitched buffer verified on the CPU.
// Touched device ranges are saved and restored (V2 part). Large-range registration only
// registers, it does not write.
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <time.h>
#include <sys/mman.h>
#include <cuda_runtime.h>
#define SEG (32ul<<20)
static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec*1e-9;}
int main(int argc,char**argv){
  const char*dev=argc>1?argv[1]:"/dev/dax0.0"; int nseg=argc>2?atoi(argv[2]):16;
  int fd=open(dev,O_RDWR); if(fd<0){perror("open");return 1;}
  size_t len=nseg*SEG;
  // scattered, out-of-order device segments: 97, 3, 1201, 45, ... (stride pattern)
  off_t *segoff=malloc(nseg*sizeof(off_t)); for(int i=0;i<nseg;i++) segoff[i]=(off_t)((i*397+ (i%2?1201:3))%4000)*SEG;
  unsigned char*base=mmap(0,len,PROT_NONE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0); if(base==MAP_FAILED){perror("reserve");return 1;}
  double t=now();
  for(int i=0;i<nseg;i++){void*q=mmap(base+i*SEG,SEG,PROT_READ|PROT_WRITE,MAP_SHARED|MAP_FIXED,fd,segoff[i]); if(q==MAP_FAILED){perror("mmap fixed");return 1;}}
  printf("V2 stitch: %d segments mapped at adjacent addresses in %.3f ms\n",nseg,(now()-t)*1e3);
  unsigned char*save=malloc(len); memcpy(save,base,len);
  for(size_t i=0;i<len;i+=8){unsigned long v=i*0x9E3779B97F4A7C15ul; memcpy(base+i,&v,8);}
  // verify through an independent linear mapping of each device segment
  int bad=0; for(int i=0;i<nseg&&!bad;i++){unsigned char*lin=mmap(0,SEG,PROT_READ,MAP_SHARED,fd,segoff[i]);
    for(size_t o=0;o<SEG;o+=8){unsigned long v=((size_t)i*SEG+o)*0x9E3779B97F4A7C15ul; if(memcmp(lin+o,&v,8)){bad=1;break;}} munmap(lin,SEG);}
  // a write that straddles every seam
  for(int i=1;i<nseg;i++){memset(base+i*SEG-24,0xAB,48);} 
  for(int i=1;i<nseg&&!bad;i++){for(int k=-24;k<24;k++) if(base[i*SEG+k]!=0xAB){bad=1;break;}}
  printf("V2 data across seams: %s\n",bad?"MISMATCH":"verified");
  // V3a: register the stitched buffer, GPU copies into it
  void*d; cudaMalloc(&d,len); unsigned char*pat=malloc(len); for(size_t i=0;i<len;i++)pat[i]=(unsigned char)(i*40503u>>7);
  cudaMemcpy(d,pat,len,cudaMemcpyHostToDevice);
  t=now(); cudaError_t e=cudaHostRegister(base,len,cudaHostRegisterDefault); double tr=now()-t;
  printf("V3a register stitched %zu MiB: %s (%.1f ms)\n",len>>20,e?cudaGetErrorString(e):"OK",tr*1e3);
  if(!e){memset(base,0,len); t=now(); cudaMemcpy(base,d,len,cudaMemcpyDeviceToHost); t=now()-t;
    printf("V3a GPU -> stitched buffer: %.2f GiB/s, verify %s\n",(len/1073741824.0)/t,memcmp(base,pat,len)?"MISMATCH":"match"); cudaHostUnregister(base);} else cudaGetLastError();
  memcpy(base,save,len); munmap(base,len); cudaFree(d);
  // V3b: large plain ranges (register only)
  double gib[]={1,8,64,200};
  for(int k=0;k<4;k++){size_t L=(size_t)(gib[k]*1073741824.0); unsigned char*p=mmap(0,L,PROT_READ|PROT_WRITE,MAP_SHARED,fd,0); if(p==MAP_FAILED){perror("mmap big");break;}
    t=now(); e=cudaHostRegister(p,L,cudaHostRegisterDefault); tr=now()-t;
    printf("V3b register %5.0f GiB: %s  %.2f s  (%.1f ms/GiB)\n",gib[k],e?cudaGetErrorString(e):"OK",tr,tr*1e3/gib[k]);
    if(!e){t=now(); cudaHostUnregister(p); printf("     unregister %.2f s\n",now()-t);} else cudaGetLastError();
    munmap(p,L);}
  return bad;}
