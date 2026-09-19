// V1: can O_DIRECT write to NVMe use a devdax (CXL) mapping as the source buffer?
// Writes a pattern into devdax, pwrite()s it with O_DIRECT, reads the file back through
// a normal DRAM buffer and compares. The devdax range is saved and restored.
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
#include <time.h>
#include <sys/mman.h>
static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec*1e-9;}
int main(int argc,char**argv){
  const char*dev=argc>1?argv[1]:"/dev/dax0.0"; const char*out=argc>2?argv[2]:"/mnt/local/ghu4/v1.bin";
  size_t len=(size_t)(argc>3?atol(argv[3]):1024)<<20, chunk=32ul<<20;
  int dfd=open(dev,O_RDWR); if(dfd<0){perror("open dax");return 1;}
  unsigned char*p=mmap(0,len,PROT_READ|PROT_WRITE,MAP_SHARED,dfd,0); if(p==MAP_FAILED){perror("mmap");return 1;}
  unsigned char*save=malloc(len); memcpy(save,p,len);
  for(size_t i=0;i<len;i++)p[i]=(unsigned char)(i*2654435761u>>11);
  int rc=0;
  for(int direct=1;direct>=0;direct--){
    int fd=open(out,O_WRONLY|O_CREAT|O_TRUNC|(direct?O_DIRECT:0),0644); if(fd<0){perror("open out");rc=1;break;}
    double t=now(); size_t off=0; int err=0;
    while(off<len){ssize_t w=pwrite(fd,p+off,chunk,off); if(w<0){err=errno;break;} off+=w;}
    fsync(fd); t=now()-t; close(fd);
    if(err){printf("%s from devdax: FAILED at offset %zu: %s\n",direct?"O_DIRECT":"buffered",off,strerror(err)); if(direct)rc=2; continue;}
    unsigned char*chk; posix_memalign((void**)&chk,4096,chunk); int rfd=open(out,O_RDONLY|O_DIRECT); int bad=0;
    for(size_t o=0;o<len&&!bad;o+=chunk){if(pread(rfd,chk,chunk,o)!=(ssize_t)chunk||memcmp(chk,p+o,chunk))bad=1;}
    close(rfd); free(chk);
    printf("%s from devdax: OK, %zu MiB in %.2fs = %.2f GiB/s, verify %s\n",direct?"O_DIRECT":"buffered",len>>20,t,(len/1073741824.0)/t,bad?"MISMATCH":"match");
    if(bad)rc=3;
  }
  // reference: O_DIRECT from an aligned DRAM buffer
  {unsigned char*d; posix_memalign((void**)&d,2ul<<20,len); memcpy(d,p,len);
   int fd=open(out,O_WRONLY|O_CREAT|O_TRUNC|O_DIRECT,0644); double t=now();
   for(size_t o=0;o<len;o+=chunk)if(pwrite(fd,d+o,chunk,o)<0){perror("ref");break;} fsync(fd); t=now()-t; close(fd);
   printf("reference O_DIRECT from DRAM: %.2f GiB/s\n",(len/1073741824.0)/t); free(d);}
  unlink(out); memcpy(p,save,len); munmap(p,len); return rc;}
