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

#define CXLP_NIL      UINT32_MAX
#define CXLP_KEY_TOMB UINT64_MAX
enum { OBJ_EMPTY = 0, OBJ_CREATING = 1, OBJ_COMMITTED = 2, OBJ_TOMB = 3 };

typedef struct {                   /* one extent of an object */
    _Atomic uint32_t used;
    uint32_t dev, seg, off, len;
    _Atomic uint32_t next;
} cxlp_ext_t;

typedef struct {                   /* open-addressing hash slot */
    _Atomic uint64_t key;
    _Atomic uint32_t state;
    uint32_t owner, klass;
    _Atomic uint32_t head, tail, next_pad;
    _Atomic uint64_t bytes;
} cxlp_obj_t;

#define CXLP_BS_MAXSEG 2048          /* 64 GiB per set */
typedef struct {
    _Atomic uint64_t client;       /* 0 = slot free */
    _Atomic uint32_t state[2];
    _Atomic uint32_t drained[2];
    _Atomic uint64_t version[2];
    uint32_t dev[2], nseg[2];
    uint64_t bytes[2];
    uint64_t segtab_off[2];        /* offset in metadata of uint32_t seg[nseg] */
} cxlp_bufset_t;

typedef struct {
    _Atomic uint64_t magic;        /* written LAST by the creator */
    uint32_t version, ndev;
    uint64_t meta_bytes;
    uint32_t nseg_total, nobj;     /* nobj: power of two */
    uint32_t next_cap; _Atomic uint32_t ext_hint;
    uint64_t obj_off, ext_off;     /* byte offsets of the tables inside the metadata */
    uint64_t bs_segtab_off;        /* CXLP_MAX_BUFSETS * 2 * CXLP_BS_MAXSEG uint32_t */
    cxlp_bufset_t bufset[16];
    cxlp_devmeta_t dev[CXLP_MAX_DEVS];
    /* followed by cxlp_seg_t seg[nseg_total], cxlp_obj_t obj[nobj], cxlp_ext_t ext[next_cap] */
} cxlp_meta_t;

typedef struct {
    cxlp_meta_t *meta;
    cxlp_seg_t  *seg;
    cxlp_obj_t  *obj;
    cxlp_ext_t  *ext;
    uint64_t     meta_bytes;
    void        *base[CXLP_MAX_DEVS];
    int          fd[CXLP_MAX_DEVS];
    uint32_t     pid;
} cxlp_state_t;

extern cxlp_state_t cxlp_g;
void cxlp_seg_try_free(int dev, uint32_t seg);
void cxlp_seg_force_seal(int dev, uint32_t seg, uint64_t live);
#define ST_STATE(x) ((x) & 0xffu)
#define ST_GEN(x)   ((x) >> 8)
#define ST_MAKE(gen, state) ((((gen) & 0xffffffu) << 8) | (uint32_t)(state))
#endif
