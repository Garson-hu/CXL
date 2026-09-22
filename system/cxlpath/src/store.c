/* Component A, part 1: device layer + shared segment table (steps A1, A2). */
#define _GNU_SOURCE
#include "internal.h"
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/stat.h>

cxlp_state_t cxlp_g;

static void meta_path(const char *name, char *out, size_t n) { snprintf(out, n, "/dev/shm/cxlpath.%s", name); }

static int map_devices(void) {
    cxlp_meta_t *m = cxlp_g.meta;
    for (uint32_t d = 0; d < m->ndev; d++) {
        /* The DRAM pool is a tmpfs file the store creates itself; CXL devices must exist. */
        int fd = open(m->dev[d].path, m->dev[d].kind == CXLP_DEV_DRAM ? (O_RDWR | O_CREAT) : O_RDWR, 0600);
        if (fd < 0) { fprintf(stderr, "cxlpath: open %s: %s\n", m->dev[d].path, strerror(errno)); return -1; }
        if (m->dev[d].kind == CXLP_DEV_DRAM) {
            /* The DRAM pool is a tmpfs file, i.e. 4 KiB pages (shmem THP needs root). Allocate its pages
             * once here and map them populated, so no page fault or zeroing ever sits on the data path
             * (first-touch faults made a spilled 32 MiB chunk ~5x slower than a CXL chunk). */
            struct stat sb; uint64_t need = m->dev[d].offset + m->dev[d].bytes;
            if (fstat(fd, &sb) == 0 && (uint64_t)sb.st_size < need) {
                if (ftruncate(fd, (off_t)need) != 0 || fallocate(fd, 0, (off_t)m->dev[d].offset, (off_t)m->dev[d].bytes) != 0) { close(fd); return -1; }
            }
        }
        void *p = mmap(NULL, (size_t)m->dev[d].nseg * CXLP_SEG_BYTES, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_POPULATE, fd,
                       (off_t)m->dev[d].offset);
        if (p == MAP_FAILED) { fprintf(stderr, "cxlpath: mmap %s: %s\n", m->dev[d].path, strerror(errno)); close(fd); return -1; }
        cxlp_g.base[d] = p; cxlp_g.fd[d] = fd;
    }
    return 0;
}

static void bind_tables(void) {
    cxlp_g.obj = (cxlp_obj_t *)((char *)cxlp_g.meta + cxlp_g.meta->obj_off);
    cxlp_g.ext = (cxlp_ext_t *)((char *)cxlp_g.meta + cxlp_g.meta->ext_off);
}

static int map_meta(int fd, uint64_t bytes) {
    void *p = mmap(NULL, bytes, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (p == MAP_FAILED) return -1;
    cxlp_g.meta = p; cxlp_g.meta_bytes = bytes; cxlp_g.seg = (cxlp_seg_t *)((char *)p + sizeof(cxlp_meta_t));
    cxlp_g.obj = NULL; cxlp_g.ext = NULL;       /* set by bind_tables() once the header is valid */
    cxlp_g.pid = (uint32_t)getpid();
    return 0;
}

int cxlp_attach(const char *name) {
    char path[256]; meta_path(name, path, sizeof path);
    int fd = open(path, O_RDWR);
    if (fd < 0) return -1;
    struct stat sb;
    for (int tries = 0; tries < 5000; tries++) {           /* wait for the creator to finish */
        if (fstat(fd, &sb) == 0 && (uint64_t)sb.st_size >= sizeof(cxlp_meta_t)) {
            if (map_meta(fd, (uint64_t)sb.st_size) == 0) {
                uint64_t mg = atomic_load(&cxlp_g.meta->magic);
                if (mg == CXLP_MAGIC && cxlp_g.meta->meta_bytes == (uint64_t)sb.st_size) {
                    close(fd); bind_tables(); return map_devices();
                }
                munmap(cxlp_g.meta, cxlp_g.meta_bytes); cxlp_g.meta = NULL;
                /* A different layout version is not "still being created": say so at once. A client that
                 * links an old copy of this library must not wait 5 s and then fall back silently. */
                if (mg != 0 && (mg >> 8) == (CXLP_MAGIC >> 8)) {
                    fprintf(stderr, "cxlpath: store '%s' has metadata layout %c, this library expects %c — rebuild the client against the current libcxlpath\n", name, (int)(mg & 0xff), (int)(CXLP_MAGIC & 0xff));
                    close(fd); return -2;
                }
            }
        }
        usleep(1000);
    }
    close(fd); return -1;
}

int cxlp_open(const cxlp_config_t *cfg) {
    if (cfg->ndev < 1 || cfg->ndev > CXLP_MAX_DEVS) return -1;
    char path[256]; meta_path(cfg->name, path, sizeof path);
    int fd = open(path, O_RDWR | O_CREAT | O_EXCL, 0600);
    if (fd < 0) { if (errno == EEXIST) return cxlp_attach(cfg->name); return -1; }
    uint32_t total = 0, nseg[CXLP_MAX_DEVS];
    for (int d = 0; d < cfg->ndev; d++) { nseg[d] = (uint32_t)(cfg->dev[d].bytes / CXLP_SEG_BYTES); total += nseg[d]; }
    /* object slots: 8 per segment (KV blocks are tens of MiB; small objects share segments),
     * at least 4096, power of two; extents: 4 per slot. tmpfs pages are allocated on touch. */
    uint32_t want = cfg->obj_slots ? cfg->obj_slots : total * 8u, nobj = 4096; while (nobj < want) nobj <<= 1;
    uint32_t next_cap = nobj * 4u;
    uint64_t obj_off = (sizeof(cxlp_meta_t) + (uint64_t)total * sizeof(cxlp_seg_t) + 63) & ~63ull;
    uint64_t ext_off = (obj_off + (uint64_t)nobj * sizeof(cxlp_obj_t) + 63) & ~63ull;
    uint64_t bs_off = (ext_off + (uint64_t)next_cap * sizeof(cxlp_ext_t) + 63) & ~63ull;
    uint64_t bytes = bs_off + (uint64_t)CXLP_MAX_BUFSETS * 2 * CXLP_BS_MAXSEG * sizeof(uint32_t);
    bytes = (bytes + 4095) & ~4095ull;
    if (ftruncate(fd, (off_t)bytes) != 0 || map_meta(fd, bytes) != 0) { close(fd); unlink(path); return -1; }
    close(fd);
    cxlp_meta_t *m = cxlp_g.meta;                          /* tmpfs pages start zeroed: all FREE */
    m->version = 5; m->ndev = (uint32_t)cfg->ndev; m->meta_bytes = bytes; m->nseg_total = total;
    m->nobj = nobj; m->next_cap = next_cap; m->obj_off = obj_off; m->ext_off = ext_off; m->bs_segtab_off = bs_off; bind_tables();
    atomic_store(&m->policy.force_spill16, -1); atomic_store(&m->policy.bound_x1000, 1100); atomic_store(&m->drain_lowspace_pct, 25); atomic_store(&m->drain_lag_ms, 2000);
    uint32_t first = 0;
    for (int d = 0; d < cfg->ndev; d++) {
        snprintf(m->dev[d].path, CXLP_PATHLEN, "%s", cfg->dev[d].path);
        m->dev[d].offset = cfg->dev[d].offset; m->dev[d].bytes = (uint64_t)nseg[d] * CXLP_SEG_BYTES;
        m->dev[d].kind = cfg->dev[d].kind; m->dev[d].nseg = nseg[d]; m->dev[d].first = first;
        atomic_store(&m->dev[d].nfree, nseg[d]); first += nseg[d];
    }
    if (map_devices() != 0) { unlink(path); return -1; }
    atomic_store(&m->magic, CXLP_MAGIC);
    return 0;
}

void cxlp_close(void) {
    if (!cxlp_g.meta) return;
    for (uint32_t d = 0; d < cxlp_g.meta->ndev; d++) {
        if (cxlp_g.base[d]) munmap(cxlp_g.base[d], (size_t)cxlp_g.meta->dev[d].nseg * CXLP_SEG_BYTES);
        if (cxlp_g.fd[d] > 0) close(cxlp_g.fd[d]);
    }
    munmap(cxlp_g.meta, cxlp_g.meta_bytes);
    memset(&cxlp_g, 0, sizeof cxlp_g);
}

int cxlp_destroy(const char *name) { char path[256]; meta_path(name, path, sizeof path); return unlink(path); }

int      cxlp_ndev(void)            { return (int)cxlp_g.meta->ndev; }
uint32_t cxlp_dev_nseg(int dev)     { return cxlp_g.meta->dev[dev].nseg; }
uint32_t cxlp_dev_free(int dev)     { return atomic_load(&cxlp_g.meta->dev[dev].nfree); }
cxlp_devkind_t cxlp_dev_kind(int dev) { return (cxlp_devkind_t)cxlp_g.meta->dev[dev].kind; }
void    *cxlp_seg_ptr(int dev, uint32_t seg) { return (char *)cxlp_g.base[dev] + (size_t)seg * CXLP_SEG_BYTES; }
uint32_t cxlp_seg_owner(int dev, uint32_t seg) { return atomic_load(&cxlp_g.seg[cxlp_g.meta->dev[dev].first + seg].owner); }

uint32_t cxlp_seg_claim(int dev, cxlp_segstate_t as) {
    cxlp_devmeta_t *dm = &cxlp_g.meta->dev[dev];
    cxlp_seg_t *tab = cxlp_g.seg + dm->first;
    uint32_t n = dm->nseg, start = atomic_fetch_add(&dm->hint, 1) % (n ? n : 1);
    for (uint32_t k = 0; k < n; k++) {
        uint32_t i = start + k; if (i >= n) i -= n;
        uint32_t cur = atomic_load(&tab[i].st);
        if (ST_STATE(cur) != CXLP_SEG_FREE) continue;
        if (atomic_compare_exchange_strong(&tab[i].st, &cur, ST_MAKE(ST_GEN(cur) + 1, as))) {
            atomic_store(&tab[i].owner, cxlp_g.pid);
            atomic_store(&tab[i].live, 0);
            if (dm->kind == CXLP_DEV_DRAM) atomic_store(&tab[i].touched, 1);
            atomic_fetch_sub(&dm->nfree, 1);
            return i;
        }
    }
    return CXLP_NO_SEG;
}

/* Every way back to FREE goes through FREEING, which exactly one thread can enter: the owner
 * field is cleared while nobody else can claim the segment (clearing it after FREE would erase
 * the next claimer's pid — the bug the A2 stress test found). */
int cxlp_seg_to_free(int dev, uint32_t seg, int only_if_sealed_empty) {
    cxlp_devmeta_t *dm = &cxlp_g.meta->dev[dev];
    cxlp_seg_t *s = cxlp_g.seg + dm->first + seg;
    uint32_t cur = atomic_load(&s->st);
    for (;;) {
        uint32_t state = ST_STATE(cur);
        if (state == CXLP_SEG_FREE || state == CXLP_SEG_FREEING) return 0;
        if (only_if_sealed_empty && (state != CXLP_SEG_SEALED || atomic_load(&s->live) != 0)) return 0;
        if (atomic_compare_exchange_weak(&s->st, &cur, ST_MAKE(ST_GEN(cur), CXLP_SEG_FREEING))) break;
    }
    atomic_store(&s->owner, 0);
    atomic_store(&s->st, ST_MAKE(ST_GEN(cur), CXLP_SEG_FREE));
    atomic_fetch_add(&dm->nfree, 1);
    cxlp_policy_wake();
    return 1;
}

void cxlp_seg_release(int dev, uint32_t seg) { cxlp_seg_to_free(dev, seg, 0); }
