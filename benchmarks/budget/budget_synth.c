/* budget_synth — synthetic victim, DRAM latency probe and a rate-limited write stream in ONE process,
 * so the measurement window and the stream overlap by construction (METHODOLOGY: verified overlap).
 *   victim : 8 streaming readers on cpus 0-7 (CCD0), 1 GiB each
 *   probe  : cpu 16 (CCD1), 1000 dependent loads every 10 ms (the cxlpath probe)
 *   writers: spread over CCD2-7 (cpus 32..127); <= 12 GiB/s per thread when rate-limited
 * usage: budget_synth <rate GiB/s | 0 none | -N = N unlimited threads> <pure|copy> <dram|/dev/daxX.Y> <seconds> */
#include "writer.h"
#include "cxlpath_daemon.h"
typedef struct { int cpu; uint64_t done; } rd_t;
static volatile int r_go, r_stop;
static void *reader(void *a) { rd_t *r = a; w_pin(r->cpu); size_t n = (1ul << 30) / 8; uint64_t *b = mmap(NULL, 1ul << 30, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    madvise(b, 1ul << 30, MADV_HUGEPAGE); for (size_t i = 0; i < n; i++) b[i] = i; __sync_fetch_and_add(&r_go, 1); while (r_go < 100) usleep(1000);
    uint64_t s = 0; while (!r_stop) { for (size_t i = 0; i < n; i++) s += b[i]; r->done += 1ul << 30; } if (s == 42) puts(""); return NULL; }
static int cmpd(const void *a, const void *b) { double x = *(const double *)a, y = *(const double *)b; return x < y ? -1 : x > y; }
int main(int argc, char **argv) {
    if (argc < 5) { fprintf(stderr, "usage\n"); return 2; }
    double rate = atof(argv[1]); int mode = !strcmp(argv[2], "copy"); const char *target = argv[3]; double secs = atof(argv[4]);
    int nw = rate < 0 ? (int)-rate : (rate > 0 ? (int)((rate + 11.999) / 12) : 0); if (rate < 0) rate = 0;
    w_pin(16); cxlp_probe_t *pr = cxlp_probe_create(256ul << 20);
    pthread_t rt[8]; rd_t rd[8]; for (int i = 0; i < 8; i++) { rd[i] = (rd_t){ i, 0 }; pthread_create(&rt[i], NULL, reader, &rd[i]); }
    while (r_go < 8) usleep(1000);
    wr_t w[128]; int cpus[128]; pthread_t wt[128]; for (int i = 0; i < nw; i++) cpus[i] = 32 + 16 * (i % 6) + i / 6;
    if (nw && w_setup(w, nw, cpus, mode, target, rate)) return 1;
    pthread_barrier_init(&w_bar, NULL, (unsigned)nw + 1); for (int i = 0; i < nw; i++) pthread_create(&wt[i], NULL, w_thread, &w[i]);
    r_go = 100; if (nw) pthread_barrier_wait(&w_bar); sleep(3);                       /* everything running; settle 3 s */
    uint64_t r0 = 0, w0 = 0; for (int i = 0; i < 8; i++) r0 += rd[i].done; for (int i = 0; i < nw; i++) w0 += w[i].done;
    uint64_t t0 = w_now(); int cap = (int)(secs * 100) + 8, ns = 0; double *lat = malloc((size_t)cap * sizeof *lat);
    while ((w_now() - t0) / 1e9 < secs && ns < cap) { lat[ns++] = cxlp_probe_once(pr, 1000); usleep(10000); }
    double dt = (w_now() - t0) / 1e9; uint64_t r1 = 0, w1 = 0; for (int i = 0; i < 8; i++) r1 += rd[i].done; for (int i = 0; i < nw; i++) w1 += w[i].done;
    r_stop = 1; w_stop = 1; for (int i = 0; i < 8; i++) pthread_join(rt[i], NULL); for (int i = 0; i < nw; i++) pthread_join(wt[i], NULL);
    qsort(lat, (size_t)ns, sizeof *lat, cmpd);
    printf("RESULT victim=synth mode=%s target=%s asked_GiBs=%.0f writers=%d write_GiBs=%.2f victim_GiBs=%.2f probe_p50=%.1f probe_p90=%.1f n=%d\n", mode ? "copy" : "pure", target, atof(argv[1]), nw,
           (w1 - w0) / dt / 1073741824.0, (r1 - r0) / dt / 1073741824.0, lat[ns / 2], lat[ns * 9 / 10], ns);
    return 0;
}
