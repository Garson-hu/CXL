/* probe_log <cpu> <outfile> — the cxlpath DRAM latency probe as a logger: "mono_ns ns_per_load" every 10 ms until SIGTERM. */
#define _GNU_SOURCE
#include "cxlpath_daemon.h"
#include <sched.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
static volatile int stop; static void on_term(int s) { (void)s; stop = 1; }
int main(int argc, char **argv) { if (argc < 3) return 2; cpu_set_t s; CPU_ZERO(&s); CPU_SET(atoi(argv[1]), &s); sched_setaffinity(0, sizeof s, &s);
    signal(SIGTERM, on_term); cxlp_probe_t *p = cxlp_probe_create(256ul << 20); FILE *f = fopen(argv[2], "w"); setvbuf(f, NULL, _IOFBF, 1 << 20);
    while (!stop) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); fprintf(f, "%llu %.1f\n", (unsigned long long)t.tv_sec * 1000000000ull + t.tv_nsec, cxlp_probe_once(p, 1000)); usleep(10000); }
    fclose(f); return 0; }
