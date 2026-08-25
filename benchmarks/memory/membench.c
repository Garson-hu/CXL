/*
 * membench — minimal memory benchmark for DRAM vs CXL on c28.
 *
 * Modes:
 *   latency        pointer-chase idle latency
 *   stream-read    sequential read bandwidth
 *   stream-write   sequential write bandwidth
 *   random-read    random 64-byte gather bandwidth
 *   mixed          configurable read/write ratio bandwidth
 *   loaded-latency one pointer-chase victim + N-1 streaming aggressors
 *
 * Trustworthiness features:
 *   --verify-placement   sample pages with move_pages() and confirm node
 *   --strict-placement   exit non-zero if any sampled page is on wrong node
 *   pthread barrier so worker threads start measurement simultaneously
 *
 * CSV output to stdout. Errors and config dump to stderr.
 *
 * Built against libnuma. Refuses to allocate on a NUMA node with zero capacity
 * and prints the exact unblock command for c28.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <inttypes.h>
#include <pthread.h>
#include <sched.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>
#include <numa.h>
#include <numaif.h>
#include <immintrin.h>

#define CACHELINE 64
#define DEFAULT_DURATION_NS 3000000000ULL  /* 3 s */
#define VERIFY_SAMPLE_MAX 1024

enum mode {
    MODE_LATENCY,
    MODE_STREAM_READ,
    MODE_STREAM_WRITE,
    MODE_RANDOM_READ,
    MODE_MIXED,
    MODE_LOADED_LATENCY,
    MODE_STREAM_WRITE_NT,
    MODE_DUPLEX,
};

static const char *MODE_NAMES[] = {
    "latency", "stream-read", "stream-write",
    "random-read", "mixed", "loaded-latency",
    "stream-write-nt", "duplex"
};

struct opts {
    int node;
    enum mode mode;
    size_t size_bytes;        /* per-thread buffer size */
    int threads;
    int read_pct;             /* for mixed mode, 0..100 */
    uint64_t duration_ns;
    int csv;
    int verify_placement;
    int strict_placement;
    int cpu_offset;           /* first node-0 CPU index used for thread 0 */
    const char *tag;          /* CSV label */
    int write_threads;        /* duplex: how many of --threads are NT writers */
    int write_node;           /* duplex: node for writer buffers (-1 = --node) */
    int aggressor_write;      /* loaded-latency: aggressors NT-write, not read */
    int aggressor_node;       /* loaded-latency: aggressor buffer node (-1 = --node) */
};

struct thread_ctx {
    int tid;
    int cpu;
    void *buf;
    size_t buf_bytes;
    enum mode mode;
    int read_pct;
    uint64_t duration_ns;
    pthread_barrier_t *barrier;
    int is_aggressor;         /* loaded-latency: tid != 0 */
    int is_writer;            /* duplex writer / NT-writing aggressor */
    int mem_node;             /* node this thread's buffer actually lives on */
    /* outputs */
    uint64_t bytes;
    uint64_t ops;
    double seconds;
    double avg_latency_ns;
};

static uint64_t now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

static void die(const char *msg) {
    fprintf(stderr, "membench: %s\n", msg);
    exit(2);
}

/* Wrap syscall directly so we don't depend on a particular numaif/libnuma version. */
static long query_move_pages(pid_t pid, unsigned long count,
                             void **pages, const int *nodes,
                             int *status, int flags) {
    return syscall(SYS_move_pages, pid, count, pages, nodes, status, flags);
}

static void check_node_or_die(int node) {
    if (numa_available() < 0) die("libnuma unavailable");
    int maxn = numa_max_node();
    if (node < 0 || node > maxn) {
        fprintf(stderr,
                "membench: NUMA node %d is out of range (max=%d)\n",
                node, maxn);
        exit(3);
    }
    long long sz = numa_node_size64(node, NULL);
    if (sz <= 0) {
        fprintf(stderr,
                "membench: NUMA node %d has 0 MB online memory.\n"
                "  If this is the CXL node on c28 (likely node 1), an admin\n"
                "  still needs to run:\n"
                "    sudo daxctl online-memory dax2.0\n"
                "  Then re-check with: numactl --hardware\n", node);
        exit(4);
    }
}

/* Allocate a buffer bound to a NUMA node and pre-touch it. */
static void *alloc_on_node(int node, size_t bytes) {
    void *p = numa_alloc_onnode(bytes, node);
    if (!p) {
        fprintf(stderr,
                "membench: numa_alloc_onnode(node=%d, bytes=%zu) failed: %s\n",
                node, bytes, strerror(errno));
        exit(5);
    }
    /* Touch every page so it's actually backed before placement verification
     * and the timing loop. Linux faults pages lazily otherwise. */
    memset(p, 0, bytes);
    return p;
}

/* Sample up to VERIFY_SAMPLE_MAX pages from buf and query their NUMA node.
 * Returns number of pages on the wrong node (0 == all good, -1 on syscall error). */
static int verify_buffer_placement(void *buf, size_t bytes, int expected_node,
                                   int tid) {
    long page_size = sysconf(_SC_PAGESIZE);
    if (page_size <= 0) page_size = 4096;
    size_t n_pages = bytes / (size_t)page_size;
    if (n_pages == 0) return 0;

    size_t target = n_pages < VERIFY_SAMPLE_MAX ? n_pages : VERIFY_SAMPLE_MAX;
    size_t stride = n_pages / target;
    if (stride == 0) stride = 1;

    void **pages = calloc(target, sizeof(void *));
    int *status = calloc(target, sizeof(int));
    if (!pages || !status) { free(pages); free(status); return -1; }

    size_t count = 0;
    for (size_t i = 0; i < n_pages && count < target; i += stride) {
        pages[count++] = (char *)buf + (size_t)i * (size_t)page_size;
    }

    long rc = query_move_pages(0, count, pages, NULL, status, 0);
    if (rc < 0) {
        fprintf(stderr,
                "verify_placement(tid=%d): move_pages query failed: %s\n",
                tid, strerror(errno));
        free(pages); free(status);
        return -1;
    }

    int wrong = 0;
    int printed = 0;
    for (size_t i = 0; i < count; i++) {
        if (status[i] != expected_node) {
            wrong++;
            if (printed < 5) {
                fprintf(stderr,
                        "  wrong page (tid=%d): addr=%p got_node=%d expected=%d\n",
                        tid, pages[i], status[i], expected_node);
                printed++;
            }
        }
    }
    fprintf(stderr,
            "placement check (tid=%d): expected_node=%d sampled=%zu correct=%zu wrong=%d\n",
            tid, expected_node, count, count - (size_t)wrong, wrong);
    free(pages); free(status);
    return wrong;
}

static void pin_self(int cpu) {
    cpu_set_t set;
    CPU_ZERO(&set);
    CPU_SET(cpu, &set);
    if (sched_setaffinity(0, sizeof(set), &set) != 0)
        fprintf(stderr, "membench: warning: cannot pin to CPU %d\n", cpu);
}

/* Build a pointer-chase cycle (random permutation) over cache-line-sized slots. */
static void build_chase(void *buf, size_t bytes) {
    size_t n = bytes / CACHELINE;
    if (n < 2) die("buffer too small for chase");
    uint64_t **slots = (uint64_t **)buf;
    for (size_t i = 0; i < n; i++) {
        slots[i * (CACHELINE / sizeof(void *))] =
            (uint64_t *)&slots[((i + 1) % n) * (CACHELINE / sizeof(void *))];
    }
    size_t *perm = malloc(n * sizeof(size_t));
    if (!perm) die("oom perm");
    for (size_t i = 0; i < n; i++) perm[i] = i;
    unsigned int rng = 1;
    for (size_t i = n - 1; i > 1; i--) {
        rng = rng * 1103515245u + 12345u;
        size_t j = 1 + (rng % i);
        size_t t = perm[i];
        perm[i] = perm[j];
        perm[j] = t;
    }
    for (size_t i = 0; i < n; i++) {
        size_t cur = perm[i];
        size_t nxt = perm[(i + 1) % n];
        slots[cur * (CACHELINE / sizeof(void *))] =
            (uint64_t *)&slots[nxt * (CACHELINE / sizeof(void *))];
    }
    free(perm);
}

/* Pointer chase latency kernel. */
static void run_latency(struct thread_ctx *c) {
    build_chase(c->buf, c->buf_bytes);
    uint64_t **p = (uint64_t **)c->buf;
    uint64_t deadline = now_ns() + c->duration_ns;
    uint64_t ops = 0;
    for (int i = 0; i < 1000000; i++) p = (uint64_t **)*p;
    uint64_t t0 = now_ns();
    while ((ops & 0xFFFFF) || now_ns() < deadline) {
        p = (uint64_t **)*p;
        p = (uint64_t **)*p;
        p = (uint64_t **)*p;
        p = (uint64_t **)*p;
        p = (uint64_t **)*p;
        p = (uint64_t **)*p;
        p = (uint64_t **)*p;
        p = (uint64_t **)*p;
        ops += 8;
        if ((ops & 0xFFFFF) == 0 && now_ns() >= deadline) break;
    }
    uint64_t t1 = now_ns();
    asm volatile("" :: "r"(p));
    c->ops = ops;
    c->seconds = (t1 - t0) / 1e9;
    c->avg_latency_ns = (t1 - t0) / (double)ops;
    c->bytes = ops * CACHELINE;
}

static void run_stream_read(struct thread_ctx *c) {
    volatile uint64_t *p = (uint64_t *)c->buf;
    size_t n = c->buf_bytes / sizeof(uint64_t);
    uint64_t deadline = now_ns() + c->duration_ns;
    uint64_t bytes = 0;
    uint64_t acc = 0;
    uint64_t t0 = now_ns();
    while (now_ns() < deadline) {
        for (size_t i = 0; i + 8 <= n; i += 8) {
            acc += p[i + 0];
            acc += p[i + 1];
            acc += p[i + 2];
            acc += p[i + 3];
            acc += p[i + 4];
            acc += p[i + 5];
            acc += p[i + 6];
            acc += p[i + 7];
        }
        bytes += c->buf_bytes;
    }
    uint64_t t1 = now_ns();
    asm volatile("" :: "r"(acc));
    c->bytes = bytes;
    c->ops = bytes / CACHELINE;
    c->seconds = (t1 - t0) / 1e9;
}

static void run_stream_write(struct thread_ctx *c) {
    volatile uint64_t *p = (uint64_t *)c->buf;
    size_t n = c->buf_bytes / sizeof(uint64_t);
    uint64_t deadline = now_ns() + c->duration_ns;
    uint64_t bytes = 0;
    uint64_t v = 0xdeadbeefcafebabeULL;
    uint64_t t0 = now_ns();
    while (now_ns() < deadline) {
        for (size_t i = 0; i + 8 <= n; i += 8) {
            p[i + 0] = v;
            p[i + 1] = v;
            p[i + 2] = v;
            p[i + 3] = v;
            p[i + 4] = v;
            p[i + 5] = v;
            p[i + 6] = v;
            p[i + 7] = v;
        }
        bytes += c->buf_bytes;
        v++;
    }
    uint64_t t1 = now_ns();
    c->bytes = bytes;
    c->ops = bytes / CACHELINE;
    c->seconds = (t1 - t0) / 1e9;
}

/* Non-temporal (streaming) stores: MOVNTI bypasses the cache, so each written
 * line costs ONLY a host->device transfer — no RFO read, no writeback. This is
 * the kernel that isolates the write direction of the link. */
static void run_stream_write_nt(struct thread_ctx *c) {
    uint64_t *p = (uint64_t *)c->buf;
    size_t n = c->buf_bytes / sizeof(uint64_t);
    uint64_t deadline = now_ns() + c->duration_ns;
    uint64_t bytes = 0;
    long long v = 0x5ca1ab1e0ddba11LL;
    uint64_t t0 = now_ns();
    while (now_ns() < deadline) {
        for (size_t i = 0; i + 8 <= n; i += 8) {
            _mm_stream_si64((long long *)&p[i + 0], v);
            _mm_stream_si64((long long *)&p[i + 1], v);
            _mm_stream_si64((long long *)&p[i + 2], v);
            _mm_stream_si64((long long *)&p[i + 3], v);
            _mm_stream_si64((long long *)&p[i + 4], v);
            _mm_stream_si64((long long *)&p[i + 5], v);
            _mm_stream_si64((long long *)&p[i + 6], v);
            _mm_stream_si64((long long *)&p[i + 7], v);
        }
        _mm_sfence();
        bytes += c->buf_bytes;
        v++;
    }
    uint64_t t1 = now_ns();
    c->bytes = bytes;
    c->ops = bytes / CACHELINE;
    c->seconds = (t1 - t0) / 1e9;
}

static void run_random_read(struct thread_ctx *c) {
    volatile uint64_t *p = (uint64_t *)c->buf;
    size_t lines = c->buf_bytes / CACHELINE;
    size_t qwords_per_line = CACHELINE / sizeof(uint64_t);
    uint64_t deadline = now_ns() + c->duration_ns;
    uint64_t bytes = 0;
    uint64_t acc = 0;
    uint64_t rng = (uint64_t)c->tid * 0x9e3779b97f4a7c15ULL + 1;
    uint64_t t0 = now_ns();
    while (now_ns() < deadline) {
        for (int b = 0; b < 65536; b++) {
            rng = rng * 6364136223846793005ULL + 1442695040888963407ULL;
            size_t line = (rng >> 16) % lines;
            volatile uint64_t *q = p + line * qwords_per_line;
            acc += q[0]; acc += q[1]; acc += q[2]; acc += q[3];
            acc += q[4]; acc += q[5]; acc += q[6]; acc += q[7];
        }
        bytes += 65536ULL * CACHELINE;
    }
    uint64_t t1 = now_ns();
    asm volatile("" :: "r"(acc));
    c->bytes = bytes;
    c->ops = bytes / CACHELINE;
    c->seconds = (t1 - t0) / 1e9;
}

static void run_mixed(struct thread_ctx *c) {
    volatile uint64_t *p = (uint64_t *)c->buf;
    size_t lines = c->buf_bytes / CACHELINE;
    size_t qwords_per_line = CACHELINE / sizeof(uint64_t);
    uint64_t deadline = now_ns() + c->duration_ns;
    uint64_t bytes = 0;
    uint64_t acc = 0;
    uint64_t rng = (uint64_t)c->tid * 0x9e3779b97f4a7c15ULL + 1;
    int read_pct = c->read_pct;
    uint64_t t0 = now_ns();
    while (now_ns() < deadline) {
        for (int b = 0; b < 65536; b++) {
            rng = rng * 6364136223846793005ULL + 1442695040888963407ULL;
            size_t line = (rng >> 16) % lines;
            volatile uint64_t *q = p + line * qwords_per_line;
            if ((int)((rng >> 8) % 100) < read_pct) {
                acc += q[0]; acc += q[1]; acc += q[2]; acc += q[3];
                acc += q[4]; acc += q[5]; acc += q[6]; acc += q[7];
            } else {
                q[0] = acc; q[1] = acc + 1; q[2] = acc + 2; q[3] = acc + 3;
                q[4] = acc + 4; q[5] = acc + 5; q[6] = acc + 6; q[7] = acc + 7;
            }
        }
        bytes += 65536ULL * CACHELINE;
    }
    uint64_t t1 = now_ns();
    asm volatile("" :: "r"(acc));
    c->bytes = bytes;
    c->ops = bytes / CACHELINE;
    c->seconds = (t1 - t0) / 1e9;
}

static void *thread_main(void *arg) {
    struct thread_ctx *c = (struct thread_ctx *)arg;
    pin_self(c->cpu);
    /* All threads converge here before any timing starts. */
    if (c->barrier) pthread_barrier_wait(c->barrier);
    switch (c->mode) {
    case MODE_LATENCY:       run_latency(c); break;
    case MODE_STREAM_READ:   run_stream_read(c); break;
    case MODE_STREAM_WRITE:  run_stream_write(c); break;
    case MODE_RANDOM_READ:   run_random_read(c); break;
    case MODE_MIXED:         run_mixed(c); break;
    case MODE_LOADED_LATENCY:
        if (c->tid == 0)        run_latency(c);
        else if (c->is_writer)  run_stream_write_nt(c);
        else                    run_stream_read(c);
        break;
    case MODE_STREAM_WRITE_NT: run_stream_write_nt(c); break;
    case MODE_DUPLEX:
        if (c->is_writer) run_stream_write_nt(c);
        else              run_stream_read(c);
        break;
    }
    return NULL;
}

static enum mode parse_mode(const char *s) {
    for (size_t i = 0; i < sizeof(MODE_NAMES) / sizeof(MODE_NAMES[0]); i++)
        if (!strcmp(s, MODE_NAMES[i])) return (enum mode)i;
    fprintf(stderr, "membench: unknown mode '%s'\n", s);
    exit(2);
}

/* Accept decimal/hex byte counts with optional K/M/G/T suffix. */
static size_t parse_size(const char *s) {
    char *end = NULL;
    errno = 0;
    unsigned long long v = strtoull(s, &end, 0);
    if (errno != 0 || end == s) {
        fprintf(stderr, "membench: bad --size value '%s'\n", s);
        exit(2);
    }
    if (*end == '\0' || *end == 'B' || *end == 'b') {
        /* bytes */
    } else if (*end == 'K' || *end == 'k') {
        v <<= 10;
    } else if (*end == 'M' || *end == 'm') {
        v <<= 20;
    } else if (*end == 'G' || *end == 'g') {
        v <<= 30;
    } else if (*end == 'T' || *end == 't') {
        v <<= 40;
    } else {
        fprintf(stderr, "membench: bad size suffix '%c' in '%s'\n", *end, s);
        exit(2);
    }
    return (size_t)v;
}

/* Strict parser: only "R:W" with R+W == 100. */
static int parse_rw(const char *s) {
    int r = -1, w = -1;
    char tail = 0;
    int matched = sscanf(s, "%d:%d%c", &r, &w, &tail);
    if (matched < 2 || (matched == 3 && tail != 0)) {
        fprintf(stderr,
                "membench: --rw must be R:W where R+W=100 "
                "(e.g. --rw=70:30), got '%s'\n", s);
        exit(2);
    }
    if (r < 0 || w < 0 || r + w != 100) {
        fprintf(stderr,
                "membench: --rw R+W must equal 100 (got R=%d W=%d)\n", r, w);
        exit(2);
    }
    return r;
}

static void usage(const char *argv0) {
    fprintf(stderr,
"usage: %s --node=N --mode=MODE [--size=BYTES[K|M|G|T]] [--threads=T]\n"
"          [--rw=R:W] [--duration=SEC] [--tag=NAME] [--csv]\n"
"          [--verify-placement] [--strict-placement] [--cpu-offset=N]\n"
"          [--write-threads=W] [--write-node=N]\n"
"          [--aggressor-kind=read|write-nt] [--aggressor-node=N]\n"
"  modes: latency stream-read stream-write random-read mixed loaded-latency\n"
"         stream-write-nt duplex\n"
"  duplex: (threads - W) stream-readers on --node + W NT-writers on\n"
"          --write-node (default --node); CSV: write side in the\n"
"          aggressor_bandwidth column, read side = total - write\n"
"  loaded-latency: victim chase on --node; aggressors read or NT-write\n"
"          (--aggressor-kind) on --aggressor-node (default --node)\n"
"  --size default 1G (per thread); --threads default 1; --rw default 50:50\n"
"  --duration default 3 seconds; --csv prints one CSV row per run\n",
        argv0);
    exit(2);
}

int main(int argc, char **argv) {
    struct opts o = {
        .node = -1,
        .mode = MODE_LATENCY,
        .size_bytes = 1ULL << 30,  /* 1 GiB per thread */
        .threads = 1,
        .read_pct = 50,
        .duration_ns = DEFAULT_DURATION_NS,
        .csv = 0,
        .verify_placement = 0,
        .strict_placement = 0,
        .cpu_offset = 0,
        .tag = "run",
        .write_threads = 0,
        .write_node = -1,
        .aggressor_write = 0,
        .aggressor_node = -1,
    };
    int has_mode = 0;
    for (int i = 1; i < argc; i++) {
        const char *a = argv[i];
        if (!strncmp(a, "--node=", 7))             o.node = atoi(a + 7);
        else if (!strncmp(a, "--mode=", 7))        { o.mode = parse_mode(a + 7); has_mode = 1; }
        else if (!strncmp(a, "--size=", 7))        o.size_bytes = parse_size(a + 7);
        else if (!strncmp(a, "--threads=", 10))    o.threads = atoi(a + 10);
        else if (!strncmp(a, "--rw=", 5))          o.read_pct = parse_rw(a + 5);
        else if (!strncmp(a, "--duration=", 11))   o.duration_ns = (uint64_t)(atof(a + 11) * 1e9);
        else if (!strncmp(a, "--tag=", 6))         o.tag = a + 6;
        else if (!strcmp(a, "--csv"))              o.csv = 1;
        else if (!strncmp(a, "--cpu-offset=", 13)) o.cpu_offset = atoi(a + 13);
        else if (!strncmp(a, "--write-threads=", 16)) o.write_threads = atoi(a + 16);
        else if (!strncmp(a, "--write-node=", 13))    o.write_node = atoi(a + 13);
        else if (!strncmp(a, "--aggressor-node=", 17)) o.aggressor_node = atoi(a + 17);
        else if (!strncmp(a, "--aggressor-kind=", 17)) {
            const char *k = a + 17;
            if (!strcmp(k, "read"))          o.aggressor_write = 0;
            else if (!strcmp(k, "write-nt")) o.aggressor_write = 1;
            else { fprintf(stderr, "membench: --aggressor-kind must be read|write-nt\n"); exit(2); }
        }
        else if (!strcmp(a, "--verify-placement")) o.verify_placement = 1;
        else if (!strcmp(a, "--strict-placement")) { o.verify_placement = 1; o.strict_placement = 1; }
        else if (!strcmp(a, "--help") || !strcmp(a, "-h")) usage(argv[0]);
        else { fprintf(stderr, "membench: unknown arg %s\n", a); usage(argv[0]); }
    }
    if (o.node < 0 || !has_mode) usage(argv[0]);
    check_node_or_die(o.node);
    if (o.write_node < 0) o.write_node = o.node;
    if (o.aggressor_node < 0) o.aggressor_node = o.node;
    if (o.mode == MODE_DUPLEX) {
        if (o.write_threads < 0 || o.write_threads > o.threads)
            die("--write-threads must be within 0..--threads for duplex");
        check_node_or_die(o.write_node);
    }
    if (o.mode == MODE_LOADED_LATENCY) check_node_or_die(o.aggressor_node);

    /* Choose CPUs from the CPU-bearing node (node 0 on c28). */
    struct bitmask *cpus_node0 = numa_allocate_cpumask();
    if (numa_node_to_cpus(0, cpus_node0) != 0) die("numa_node_to_cpus(0) failed");
    int cpu_max = numa_num_configured_cpus();
    int *cpu_list = malloc(sizeof(int) * cpu_max);
    int cpu_count = 0;
    for (int c = 0; c < cpu_max; c++) {
        if (numa_bitmask_isbitset(cpus_node0, c)) cpu_list[cpu_count++] = c;
    }
    if (cpu_count == 0) die("no CPUs on node 0?");

    pthread_t *th = calloc(o.threads, sizeof(pthread_t));
    struct thread_ctx *ctx = calloc(o.threads, sizeof(struct thread_ctx));

    /* Allocate + pre-touch every per-thread buffer. */
    for (int i = 0; i < o.threads; i++) {
        ctx[i].tid = i;
        ctx[i].cpu = cpu_list[(o.cpu_offset + i) % cpu_count];
        ctx[i].buf_bytes = o.size_bytes;
        ctx[i].mode = o.mode;
        ctx[i].read_pct = o.read_pct;
        ctx[i].duration_ns = o.duration_ns;
        ctx[i].is_aggressor = (o.mode == MODE_LOADED_LATENCY && i != 0);
        ctx[i].is_writer =
            (o.mode == MODE_DUPLEX && i >= o.threads - o.write_threads) ||
            (o.mode == MODE_LOADED_LATENCY && i != 0 && o.aggressor_write) ||
            (o.mode == MODE_STREAM_WRITE || o.mode == MODE_STREAM_WRITE_NT);
        ctx[i].mem_node = o.node;
        if (o.mode == MODE_DUPLEX && ctx[i].is_writer)
            ctx[i].mem_node = o.write_node;
        if (o.mode == MODE_LOADED_LATENCY && i != 0)
            ctx[i].mem_node = o.aggressor_node;
        ctx[i].buf = alloc_on_node(ctx[i].mem_node, ctx[i].buf_bytes);
    }

    /* Config dump (always to stderr; quiet enough to live alongside CSV stdout). */
    fprintf(stderr,
            "membench config:\n"
            "  mode=%s\n  node=%d\n  threads=%d\n  bytes_per_thread=%zu\n"
            "  duration_sec=%.3f\n",
            MODE_NAMES[o.mode], o.node, o.threads, o.size_bytes,
            o.duration_ns / 1e9);
    if (o.mode == MODE_MIXED)
        fprintf(stderr, "  read_pct=%d\n", o.read_pct);
    if (o.mode == MODE_DUPLEX)
        fprintf(stderr, "  write_threads=%d\n  write_node=%d\n",
                o.write_threads, o.write_node);
    if (o.mode == MODE_LOADED_LATENCY)
        fprintf(stderr, "  aggressor_kind=%s\n  aggressor_node=%d\n",
                o.aggressor_write ? "write-nt" : "read", o.aggressor_node);
    fprintf(stderr,
            "  verify_placement=%d\n  strict_placement=%d\n  cpu_offset=%d\n",
            o.verify_placement, o.strict_placement, o.cpu_offset);
    for (int i = 0; i < o.threads; i++)
        fprintf(stderr, "  thread %d cpu %d\n", i, ctx[i].cpu);

    /* Placement verification — runs AFTER memset, BEFORE timing. */
    if (o.verify_placement) {
        int total_wrong = 0;
        for (int i = 0; i < o.threads; i++) {
            int wrong = verify_buffer_placement(ctx[i].buf, ctx[i].buf_bytes,
                                                ctx[i].mem_node, i);
            if (wrong < 0) {
                fprintf(stderr,
                        "membench: placement verification syscall failed\n");
                if (o.strict_placement) exit(6);
            } else {
                total_wrong += wrong;
            }
        }
        if (total_wrong > 0 && o.strict_placement) {
            fprintf(stderr,
                    "membench: --strict-placement set and %d pages were on the "
                    "wrong node; exiting non-zero.\n", total_wrong);
            exit(7);
        }
    }

    /* Barrier so all worker threads start the kernel together. */
    pthread_barrier_t barrier;
    if (pthread_barrier_init(&barrier, NULL, (unsigned)o.threads) != 0)
        die("pthread_barrier_init failed");
    for (int i = 0; i < o.threads; i++) ctx[i].barrier = &barrier;

    uint64_t global_t0 = now_ns();
    for (int i = 0; i < o.threads; i++) {
        if (pthread_create(&th[i], NULL, thread_main, &ctx[i]) != 0)
            die("pthread_create failed");
    }
    for (int i = 0; i < o.threads; i++) pthread_join(th[i], NULL);
    uint64_t global_t1 = now_ns();
    pthread_barrier_destroy(&barrier);
    double total_sec = (global_t1 - global_t0) / 1e9;

    /* Aggregate global metrics. */
    uint64_t total_bytes = 0, total_ops = 0;
    double sum_latency = 0;
    int latency_threads = 0;
    /* Loaded-latency split. */
    uint64_t agg_bytes = 0;
    double max_kernel_sec = 0;       /* common elapsed time for BW reporting */
    double victim_latency_ns = 0;
    uint64_t read_bytes = 0, write_bytes = 0;   /* duplex split */
    for (int i = 0; i < o.threads; i++) {
        total_bytes += ctx[i].bytes;
        total_ops += ctx[i].ops;
        if (ctx[i].seconds > max_kernel_sec) max_kernel_sec = ctx[i].seconds;
        if (o.mode == MODE_DUPLEX) {
            if (ctx[i].is_writer) write_bytes += ctx[i].bytes;
            else                  read_bytes  += ctx[i].bytes;
        }
        if (ctx[i].mode == MODE_LATENCY ||
            (ctx[i].mode == MODE_LOADED_LATENCY && ctx[i].tid == 0)) {
            sum_latency += ctx[i].avg_latency_ns;
            latency_threads++;
        }
        if (o.mode == MODE_LOADED_LATENCY) {
            if (ctx[i].tid == 0) {
                victim_latency_ns = ctx[i].avg_latency_ns;
            } else {
                agg_bytes += ctx[i].bytes;
            }
        }
    }
    /* Existing bandwidth_gib_s column keeps its semantics: total bytes / global
     * wall time. Includes pthread_create/join/barrier overhead — a small amount
     * for long runs but enough to make it strictly < the new total_bandwidth_gib_s
     * for short runs. */
    double bw_gbps = (total_sec > 0) ? (total_bytes / total_sec) / (1ULL << 30) : 0.0;
    double avg_lat = latency_threads ? sum_latency / latency_threads : 0.0;

    /* For the loaded-latency split: aggressor_bandwidth and total_bandwidth use
     * the SAME denominator = max per-thread kernel-loop seconds, so that
     *   total_bandwidth_gib_s >= aggressor_bandwidth_gib_s
     * is structurally guaranteed (total adds the victim's tiny pointer-chase
     * traffic to the aggressors' streaming traffic, on a common time base). */
    double agg_bw_gbps = 0.0, total_bw_gbps = 0.0;
    if (o.mode == MODE_LOADED_LATENCY && max_kernel_sec > 0) {
        agg_bw_gbps   = (agg_bytes  / max_kernel_sec) / (1ULL << 30);
        total_bw_gbps = (total_bytes / max_kernel_sec) / (1ULL << 30);
    } else {
        /* Non-loaded modes: keep the new columns sensible but don't claim
         * a separate "aggressor" exists. */
        victim_latency_ns = (o.mode == MODE_LATENCY) ? avg_lat : 0.0;
        agg_bw_gbps = 0.0;
        total_bw_gbps = (max_kernel_sec > 0)
            ? (total_bytes / max_kernel_sec) / (1ULL << 30) : 0.0;
    }
    /* Duplex split: read/write sides on the common time base; the write side
     * is exported in the aggressor_bandwidth CSV column. */
    double read_bw_gbps = 0.0, write_bw_gbps = 0.0;
    if (o.mode == MODE_DUPLEX && max_kernel_sec > 0) {
        read_bw_gbps  = (read_bytes  / max_kernel_sec) / (1ULL << 30);
        write_bw_gbps = (write_bytes / max_kernel_sec) / (1ULL << 30);
        agg_bw_gbps = write_bw_gbps;
    }

    if (o.csv) {
        if (!strncmp(o.tag, "header:", 7)) {
            printf("tag,node,mode,threads,size_per_thread_bytes,read_pct,"
                   "duration_sec,total_bytes,bandwidth_gib_s,avg_latency_ns,"
                   "victim_latency_ns,aggressor_bandwidth_gib_s,total_bandwidth_gib_s\n");
            fflush(stdout);
        }
        printf("%s,%d,%s,%d,%zu,%d,%.3f,%" PRIu64
               ",%.3f,%.3f,%.3f,%.3f,%.3f\n",
               o.tag, o.node, MODE_NAMES[o.mode], o.threads, o.size_bytes,
               o.read_pct, total_sec, total_bytes, bw_gbps, avg_lat,
               victim_latency_ns, agg_bw_gbps, total_bw_gbps);
    } else {
        printf("mode=%s node=%d threads=%d size=%zu MiB/thread\n",
               MODE_NAMES[o.mode], o.node, o.threads, o.size_bytes >> 20);
        printf("  wall_time      = %.3f s\n", total_sec);
        printf("  total_bytes    = %" PRIu64 "\n", total_bytes);
        printf("  bandwidth      = %.3f GiB/s\n", bw_gbps);
        if (latency_threads)
            printf("  avg_latency    = %.2f ns (avg of %d thread(s))\n",
                   avg_lat, latency_threads);
        if (o.mode == MODE_DUPLEX) {
            printf("  read_bw        = %.3f GiB/s (%d reader thread(s))\n",
                   read_bw_gbps, o.threads - o.write_threads);
            printf("  write_bw       = %.3f GiB/s (%d NT-writer thread(s) -> node %d)\n",
                   write_bw_gbps, o.write_threads, o.write_node);
            printf("  duplex_total   = %.3f GiB/s (same denominator)\n",
                   total_bw_gbps);
        }
        if (o.mode == MODE_LOADED_LATENCY) {
            printf("  victim_latency = %.2f ns (thread 0 only)\n",
                   victim_latency_ns);
            printf("  aggressor_bw   = %.3f GiB/s "
                   "(%d aggressor thread(s), bytes / max_kernel_sec)\n",
                   agg_bw_gbps, o.threads - 1);
            printf("  total_bw       = %.3f GiB/s "
                   "(all threads, same denominator)\n", total_bw_gbps);
            printf("  max_kernel_sec = %.4f s\n", max_kernel_sec);
        }
    }
    for (int i = 0; i < o.threads; i++) numa_free(ctx[i].buf, ctx[i].buf_bytes);
    free(ctx); free(th); free(cpu_list); numa_free_cpumask(cpus_node0);
    (void)total_ops;
    return 0;
}
