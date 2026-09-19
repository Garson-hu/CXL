// Feasibility check: can a CUDA GPU copy directly into a devdax (CXL) mapping?
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <time.h>
#include <sys/mman.h>
#include <cuda_runtime.h>
static double now(){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec*1e-9;}
static const char* es(cudaError_t e){return cudaGetErrorString(e);}
int main(int argc,char**argv){
  const char*dev=argc>1?argv[1]:"/dev/dax0.0";
  size_t len=(size_t)(argc>2?atol(argv[2]):1024)<<20;   // MiB
  int fd=open(dev,O_RDWR); if(fd<0){perror("open");return 1;}
  unsigned char*p=mmap(0,len,PROT_READ|PROT_WRITE,MAP_SHARED,fd,0);
  if(p==MAP_FAILED){perror("mmap");return 1;}
  unsigned char*save=malloc(len); memcpy(save,p,len);           // restore later
  unsigned char*d; cudaError_t e=cudaMalloc((void**)&d,len); if(e){printf("cudaMalloc: %s\n",es(e));return 1;}
  unsigned char*pat=malloc(len); for(size_t i=0;i<len;i++)pat[i]=(unsigned char)(i*2654435761u>>13);
  cudaMemcpy(d,pat,len,cudaMemcpyHostToDevice);
  // 1) register the devdax mapping
  e=cudaHostRegister(p,len,cudaHostRegisterDefault);
  printf("cudaHostRegister(%s, %zu MiB): %s\n",dev,len>>20,e?es(e):"OK");
  int reg=(e==0); if(!reg) cudaGetLastError();
  // 2) GPU -> devdax copy, verify on CPU
  memset(p,0,len);
  double t=now(); e=cudaMemcpy(p,d,len,cudaMemcpyDeviceToHost); cudaDeviceSynchronize(); t=now()-t;
  printf("D2H into devdax: %s, %.2f GiB/s, verify %s\n",e?es(e):"OK",(len/1073741824.0)/t,memcmp(p,pat,len)?"MISMATCH":"match");
  for(int r=0;r<3;r++){t=now();cudaMemcpy(p,d,len,cudaMemcpyDeviceToHost);cudaDeviceSynchronize();t=now()-t;printf("  rep%d %.2f GiB/s\n",r,(len/1073741824.0)/t);}
  // 3) devdax -> GPU -> check
  cudaMemset(d,0,len); e=cudaMemcpy(d,p,len,cudaMemcpyHostToDevice);
  unsigned char*back=malloc(len); cudaMemcpy(back,d,len,cudaMemcpyDeviceToHost);
  printf("H2D from devdax: %s, verify %s\n",e?es(e):"OK",memcmp(back,pat,len)?"MISMATCH":"match");
  // 4) zero-copy device pointer?
  if(reg){void*dp=0; e=cudaHostGetDevicePointer(&dp,p,0); printf("cudaHostGetDevicePointer: %s\n",e?es(e):"OK");}
  // reference: pinned DRAM and pageable DRAM
  unsigned char*h; cudaMallocHost((void**)&h,len);
  for(int r=0;r<3;r++){t=now();cudaMemcpy(h,d,len,cudaMemcpyDeviceToHost);cudaDeviceSynchronize();t=now()-t;printf("ref pinned DRAM rep%d %.2f GiB/s\n",r,(len/1073741824.0)/t);}
  unsigned char*m=malloc(len); memset(m,1,len);
  for(int r=0;r<3;r++){t=now();cudaMemcpy(m,d,len,cudaMemcpyDeviceToHost);cudaDeviceSynchronize();t=now()-t;printf("ref pageable DRAM rep%d %.2f GiB/s\n",r,(len/1073741824.0)/t);}
  if(reg) cudaHostUnregister(p);
  memcpy(p,save,len); munmap(p,len); return 0;}
