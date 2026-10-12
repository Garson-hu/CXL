/* reader_victim — the synthetic DRAM-bound victim as a standalone process: N streaming readers on cpus
 * <first_cpu>.., 1 GiB each; the main thread prints "T <mono ns> <GiB/s over the last 100 ms>" until SIGTERM.
 * usage: reader_victim [N=8] [first_cpu=0] [chunk_MiB=1024]. Progress is counted every chunk_MiB; the default (one 1 GiB
 * pass) quantizes a 100 ms sample to ~10% steps — use 64 for per-sample tails (2026-10-12). */
#define _GNU_SOURCE
#include <pthread.h>
#include <sched.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
#include <sys/mman.h>
static volatile int stop, go; static uint64_t done[64]; static int cpu0; static size_t chunk = 1ul << 30;
static void on_term(int sig) { (void)sig; stop = 1; }
static uint64_t now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return (uint64_t)t.tv_sec * 1000000000ull + (uint64_t)t.tv_nsec; }
static void *reader(void *a) {
    long id = (long)a; cpu_set_t cs; CPU_ZERO(&cs); CPU_SET(cpu0 + (int)id, &cs); pthread_setaffinity_np(pthread_self(), sizeof cs, &cs);
    size_t n = (1ul << 30) / 8; uint64_t *b = mmap(NULL, 1ul << 30, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0); madvise(b, 1ul << 30, MADV_HUGEPAGE);
    for (size_t i = 0; i < n; i++) b[i] = i;
    __sync_fetch_and_add(&go, 1); while (go < 100) usleep(1000);
    uint64_t acc = 0;
    size_t ce = chunk / 8;
    while (!stop) for (size_t c = 0; c < n && !stop; c += ce) { for (size_t i = c; i < c + ce; i++) acc += b[i]; __atomic_fetch_add(&done[id], chunk, __ATOMIC_RELAXED); }   /* atomic: a plain += was hoisted out of the loop by the compiler */
    if (acc == 42) puts("");
    return NULL;
}
int main(int argc, char **argv) {
    int n = argc > 1 ? atoi(argv[1]) : 8; cpu0 = argc > 2 ? atoi(argv[2]) : 0; if (argc > 3) chunk = (size_t)atoi(argv[3]) << 20; signal(SIGTERM, on_term);
    pthread_t th[64]; for (long i = 0; i < n; i++) pthread_create(&th[i], NULL, reader, (void *)i);
    while (go < n) usleep(1000);
    go = 100; uint64_t prev = 0, tp = now(); printf("READY %llu\n", (unsigned long long)tp); fflush(stdout);
    while (!stop) {
        usleep(100000); uint64_t t = now(), tot = 0; for (int i = 0; i < n; i++) tot += done[i];
        printf("T %llu %.2f\n", (unsigned long long)t, (tot - prev) / ((t - tp) / 1e9) / 1073741824.0); prev = tot; tp = t; fflush(stdout);
    }
    for (int i = 0; i < n; i++) pthread_join(th[i], NULL); return 0;
}
