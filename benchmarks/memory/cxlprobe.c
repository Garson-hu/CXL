/* cxlprobe.c — probes for per-card CXL experiments on interleaved regions.
 *
 * Modes:
 *   stream     sequential 64B-line reads over a node-bound region
 *   stride     read CHUNK bytes every STRIDE bytes at OFFSET within each 2MB page
 *              (targets one card of a 2-way 256B-interleaved pair: stride=512,
 *               chunk=256, offset=0 or 256)
 *   chase      pointer-chase latency with per-load percentiles (p50..p99.99)
 *   daxstream  read-only sequential reads over an mmap'd devdax chardev
 *   daxchase   read-only dependent-load latency percentiles on a devdax chardev
 *
 * All threads run on node-0 CPUs (node 1 is CPU-less); pin start with --cpu-offset.
 * Region memory is bound to --node with mbind; THP requested via madvise.
 *
 * gcc -O2 -o cxlprobe cxlprobe.c -lnuma -lpthread
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <pthread.h>
#include <sched.h>
#include <time.h>
#include <sys/mman.h>
#include <numaif.h>
#include <numa.h>
#include <x86intrin.h>

#define LINE 64
#define PG2M (2UL * 1024 * 1024)

static inline uint64_t now_ns(void) {
    struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ull + ts.tv_nsec;
}
static inline uint64_t rdtscp_ser(void) {
    unsigned aux; uint64_t t = __rdtscp(&aux); return t;
}

static double g_ns_per_tsc;
static void calibrate_tsc(void) {
    uint64_t n0 = now_ns(), t0 = rdtscp_ser();
    struct timespec r = {0, 200 * 1000 * 1000}; nanosleep(&r, NULL);
    uint64_t n1 = now_ns(), t1 = rdtscp_ser();
    g_ns_per_tsc = (double)(n1 - n0) / (double)(t1 - t0);
}

struct opts {
    const char *mode, *tag, *daxpath;
    int node, threads, secs, cpu_offset, csv;
    size_t size, stride, chunk, offset, dax_offset, samples;
};

struct tctx {
    struct opts *o; int tid; uint8_t *base; size_t len;
    volatile int *stop; uint64_t bytes; uint64_t sink;
    uint32_t *samples_ns; size_t nsamples;
};

static void pin(int cpu) {
    cpu_set_t s; CPU_ZERO(&s); CPU_SET(cpu, &s);
    pthread_setaffinity_np(pthread_self(), sizeof(s), &s);
}

/* ---------- allocation ---------- */
static uint8_t *alloc_node(size_t size, int node) {
    size_t sz = size + PG2M;
    uint8_t *raw = mmap(NULL, sz, PROT_READ | PROT_WRITE,
                        MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (raw == MAP_FAILED) { perror("mmap"); exit(1); }
    uint8_t *p = (uint8_t *)(((uintptr_t)raw + PG2M - 1) & ~(PG2M - 1));
    madvise(p, size, MADV_HUGEPAGE);
    unsigned long mask = 1UL << node;
    if (mbind(p, size, MPOL_BIND, &mask, sizeof(mask) * 8, 0))
        { perror("mbind"); exit(1); }
    for (size_t i = 0; i < size; i += 4096) p[i] = (uint8_t)i;  /* touch */
#ifndef MADV_COLLAPSE
#define MADV_COLLAPSE 25
#endif
    int crc = madvise(p, size, MADV_COLLAPSE);   /* force THP (Linux 6.1+) */
    FILE *f = fopen("/proc/self/smaps_rollup", "r");
    if (f) {
        char line[256]; unsigned long thp_kb = 0;
        while (fgets(line, sizeof(line), f))
            if (sscanf(line, "AnonHugePages: %lu", &thp_kb) == 1) break;
        fclose(f);
        fprintf(stderr, "# thp: collapse_rc=%d anon_huge=%lu MB (region %zu MB)\n",
                crc, thp_kb / 1024, size >> 20);
    }
    return p;
}
static uint8_t *map_dax(const char *path, size_t off, size_t size) {
    int fd = open(path, O_RDONLY);
    if (fd < 0) { perror("open dax"); exit(1); }
    uint8_t *p = mmap(NULL, size, PROT_READ, MAP_SHARED, fd, off);
    if (p == MAP_FAILED) { perror("mmap dax"); exit(1); }
    return p;
}

/* ---------- workers ---------- */
static void *w_stream(void *a) {
    struct tctx *c = a; pin(c->o->cpu_offset + c->tid);
    volatile uint64_t *end = (volatile uint64_t *)(c->base + c->len);
    uint64_t s = 0, bytes = 0;
    while (!*c->stop) {
        for (volatile uint64_t *q = (volatile uint64_t *)c->base; q < end; q += 8) {
            s += *q;                       /* one 64B line per iteration */
            if (__builtin_expect(*c->stop, 0)) break;
        }
        bytes += c->len;
    }
    c->bytes = bytes; c->sink = s; return NULL;
}

static void *w_stride(void *a) {
    struct tctx *c = a; pin(c->o->cpu_offset + c->tid);
    size_t stride = c->o->stride, chunk = c->o->chunk, off0 = c->o->offset;
    uint64_t s = 0, bytes = 0;
    while (!*c->stop) {
        for (uint8_t *pg = c->base; pg < c->base + c->len; pg += PG2M) {
            for (size_t off = off0; off + chunk <= PG2M; off += stride) {
                volatile uint64_t *q = (volatile uint64_t *)(pg + off);
                for (size_t l = 0; l < chunk; l += LINE) s += q[l / 8];
                bytes += chunk;
            }
            if (*c->stop) break;
        }
    }
    c->bytes = bytes; c->sink = s; return NULL;
}

/* build a random cyclic pointer chain over cache lines (Sattolo) */
static void build_chain(uint8_t *base, size_t len) {
    size_t n = len / LINE;
    uint32_t *perm = malloc(n * sizeof(uint32_t));
    for (size_t i = 0; i < n; i++) perm[i] = i;
    srandom(12345);
    for (size_t i = n - 1; i > 0; i--) {           /* Sattolo: single cycle */
        size_t j = random() % i;
        uint32_t t = perm[i]; perm[i] = perm[j]; perm[j] = t;
    }
    for (size_t i = 0; i < n; i++) {
        size_t from = perm[i], to = perm[(i + 1) % n];
        *(uint64_t *)(base + from * LINE) = (uint64_t)(base + to * LINE);
    }
    free(perm);
}

static int cmp_u32(const void *a, const void *b) {
    uint32_t x = *(const uint32_t *)a, y = *(const uint32_t *)b;
    return x < y ? -1 : x > y;
}

static void *w_chase(void *a) {                    /* single-thread percentiles */
    struct tctx *c = a; pin(c->o->cpu_offset);
    size_t want = c->o->samples;
    uint32_t *out = c->samples_ns;
    uint8_t *p = c->base;
    for (size_t i = 0; i < 200000; i++) p = *(uint8_t **)p;   /* warm */
    /* measure timing overhead on an L1-hot pointer */
    uint8_t *selfp = (uint8_t *)&selfp; (void)selfp;
    uint64_t ovh_min = UINT64_MAX;
    static uint8_t *hot; hot = (uint8_t *)&hot;
    for (int i = 0; i < 10000; i++) {
        uint64_t t0 = rdtscp_ser();
        hot = *(uint8_t **)hot;
        _mm_lfence();
        uint64_t t1 = rdtscp_ser();
        if (t1 - t0 < ovh_min) ovh_min = t1 - t0;
    }
    size_t got = 0;
    uint64_t deadline = now_ns() + (uint64_t)c->o->secs * 1000000000ull;
    while (got < want && now_ns() < deadline) {
        for (int b = 0; b < 4096 && got < want; b++) {
            uint64_t t0 = rdtscp_ser();
            p = *(uint8_t **)p;
            _mm_lfence();
            uint64_t t1 = rdtscp_ser();
            uint64_t d = (t1 - t0 > ovh_min) ? t1 - t0 - ovh_min : 0;
            out[got++] = (uint32_t)((double)d * g_ns_per_tsc);
        }
    }
    c->nsamples = got; c->sink = (uint64_t)p; return NULL;
}

static void *w_daxstream(void *a) {
    struct tctx *c = a; pin(c->o->cpu_offset + c->tid);
    volatile uint64_t *end = (volatile uint64_t *)(c->base + c->len);
    uint64_t s = 0, bytes = 0;
    while (!*c->stop) {
        for (volatile uint64_t *q = (volatile uint64_t *)c->base; q < end; q += 8) {
            s += *q;
            if (__builtin_expect(*c->stop, 0)) break;
        }
        bytes += c->len;
    }
    c->bytes = bytes; c->sink = s; return NULL;
}

static void *w_daxchase(void *a) {                 /* read-only dependent loads */
    struct tctx *c = a; pin(c->o->cpu_offset);
    size_t mask = (c->len - 1) & ~(size_t)(LINE - 1); /* len must be pow2 */
    size_t want = c->o->samples, got = 0;
    uint32_t *out = c->samples_ns;
    uint64_t idx = 0, v = 0;
    for (int i = 0; i < 100000; i++) {             /* warm + establish chain */
        v = *(volatile uint64_t *)(c->base + idx);
        idx = ((idx + v + 0x9E3779B97F4A7C15ull) * 2654435761u) & mask;
    }
    uint64_t ovh_min = UINT64_MAX;
    for (int i = 0; i < 10000; i++) {              /* overhead: L1-hot load */
        uint64_t t0 = rdtscp_ser();
        v += *(volatile uint64_t *)c->base;
        _mm_lfence();
        uint64_t t1 = rdtscp_ser();
        if (t1 - t0 < ovh_min) ovh_min = t1 - t0;
    }
    uint64_t deadline = now_ns() + (uint64_t)c->o->secs * 1000000000ull;
    while (got < want && now_ns() < deadline) {
        for (int b = 0; b < 4096 && got < want; b++) {
            uint64_t t0 = rdtscp_ser();
            v = *(volatile uint64_t *)(c->base + idx);
            _mm_lfence();
            uint64_t t1 = rdtscp_ser();
            idx = ((idx + v + 0x9E3779B97F4A7C15ull) * 2654435761u) & mask;
            uint64_t d = (t1 - t0 > ovh_min) ? t1 - t0 - ovh_min : 0;
            out[got++] = (uint32_t)((double)d * g_ns_per_tsc);
        }
    }
    c->nsamples = got; c->sink = v; return NULL;
}

/* ---------- main ---------- */
static size_t parse_size(const char *s) {
    char *e; double v = strtod(s, &e); size_t m = 1;
    if (*e == 'K') m = 1UL << 10; else if (*e == 'M') m = 1UL << 20;
    else if (*e == 'G') m = 1UL << 30; else if (*e == 'T') m = 1UL << 40;
    return (size_t)(v * m);
}

int main(int argc, char **argv) {
    struct opts o = { .mode = NULL, .tag = "run", .daxpath = NULL,
        .node = 1, .threads = 1, .secs = 3, .cpu_offset = 0, .csv = 0,
        .size = 4UL << 30, .stride = 512, .chunk = 256, .offset = 0,
        .dax_offset = 0, .samples = 1000000 };
    for (int i = 1; i < argc; i++) {
        char *a = argv[i];
        if      (!strncmp(a, "--mode=", 7))       o.mode = a + 7;
        else if (!strncmp(a, "--node=", 7))       o.node = atoi(a + 7);
        else if (!strncmp(a, "--threads=", 10))   o.threads = atoi(a + 10);
        else if (!strncmp(a, "--secs=", 7))       o.secs = atoi(a + 7);
        else if (!strncmp(a, "--size=", 7))       o.size = parse_size(a + 7);
        else if (!strncmp(a, "--stride=", 9))     o.stride = parse_size(a + 9);
        else if (!strncmp(a, "--chunk=", 8))      o.chunk = parse_size(a + 8);
        else if (!strncmp(a, "--offset=", 9))     o.offset = parse_size(a + 9);
        else if (!strncmp(a, "--dax=", 6))        o.daxpath = a + 6;
        else if (!strncmp(a, "--dax-offset=", 13)) o.dax_offset = parse_size(a + 13);
        else if (!strncmp(a, "--samples=", 10))   o.samples = parse_size(a + 10);
        else if (!strncmp(a, "--cpu-offset=", 13)) o.cpu_offset = atoi(a + 13);
        else if (!strncmp(a, "--tag=", 6))        o.tag = a + 6;
        else if (!strcmp(a, "--csv"))             o.csv = 1;
        else { fprintf(stderr, "unknown arg %s\n", a); return 1; }
    }
    if (!o.mode) {
        fprintf(stderr, "usage: cxlprobe --mode=stream|stride|chase|daxstream|daxchase|daxstride\n"
            "  [--node=N] [--threads=T] [--secs=S] [--size=BYTES]\n"
            "  [--stride=B --chunk=B --offset=B]   (stride mode)\n"
            "  [--dax=/dev/daxX.Y --dax-offset=B]  (dax modes)\n"
            "  [--samples=N] [--cpu-offset=N] [--tag=NAME] [--csv]\n");
        return 1;
    }
    calibrate_tsc();

    int is_dax = !strncmp(o.mode, "dax", 3);
    int is_lat = !strcmp(o.mode, "chase") || !strcmp(o.mode, "daxchase");
    if (is_lat) o.threads = 1;

    uint8_t *base;
    if (is_dax) base = map_dax(o.daxpath, o.dax_offset, o.size);
    else        base = alloc_node(o.size, o.node);
    if (!strcmp(o.mode, "chase")) build_chain(base, o.size);

    volatile int stop = 0;
    struct tctx *ctx = calloc(o.threads, sizeof(*ctx));
    pthread_t *th = calloc(o.threads, sizeof(*th));
    size_t per = (o.size / o.threads) & ~(PG2M - 1);
    if (per == 0) per = o.size;
    uint32_t *samples = is_lat ? malloc(o.samples * sizeof(uint32_t)) : NULL;

    void *(*fn)(void *) =
        !strcmp(o.mode, "stream")    ? w_stream    :
        !strcmp(o.mode, "stride")    ? w_stride    :
        !strcmp(o.mode, "chase")     ? w_chase     :
        !strcmp(o.mode, "daxstream") ? w_daxstream :
        !strcmp(o.mode, "daxchase")  ? w_daxchase  :
        !strcmp(o.mode, "daxstride") ? w_stride    : NULL;
    if (!fn) { fprintf(stderr, "bad mode\n"); return 1; }

    uint64_t t_start = now_ns();
    for (int i = 0; i < o.threads; i++) {
        ctx[i] = (struct tctx){ .o = &o, .tid = i,
            .base = base + (is_lat ? 0 : (size_t)i * per),
            .len = is_lat ? o.size : per,
            .stop = &stop, .samples_ns = samples };
        pthread_create(&th[i], NULL, fn, &ctx[i]);
    }
    if (!is_lat) { sleep(o.secs); stop = 1; }
    for (int i = 0; i < o.threads; i++) pthread_join(th[i], NULL);
    double el = (now_ns() - t_start) / 1e9;

    if (is_lat) {
        size_t n = ctx[0].nsamples;
        qsort(samples, n, sizeof(uint32_t), cmp_u32);
        double mean = 0; for (size_t i = 0; i < n; i++) mean += samples[i];
        mean /= (double)n;
        #define PCT(p) samples[(size_t)((double)(n - 1) * (p))]
        if (o.csv)
            printf("%s,%s,%d,%zu,%.1f,%u,%u,%u,%u,%u,%u\n",
                o.tag, o.mode, o.node, n, mean,
                PCT(0.50), PCT(0.90), PCT(0.99), PCT(0.999), PCT(0.9999),
                samples[n - 1]);
        else
            printf("%s %s node=%d samples=%zu mean=%.1fns p50=%u p90=%u "
                   "p99=%u p99.9=%u p99.99=%u max=%u\n",
                o.tag, o.mode, o.node, n, mean,
                PCT(0.50), PCT(0.90), PCT(0.99), PCT(0.999), PCT(0.9999),
                samples[n - 1]);
    } else {
        uint64_t bytes = 0; for (int i = 0; i < o.threads; i++) bytes += ctx[i].bytes;
        double gibs = (double)bytes / el / (1UL << 30);
        if (o.csv)
            printf("%s,%s,%d,%d,%zu,%zu,%zu,%.2f,%.2f\n",
                o.tag, o.mode, o.node, o.threads, o.stride, o.offset,
                o.size, el, gibs);
        else
            printf("%s %s node=%d threads=%d stride=%zu offset=%zu "
                   "elapsed=%.2fs bw=%.2f GiB/s\n",
                o.tag, o.mode, o.node, o.threads, o.stride, o.offset, el, gibs);
    }
    return 0;
}
