#ifndef CXLP_INTERNAL_H
#define CXLP_INTERNAL_H
#include "cxlpath.h"
#include <stdatomic.h>
#include <time.h>

#define CXLP_MAGIC   0x435850415448303Cull   /* "CXPATH0<" */
#define CXLP_PATHLEN 192
#define CXLP_NIL      UINT32_MAX
#define CXLP_KEY_TOMB UINT64_MAX
#define CXLP_SEG_FREEING 4                    /* internal: exactly one thread is freeing it */
enum { OBJ_EMPTY = 0, OBJ_CREATING = 1, OBJ_COMMITTED = 2, OBJ_TOMB = 3 };

/* One entry per segment, in shared memory. `st` packs state (low 8 bits) and a generation
 * (upper 24 bits). */
typedef struct {
    _Atomic uint32_t st;
    _Atomic uint32_t owner;        /* pid */
    _Atomic uint64_t live;         /* reserved + committed live bytes */
    _Atomic uint32_t touched;      /* DRAM pool: pages may be resident, daemon trims when FREE */
    uint32_t         pad;
} cxlp_seg_t;

typedef struct {
    char     path[CXLP_PATHLEN];
    uint64_t offset, bytes;
    uint32_t kind, nseg;
    uint32_t first;                /* index of this device's first entry in the segment table */
    _Atomic uint32_t nfree;
    _Atomic uint32_t hint;         /* rotating scan start */
} cxlp_devmeta_t;

typedef struct {                   /* one extent of an object */
    _Atomic uint32_t used;
    uint32_t dev, seg, off, len;   /* dev/seg/off change only under the object's seqlock (promotion) */
    _Atomic uint32_t next;
    uint32_t obj;                  /* owning object slot */
    _Atomic uint32_t rd_cur, rd_prev, rd_bucket;   /* reads in the current / previous bucket */
    _Atomic uint32_t queued;       /* waiting in the promotion ring */
    _Atomic uint32_t drain_state;  /* 0 pending, 1 being written, 2 on NVMe */
    uint64_t obj_off;              /* offset of this extent inside its object */
} cxlp_ext_t;

typedef struct {                   /* open-addressing hash slot */
    _Atomic uint64_t key;
    _Atomic uint32_t state;
    uint32_t owner, klass;
    _Atomic uint32_t head, tail, flags;
    _Atomic uint64_t bytes;
    _Atomic uint32_t pins;         /* readers holding pointers into this object */
    _Atomic uint32_t seq;          /* seqlock: odd while extents are being relocated */
    _Atomic uint32_t drain_idx;    /* drain descriptor, CXLP_NIL = never drained */
    _Atomic uint32_t drained;      /* 1 = complete on NVMe and fsynced */
    uint64_t chain, version;       /* checkpoint version chain (0 = none): older drained versions are reclaimed by the runtime */
    _Atomic uint64_t gen;          /* commit order: of several committed objects under one key the highest gen is THE object */
    _Atomic uint32_t superseded;   /* a newer writer of the same key exists: drain cancelled, released when unpinned */
    uint32_t drain_whole;          /* the object owns its file: truncate to the object's size when drained */
} cxlp_obj_t;

#define CXLP_NDRAIN 1024
typedef struct {                   /* where an object goes on NVMe (Component D) */
    _Atomic uint32_t used;
    uint32_t obj;
    uint64_t file_off;
    char path[240];
} cxlp_drain_t;

#define CXLP_BS_MAXSEG 2048          /* 64 GiB per set */
typedef struct {
    _Atomic uint64_t client;       /* 0 = slot free */
    _Atomic uint32_t state[2];
    _Atomic uint32_t drained[2];
    _Atomic uint64_t version[2];
    uint32_t dev[2], nseg[2];
    uint64_t bytes[2];
    uint64_t segtab_off[2];
    char     drain_path[2][240];
    _Atomic uint32_t drain_armed[2], drain_next[2], drain_done[2];
    uint64_t used[2];              /* bytes of the set that hold data: only these are drained */
} cxlp_bufset_t;

/* Shared policy page (Component B). Written by the background process, READ by reserve():
 * no IPC and no syscall on the data path. The ledger is written by the writers. */
typedef struct {
    _Atomic uint32_t daemon_pid;
    _Atomic uint32_t bound_x1000;              /* 1100 = probe may be 1.10 x idle            */
    _Atomic uint64_t heartbeat_ns;             /* CLOCK_MONOTONIC                             */
    _Atomic uint64_t epoch;
    _Atomic uint32_t spill16[CXLP_NSTREAM];    /* CPU sources: n of every 16 new segments -> DRAM */
    _Atomic uint32_t staged16[CXLP_NSTREAM];   /* GPU sources: n of every 16 chunks -> staged path */
    _Atomic uint32_t dram_ok;                  /* probe within bound: DRAM may take overflow / promotions */
    _Atomic uint32_t cxl_full, gpu_full;
    _Atomic uint32_t probe_x10, base_x10;      /* ns per load x 10 (epoch mean, idle baseline) */
    _Atomic int32_t  force_spill16;            /* admin/test knob: >= 0 overrides the controller */
    _Atomic uint32_t waiters, free_event;      /* blocked reserve() calls sleep on free_event  */
    _Atomic uint64_t reserve_seq;              /* activity indicator                           */
    struct { _Atomic uint64_t bytes, ns; } led[CXLP_MAX_DEVS];        /* timed copies per device */
    struct { _Atomic uint64_t bytes; } sled[CXLP_NSTREAM];            /* bytes per stream        */
    struct { _Atomic uint64_t bytes, ns; } gpu_direct, gpu_staged;    /* GPU paths (B5)          */
    _Atomic uint64_t gpu_link_bps;             /* what the GPU source can push (calibrated)    */
    /* Component C: promotion threshold per consumer type (0 = never), published by the daemon */
    _Atomic uint32_t k_read[2];                /* [CXLP_CONSUMER_CPU], [CXLP_CONSUMER_GPU]     */
    _Atomic uint32_t read_bucket_ms;           /* window = two buckets; default 300000 (10 min) */
    _Atomic uint64_t gpu_rd_cxl_bps, gpu_rd_dram_bps;   /* GPU consumer constants (GPU module) */
    _Atomic uint64_t promoted_bytes, promoted_extents;
#define CXLP_PROMO_RING 1024
    _Atomic uint32_t promo_tail; _Atomic uint32_t promo_ring[CXLP_PROMO_RING];   /* extent index + 1 */
    /* Producer pacing, the last resort (§10.11 item 17): when nothing is being lent and the stream's total
     * effect on DRAM readers (its source reads included) still exceeds the bound, the daemon publishes a
     * byte rate per stream and refills a token bucket every tick; reserve() waits for tokens. */
    _Atomic uint32_t pace_on[CXLP_NSTREAM];
    _Atomic int64_t  pace_tokens[CXLP_NSTREAM];
    _Atomic uint64_t pace_bps[CXLP_NSTREAM];
    _Atomic uint64_t paced_waits;              /* how often a reserve had to wait for tokens */
} cxlp_policy_t;

typedef struct {
    _Atomic uint64_t magic;        /* written LAST by the creator */
    uint32_t version, ndev;
    uint64_t meta_bytes;
    uint32_t nseg_total, nobj;     /* nobj: power of two */
    uint32_t next_cap; _Atomic uint32_t ext_hint;
    _Atomic uint64_t obj_gen;      /* source of cxlp_obj_t.gen */
    uint64_t obj_off, ext_off;     /* byte offsets of the tables inside the metadata */
    uint64_t bs_segtab_off;        /* CXLP_MAX_BUFSETS * 2 * CXLP_BS_MAXSEG uint32_t */
    cxlp_bufset_t bufset[CXLP_MAX_BUFSETS];
    cxlp_policy_t policy;
    cxlp_drain_t drain[CXLP_NDRAIN];
    _Atomic uint64_t drained_bytes; _Atomic uint32_t drain_lowspace_pct;   /* below this share of free CXL segments the drain stops yielding */
    _Atomic uint64_t drain_wanted_ns;      /* a writer is blocked until a drain completes (buffer-set overwrite rule) */
    _Atomic uint32_t drain_lag_ms;         /* pending work older than this is drained whatever the writers do (durability lag bound) */
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
#define ST_STATE(x) ((x) & 0xffu)
#define ST_GEN(x)   ((x) >> 8)
#define ST_MAKE(gen, state) ((((gen) & 0xffffffu) << 8) | (uint32_t)(state))
#define POL (&cxlp_g.meta->policy)

static inline uint64_t cxlp_now_ns(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return (uint64_t)t.tv_sec * 1000000000ull + (uint64_t)t.tv_nsec; }

/* store.c */
int  cxlp_seg_to_free(int dev, uint32_t seg, int only_if_sealed_empty);   /* 1 if this caller freed it */
void cxlp_seg_force_seal(int dev, uint32_t seg, uint64_t live);
/* object.c */
cxlp_obj_t *cxlp_obj_find(cxlp_key_t key);
int  cxlp_obj_release_slot(cxlp_obj_t *o);      /* 0, -2 if pinned, -1 if someone else got it */
int  cxlp_obj_reap_superseded(void);            /* release superseded objects that nobody pins any more */
/* policy.c */
int  cxlp_policy_daemon_alive(void);
int  cxlp_policy_pick(uint32_t stream, uint32_t nclaim);
void cxlp_policy_wake(void);
int  cxlp_policy_wait_free(uint32_t seen_event, int ms);
void cxlp_policy_pace_wait(uint32_t stream, uint64_t len);
#endif
