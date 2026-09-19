// V6 (time-boxed): does anything user-visible change the ~3.9 GiB/s GPU -> devdax write cap?
// Variants: registration flags; copy through the mapped device pointer (GPU-side memcpy);
// two concurrent streams into dax0.0 and dax1.0; small vs large offsets. Ranges restored.
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <time.h>
#include <sys/mman.h>
#include <cuda_runtime.h>
static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec*1e-9;}
#define LEN (1ul<<30)
int main(void){void*d;cudaMalloc(&d,LEN);cudaMemset(d,7,LEN);
  int f0=open("/dev/dax0.0",O_RDWR),f1=open("/dev/dax1.0",O_RDWR);
  unsigned char*p0=mmap(0,LEN,PROT_READ|PROT_WRITE,MAP_SHARED,f0,0),*p1=mmap(0,LEN,PROT_READ|PROT_WRITE,MAP_SHARED,f1,0);
  unsigned char*s0=malloc(LEN),*s1=malloc(LEN);memcpy(s0,p0,LEN);memcpy(s1,p1,LEN);
  unsigned flags[]={cudaHostRegisterDefault,cudaHostRegisterPortable,cudaHostRegisterMapped,cudaHostRegisterPortable|cudaHostRegisterMapped};
  const char*fn[]={"default","portable","mapped","portable+mapped"};
  for(int k=0;k<4;k++){cudaError_t e=cudaHostRegister(p0,LEN,flags[k]);if(e){printf("flag %-16s register: %s\n",fn[k],cudaGetErrorString(e));cudaGetLastError();continue;}
    double t=now();cudaMemcpy(p0,d,LEN,cudaMemcpyDeviceToHost);t=now()-t;printf("flag %-16s D2H cudaMemcpy        %.2f GiB/s\n",fn[k],1.0/t);
    if(flags[k]&cudaHostRegisterMapped){void*dp;if(!cudaHostGetDevicePointer(&dp,p0,0)){t=now();cudaMemcpy(dp,d,LEN,cudaMemcpyDeviceToDevice);cudaDeviceSynchronize();t=now()-t;printf("flag %-16s GPU-side copy to mapped ptr %.2f GiB/s\n",fn[k],1.0/t);}}
    cudaHostUnregister(p0);}
  // two streams at once, one per dax device
  cudaHostRegister(p0,LEN,0);cudaHostRegister(p1,LEN,0);cudaStream_t a,b;cudaStreamCreate(&a);cudaStreamCreate(&b);void*d2;
  if(!cudaMalloc(&d2,LEN)){double t=now();cudaMemcpyAsync(p0,d,LEN,cudaMemcpyDeviceToHost,a);cudaMemcpyAsync(p1,d2,LEN,cudaMemcpyDeviceToHost,b);cudaDeviceSynchronize();t=now()-t;
    printf("two concurrent streams (dax0.0 + dax1.0): %.2f GiB/s total\n",2.0/t);}
  // one stream to CXL while another goes to pinned DRAM: is the cap on the CXL side only?
  void*h;cudaMallocHost(&h,LEN);{double t=now();cudaMemcpyAsync(p0,d,LEN,cudaMemcpyDeviceToHost,a);cudaMemcpyAsync(h,d2,LEN,cudaMemcpyDeviceToHost,b);cudaStreamSynchronize(b);double tb=now()-t;cudaStreamSynchronize(a);double ta=now()-t;
    printf("concurrent: to CXL %.2f GiB/s, to pinned DRAM %.2f GiB/s\n",1.0/ta,1.0/tb);}
  cudaHostUnregister(p0);cudaHostUnregister(p1);memcpy(p0,s0,LEN);memcpy(p1,s1,LEN);return 0;}
