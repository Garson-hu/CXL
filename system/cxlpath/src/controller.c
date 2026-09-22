/* Component B: slow-increase / fast-decrease controller, idle baseline, DRAM pool trim (B2-B4). */
#define _GNU_SOURCE
#include "internal.h"
#include "cxlpath_daemon.h"
#include <fcntl.h>
#include <stdlib.h>
#include <string.h>

void cxlp_ctl_init(cxlp_ctl_t *c, double bound, double margin) { memset(c, 0, sizeof *c); c->bound = bound; c->margin = margin; }

int cxlp_ctl_probe(cxlp_ctl_t *c, double probe_ns, double base_ns) { return cxlp_ctl_probe_b(c, probe_ns, base_ns, c->bound); }

int cxlp_ctl_probe_b(cxlp_ctl_t *c, double probe_ns, double base_ns, double bound) {
    if (base_ns <= 0 || probe_ns > bound * base_ns) c->over++; else c->over = 0;
    if (c->over < 2) return 0;
    c->over = 0;
    /* halve whoever caused the pressure: our spill, or somebody else's writes */
    c->cpu /= 2; c->gpu /= 2;
    for (int s = 0; s < CXLP_NSTREAM; s++) { c->mem_cpu[s] /= 2; c->mem_gpu[s] /= 2; }
    c->n_halve++;
    return 1;
}

void cxlp_ctl_epoch(cxlp_ctl_t *c, int cpu_full, int gpu_full, double mean5_ns, double base_ns) {
    if (cpu_full >= 0) c->last_loaded_cpu = c->cpu;           /* a periodic writer resumes from the ratio it ran with while loading CXL, not from its tail-off */
    if (cpu_full < 0 && c->cpu > 0) c->cpu--;                 /* CXL has slack again: hand DRAM back, whatever the probe says */
    if (base_ns <= 0 || mean5_ns > c->margin * base_ns) return;   /* DRAM not clearly calm, or no headroom: hold */
    if (cpu_full > 0 && c->cpu < 16) { c->cpu++; c->n_up++; }
    if (gpu_full && c->gpu < 16) { c->gpu++; c->n_up++; }
}

void cxlp_ctl_stream_idle(cxlp_ctl_t *c, int s) { c->mem_cpu[s] = c->last_loaded_cpu > c->cpu ? c->last_loaded_cpu : c->cpu; c->mem_gpu[s] = c->gpu; }

void cxlp_ctl_burst_start(cxlp_ctl_t *c, uint32_t mask, double mean5_ns, double base_ns) {
    uint32_t cpu = 0, gpu = 0;
    for (int s = 0; s < CXLP_NSTREAM; s++) if (mask & (1u << s)) { if (c->mem_cpu[s] > cpu) cpu = c->mem_cpu[s]; if (c->mem_gpu[s] > gpu) gpu = c->mem_gpu[s]; }
    if (base_ns <= 0 || mean5_ns > c->margin * base_ns) cpu = gpu = 0;   /* never start a burst by spilling into a busy DRAM */
    c->cpu = cpu; c->gpu = gpu;
}

void cxlp_pace_init(cxlp_pace_t *p) { memset(p, 0, sizeof *p); }
double cxlp_pace_epoch(cxlp_pace_t *p, int lending, double mean5, double idle_ref, double bound, double margin, double achieved, double cap) {
    if (lending || idle_ref <= 0 || cap <= 0) { p->over_epochs = 0; return p->on ? p->bps : 0; }   /* the loan is taken back first; pacing keeps its rate meanwhile */
    int over = mean5 > bound * idle_ref, calm = mean5 <= margin * idle_ref;
    p->over_epochs = over ? p->over_epochs + 1 : 0;
    if (!p->on) { if (p->over_epochs >= 2) { p->on = 1; p->bps = 0.75 * (achieved > 0 ? achieved : cap); p->over_epochs = 0; } return p->on ? p->bps : 0; }
    if (over) { if (p->over_epochs >= 2) { p->bps *= 0.75; p->over_epochs = 0; } }
    else if (calm) { p->bps += cap / 16; if (p->bps >= cap) { p->on = 0; p->bps = 0; } }
    if (p->on && p->bps < cap / 32) p->bps = cap / 32;                       /* never below 1/32 of the capacity: a paced writer still makes progress */
    return p->on ? p->bps : 0;
}
void cxlp_pace_stream_idle(cxlp_pace_t *p, int s) { p->mem[s] = p->on ? p->bps : 0; }
void cxlp_pace_burst_start(cxlp_pace_t *p, uint32_t mask) {
    double m = 0; int any = 0;
    for (int s = 0; s < CXLP_NSTREAM; s++) if (mask & (1u << s)) { if (p->mem[s] > 0 && (!any || p->mem[s] < m)) m = p->mem[s]; if (p->mem[s] > 0) any = 1; }
    if (any) { p->on = 1; p->bps = m; } else { p->on = 0; p->bps = 0; }
    p->over_epochs = 0;
}

void cxlp_ref_init(cxlp_ref_t *r, uint64_t window_ms) { memset(r, 0, sizeof *r); r->window_ms = window_ms; }
static int cmp_d(const void *a, const void *b) { double x = *(const double *)a, y = *(const double *)b; return x < y ? -1 : x > y; }
double cxlp_ref_feed(cxlp_ref_t *r, double mean, uint64_t now_ms) {
    r->v[r->head] = mean; r->t_ms[r->head] = now_ms; r->head = (r->head + 1) % CXLP_REF_N; if (r->n < CXLP_REF_N) r->n++;
    r->nsamples++;
    double tmp[CXLP_REF_N]; int k = 0;
    for (int i = 0; i < r->n; i++) if (now_ms - r->t_ms[i] < r->window_ms) tmp[k++] = r->v[i];
    if (k) { qsort(tmp, (size_t)k, sizeof *tmp, cmp_d); r->last = tmp[k / 2]; if (r->low == 0 || r->last < r->low) r->low = r->last; }
    return r->last;
}

int cxlp_dram_trim(void) {
    int n = 0; cxlp_meta_t *m = cxlp_g.meta;
    for (uint32_t d = 0; d < m->ndev; d++) {
        if (m->dev[d].kind != CXLP_DEV_DRAM) continue;
        for (uint32_t s = 0; s < m->dev[d].nseg; s++) {
            cxlp_seg_t *sg = cxlp_g.seg + m->dev[d].first + s;
            uint32_t cur = atomic_load(&sg->st);
            if (ST_STATE(cur) != CXLP_SEG_FREE || !atomic_load(&sg->touched)) continue;
            /* take it out of circulation while the hole is punched, then put it back */
            if (!atomic_compare_exchange_strong(&sg->st, &cur, ST_MAKE(ST_GEN(cur), CXLP_SEG_FREEING))) continue;
            fallocate(cxlp_g.fd[d], FALLOC_FL_PUNCH_HOLE | FALLOC_FL_KEEP_SIZE, (off_t)(m->dev[d].offset + (uint64_t)s * CXLP_SEG_BYTES), (off_t)CXLP_SEG_BYTES);
            atomic_store(&sg->touched, 0);
            atomic_store(&sg->st, ST_MAKE(ST_GEN(cur), CXLP_SEG_FREE));
            n++;
        }
    }
    return n;
}
