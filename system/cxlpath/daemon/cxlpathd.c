/* cxlpathd — the background process of cxlpath (one per node, no root).
 * It is never on the data path: it measures, decides and PUBLISHES in shared memory.
 *   tick  : 10 ms while writers are active, 200 ms when idle — one DRAM latency probe
 *   epoch : 5 ticks when active, 1 tick when idle — signals, controller, publish, log
 *   1 s   : crash cleanup, DRAM pool trim
 * usage: cxlpathd <store> [--cpu N] [--log FILE] [--bound 1.10] [--margin 1.05] [--guard 1.3] [--idle-ns N] [--no-pace] [--trim] [--no-calibrate] [--ccd-size 16] [--smt-offset 128]
 *                         [--shadow-cap-gib G] [--k-latency K]   (read path: DRAM copies allowed, default half the pool; k for serving-hit objects, default 1)
 */
#define _GNU_SOURCE
#include "../src/internal.h"
#include "cxlpath_daemon.h"
#include <pthread.h>
#include <sched.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static const char *opt(int argc, char **argv, const char *k, const char *dflt) { for (int i = 2; i + 1 < argc; i++) if (!strcmp(argv[i], k)) return argv[i + 1]; return dflt; }
static int flag(int argc, char **argv, const char *k) { for (int i = 2; i < argc; i++) if (!strcmp(argv[i], k)) return 1; return 0; }

static volatile sig_atomic_t quit;
static void on_sig(int s) { (void)s; quit = 1; }
static int cmp_double(const void *a, const void *b) { double x = *(const double *)a, y = *(const double *)b; return x < y ? -1 : x > y; }

/* ---- start-up calibration of the CXL write path: solo speed and aggregate capacity ---- */
typedef struct { void *dst[2]; const char *src; int rounds; uint64_t bytes, ns; pthread_barrier_t *bar; } cal_t;
static void *cal_thread(void *a) {
    cal_t *c = a; if (c->bar) pthread_barrier_wait(c->bar);
    uint64_t t0 = cxlp_now_ns();
    for (int r = 0; r < c->rounds; r++) for (int k = 0; k < 2; k++) { cxlp_copy_in(c->dst[k], c->src, CXLP_SEG_BYTES); c->bytes += CXLP_SEG_BYTES; }
    c->ns = cxlp_now_ns() - t0; return NULL;
}
static void calibrate(double *solo_bps, double *cap_bps) {
    *solo_bps = *cap_bps = 0;
    int dev = -1; for (int d = 0; d < cxlp_ndev(); d++) if (cxlp_dev_kind(d) == CXLP_DEV_CXL && cxlp_dev_free(d) >= 16) { dev = d; break; }
    if (dev < 0) return;
    uint32_t seg[8]; for (int i = 0; i < 8; i++) seg[i] = cxlp_seg_claim(dev, CXLP_SEG_OPEN);
    char *src = aligned_alloc(4096, CXLP_SEG_BYTES); memset(src, 0x5c, CXLP_SEG_BYTES);
    cal_t one = { { cxlp_seg_ptr(dev, seg[0]), cxlp_seg_ptr(dev, seg[1]) }, src, 6, 0, 0, NULL };
    cal_thread(&one); *solo_bps = one.bytes * 1e9 / one.ns;
    pthread_barrier_t bar; pthread_barrier_init(&bar, NULL, 4); pthread_t th[4]; cal_t c[4];
    for (int i = 0; i < 4; i++) { c[i] = (cal_t){ { cxlp_seg_ptr(dev, seg[2 * i]), cxlp_seg_ptr(dev, seg[2 * i + 1]) }, src, 6, 0, 0, &bar }; pthread_create(&th[i], NULL, cal_thread, &c[i]); }
    uint64_t tb = 0, tn = 0; for (int i = 0; i < 4; i++) { pthread_join(th[i], NULL); tb += c[i].bytes; if (c[i].ns > tn) tn = c[i].ns; }
    *cap_bps = tb * 1e9 / tn;
    for (int i = 0; i < 8; i++) cxlp_seg_release(dev, seg[i]);
    free(src);
}

/* ---- start-up calibration of the read path for a CPU consumer (Component C): seconds per byte to
 * stream-read from DRAM and from CXL, and to copy CXL -> DRAM. 4 segments each (128 MiB > L3). ---- */
static double stream_read(void *p[4]) { uint64_t t0 = cxlp_now_ns(), s = 0; for (int k = 0; k < 4; k++) { const uint64_t *q = p[k]; for (size_t i = 0; i < CXLP_SEG_BYTES / 8; i++) s += q[i]; } __asm__ volatile("" : : "r"(s)); return (cxlp_now_ns() - t0) / 1e9 / (4.0 * CXLP_SEG_BYTES); }
static int calibrate_read(double *t_dram, double *t_cxl, double *t_copy) {
    int cd = -1, dd = -1; for (int d = 0; d < cxlp_ndev(); d++) { if (cxlp_dev_free(d) < 8) continue; if (cxlp_dev_kind(d) == CXLP_DEV_CXL && cd < 0) cd = d; if (cxlp_dev_kind(d) == CXLP_DEV_DRAM && dd < 0) dd = d; }
    if (cd < 0 || dd < 0) return -1;
    uint32_t cs[4], ds[4]; void *cp[4], *dp[4];
    for (int k = 0; k < 4; k++) { cs[k] = cxlp_seg_claim(cd, CXLP_SEG_OPEN); ds[k] = cxlp_seg_claim(dd, CXLP_SEG_OPEN); cp[k] = cxlp_seg_ptr(cd, cs[k]); dp[k] = cxlp_seg_ptr(dd, ds[k]); }
    char *src = aligned_alloc(4096, CXLP_SEG_BYTES); for (size_t i = 0; i < CXLP_SEG_BYTES; i++) src[i] = (char)(i * 131);
    for (int k = 0; k < 4; k++) { cxlp_copy_in(cp[k], src, CXLP_SEG_BYTES); cxlp_copy_in(dp[k], src, CXLP_SEG_BYTES); }
    *t_dram = *t_cxl = *t_copy = 1e9;
    for (int r = 0; r < 3; r++) {
        double a = stream_read(dp), b = stream_read(cp); if (a < *t_dram) *t_dram = a; if (b < *t_cxl) *t_cxl = b;
        uint64_t t0 = cxlp_now_ns(); for (int k = 0; k < 4; k++) cxlp_copy_in(dp[k], cp[k], CXLP_SEG_BYTES); double c = (cxlp_now_ns() - t0) / 1e9 / (4.0 * CXLP_SEG_BYTES); if (c < *t_copy) *t_copy = c;
    }
    for (int k = 0; k < 4; k++) { cxlp_seg_release(cd, cs[k]); cxlp_seg_release(dd, ds[k]); }
    free(src); return 0;
}

/* ---- promoter thread (Component C): relocates hot extents to the DRAM pool, off the probe's CCD ---- */
/* ---- drain thread (Component D): CXL -> NVMe with O_DIRECT; one thread is enough, the NVMe on c28
 * sustains 0.9 GiB/s whatever the parallelism (measured with 1-16 writers) ---- */
static void *drainer(void *arg) { (void)arg; while (!quit) { if (cxlp_drain_step(1) <= 0) usleep(20000); } return NULL; }

static void *promoter(void *arg) { (void)arg; while (!quit) { cxlp_promote_pending((int)atomic_load(&POL->dram_ok)); usleep(50000); } return NULL; }

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "usage: cxlpathd <store> [--cpu N] [--log FILE] [--bound X] [--no-calibrate]\n"); return 2; }
    int cpu = atoi(opt(argc, argv, "--cpu", "16")), ccd = atoi(opt(argc, argv, "--ccd-size", "16")), smt = atoi(opt(argc, argv, "--smt-offset", "128"));
    double bound = atof(opt(argc, argv, "--bound", "1.10")), guard = atof(opt(argc, argv, "--guard", "1.3")), idle_loose = atof(opt(argc, argv, "--idle-bound", "1.5"));
    double margin = atof(opt(argc, argv, "--margin", "1.05")); int do_trim = flag(argc, argv, "--trim");   /* margin < bound; --trim gives free DRAM-pool pages back (they must then be re-faulted: off by default) */ const char *logp = opt(argc, argv, "--log", NULL);
    for (int i = 0; i < 100 && cxlp_attach(argv[1]) != 0; i++) usleep(100000);
    if (!cxlp_g.meta) { fprintf(stderr, "cxlpathd: store %s not found\n", argv[1]); return 1; }
    if (cxlp_policy_daemon_alive()) { fprintf(stderr, "cxlpathd: another daemon (pid %u) serves this store\n", atomic_load(&POL->daemon_pid)); return 1; }
    signal(SIGTERM, on_sig); signal(SIGINT, on_sig);
    FILE *lg = logp ? fopen(logp, "w") : NULL;
    if (lg) setvbuf(lg, NULL, _IOFBF, 8u << 20);           /* the loop must never wait for I/O: flush only when idle */

    /* everything except the probe stays off the probe's CCD */
    long ncpu = sysconf(_SC_NPROCESSORS_ONLN); int lo = cpu / ccd * ccd, hi = lo + ccd - 1;
    cpu_set_t rest; CPU_ZERO(&rest);
    for (int i = 0; i < ncpu; i++) { int core = i >= smt ? i - smt : i; if (core < lo || core > hi) CPU_SET(i, &rest); }
    sched_setaffinity(0, sizeof rest, &rest);
    double solo = 0, cap = 0, t_dram = 0, t_cxl = 0, t_copy = 0, w_press = atof(opt(argc, argv, "--w", "10")); int have_rd = 0;
    if (!flag(argc, argv, "--no-calibrate")) { calibrate(&solo, &cap); have_rd = calibrate_read(&t_dram, &t_cxl, &t_copy) == 0; }
    pthread_t prom, drn; pthread_create(&prom, NULL, promoter, NULL); pthread_create(&drn, NULL, drainer, NULL);         /* inherits the affinity: not on the probe's CCD */
    cpu_set_t pc; CPU_ZERO(&pc); CPU_SET(cpu, &pc); sched_setaffinity(0, sizeof pc, &pc);   /* main thread = probe thread */

    cxlp_probe_t *pr = cxlp_probe_create(256ul << 20);
    atomic_store(&POL->shadow_cap, (uint64_t)(atof(opt(argc, argv, "--shadow-cap-gib", "0")) * 1073741824.0)); atomic_store(&POL->k_read_latency, (uint32_t)atoi(opt(argc, argv, "--k-latency", "1")));
    cxlp_ctl_t ctl; cxlp_ctl_init(&ctl, bound, margin); cxlp_pace_t pace; cxlp_pace_init(&pace); int no_pace = flag(argc, argv, "--no-pace"); double pace_bps = 0; cxlp_ref_t ref_idle, ref_act; cxlp_ref_init(&ref_idle, 60000); cxlp_ref_init(&ref_act, 2000);
    atomic_store(&POL->bound_x1000, (uint32_t)(bound * 1000 + 0.5));
    double ring[5]; int nring = 0; double base = 0; double ring50[50] = { 0 }; int n50 = 0;   /* 500 ms mean for pacing: a read-saturated victim's own phases scatter single probes +-25% */
    for (int i = 0; i < 25; i++) { ring[i % 5] = cxlp_probe_once(pr, 1000); if (i % 5 == 4) { double m = 0; for (int k = 0; k < 5; k++) m += ring[k]; base = cxlp_ref_feed(&ref_idle, m / 5, cxlp_now_ns() / 1000000ull); } usleep(10000); }
    /* The headroom guard compares the reference in use with the UNLOADED level of this machine. That level
     * is calibrated here over 2 s (median of 200 probes; single idle probes scatter 100-160 ns on c28, and
     * the lowest windowed reference ever seen was too fragile: one low start-up window denied the loan to a
     * victim with plenty of headroom). A daemon started on an already loaded machine passes --idle-ns. */
    double idle_ns = atof(opt(argc, argv, "--idle-ns", "0"));
    if (idle_ns <= 0) { double v[200]; for (int i = 0; i < 200; i++) { v[i] = cxlp_probe_once(pr, 1000); usleep(10000); } qsort(v, 200, sizeof *v, cmp_double); idle_ns = v[100]; }
    nring = 5;
    if (lg) { fprintf(lg, "# cxlpathd store=%s probe_cpu=%d bound=%.3f margin=%.3f guard=%.2f idle_ns=%.1f pacing=%s solo_GiBs=%.2f cap_GiBs=%.2f base_ns=%.1f t0_mono_ns=%llu\n", argv[1], cpu, bound, margin, guard, idle_ns, no_pace ? "off" : "on", solo / 1073741824.0, cap / 1073741824.0, base, (unsigned long long)cxlp_now_ns());
              if (have_rd) fprintf(lg, "# read path, CPU consumer: DRAM %.2f GiB/s, CXL %.2f GiB/s (%.2fx), copy CXL->DRAM %.2f GiB/s -> k = %u when DRAM is calm\n", 1 / t_dram / 1073741824.0, 1 / t_cxl / 1073741824.0, t_cxl / t_dram, 1 / t_copy / 1073741824.0, cxlp_k_compute(t_copy, t_cxl, t_dram, w_press, 0));
              fprintf(lg, "t_ms,probe_ns,mean5_ns,ref_in_use_ns,spill16,staged16,cxl_full,gpu_full,active,cxl_GiBs,dram_GiBs,per_writer_GiBs,conc,halved,ref_idle_ns,ref_active_ns,pace_GiBs,shadow_MiB,promoted,shadow_drops\n"); fflush(lg); }

    atomic_store(&POL->daemon_pid, (uint32_t)getpid());
    uint64_t t_start = cxlp_now_ns(), next = t_start, last_sec = 0, last_epoch_ns = t_start, last_act_ns = 0;
    uint64_t pb[CXLP_MAX_DEVS], pn[CXLP_MAX_DEVS], ps[CXLP_NSTREAM], s_last[CXLP_NSTREAM] = { 0 };
    for (int d = 0; d < CXLP_MAX_DEVS; d++) { pb[d] = atomic_load(&POL->led[d].bytes); pn[d] = atomic_load(&POL->led[d].ns); }
    for (int s = 0; s < CXLP_NSTREAM; s++) ps[s] = atomic_load(&POL->sled[s].bytes);
    uint64_t p_seq = atomic_load(&POL->reserve_seq), pgd_b = atomic_load(&POL->gpu_direct.bytes), pgd_n = atomic_load(&POL->gpu_direct.ns);
    uint64_t pgs_b = atomic_load(&POL->gpu_staged.bytes), prev_cb = 0; uint32_t prev_mask = 0; int tick = 0, halved_in_epoch = 0, gpu_full = 0, cxl_full = 0;

    while (!quit) {
        uint64_t now = cxlp_now_ns();
        double p = cxlp_probe_once(pr, 1000); ring[nring++ % 5] = p; ring50[n50++ % 50] = p;
        double mean5 = 0; for (int k = 0; k < 5; k++) mean5 += ring[k]; mean5 /= 5;
        double mean50 = 0; { int m = n50 < 50 ? n50 : 50; for (int k = 0; k < m; k++) mean50 += ring50[k]; mean50 /= m; }
        int forced = atomic_load(&POL->force_spill16);

        /* which streams moved bytes in the last 200 ms */
        uint32_t mask = 0;
        for (int s = 0; s < CXLP_NSTREAM; s++) {
            uint64_t b = atomic_load(&POL->sled[s].bytes);
            if (b != ps[s]) { ps[s] = b; s_last[s] = now; }
            if (s_last[s] && now - s_last[s] < 200000000ull) mask |= 1u << s;
        }
        uint64_t seq = atomic_load(&POL->reserve_seq);
        if (seq != p_seq || mask) last_act_ns = now;
        p_seq = seq;
        int active = last_act_ns && now - last_act_ns < 200000000ull;

        /* per-stream memory: leaving streams remember, the first stream of a burst restores */
        for (int s = 0; s < CXLP_NSTREAM; s++) if ((prev_mask & (1u << s)) && !(mask & (1u << s))) cxlp_ctl_stream_idle(&ctl, s);
        /* reference in use: writers active -> the active reference (0 = not known yet), else idle */
        double ref_a = cxlp_ref_value(&ref_act, 5);
        base = mask ? ref_a : ref_idle.last;
        int room = base > 0 && base <= guard * idle_ns;             /* headroom guard: DRAM already loaded beyond guard x unloaded -> no loan */
        /* A burst may start from its remembered ratio unless DRAM is under OBVIOUS pressure right now.
         * Idle readings are too noisy for the 10% bound (100-160 ns on an idle c28), so the idle state
         * uses a loose factor; the burst itself re-checks against the active reference within 20-50 ms. */
        if (mask && !prev_mask) cxlp_ctl_burst_start(&ctl, mask, mean5 / idle_loose * ctl.margin, ref_idle.last <= guard * idle_ns ? ref_idle.last : 0);
        prev_mask = mask;

        /* fast decrease, every probe; skipped while the active reference is being learned */
        int halved = (mask && ref_a == 0) ? 0 : cxlp_ctl_probe_b(&ctl, p, room ? base : 0, mask ? bound : idle_loose);
        if (halved) { halved_in_epoch = 1; if (lg) { fprintf(lg, "#HALVE,%.1f,%.1f,%u,%u\n", (now - t_start) / 1e6, p, ctl.cpu, ctl.gpu); } }
        tick++;
        int epoch = !active || tick % 5 == 0;
        if (epoch) {
            double dt = (now - last_epoch_ns) / 1e9; if (dt <= 0) dt = 1e-3;
            last_epoch_ns = now;
            uint64_t cb = 0, cn = 0, db = 0;
            for (uint32_t d = 0; d < cxlp_g.meta->ndev; d++) {
                uint64_t bb = atomic_load(&POL->led[d].bytes), nn = atomic_load(&POL->led[d].ns);
                if (cxlp_g.meta->dev[d].kind == CXLP_DEV_CXL) { cb += bb - pb[d]; cn += nn - pn[d]; } else db += bb - pb[d];
                pb[d] = bb; pn[d] = nn;
            }
            uint64_t gsb = atomic_load(&POL->gpu_staged.bytes);
            if (!mask && !active) cxlp_ref_feed(&ref_idle, mean5, now / 1000000ull);
            else if (mask && cb > 0 && db == 0 && gsb == pgs_b) cxlp_ref_feed(&ref_act, mean5, now / 1000000ull);   /* writers moved CXL bytes THIS epoch, none of ours in DRAM (the 200 ms tail of a burst polluted it with idle values and caused halvings at the next burst) */
            pgs_b = gsb;
            double agg = cb / dt, per_writer = cn ? cb * 1e9 / (double)cn : 0, conc = cn / 1e9 / dt;
            /* CXL write direction, seen through our own ledger and the capacity calibrated at start-up:
             *   full  (+1): we push >= 90% of the capacity  -> more writers would only queue, spill may grow
             *   slack (-1): we push <  70%                  -> spill shrinks: DRAM is only for the excess
             * A per-writer-speed rule was tried first and over-spilled (live B4: it kept raising spill to
             * 11/16 for a 60 GiB/s demand because concurrent writers always look slow individually). Not
             * covered: another tenant writing to the same cards outside cxlpath (would need a CXL write probe). */
            /* The tail of a burst (an epoch only partly covered by the stream) must not count as slack:
             * slack needs bytes in this epoch AND in the previous one (the first smoke test of periodic
             * 8 GiB bursts lost its whole ramp to tail-off decrements and restarted every burst from 0). */
            cxl_full = cap > 0 ? (agg >= 0.9 * cap ? 1 : ((agg < 0.7 * cap && cb > 0 && prev_cb > 0) ? -1 : 0)) : 0;
            prev_cb = cb;
            /* GPU sources: the direct path is "full" when it delivers < 80% of what the GPU link can
             * push; sticky, because with everything staged there is no direct sample to look at. */
            uint64_t gb = atomic_load(&POL->gpu_direct.bytes), gn = atomic_load(&POL->gpu_direct.ns), link = atomic_load(&POL->gpu_link_bps);
            if (gn != pgd_n && link) gpu_full = (gb - pgd_b) * 1e9 / (double)(gn - pgd_n) < 0.8 * (double)link;
            pgd_b = gb; pgd_n = gn;
            if (mask) cxlp_ctl_epoch(&ctl, cxl_full, gpu_full, mean5, room ? base : 0);   /* slow increase */
            /* last resort: nothing lent and the stream's total effect (source reads included) still over the bound
             * relative to the level WITHOUT any writer -> pace the producer */
            pace_bps = (mask && !no_pace) ? cxlp_pace_epoch(&pace, ctl.cpu > 0 || ctl.gpu > 0, mean50, ref_idle.last, bound, margin, agg, cap) : (no_pace ? 0 : (pace.on ? pace.bps : 0));
            atomic_store(&POL->cxl_full, (uint32_t)(cxl_full > 0)); atomic_store(&POL->gpu_full, (uint32_t)gpu_full);
            atomic_store(&POL->probe_x10, (uint32_t)(mean5 * 10)); atomic_store(&POL->base_x10, (uint32_t)(base * 10));
            /* Component C: promotion thresholds. Pressure makes the copy dearer: k grows with the probe. */
            double pressure = base > 0 ? mean5 / base - 1.0 : 0;
            if (have_rd) atomic_store(&POL->k_read[CXLP_CONSUMER_CPU], cxlp_k_compute(t_copy, t_cxl, t_dram, w_press, pressure));
            uint64_t grc = atomic_load(&POL->gpu_rd_cxl_bps), grd = atomic_load(&POL->gpu_rd_dram_bps);
            if (grc && grd) atomic_store(&POL->k_read[CXLP_CONSUMER_GPU], cxlp_k_compute(have_rd ? t_copy : 1.0 / (double)grd, 1.0 / (double)grc, 1.0 / (double)grd, w_press, pressure));
            atomic_fetch_add(&POL->epoch, 1);
            /* the loan must never be blocked by promoted copies: when the DRAM pool runs low, drop the least recently hit shadows */
            { uint32_t pf = 0, pt = 0; for (int d = 0; d < cxlp_ndev(); d++) if (cxlp_dev_kind(d) == CXLP_DEV_DRAM) { pf += cxlp_dev_free(d); pt += cxlp_dev_nseg(d); }
              if (pt && pf * 8 < pt && atomic_load(&POL->shadow_bytes)) cxlp_shadow_trim(atomic_load(&POL->shadow_bytes) / 2); }
            if (lg) { fprintf(lg, "%.1f,%.1f,%.1f,%.1f,%u,%u,%d,%d,%d,%.2f,%.2f,%.2f,%.2f,%d,%.1f,%.1f,%.2f,%.1f,%llu,%llu\n", (now - t_start) / 1e6, p, mean5, base,
                        forced >= 0 ? (uint32_t)forced : ctl.cpu, ctl.gpu, cxl_full, gpu_full, active, agg / 1073741824.0, db / dt / 1073741824.0, per_writer / 1073741824.0, conc, halved_in_epoch, ref_idle.last, ref_a, pace_bps / 1073741824.0,
                        atomic_load(&POL->shadow_bytes) / 1048576.0, (unsigned long long)atomic_load(&POL->promoted_extents), (unsigned long long)atomic_load(&POL->shadow_drops)); if (!active) fflush(lg); }
            halved_in_epoch = 0;
        }
        if (epoch || halved)                                  /* publish: active streams get the live value, idle ones their memory */
            for (int s = 0; s < CXLP_NSTREAM; s++) {
                int on = (mask >> s) & 1;
                atomic_store(&POL->spill16[s], forced >= 0 ? (uint32_t)forced : (on ? ctl.cpu : ctl.mem_cpu[s]));
                atomic_store(&POL->staged16[s], on ? ctl.gpu : ctl.mem_gpu[s]);
                double r = on ? pace_bps : pace.mem[s];
                atomic_store(&POL->pace_bps[s], (uint64_t)r);
                if (r > 0 && !atomic_load(&POL->pace_on[s])) atomic_store(&POL->pace_tokens[s], (int64_t)(r * 0.05));
                atomic_store(&POL->pace_on[s], r > 0);
            }
        /* token refill every tick (10 ms active / 200 ms idle), capped at 100 ms worth so a pause cannot bank a burst */
        for (int s = 0; s < CXLP_NSTREAM; s++) if (atomic_load(&POL->pace_on[s])) {
            double r = (double)atomic_load(&POL->pace_bps[s]); int64_t add = (int64_t)(r * (active ? 0.010 : 0.200)), capt = (int64_t)(r * 0.100);
            int64_t t = atomic_load(&POL->pace_tokens[s]), nt = t + add; if (nt > capt) nt = capt;
            atomic_compare_exchange_strong(&POL->pace_tokens[s], &t, nt);
        }
        atomic_store(&POL->dram_ok, room && p <= bound * base && mean5 <= bound * base);
        atomic_store(&POL->heartbeat_ns, now);
        if (now / 1000000000ull != last_sec) { last_sec = now / 1000000000ull; cxlp_cleanup_dead(); if (!active && do_trim) cxlp_dram_trim(); }

        next += active ? 10000000ull : 200000000ull;
        uint64_t n2 = cxlp_now_ns(); if (next < n2) next = n2;
        /* an idle sleep ends early when writers show up: look at the activity counter every 10 ms */
        while (!quit) {
            uint64_t t = cxlp_now_ns(); if (t >= next) break;
            uint64_t left = next - t; struct timespec ts = { 0, (long)(left < 10000000ull ? left : 10000000ull) }; nanosleep(&ts, NULL);
            if (!active && atomic_load(&POL->reserve_seq) != p_seq) break;
        }
        if (!active && atomic_load(&POL->reserve_seq) != p_seq) next = cxlp_now_ns();
    }
    atomic_store(&POL->daemon_pid, 0);
    pthread_join(prom, NULL); pthread_join(drn, NULL);
    if (lg) fclose(lg);
    cxlp_probe_destroy(pr); cxlp_close();
    return 0;
}
