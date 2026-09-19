#ifndef CXLP_INTERNAL_H
#define CXLP_INTERNAL_H
#include "cxlpath.h"
#include <stdatomic.h>

#define CXLP_MAGIC   0x4358504154483031ull   /* "CXPATH01" */
#define CXLP_PATHLEN 192

/* One entry per segment, in shared memory. `st` packs state (low 8 bits) and a generation
 * (upper 24 bits) so a stale claimer cannot release a segment that was recycled. */
typedef struct {
    _Atomic uint32_t st;
    _Atomic uint32_t owner;        /* pid */
    _Atomic uint64_t live;         /* committed live bytes (A3) */
    uint64_t         pad;
} cxlp_seg_t;

typedef struct {
    char     path[CXLP_PATHLEN];
    uint64_t offset, bytes;
    uint32_t kind, nseg;
    uint32_t first;                /* index of this device's first entry in the segment table */
    _Atomic uint32_t nfree;
    _Atomic uint32_t hint;         /* rotating scan start */
} cxlp_devmeta_t;

typedef struct {
    _Atomic uint64_t magic;        /* written LAST by the creator */
    uint32_t version, ndev;
    uint64_t meta_bytes;
    uint32_t nseg_total, pad;
    cxlp_devmeta_t dev[CXLP_MAX_DEVS];
    /* followed by cxlp_seg_t seg[nseg_total] */
} cxlp_meta_t;

typedef struct {
    cxlp_meta_t *meta;
    cxlp_seg_t  *seg;
    uint64_t     meta_bytes;
    void        *base[CXLP_MAX_DEVS];
    int          fd[CXLP_MAX_DEVS];
    uint32_t     pid;
} cxlp_state_t;

extern cxlp_state_t cxlp_g;
#define ST_STATE(x) ((x) & 0xffu)
#define ST_GEN(x)   ((x) >> 8)
#define ST_MAKE(gen, state) ((((gen) & 0xffffffu) << 8) | (uint32_t)(state))
#endif
