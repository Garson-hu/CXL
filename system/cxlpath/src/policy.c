/* Component B, library side (B1): read the published policy, feed the ledger, sleep when full.
 * Nothing here talks to the background process: it only reads and writes shared memory. The
 * single syscall is the futex a BLOCKED reserve() sleeps on (and the matching wake). */
#define _GNU_SOURCE
#include "internal.h"
#include <limits.h>
#include <unistd.h>
#include <linux/futex.h>
#include <sys/syscall.h>
#include <time.h>

int cxlp_policy_daemon_alive(void) {
    if (atomic_load(&POL->daemon_pid) == 0) return 0;
    return cxlp_now_ns() - atomic_load(&POL->heartbeat_ns) < 2000000000ull;
}

static int best_dev(cxlp_devkind_t kind) {
    int best = -1; uint32_t bf = 0;
    for (uint32_t d = 0; d < cxlp_g.meta->ndev; d++) {
        if (cxlp_g.meta->dev[d].kind != (uint32_t)kind) continue;
        uint32_t f = atomic_load(&cxlp_g.meta->dev[d].nfree);
        if (f > bf) { bf = f; best = (int)d; }
    }
    return best;
}

/* 4-bit bit reversal spreads "n of every 16" evenly: n = 8 alternates, n = 4 is every 4th. */
static uint32_t br4(uint32_t k) { k &= 15; return ((k & 1) << 3) | ((k & 2) << 1) | ((k & 4) >> 1) | ((k & 8) >> 3); }

/* Device for this thread's NEXT segment. nclaim is the thread's running count of new segments. */
int cxlp_policy_pick(uint32_t stream, uint32_t nclaim) {
    int alive = cxlp_policy_daemon_alive();
    uint32_t spill = alive ? atomic_load(&POL->spill16[stream % CXLP_NSTREAM]) : 0;
    int want_dram = br4(nclaim) < spill;
    int dev = best_dev(want_dram ? CXLP_DEV_DRAM : CXLP_DEV_CXL);
    if (dev >= 0) return dev;
    if (want_dram) return best_dev(CXLP_DEV_CXL);           /* DRAM pool exhausted: CXL is always allowed */
    /* CXL has no free segment: DRAM only if the probe says DRAM readers are within the bound */
    if (!alive || atomic_load(&POL->dram_ok)) return best_dev(CXLP_DEV_DRAM);
    return -1;
}

void cxlp_policy_wake(void) {
    atomic_fetch_add(&POL->free_event, 1);
    if (atomic_load(&POL->waiters)) syscall(SYS_futex, &POL->free_event, FUTEX_WAKE, INT_MAX, NULL, NULL, 0);
}

int cxlp_policy_wait_free(uint32_t seen_event, int ms) {
    struct timespec ts = { ms / 1000, (long)(ms % 1000) * 1000000L };
    atomic_fetch_add(&POL->waiters, 1);
    long r = syscall(SYS_futex, &POL->free_event, FUTEX_WAIT, seen_event, &ts, NULL, 0);
    atomic_fetch_sub(&POL->waiters, 1);
    return (int)r;
}

/* Last resort: a paced stream takes `len` bytes from its token bucket before it may reserve. Waiting
 * here is the only place a paced writer slows down; unpaced streams never touch this. */
void cxlp_policy_pace_wait(uint32_t stream, uint64_t len) {
    uint32_t s = stream % CXLP_NSTREAM; int waited = 0;
    while (atomic_load(&POL->pace_on[s]) && cxlp_policy_daemon_alive()) {
        int64_t t = atomic_load(&POL->pace_tokens[s]);
        if (t >= (int64_t)len && atomic_compare_exchange_weak(&POL->pace_tokens[s], &t, t - (int64_t)len)) break;
        if (t >= (int64_t)len) continue;
        if (!waited) { waited = 1; atomic_fetch_add(&POL->paced_waits, 1); }
        struct timespec ts = { 0, 200000 }; nanosleep(&ts, NULL);
    }
}

void cxlp_account(int dev, uint32_t stream, uint64_t bytes, uint64_t ns) {
    atomic_fetch_add(&POL->led[dev].bytes, bytes);
    atomic_fetch_add(&POL->led[dev].ns, ns);
    atomic_fetch_add(&POL->sled[stream % CXLP_NSTREAM].bytes, bytes);
}

void cxlp_copy_to(const cxlp_res_t *r, size_t off, const void *src, size_t n) {
    uint64_t t0 = cxlp_now_ns();
    cxlp_copy_in((char *)r->ptr + off, src, n);
    cxlp_account(r->dev, r->stream, n, cxlp_now_ns() - t0);
}

void cxlp_policy_view(uint32_t stream, cxlp_policy_view_t *o) {
    o->daemon_alive = cxlp_policy_daemon_alive();
    o->spill16 = atomic_load(&POL->spill16[stream % CXLP_NSTREAM]);
    o->staged16 = atomic_load(&POL->staged16[stream % CXLP_NSTREAM]);
    o->dram_ok = atomic_load(&POL->dram_ok); o->cxl_full = atomic_load(&POL->cxl_full); o->gpu_full = atomic_load(&POL->gpu_full);
    o->probe_ns = atomic_load(&POL->probe_x10) / 10.0; o->base_ns = atomic_load(&POL->base_x10) / 10.0;
    o->bound = atomic_load(&POL->bound_x1000) / 1000.0; o->epoch = atomic_load(&POL->epoch);
    o->pace_on = atomic_load(&POL->pace_on[stream % CXLP_NSTREAM]); o->pace_GiBs = atomic_load(&POL->pace_bps[stream % CXLP_NSTREAM]) / 1073741824.0;
    for (int d = 0; d < CXLP_MAX_DEVS; d++) o->dev_bytes[d] = atomic_load(&POL->led[d].bytes);
}

void cxlp_policy_force(int spill16) { atomic_store(&POL->force_spill16, spill16); }
