/* dram_aggressor <threads> <first_cpu> <seconds> — NT-store writers into DRAM (the "other tenant").
 * Buffers are pre-touched SERIALLY by the main thread (a gentle ~5 GiB/s), so the pressure begins
 * at the START line, not during set-up. Prints START/END as CLOCK_MONOTONIC ns. */
#define _GNU_SOURCE
#include <immintrin.h>
#include <pthread.h>
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/mman.h>
static volatile int stop; static pthread_barrier_t bar;
typedef struct { int cpu; long long *buf; unsigned long done; } a_t;
#define BYTES (256ul << 20)
static void *run(void *x) { a_t *a = x; cpu_set_t s; CPU_ZERO(&s); CPU_SET(a->cpu, &s); pthread_setaffinity_np(pthread_self(), sizeof s, &s);
    pthread_barrier_wait(&bar);
    while (!stop) { for (size_t i = 0; i < BYTES / 8; i++) _mm_stream_si64(a->buf + i, (long long)i); _mm_sfence(); a->done += BYTES; } return NULL; }
static unsigned long long mono(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return (unsigned long long)t.tv_sec * 1000000000ull + t.tv_nsec; }
int main(int argc, char **argv) {
    if (argc < 4) return 2;
    int n = atoi(argv[1]), cpu0 = atoi(argv[2]); double secs = atof(argv[3]);
    pthread_t th[256]; a_t a[256]; pthread_barrier_init(&bar, NULL, (unsigned)n + 1);
    for (int i = 0; i < n; i++) { a[i] = (a_t){ cpu0 + i, mmap(NULL, BYTES, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0), 0 }; madvise(a[i].buf, BYTES, MADV_HUGEPAGE); memset(a[i].buf, 1, BYTES); }
    for (int i = 0; i < n; i++) pthread_create(&th[i], NULL, run, &a[i]);
    usleep(200000); printf("START %llu\n", mono()); fflush(stdout); pthread_barrier_wait(&bar);
    struct timespec ts = { (time_t)secs, (long)((secs - (time_t)secs) * 1e9) }; nanosleep(&ts, NULL);
    stop = 1; printf("END %llu\n", mono()); unsigned long t = 0; for (int i = 0; i < n; i++) { pthread_join(th[i], NULL); t += a[i].done; }
    printf("AGGRESSOR threads=%d GiBs=%.1f\n", n, t / secs / 1073741824.0); return 0;
}
