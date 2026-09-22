/* dram_writer — the write stream beside a REAL application (separate process).
 * usage: dram_writer <rate GiB/s (0 = unlimited)> <pure|copy> <dram|/dev/daxX.Y> <threads> <first_cpu>
 * Prints "START <mono ns>" when the stream begins; on SIGTERM prints "END <mono ns> write_GiBs=<achieved>". */
#include "writer.h"
#include <signal.h>
static void on_term(int s) { (void)s; w_stop = 1; }
int main(int argc, char **argv) {
    if (argc < 6) { fprintf(stderr, "usage\n"); return 2; }
    double rate = atof(argv[1]); int mode = !strcmp(argv[2], "copy"), n = atoi(argv[4]), c0 = atoi(argv[5]);
    wr_t w[128]; int cpus[128]; pthread_t t[128]; for (int i = 0; i < n; i++) cpus[i] = c0 + i;
    signal(SIGTERM, on_term); signal(SIGINT, on_term);
    if (w_setup(w, n, cpus, mode, argv[3], rate)) return 1;
    pthread_barrier_init(&w_bar, NULL, (unsigned)n + 1); for (int i = 0; i < n; i++) pthread_create(&t[i], NULL, w_thread, &w[i]);
    pthread_barrier_wait(&w_bar); uint64_t t0 = w_now(); printf("START %llu\n", (unsigned long long)t0); fflush(stdout);
    while (!w_stop) usleep(20000);
    uint64_t t1 = w_now(), b = 0; for (int i = 0; i < n; i++) { pthread_join(t[i], NULL); b += w[i].done; }
    printf("END %llu write_GiBs=%.2f\n", (unsigned long long)t1, b / ((t1 - t0) / 1e9) / 1073741824.0); return 0;
}
