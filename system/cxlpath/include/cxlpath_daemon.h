/* Pieces of Component B that the background process and the tests share. Not a client API. */
#ifndef CXLPATH_DAEMON_H
#define CXLPATH_DAEMON_H
#include "cxlpath.h"

/* --- DRAM latency probe (signal 3). Calibrated in check V5: 138 ns idle on c28, 1.18x at a 13%
 * reader slowdown, 6.5x when DRAM writes saturate. One probe = `loads` dependent random loads
 * over a region larger than the cache; ~0.14 ms for 1000 loads. */
typedef struct cxlp_probe cxlp_probe_t;
cxlp_probe_t *cxlp_probe_create(size_t region_bytes);
double        cxlp_probe_once(cxlp_probe_t *p, int loads);     /* ns per load */
void          cxlp_probe_destroy(cxlp_probe_t *p);

/* --- Controller: slow increase, fast decrease (DESIGN 10.4). Pure functions of their inputs so
 * they can be tested with injected signals. Two values 0..16: `cpu` = share of new segments that
 * go to DRAM, `gpu` = share of GPU chunks that take the staged path. */
typedef struct {
    uint32_t cpu, gpu;
    uint32_t mem_cpu[CXLP_NSTREAM], mem_gpu[CXLP_NSTREAM];   /* per-stream memory */
    int      over;               /* consecutive probes above the bound */
    double   bound, margin;      /* 1.10, 1.05 */
    uint64_t n_up, n_halve;
} cxlp_ctl_t;
void cxlp_ctl_init(cxlp_ctl_t *c, double bound, double margin);
/* every probe: two consecutive probes above bound x base halve everything. Returns 1 if it did.
 * base_ns <= 0 means "no headroom": every probe counts as over the bound. */
int  cxlp_ctl_probe(cxlp_ctl_t *c, double probe_ns, double base_ns);
int  cxlp_ctl_probe_b(cxlp_ctl_t *c, double probe_ns, double base_ns, double bound);   /* explicit bound (idle state uses a loose one) */
/* every epoch while writers are active: +1/16 when the path is full and DRAM is calm;
 * -1/16 when the CXL path has clear slack (cpu_path_full < 0): DRAM is only for the excess. */
void cxlp_ctl_epoch(cxlp_ctl_t *c, int cpu_path_full, int gpu_path_full, double mean5_ns, double base_ns);
/* a stream went idle: remember the ratio its burst ended with */
void cxlp_ctl_stream_idle(cxlp_ctl_t *c, int stream);
/* writers resumed after an idle period: start from what the resuming streams remember,
 * unless DRAM is not calm right now */
void cxlp_ctl_burst_start(cxlp_ctl_t *c, uint32_t active_mask, double mean5_ns, double base_ns);

/* --- Reference level of the probe: "what the probe reads when cxlpath writes nothing to DRAM".
 * The bound is relative to it (DRAM readers slow down by no more than X because of OUR writes).
 * Two trackers, because the writers' own activity moves the level even with zero spill (live
 * test B4: four writers reading their source data from DRAM at 50 GiB/s lift the probe ~20%):
 *   idle reference   : epochs of the last 60 s without any writer activity
 *   active reference : epochs of the last 2 s with writer activity but NO DRAM bytes from us;
 *                      frozen while we spill (so our spill cannot ratchet it up), known only
 *                      after 5 such epochs (a first burst spends ~250 ms on CXL only).
 * The reference is the MEDIAN of those epoch means, not the minimum: on c28 an idle machine
 * reads 100-160 ns from one probe to the next (memory and cores drop into power-saving states),
 * and a minimum sits 15-25% below the typical value, which made every normal reading look like
 * pressure (first live run of B4). `low` is the lowest reference ever produced; the headroom
 * guard compares against it: a reference above guard x low means DRAM is near its write cliff
 * (check V5: 2.1x at 73% load) and nothing may spill at all. */
#define CXLP_REF_N 512
typedef struct { double v[CXLP_REF_N]; uint64_t t_ms[CXLP_REF_N]; int head, n; uint64_t window_ms, nsamples; double last, low; } cxlp_ref_t;
void   cxlp_ref_init(cxlp_ref_t *r, uint64_t window_ms);
double cxlp_ref_feed(cxlp_ref_t *r, double epoch_mean_ns, uint64_t now_ms);      /* returns the reference */
static inline double cxlp_ref_value(const cxlp_ref_t *r, uint64_t min_samples) { return r->nsamples >= min_samples ? r->last : 0; }

/* DRAM pool hygiene: give the pages of FREE DRAM segments back to the system. */
int cxlp_dram_trim(void);
#endif
