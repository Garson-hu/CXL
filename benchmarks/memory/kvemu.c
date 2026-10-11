/* kvemu — trace-driven HOST MEMORY TRAFFIC EMULATION of a KV-cache tier (layer 2 of 2026-10-10-lmcache-kv-traffic).
 * Not a model of multi-GPU serving: it reproduces the host-memory side only — KV stores as non-temporal writes from a
 * cache-resident source (a GPU's DMA writes do not read host DRAM) and KV loads as streaming reads (a DMA read) — so the
 * traffic a KV tier puts on DRAM or CXL can be put beside neighbour programs.
 *
 * The LRU tier is warmed with the trace from 0 to t0 without any traffic; requests in [t0, t1) generate traffic.
 * Per request of a Mooncake trace window (timestamps / speed): its blocks are looked up in an LRU host tier of
 * <capacity> GiB (blocks = 512-token hash blocks of <block_KiB>). Hits are LOADED at arrival; new blocks are STORED in
 * chunks of <chunk_blocks> blocks, chunk k issued at arrival + k * chunk_tokens / <prefill_tok_s> (the prefill that
 * produces it). Every load/store job is executed by one worker at no more than <link_GBps> (a per-transfer cap, as one
 * GPU link would impose). Defaults are the layer-1 calibration (chunk = 2048 tokens = 4 blocks, link 2.9 GB/s payload,
 * prefill 4600 tokens/s per request stream). Jobs that find no free worker queue up: target vs achieved rate and the
 * backlog are logged per 20 ms window.
 *
 * usage: kvemu <trace.jsonl> <block_KiB> <t0_s> <t1_s> <speed> <capacity_GiB> <dram|cxl> <workers> <first_cpu>
 *              [chunk_blocks=4] [link_GBps=2.9] [prefill_tok_s=4600] [store_cap_GBps=0]
 *   store_cap_GBps > 0: a global cap on all stores together (2026-10-11, the throttled-DRAM baseline): every 2 MiB piece
 *   of every store starts no earlier than the previous one + piece / cap, so the aggregate never exceeds the cap.
 *   cxl = /dev/dax0.0 (cards c1+e1) from offset 0; dram = anonymous memory with huge pages.
 *   workers: worker i runs on cpu first_cpu + i%32 (+128 for i in 32..63, the SMT siblings); each block is one job.
 * output: "W <mono_ns> <target_GBps> <store_GBps> <load_GBps> <backlog_GB> <max_late_ms>" every 20 ms, then "S ..." summary.
 * (2026-10-10) */
#define _GNU_SOURCE
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
static uint64_t now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return (uint64_t)t.tv_sec * 1000000000ull + (uint64_t)t.tv_nsec; }
static void pin(int c) { cpu_set_t s; CPU_ZERO(&s); CPU_SET(c, &s); pthread_setaffinity_np(pthread_self(), sizeof s, &s); }

typedef struct { uint64_t due_ns; uint32_t slot, nblk; uint8_t store; } job_t;   /* nblk consecutive slots from `slot` */
static job_t *jobs; static size_t njobs, jcap;
static _Atomic size_t next_job;                    /* workers take jobs in due order */
static char *tier, *src; static size_t bsz;
static double link_Bps, cap_Bps;
static _Atomic uint64_t cap_clock;
static _Atomic uint64_t st_bytes, ld_bytes, late_max_ns;
static volatile int stop;
static volatile long long sink;
static uint64_t t_start;

static void add_job(uint64_t due, uint32_t slot, uint32_t nblk, int store) {
    if (njobs == jcap) { jcap = jcap ? 2 * jcap : 1 << 20; jobs = realloc(jobs, jcap * sizeof *jobs); }
    jobs[njobs++] = (job_t){ due, slot, nblk, (uint8_t)store };
}
static int cmp_job(const void *a, const void *b) { uint64_t x = ((const job_t *)a)->due_ns, y = ((const job_t *)b)->due_ns; return x < y ? -1 : x > y; }

/* LRU tier over slots: hash -> slot via open addressing; doubly linked LRU list of slots */
typedef struct { uint64_t hash; int32_t prev, next; uint8_t used; } slot_t;
static slot_t *slots; static uint32_t nslots, lru_head = UINT32_MAX, lru_tail = UINT32_MAX, nfree;
static uint32_t *htab; static size_t hcap;
static size_t hfind(uint64_t h) { size_t i = (h * 0x9E3779B97F4A7C15ull) & (hcap - 1); while (htab[i] != UINT32_MAX && slots[htab[i]].hash != h) i = (i + 1) & (hcap - 1); return i; }
static void hdel(size_t i) {               /* backward-shift deletion */
    size_t j = i;
    for (;;) {
        j = (j + 1) & (hcap - 1); if (htab[j] == UINT32_MAX) break;
        size_t k = (slots[htab[j]].hash * 0x9E3779B97F4A7C15ull) & (hcap - 1);
        if ((j > i && (k <= i || k > j)) || (j < i && (k <= i && k > j))) { htab[i] = htab[j]; i = j; }
    }
    htab[i] = UINT32_MAX;
}
static void lru_unlink(uint32_t s) { slot_t *x = &slots[s]; if (x->prev >= 0) slots[x->prev].next = x->next; else lru_head = (uint32_t)x->next; if (x->next >= 0) slots[x->next].prev = x->prev; else lru_tail = (uint32_t)x->prev; }
static void lru_push(uint32_t s) { slots[s].prev = (int32_t)lru_tail; slots[s].next = -1; if (lru_tail != UINT32_MAX) slots[lru_tail].next = (int32_t)s; else lru_head = s; lru_tail = s; }
static uint32_t take_slot(uint64_t h) {    /* a free slot, or the LRU one (evicted) */
    uint32_t s;
    if (nfree) s = nslots - nfree--;
    else { s = lru_head; lru_unlink(s); hdel(hfind(slots[s].hash)); }
    slots[s].hash = h; slots[s].used = 1; htab[hfind(h)] = s; lru_push(s); return s;
}

static void copy_paced(char *dst, size_t len, uint64_t t0) {           /* nt-store from the cache-resident source */
    for (size_t off = 0; off < len && !stop; off += PIECE) {
        size_t n = len - off < PIECE ? len - off : PIECE;
        if (cap_Bps > 0) {                                                  /* global cap: reserve a start time for this piece */
            uint64_t dur = (uint64_t)(n / cap_Bps * 1e9), t = now(), old = atomic_load(&cap_clock), st;
            do { st = old > t ? old : t; } while (!atomic_compare_exchange_weak(&cap_clock, &old, st + dur));
            if (st > t) { struct timespec d = { (time_t)((st - t) / 1000000000ull), (long)((st - t) % 1000000000ull) }; nanosleep(&d, NULL); }
        }
        for (size_t i = 0; i < n; i += 32) _mm256_stream_si256((__m256i *)(dst + off + i), _mm256_load_si256((const __m256i *)(src + ((off + i) & (PIECE - 1)))));
        _mm_sfence(); atomic_fetch_add(&st_bytes, n);
        uint64_t want = t0 + (uint64_t)((off + n) / link_Bps * 1e9), t = now();
        if (want > t) { struct timespec d = { 0, (long)(want - t) }; nanosleep(&d, NULL); }
    }
}
static void read_paced(const char *s, size_t len, uint64_t t0) {
    __m256i acc = _mm256_setzero_si256();
    for (size_t off = 0; off < len && !stop; off += PIECE) {
        size_t n = len - off < PIECE ? len - off : PIECE;
        for (size_t i = 0; i < n; i += 64) { acc = _mm256_add_epi64(acc, _mm256_stream_load_si256((__m256i *)(s + off + i))); acc = _mm256_add_epi64(acc, _mm256_stream_load_si256((__m256i *)(s + off + i + 32))); }
        atomic_fetch_add(&ld_bytes, n);
        uint64_t want = t0 + (uint64_t)((off + n) / link_Bps * 1e9), t = now();
        if (want > t) { struct timespec d = { 0, (long)(want - t) }; nanosleep(&d, NULL); }
    }
    sink += _mm256_extract_epi64(acc, 0);
}
typedef struct { int cpu; } wk_t;
static void *worker(void *a) {
    pin(((wk_t *)a)->cpu);
    for (;;) {
        size_t j = atomic_fetch_add(&next_job, 1); if (j >= njobs || stop) return NULL;
        uint64_t due = t_start + jobs[j].due_ns;
        for (uint64_t t = now(); t < due && !stop; t = now()) { uint64_t d = due - t; struct timespec ts = { 0, (long)(d > 1000000 ? 1000000 : d) }; nanosleep(&ts, NULL); }
        uint64_t t0 = now(); if (t0 > due) { uint64_t late = t0 - due, m = atomic_load(&late_max_ns); while (late > m && !atomic_compare_exchange_weak(&late_max_ns, &m, late)) {} }
        char *p = tier + (size_t)jobs[j].slot * bsz; size_t len = (size_t)jobs[j].nblk * bsz;
        if (jobs[j].store) copy_paced(p, len, t0); else read_paced(p, len, t0);
    }
}

int main(int argc, char **argv) {
    if (argc < 10) { fprintf(stderr, "usage: see the header\n"); return 2; }
    const char *trace = argv[1]; bsz = (size_t)atol(argv[2]) << 10; double t0s = atof(argv[3]), t1s = atof(argv[4]), speed = atof(argv[5]);
    double cap_gib = atof(argv[6]); int use_cxl = !strcmp(argv[7], "cxl"); int W = atoi(argv[8]), cpu0 = atoi(argv[9]);
    int chunk = argc > 10 ? atoi(argv[10]) : 4; link_Bps = (argc > 11 ? atof(argv[11]) : 2.9) * 1e9; double pf = argc > 12 ? atof(argv[12]) : 4600; cap_Bps = (argc > 13 ? atof(argv[13]) : 0) * 1e9;
    nslots = (uint32_t)(cap_gib * GiB / bsz); nfree = nslots; size_t tier_bytes = (size_t)nslots * bsz;
    slots = calloc(nslots, sizeof *slots); for (hcap = 1; hcap < 2ull * nslots; hcap <<= 1) {} htab = malloc(hcap * 4); memset(htab, 0xff, hcap * 4);
    if (use_cxl) {
        int fd = open("/dev/dax0.0", O_RDWR); if (fd < 0) { perror("/dev/dax0.0"); return 1; }
        tier = mmap(NULL, tier_bytes, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0); if (tier == MAP_FAILED) { perror("mmap dax"); return 1; }
    } else { tier = mmap(NULL, tier_bytes, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0); if (tier == MAP_FAILED) { perror("mmap"); return 1; } madvise(tier, tier_bytes, MADV_HUGEPAGE); }
    src = aligned_alloc(4096, PIECE); { uint64_t x = 0xD6E8FEB86659FD93ull; for (size_t i = 0; i < PIECE; i += 8) { x ^= x << 13; x ^= x >> 7; x ^= x << 17; *(uint64_t *)(src + i) = x; } }
    for (size_t off = 0; off < tier_bytes; off += PIECE)                /* pre-touch + data-carrying lines everywhere */
        for (size_t i = 0; i < PIECE; i += 32) _mm256_stream_si256((__m256i *)(tier + off + i), _mm256_load_si256((const __m256i *)(src + i)));
    _mm_sfence();
    /* build the job list from the trace (the LRU decides hits, slots and evictions in arrival order) */
    FILE *f = fopen(trace, "r"); if (!f) { perror(trace); return 1; }
    char *line = NULL; size_t lcap = 0; uint64_t nreq = 0, hits = 0, misses = 0; uint64_t hs[4096];
    while (getline(&line, &lcap, f) > 0) {
        double ts = atof(strstr(line, "\"timestamp\":") + 12) / 1000.0; if (ts >= t1s) break; int warm = ts < t0s;
        char *p = strstr(line, "\"hash_ids\": [") + 13; int n = 0;
        while (*p && *p != ']' && n < 4096) { hs[n++] = strtoull(p, &p, 10); while (*p == ',' || *p == ' ') p++; }
        if (warm) {                                                      /* warm-up: LRU state only */
            for (int i = 0; i < n; i++) { size_t hi = hfind(hs[i]); if (htab[hi] != UINT32_MAX) { uint32_t s = htab[hi]; lru_unlink(s); lru_push(s); } else take_slot(hs[i]); }
            continue;
        }
        uint64_t arr = (uint64_t)((ts - t0s) / speed * 1e9); nreq++;
        uint64_t per_blk = (uint64_t)(bsz / link_Bps * 1e9);            /* one block at the link rate */
        int k = 0;
        for (int i = 0; i < n; i++) {                                    /* longest cached prefix = loads, one after another */
            size_t hi = hfind(hs[i]); if (htab[hi] == UINT32_MAX) break;
            uint32_t s = htab[hi]; lru_unlink(s); lru_push(s); add_job(arr + (uint64_t)k * per_blk, s, 1, 0); hits++; k++;
        }
        uint64_t comp0 = arr + (uint64_t)k * per_blk;                    /* prefill starts after the loads */
        for (int i = k; i < n; i++) {                                    /* the rest is computed and stored, chunk by chunk */
            size_t hi = hfind(hs[i]); uint32_t s;
            if (htab[hi] != UINT32_MAX) { s = htab[hi]; lru_unlink(s); lru_push(s); } else s = take_slot(hs[i]);
            int c = (i - k) / chunk, j = (i - k) % chunk; misses++;
            add_job(comp0 + (uint64_t)((c + 1) * chunk * 512.0 / pf * 1e9) + (uint64_t)j * per_blk, s, 1, 1);
        }
    }
    fclose(f); qsort(jobs, njobs, sizeof *jobs, cmp_job);
    double span = njobs ? jobs[njobs - 1].due_ns / 1e9 + bsz / link_Bps : 0; uint64_t tot_st = 0, tot_ld = 0;
    for (size_t j = 0; j < njobs; j++) *(jobs[j].store ? &tot_st : &tot_ld) += (uint64_t)jobs[j].nblk * bsz;
    size_t nbins = (size_t)(span / 0.02) + 2; double *target = calloc(nbins, sizeof *target);
    for (size_t j = 0; j < njobs; j++) {                                 /* the demand if every job started on time */
        double a = jobs[j].due_ns / 1e9, b = a + (double)jobs[j].nblk * bsz / link_Bps, rate = link_Bps;
        for (size_t bi = (size_t)(a / 0.02); bi < nbins && bi * 0.02 < b; bi++) {
            double lo = bi * 0.02 > a ? bi * 0.02 : a, hi = (bi + 1) * 0.02 < b ? (bi + 1) * 0.02 : b;
            if (hi > lo) target[bi] += (hi - lo) * rate;
        }
    }
    printf("# kvemu %s [%g,%g) s at %gx: %lu requests, %zu jobs, block %zu KiB, tier %s %.1f GiB (%u slots), %d workers on cpus %d.., chunk %d blocks, link %.2f GB/s, prefill %.0f tok/s, store cap %.1f GB/s\n",
           trace, t0s, t1s, speed, (unsigned long)nreq, njobs, bsz >> 10, use_cxl ? "cxl(dax0.0)" : "dram", cap_gib, nslots, W, cpu0, chunk, link_Bps / 1e9, pf, cap_Bps / 1e9);
    printf("# planned: store %.1f GB, load %.1f GB over %.1f s -> %.2f + %.2f GB/s average; block hits %lu, stored blocks %lu\n",
           tot_st / 1e9, tot_ld / 1e9, span, tot_st / 1e9 / span, tot_ld / 1e9 / span, (unsigned long)hits, (unsigned long)misses);
    fflush(stdout);
    /* run */
    pthread_t th[256]; wk_t wk[256]; t_start = now() + 200000000ull;
    printf("START %lu\n", (unsigned long)t_start); fflush(stdout);
    for (int i = 0; i < W && i < 256; i++) { wk[i].cpu = cpu0 + (i % 32) + 128 * ((i / 32) % 2); pthread_create(&th[i], NULL, worker, &wk[i]); }
    uint64_t ls = 0, ll = 0; uint64_t t_end = t_start + (uint64_t)(span * 1e9) + 500000000ull; double cum_target = 0;
    for (size_t bi = 0;; bi++) {
        uint64_t tw = t_start + (bi + 1) * 20000000ull, t = now();
        if (tw > t) { struct timespec d = { (time_t)((tw - t) / 1000000000ull), (long)((tw - t) % 1000000000ull) }; nanosleep(&d, NULL); }
        double tg = bi < nbins ? target[bi] : 0; cum_target += tg;
        uint64_t s = atomic_load(&st_bytes), l = atomic_load(&ld_bytes);
        double backlog = (cum_target - (double)(s + l)) / 1e9;
        printf("W %lu %.3f %.3f %.3f %.3f %.1f\n", (unsigned long)tw, tg / 0.02 / 1e9, (s - ls) / 0.02 / 1e9, (l - ll) / 0.02 / 1e9, backlog > 0 ? backlog : 0,
               atomic_exchange(&late_max_ns, 0) / 1e6);
        ls = s; ll = l;
        if (tw > t_end && atomic_load(&next_job) >= njobs + (size_t)W) break;
        if (tw > t_end + 600000000000ull) { stop = 1; break; }              /* give up 10 min after the planned end */
    }
    stop = 1; for (int i = 0; i < W && i < 256; i++) pthread_join(th[i], NULL);
    double wall = (now() - t_start) / 1e9;
    printf("S planned_s %.1f wall_s %.1f stored_GB %.2f loaded_GB %.2f planned_store_GB %.2f planned_load_GB %.2f\n",
           span, wall, atomic_load(&st_bytes) / 1e9, atomic_load(&ld_bytes) / 1e9, tot_st / 1e9, tot_ld / 1e9);
    return 0;
}
