/* kvemu2 — ONLINE trace-driven HOST MEMORY TRAFFIC EMULATION of a two-tier (DRAM + CXL) KV cache, for the
 * capacity-matched comparison of 2026-10-11 (experiment 2b). Not a model of multi-GPU serving: stores are
 * non-temporal writes from a cache-resident source (a GPU's DMA writes do not read host DRAM), loads are streaming
 * reads; the CPU workers sit on CCDs 6-7 and their links cap the DRAM tier's peaks near 150 GB/s.
 *
 * Differences from kvemu: lookups happen when the request arrives, so a block is a hit only if its store has
 * COMPLETED by then; a block whose store is announced (computed, waiting to be written) or running counts as a
 * pending miss (recomputed, not stored again — LMCache refuses a second writer). The slot and its tier are chosen when
 * the store STARTS, as LMCache allocates at offload time and the cxlpath writer reserves at copy time — so a DRAM loan
 * granted during a burst applies to the bytes written from then on. Evictions never touch a block being written/read. Two regions: DRAM (anonymous memory, huge pages) and CXL (/dev/dax0.0 from 0).
 *
 * Policies (where a NEW block goes, and what is evicted for it):
 *   dram        all slots in DRAM (cxl_GiB ignored)                    cxl         all slots in CXL (dram_GiB ignored)
 *   lmcache     LMCache 0.5.5 hybrid L1: new blocks into a free DRAM slot, else a free CXL slot; one global LRU,
 *               eviction when occupancy exceeds <watermark> x total (LMCache default 0.8) down to the watermark
 *   split       a fixed share = DRAM's share of the slots goes to DRAM (by block hash); eviction within that tier
 *   cxlfirst    every new block to CXL; eviction within CXL (DRAM stays empty: the per-tier capacity loss)
 *   borrowtier  CXL unless the running cxlpathd lends DRAM (n of 16 new blocks, as cxlp_policy_pick); per-tier LRU
 *   borrowglob  same placement; eviction takes the GLOBAL least-recently-used block until the target tier has room
 *   borrowmig   borrowtier + MIGRATION (2026-10-12): a block read from CXL is MOVED to DRAM (copy, then its CXL slot is
 *               freed) while the daemon reports DRAM calm (dram_ok), at most 8 moves in flight; the DRAM victim is dropped.
 *   budget      BUDGET-GATED ADMISSION (2026-10-12): a new block goes to DRAM when a token bucket refilled at B GB/s holds a
 *               whole block (depth = one block: unused budget is lost, DRAM writes stay smooth), else to CXL; per-tier LRU.
 *               B = $KV2_BUDGET_GBPS, or re-read every 10 ms from the file $KV2_BUDGET_FILE (text, GB/s; an oracle signal).
 * Options by environment (2026-10-12; unset = the behaviour of experiment 2b):
 *   KV2_SPLIT_SHARE=f  split sends the share f of the blocks (by hash) to DRAM, whatever DRAM's share of the capacity
 *   KV2_WARM=common    every tiered policy is warmed with the same placement (split by capacity share: both tiers full,
 *                      same blocks), so all policies start from the same state (budget always warms this way)
 * The borrow policies attach to a cxlpath store (<store>), read the loan share the daemon publishes and report every
 * copy to the daemon's ledger (cxlp_account), so the existing controller decides exactly as for a checkpoint writer.
 *
 * usage: kvemu2 <trace.jsonl> <block_KiB> <t0_s> <t1_s> <speed> <policy> <dram_GiB> <cxl_GiB> <watermark>
 *               <workers> <first_cpu> <chunk_blocks> <link_GBps> <prefill_tok_s> [store_cap_GBps=0] [cxlpath_store]
 *   The cache is warmed with the trace from 0 to t0 (no traffic, placement by the same policy, no loan).
 * output: "W <mono_ns> <offered_GBps> <store_dram_GBps> <store_cxl_GBps> <load_GBps> <backlog_GB> <late_max_ms>
 *          <occ_dram_GiB> <occ_cxl_GiB> <spill16> <budget_GBps>" every 20 ms, then "S ..." summary lines. */
#define _GNU_SOURCE
#include "../../system/cxlpath/src/internal.h"
#include <fcntl.h>
#include <immintrin.h>
#include <pthread.h>
#include <sched.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <time.h>
#include <unistd.h>

#define MiB (1ull << 20)
#define GiB (1ull << 30)
#define PIECE (2 * MiB)
#define NIL UINT32_MAX
static uint64_t now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return (uint64_t)t.tv_sec * 1000000000ull + (uint64_t)t.tv_nsec; }
static void pin_cpu(int c) { cpu_set_t s; CPU_ZERO(&s); CPU_SET(c, &s); pthread_setaffinity_np(pthread_self(), sizeof s, &s); }
static void sleep_until(uint64_t t) { uint64_t n = now(); if (t > n) { struct timespec d = { (time_t)((t - n) / 1000000000ull), (long)((t - n) % 1000000000ull) }; nanosleep(&d, NULL); } }

enum { P_DRAM, P_CXL, P_LMCACHE, P_SPLIT, P_CXLFIRST, P_BORROWTIER, P_BORROWGLOB, P_BORROWMIG, P_BUDGET, NPOL };
static const char *pnames[] = { "dram", "cxl", "lmcache", "split", "cxlfirst", "borrowtier", "borrowglob", "borrowmig", "budget" };
static int policy; static double watermark;

/* ---------------- slots, LRU lists, hash ---------------- */
typedef struct {
    uint64_t hash; uint32_t gprev, gnext, tprev, tnext; uint8_t used;
    _Atomic uint8_t ready; _Atomic uint32_t readers;
} slot_t;
static slot_t *S; static uint32_t nslot[2], nslots;                 /* tier 0 = DRAM slots [0, nslot[0]), tier 1 = CXL */
static uint32_t ghead = NIL, gtail = NIL, thead[2] = { NIL, NIL }, ttail[2] = { NIL, NIL };
static uint32_t *freel[2]; static uint32_t nfree[2], occ[2];
static uint32_t *htab; static size_t hcap;
static char *base[2]; static size_t bsz;
static int tier_of(uint32_t s) { return s < nslot[0] ? 0 : 1; }
static char *addr_of(uint32_t s) { int t = tier_of(s); return base[t] + (size_t)(s - (t ? nslot[0] : 0)) * bsz; }
static size_t hpos(uint64_t h) { return (h * 0x9E3779B97F4A7C15ull) & (hcap - 1); }
static size_t hfind(uint64_t h) { size_t i = hpos(h); while (htab[i] != NIL && S[htab[i]].hash != h) i = (i + 1) & (hcap - 1); return i; }
static void hdel(size_t i) {
    for (size_t j = i;;) {
        j = (j + 1) & (hcap - 1); if (htab[j] == NIL) break;
        size_t k = hpos(S[htab[j]].hash);
        if ((j > i && (k <= i || k > j)) || (j < i && (k <= i && k > j))) { htab[i] = htab[j]; i = j; }
    }
    htab[i] = NIL;
}
static void g_unlink(uint32_t s) { slot_t *x = &S[s]; if (x->gprev != NIL) S[x->gprev].gnext = x->gnext; else ghead = x->gnext; if (x->gnext != NIL) S[x->gnext].gprev = x->gprev; else gtail = x->gprev; }
static void g_push(uint32_t s) { S[s].gprev = gtail; S[s].gnext = NIL; if (gtail != NIL) S[gtail].gnext = s; else ghead = s; gtail = s; }
static void t_unlink(uint32_t s) { int t = tier_of(s); slot_t *x = &S[s]; if (x->tprev != NIL) S[x->tprev].tnext = x->tnext; else thead[t] = x->tnext; if (x->tnext != NIL) S[x->tnext].tprev = x->tprev; else ttail[t] = x->tprev; }
static void t_push(uint32_t s) { int t = tier_of(s); S[s].tprev = ttail[t]; S[s].tnext = NIL; if (ttail[t] != NIL) S[ttail[t]].tnext = s; else thead[t] = s; ttail[t] = s; }
static void touch(uint32_t s) { g_unlink(s); g_push(s); t_unlink(s); t_push(s); }
static int evictable(uint32_t s) { return S[s].used && atomic_load(&S[s].ready) && atomic_load(&S[s].readers) == 0; }
static uint64_t evictions;
static void evict(uint32_t s) {
    g_unlink(s); t_unlink(s); hdel(hfind(S[s].hash)); S[s].used = 0; int t = tier_of(s); occ[t]--; freel[t][nfree[t]++] = s; evictions++;
}
static int evict_global(void) { for (uint32_t s = ghead; s != NIL; s = S[s].gnext) if (evictable(s)) { evict(s); return 1; } return 0; }
static int evict_tier(int t) { for (uint32_t s = thead[t]; s != NIL; s = S[s].tnext) if (evictable(s)) { evict(s); return 1; } return 0; }
static uint32_t place(uint64_t h, int t, int ready) {      /* take a free slot of tier t (caller made sure one exists) */
    uint32_t s = freel[t][--nfree[t]];
    S[s].hash = h; S[s].used = 1; atomic_store(&S[s].ready, (uint8_t)ready); atomic_store(&S[s].readers, 0);
    htab[hfind(h)] = s; g_push(s); t_push(s); occ[t]++; return s;
}

static pthread_mutex_t cm = PTHREAD_MUTEX_INITIALIZER;      /* cache structures: dispatcher and workers */
static uint64_t *pend; static size_t pendcap;                /* announced stores without a slot yet: open addressing, 0 = empty, 1 = deleted */
static size_t ppos(uint64_t h) { return ((h + 2) * 0x9E3779B97F4A7C15ull) & (pendcap - 1); }
static int pend_has(uint64_t h) { size_t i = ppos(h); while (pend[i]) { if (pend[i] == h + 2) return 1; i = (i + 1) & (pendcap - 1); } return 0; }
static void pend_add(uint64_t h) { size_t i = ppos(h); while (pend[i] > 1) i = (i + 1) & (pendcap - 1); pend[i] = h + 2; }
static void pend_del(uint64_t h) { size_t i = ppos(h); while (pend[i]) { if (pend[i] == h + 2) { pend[i] = 1; return; } i = (i + 1) & (pendcap - 1); } }

/* ---------------- placement policy ---------------- */
static int attached; static int devidx[2] = { -1, -1 }; static uint64_t nclaim, borrowed_blocks, n_noslot;
static uint32_t br4(uint32_t k) { k &= 15; return ((k & 1) << 3) | ((k & 2) << 1) | ((k & 4) >> 1) | ((k & 8) >> 3); }
static uint32_t spill_now(void) { return attached && cxlp_policy_daemon_alive() ? atomic_load(&POL->spill16[0]) : 0; }
static double split_share = -1; static int common_warm;
static double bud_Bps, bud_tokens; static uint64_t bud_last, bud_read_ns; static int bud_fd = -1;
static double budget_now(uint64_t t) {                      /* caller holds cm */
    if (bud_fd >= 0 && t - bud_read_ns >= 10000000ull) { char b[64]; ssize_t r = pread(bud_fd, b, sizeof b - 1, 0); if (r > 0) { b[r] = 0; bud_Bps = atof(b) * 1e9; } bud_read_ns = t; }
    return bud_Bps;
}
static int cap_share_tier(uint64_t h) { return ((h * 0xD6E8FEB86659FD93ull) >> 40) % (nslot[0] + nslot[1]) < nslot[0] ? 0 : 1; }
static uint32_t insert(uint64_t h, int warm) {                /* NIL if no slot can be freed (everything busy) */
    int t;
    if (warm && nslot[0] && nslot[1] && policy != P_LMCACHE && (common_warm || policy == P_BUDGET)) { t = cap_share_tier(h); if (!nfree[t] && !evict_tier(t)) return NIL; return place(h, t, warm); }
    switch (policy) {
    case P_DRAM: t = 0; break;
    case P_CXL: case P_CXLFIRST: t = 1; break;
    case P_SPLIT: t = split_share < 0 ? cap_share_tier(h) : (((h * 0xD6E8FEB86659FD93ull) >> 40) / 16777216.0 < split_share ? 0 : 1); break;
    case P_BUDGET: {                                          /* token bucket of one block, refilled at the current budget */
        uint64_t tn = now(); double B = budget_now(tn);
        if (bud_last) bud_tokens += (tn - bud_last) / 1e9 * B; bud_last = tn; if (bud_tokens > (double)bsz) bud_tokens = (double)bsz;
        t = 1;
        if (nslot[0] && bud_tokens >= (double)bsz && (nfree[0] || evict_tier(0))) { t = 0; bud_tokens -= (double)bsz; }
        break; }
    case P_LMCACHE:
        if (!nfree[0] && !nfree[1] && !evict_global()) return NIL;
        t = nfree[0] ? 0 : 1;
        { uint32_t s = place(h, t, warm);
          while ((double)(occ[0] + occ[1]) > watermark * nslots && evict_global()) {}
          return s; }
    default: {                                                /* borrowtier / borrowglob / borrowmig */
        uint32_t sp = warm ? 0 : spill_now(); t = (br4((uint32_t)nclaim++) < sp && nslot[0]) ? 0 : 1;
        if (t == 0) borrowed_blocks++;
        if (policy == P_BORROWGLOB) { while (!nfree[t]) if (!evict_global()) return NIL; return place(h, t, warm); }
    } }
    if (!nfree[t] && !evict_tier(t)) return NIL;
    return place(h, t, warm);
}

/* ---------------- jobs ---------------- */
typedef struct { uint64_t due; uint64_t hash; uint32_t slot; uint8_t store; uint32_t dst; } job_t;   /* store 2 = move slot -> dst */
static job_t *heap; static size_t nheap, hcapj; static pthread_mutex_t hm = PTHREAD_MUTEX_INITIALIZER; static pthread_cond_t hc = PTHREAD_COND_INITIALIZER;
static void hpush(job_t j) {
    pthread_mutex_lock(&hm);
    if (nheap == hcapj) { hcapj = hcapj ? 2 * hcapj : 1 << 16; heap = realloc(heap, hcapj * sizeof *heap); }
    size_t i = nheap++; while (i && heap[(i - 1) / 2].due > j.due) { heap[i] = heap[(i - 1) / 2]; i = (i - 1) / 2; } heap[i] = j;
    pthread_cond_signal(&hc); pthread_mutex_unlock(&hm);
}
static job_t hpop_locked(void) {
    job_t top = heap[0], last = heap[--nheap]; size_t i = 0;
    for (;;) { size_t c = 2 * i + 1; if (c >= nheap) break; if (c + 1 < nheap && heap[c + 1].due < heap[c].due) c++; if (heap[c].due >= last.due) break; heap[i] = heap[c]; i = c; }
    if (nheap) heap[i] = last; return top;
}
static double link_Bps, cap_Bps; static _Atomic uint64_t cap_clock;
static _Atomic uint64_t ld_bytes, late_max_ns, busy_workers; static volatile int stop, dispatch_done;
static volatile long long sink; static char *src;
static uint64_t t_start;
static _Atomic uint64_t st_bytes[2];
static _Atomic uint64_t n_moves, n_moves_aborted, mv_bytes; static _Atomic uint32_t moves_inflight;
static void paced_store(char *dst, uint64_t t0, int dev, int tier) {
    for (size_t off = 0; off < bsz; off += PIECE) {
        uint64_t p0 = now();
        size_t n = bsz - off < PIECE ? bsz - off : PIECE;
        if (cap_Bps > 0) { uint64_t dur = (uint64_t)(n / cap_Bps * 1e9), t = now(), old = atomic_load(&cap_clock), st;
                           do { st = old > t ? old : t; } while (!atomic_compare_exchange_weak(&cap_clock, &old, st + dur)); sleep_until(st); }
        for (size_t i = 0; i < n; i += 32) _mm256_stream_si256((__m256i *)(dst + off + i), _mm256_load_si256((const __m256i *)(src + ((off + i) & (PIECE - 1)))));
        _mm_sfence();
        if (dev >= 0) cxlp_account(dev, 0, n, now() - p0);   /* per 2 MiB piece, as the cxlpath writers report */
        atomic_fetch_add(&st_bytes[tier], n);                 /* per piece, so 20 ms rates are right (2026-10-12) */
        sleep_until(t0 + (uint64_t)((off + n) / link_Bps * 1e9));
    }
}
static void paced_load(const char *s, uint64_t t0) {
    __m256i acc = _mm256_setzero_si256();
    for (size_t off = 0; off < bsz; off += PIECE) {
        size_t n = bsz - off < PIECE ? bsz - off : PIECE;
        for (size_t i = 0; i < n; i += 64) { acc = _mm256_add_epi64(acc, _mm256_stream_load_si256((__m256i *)(s + off + i))); acc = _mm256_add_epi64(acc, _mm256_stream_load_si256((__m256i *)(s + off + i + 32))); }
        sleep_until(t0 + (uint64_t)((off + n) / link_Bps * 1e9));
    }
    sink += _mm256_extract_epi64(acc, 0);
}
static void *worker(void *a) {
    pin_cpu((int)(intptr_t)a);
    for (;;) {
        pthread_mutex_lock(&hm);
        for (;;) {
            if (stop || (dispatch_done && !nheap)) { pthread_mutex_unlock(&hm); return NULL; }
            if (nheap && heap[0].due <= now()) break;
            struct timespec ts; clock_gettime(CLOCK_REALTIME, &ts); ts.tv_nsec += 500000; if (ts.tv_nsec >= 1000000000) { ts.tv_sec++; ts.tv_nsec -= 1000000000; }
            pthread_cond_timedwait(&hc, &hm, &ts);
        }
        job_t j = hpop_locked(); atomic_fetch_add(&busy_workers, 1); pthread_mutex_unlock(&hm);
        uint64_t t0 = now(), late = t0 - j.due, m = atomic_load(&late_max_ns); while (late > m && !atomic_compare_exchange_weak(&late_max_ns, &m, late)) {}
        if (j.store == 1) {                                    /* choose slot and tier NOW (loan as of now) */
            pthread_mutex_lock(&cm); pend_del(j.hash);
            uint32_t sl = insert(j.hash, 0); if (sl == NIL) n_noslot++;
            pthread_mutex_unlock(&cm);
            if (sl != NIL) {
                int t = tier_of(sl); uint64_t c0 = now();
                paced_store(addr_of(sl), c0, attached ? devidx[t] : -1, t); atomic_store(&S[sl].ready, 1);
            }
        } else if (j.store == 2) {                             /* move CXL slot -> DRAM slot: copy, then switch and free */
            const char *sp = addr_of(j.slot); char *dp = addr_of(j.dst);
            for (size_t off = 0; off < bsz; off += PIECE) {
                for (size_t i = 0; i < PIECE && off + i < bsz; i += 32) _mm256_stream_si256((__m256i *)(dp + off + i), _mm256_stream_load_si256((__m256i *)(sp + off + i)));
                _mm_sfence(); atomic_fetch_add(&st_bytes[0], PIECE); sleep_until(t0 + (uint64_t)((off + PIECE) / link_Bps * 1e9));
            }
            atomic_fetch_add(&mv_bytes, bsz);
            uint64_t w0 = now(); while (atomic_load(&S[j.slot].readers) > 1 && now() - w0 < 50000000ull) { struct timespec d = { 0, 200000 }; nanosleep(&d, NULL); }
            pthread_mutex_lock(&cm);
            atomic_fetch_sub(&S[j.slot].readers, 1);                /* our own pin */
            if (atomic_load(&S[j.slot].readers) == 0 && S[j.slot].used && S[j.slot].hash == j.hash) {
                uint32_t src = j.slot, dst = j.dst;
                g_unlink(src); t_unlink(src); S[src].used = 0; occ[1]--; freel[1][nfree[1]++] = src;
                S[dst].hash = j.hash; S[dst].used = 1; atomic_store(&S[dst].readers, 0); atomic_store(&S[dst].ready, 1);
                htab[hfind(j.hash)] = dst; g_push(dst); t_push(dst); occ[0]++; atomic_fetch_add(&n_moves, 1);
            } else { S[j.dst].used = 0; freel[0][nfree[0]++] = j.dst; atomic_fetch_add(&n_moves_aborted, 1); }
            pthread_mutex_unlock(&cm); atomic_fetch_sub(&moves_inflight, 1);
        } else { paced_load(addr_of(j.slot), t0); atomic_fetch_sub(&S[j.slot].readers, 1); atomic_fetch_add(&ld_bytes, bsz); }
        atomic_fetch_sub(&busy_workers, 1);
    }
}

/* ---------------- offered timeline (bytes every job would move if it started on time) ---------------- */
static _Atomic uint64_t *offered; static size_t nbins;
static void offer(uint64_t due_rel_ns) {
    double a = due_rel_ns / 1e9, b = a + bsz / link_Bps;
    for (size_t bi = (size_t)(a / 0.02); bi < nbins && bi * 0.02 < b; bi++) {
        double lo = bi * 0.02 > a ? bi * 0.02 : a, hi = (bi + 1) * 0.02 < b ? (bi + 1) * 0.02 : b;
        if (hi > lo) atomic_fetch_add(&offered[bi], (uint64_t)((hi - lo) * link_Bps));
    }
}

/* ---------------- statistics (dispatcher only) ---------------- */
static uint64_t n_req, n_access, n_reuse, n_hit, n_hit_t[2], n_pending, n_absent_reuse, n_stored, n_nostore;
static uint64_t *seen; static size_t seencap;
static int seen_add(uint64_t h) {                            /* 1 if h was seen before */
    size_t i = (h * 0x9E3779B97F4A7C15ull) & (seencap - 1);
    while (seen[i]) { if (seen[i] == h + 1) return 1; i = (i + 1) & (seencap - 1); }
    seen[i] = h + 1; return 0;
}
static double occ_sum[2]; static uint64_t occ_n;
static volatile uint64_t log_end_ns;
static void *logger(void *a) {
    (void)a; pin_cpu(95);
    uint64_t ls[2] = { 0, 0 }, ll = 0, cum_off = 0;
    for (size_t bi = 0;; bi++) {
        uint64_t tw = t_start + (bi + 1) * 20000000ull; sleep_until(tw);
        uint64_t off = bi < nbins ? atomic_load(&offered[bi]) : 0; cum_off += off;
        uint64_t s0 = atomic_load(&st_bytes[0]), s1 = atomic_load(&st_bytes[1]), l = atomic_load(&ld_bytes);
        double backlog = ((double)cum_off - (double)(s0 + s1 + l)) / 1e9;
        uint32_t o0 = occ[0], o1 = occ[1];                    /* racy reads of dispatcher counters: fine for logging */
        occ_sum[0] += o0; occ_sum[1] += o1; occ_n++;
        printf("W %lu %.3f %.3f %.3f %.3f %.3f %.1f %.1f %.1f %u %.2f\n", (unsigned long)tw, off / 0.02 / 1e9, (s0 - ls[0]) / 0.02 / 1e9, (s1 - ls[1]) / 0.02 / 1e9,
               (l - ll) / 0.02 / 1e9, backlog > 0 ? backlog : 0, atomic_exchange(&late_max_ns, 0) / 1e6, (double)o0 * bsz / GiB, (double)o1 * bsz / GiB, spill_now(),
               policy == P_BUDGET ? bud_Bps / 1e9 : 0.0);   /* racy read of the budget: fine for logging */
        ls[0] = s0; ls[1] = s1; ll = l;
        if (log_end_ns && tw >= log_end_ns) return NULL;
    }
}

static char *map_region(int t, size_t bytes) {
    if (!bytes) return NULL;
    char *p;
    if (t == 0) { p = mmap(NULL, bytes, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0); if (p == MAP_FAILED) { perror("mmap dram"); exit(1); } madvise(p, bytes, MADV_HUGEPAGE); }
    else { int fd = open("/dev/dax0.0", O_RDWR); if (fd < 0) { perror("/dev/dax0.0"); exit(1); } p = mmap(NULL, bytes, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0); if (p == MAP_FAILED) { perror("mmap dax"); exit(1); } }
    for (size_t off = 0; off < bytes; off += PIECE)
        for (size_t i = 0; i < PIECE; i += 32) _mm256_stream_si256((__m256i *)(p + off + i), _mm256_load_si256((const __m256i *)(src + i)));
    _mm_sfence(); return p;
}

int main(int argc, char **argv) {
    if (argc < 15) { fprintf(stderr, "usage: see the header of kvemu2.c\n"); return 2; }
    const char *trace = argv[1]; bsz = (size_t)atol(argv[2]) << 10; double t0s = atof(argv[3]), t1s = atof(argv[4]), speed = atof(argv[5]);
    policy = -1; for (int i = 0; i < NPOL; i++) if (!strcmp(argv[6], pnames[i])) policy = i;
    if (policy < 0) { fprintf(stderr, "unknown policy %s\n", argv[6]); return 2; }
    double dram_gib = atof(argv[7]), cxl_gib = atof(argv[8]); watermark = atof(argv[9]);
    int W = atoi(argv[10]), cpu0 = atoi(argv[11]), chunk = atoi(argv[12]); link_Bps = atof(argv[13]) * 1e9; double pf = atof(argv[14]);
    cap_Bps = (argc > 15 ? atof(argv[15]) : 0) * 1e9; const char *store = argc > 16 ? argv[16] : NULL;
    if (policy == P_DRAM) cxl_gib = 0; if (policy == P_CXL) dram_gib = 0;
    if (policy != P_LMCACHE) watermark = 1.0;
    if (getenv("KV2_SPLIT_SHARE")) split_share = atof(getenv("KV2_SPLIT_SHARE"));
    common_warm = getenv("KV2_WARM") && !strcmp(getenv("KV2_WARM"), "common");
    if (getenv("KV2_BUDGET_GBPS")) bud_Bps = atof(getenv("KV2_BUDGET_GBPS")) * 1e9;
    if (getenv("KV2_BUDGET_FILE")) { bud_fd = open(getenv("KV2_BUDGET_FILE"), O_RDONLY); if (bud_fd < 0) { perror(getenv("KV2_BUDGET_FILE")); return 1; } bud_read_ns = 0; budget_now(now()); }
    nslot[0] = (uint32_t)(dram_gib * GiB / bsz); nslot[1] = (uint32_t)(cxl_gib * GiB / bsz); nslots = nslot[0] + nslot[1];
    S = calloc(nslots, sizeof *S); for (int t = 0; t < 2; t++) { freel[t] = malloc((nslot[t] + 1) * 4); nfree[t] = 0; }
    for (uint32_t s = nslots; s-- > 0;) { int t = tier_of(s); freel[t][nfree[t]++] = s; }      /* lowest index popped first */
    for (hcap = 1; hcap < 2ull * nslots + 2; hcap <<= 1) {} htab = malloc(hcap * 4); memset(htab, 0xff, hcap * 4);
    seencap = 1 << 20; seen = calloc(seencap, 8); pendcap = 1 << 20; pend = calloc(pendcap, 8);
    src = aligned_alloc(4096, PIECE); { uint64_t x = 0xD6E8FEB86659FD93ull; for (size_t i = 0; i < PIECE; i += 8) { x ^= x << 13; x ^= x >> 7; x ^= x << 17; *(uint64_t *)(src + i) = x; } }
    if (store) {
        if (cxlp_attach(store)) { fprintf(stderr, "cannot attach cxlpath store %s\n", store); return 1; }
        attached = 1;
        for (int d = 0; d < (int)cxlp_g.meta->ndev; d++) { uint32_t k = cxlp_g.meta->dev[d].kind; uint64_t sz = cxlp_g.meta->dev[d].bytes;
            if (!sz) continue; if (k == CXLP_DEV_DRAM && devidx[0] < 0) devidx[0] = d; if (k == CXLP_DEV_CXL && devidx[1] < 0) devidx[1] = d; }
    }
    base[0] = map_region(0, (size_t)nslot[0] * bsz); base[1] = map_region(1, (size_t)nslot[1] * bsz);

    /* read the trace: warm-up part directly, the rest into memory */
    FILE *f = fopen(trace, "r"); if (!f) { perror(trace); return 1; }
    char *line = NULL; size_t lcap = 0; uint64_t *hs = malloc(8 * 8192);
    typedef struct { double ts; uint32_t n, off; } rq_t; rq_t *rq = NULL; size_t nrq = 0, rcap = 0; uint64_t *all = NULL; size_t nall = 0, acap = 0;
    while (getline(&line, &lcap, f) > 0) {
        double ts = atof(strstr(line, "\"timestamp\":") + 12) / 1000.0; if (ts >= t1s) break;
        char *p = strstr(line, "\"hash_ids\": [") + 13; uint32_t n = 0;
        while (*p && *p != ']' && n < 8192) { hs[n++] = strtoull(p, &p, 10); while (*p == ',' || *p == ' ') p++; }
        if (ts < t0s) {                                       /* warm-up: cache state only, everything ready */
            for (uint32_t i = 0; i < n; i++) { seen_add(hs[i]); size_t hi = hfind(hs[i]); if (htab[hi] != NIL) touch(htab[hi]); else insert(hs[i], 1); }
            continue;
        }
        if (nrq == rcap) { rcap = rcap ? 2 * rcap : 4096; rq = realloc(rq, rcap * sizeof *rq); }
        while (nall + n > acap) { acap = acap ? 2 * acap : 1 << 20; all = realloc(all, acap * 8); }
        memcpy(all + nall, hs, n * 8); rq[nrq++] = (rq_t){ ts, n, (uint32_t)nall }; nall += n;
    }
    fclose(f);
    double span = nrq ? (rq[nrq - 1].ts - t0s) / speed + 60 : 60;   /* stores of the last requests trail by their prefill */
    nbins = (size_t)(span / 0.02) + 1; offered = calloc(nbins, 8);
    printf("# kvemu2 %s [%g,%g) s at %gx: %zu requests; block %zu KiB; policy %s; DRAM %.1f GiB (%u slots) + CXL %.1f GiB (%u slots), watermark %.2f; "
           "%d workers on cpus %d..; chunk %d blocks, link %.2f GB/s, prefill %.0f tok/s, store cap %.1f GB/s; cxlpath store %s (dev DRAM %d, CXL %d); "
           "split share %s; warm-up %s; budget %s\n",
           trace, t0s, t1s, speed, nrq, bsz >> 10, pnames[policy], dram_gib, nslot[0], cxl_gib, nslot[1], watermark, W, cpu0, chunk, link_Bps / 1e9, pf, cap_Bps / 1e9,
           store ? store : "-", devidx[0], devidx[1], getenv("KV2_SPLIT_SHARE") ? getenv("KV2_SPLIT_SHARE") : "capacity",
           common_warm || policy == P_BUDGET ? "common (capacity-share split)" : "by policy",
           policy != P_BUDGET ? "-" : getenv("KV2_BUDGET_FILE") ? getenv("KV2_BUDGET_FILE") : getenv("KV2_BUDGET_GBPS") ? getenv("KV2_BUDGET_GBPS") : "0");
    printf("# after warm-up: occupancy DRAM %u CXL %u of %u slots\n", occ[0], occ[1], nslots); fflush(stdout);

    pthread_t th[256], lg; t_start = now() + 200000000ull;
    printf("START %lu\n", (unsigned long)t_start); fflush(stdout);
    for (int i = 0; i < W && i < 256; i++) pthread_create(&th[i], NULL, worker, (void *)(intptr_t)(cpu0 + (i % 32) + 128 * ((i / 32) % 2)));
    pthread_create(&lg, NULL, logger, NULL);
    uint64_t per_blk = (uint64_t)(bsz / link_Bps * 1e9);
    for (size_t r = 0; r < nrq; r++) {                         /* the dispatcher: one request at its arrival time */
        uint64_t arr = (uint64_t)((rq[r].ts - t0s) / speed * 1e9); sleep_until(t_start + arr);
        uint64_t *h = all + rq[r].off; uint32_t n = rq[r].n, k = 0; n_req++;
        pthread_mutex_lock(&cm);
        for (uint32_t i = 0; i < n; i++) { n_access++; if (seen_add(h[i])) n_reuse++; }
        for (; k < n; k++) {                                   /* longest prefix of COMPLETED blocks = loads */
            size_t hi = hfind(h[k]); if (htab[hi] == NIL) break;
            uint32_t s = htab[hi]; if (!atomic_load(&S[s].ready)) break;
            touch(s); atomic_fetch_add(&S[s].readers, 1); n_hit++; n_hit_t[tier_of(s)]++;
            if (policy == P_BORROWMIG && tier_of(s) == 1 && nslot[0] && attached && cxlp_policy_daemon_alive() && atomic_load(&POL->dram_ok)
                && atomic_load(&moves_inflight) < 8) {             /* move this reused block into DRAM, the DRAM LRU victim is dropped */
                if (nfree[0] || evict_tier(0)) {
                    uint32_t d = freel[0][--nfree[0]]; S[d].used = 1; atomic_store(&S[d].ready, 0);   /* reserved: not in hash or lists */
                    atomic_fetch_add(&S[s].readers, 1); atomic_fetch_add(&moves_inflight, 1);
                    hpush((job_t){ t_start + arr + (uint64_t)(k + 1) * per_blk, h[k], s, 2, d });
                }
            }
            hpush((job_t){ t_start + arr + (uint64_t)k * per_blk, 0, s, 0, 0 }); offer(arr + (uint64_t)k * per_blk);
        }
        uint64_t comp0 = arr + (uint64_t)k * per_blk;
        for (uint32_t i = k; i < n; i++) {                     /* recomputed: store blocks the cache does not have */
            size_t hi = hfind(h[i]);
            if (htab[hi] != NIL) { uint32_t s = htab[hi]; if (!atomic_load(&S[s].ready)) n_pending++; touch(s); n_nostore++; continue; }
            if (pend_has(h[i])) { n_pending++; n_nostore++; continue; }
            pend_add(h[i]);
            uint32_t c = (i - k) / chunk, j = (i - k) % chunk; n_stored++;
            uint64_t due = comp0 + (uint64_t)((c + 1) * chunk * 512.0 / pf * 1e9) + (uint64_t)j * per_blk;
            hpush((job_t){ t_start + due, h[i], NIL, 1, 0 }); offer(due);
        }
        pthread_mutex_unlock(&cm);
    }
    pthread_mutex_lock(&hm); dispatch_done = 1; pthread_cond_broadcast(&hc); pthread_mutex_unlock(&hm);
    uint64_t deadline = now() + 600000000000ull;                /* give up 10 min after the last arrival */
    while (1) { pthread_mutex_lock(&hm); size_t left = nheap; pthread_mutex_unlock(&hm); if (!left && !atomic_load(&busy_workers)) break; if (now() > deadline) { stop = 1; break; } usleep(20000); }
    for (int i = 0; i < W && i < 256; i++) pthread_join(th[i], NULL);
    log_end_ns = now(); pthread_join(lg, NULL);
    double wall = (now() - t_start) / 1e9;
    uint64_t reuse_acc = n_reuse;
    printf("S requests %lu accesses %lu reuse_accesses %lu hits %lu (dram %lu cxl %lu) hit_share_of_reuse %.4f pending_misses %lu stored %lu present_not_stored %lu no_slot %lu evictions %lu borrowed %lu\n",
           (unsigned long)n_req, (unsigned long)n_access, (unsigned long)reuse_acc, (unsigned long)n_hit, (unsigned long)n_hit_t[0], (unsigned long)n_hit_t[1],
           reuse_acc ? (double)n_hit / reuse_acc : 0, (unsigned long)n_pending, (unsigned long)n_stored, (unsigned long)n_nostore, (unsigned long)n_noslot,
           (unsigned long)evictions, (unsigned long)borrowed_blocks);
    printf("S moves %lu moves_aborted %lu moved_GB %.2f\n", (unsigned long)n_moves, (unsigned long)n_moves_aborted, atomic_load(&mv_bytes) / 1e9);
    printf("S wall_s %.1f stored_dram_GB %.2f stored_cxl_GB %.2f loaded_GB %.2f occupancy_mean_dram_GiB %.1f occupancy_mean_cxl_GiB %.1f capacity_GiB %.1f utilization %.3f gave_up %d\n",
           wall, atomic_load(&st_bytes[0]) / 1e9, atomic_load(&st_bytes[1]) / 1e9, atomic_load(&ld_bytes) / 1e9,
           occ_n ? occ_sum[0] / occ_n * bsz / GiB : 0, occ_n ? occ_sum[1] / occ_n * bsz / GiB : 0, (double)nslots * bsz / GiB,
           occ_n ? (occ_sum[0] + occ_sum[1]) / occ_n / nslots : 0, stop);
    return 0;
}
