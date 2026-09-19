/* cxlpath — write-path runtime (design: docs/DESIGN.md §10). Public API, grown step by step. */
#ifndef CXLPATH_H
#define CXLPATH_H
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

#define CXLP_SEG_BYTES   (32ul << 20)          /* segment size (user decision 2026-09-18) */
#define CXLP_MAX_DEVS    4
#define CXLP_NO_SEG      UINT32_MAX

typedef enum { CXLP_DEV_CXL = 0, CXLP_DEV_DRAM = 1 } cxlp_devkind_t;

typedef struct {
    const char    *path;      /* /dev/daxX.Y, or a regular/shm file (tests, DRAM pool)      */
    uint64_t       offset;    /* start of the range cxlpath OWNS inside the device           */
    uint64_t       bytes;     /* length of that range; rounded down to whole segments        */
    cxlp_devkind_t kind;
} cxlp_devcfg_t;

typedef struct {
    const char   *name;       /* store name; metadata lives in /dev/shm/cxlpath.<name>       */
    int           ndev;
    cxlp_devcfg_t dev[CXLP_MAX_DEVS];
} cxlp_config_t;

/* Create the node-level store if it does not exist, otherwise attach to it. 0 on success. */
int  cxlp_open(const cxlp_config_t *cfg);
/* Attach to an existing store by name (geometry and device paths come from its metadata). */
int  cxlp_attach(const char *name);
void cxlp_close(void);
/* Remove the store's metadata (tests / administration). Devices are left untouched. */
int  cxlp_destroy(const char *name);

/* --- Component A, segment level (A2) --- */
typedef enum { CXLP_SEG_FREE = 0, CXLP_SEG_OPEN = 1, CXLP_SEG_SEALED = 2, CXLP_SEG_BUFSET = 3 } cxlp_segstate_t;

int      cxlp_ndev(void);
uint32_t cxlp_dev_nseg(int dev);
uint32_t cxlp_dev_free(int dev);                       /* free segments right now             */
void    *cxlp_seg_ptr(int dev, uint32_t seg);          /* address of a segment in this process */
/* Claim one free segment of `dev` (compare-and-swap, no locks, no IPC). CXLP_NO_SEG if none. */
uint32_t cxlp_seg_claim(int dev, cxlp_segstate_t as);
/* Give a segment back. Only the claimer (or crash cleanup) may call this. */
void     cxlp_seg_release(int dev, uint32_t seg);
uint32_t cxlp_seg_owner(int dev, uint32_t seg);        /* pid of the claimer, 0 if free       */

/* --- Component A, reservations (A3) ---
 * reserve -> fill (cxlp_copy_in or the caller's own NT stores) -> commit; release when dead.
 * A reservation is contiguous and at most one segment. WHERE it lands is decided here, at
 * reserve time, so callers must not assume a device. Each thread appends into its own open
 * segment per (device, lifetime class): no locks, the shared table is touched once per segment. */
#define CXLP_NKLASS 4
typedef struct {
    uint32_t klass;        /* lifetime class: data that dies together shares segments (0..3)  */
    uint32_t align;        /* 0 = 64 B; drain-target writes use 4096                            */
    int      dev;          /* -1 = let the placement policy choose (default)                    */
} cxlp_hints_t;

typedef struct {
    void    *ptr;
    int      dev;
    uint32_t seg, off, len;
} cxlp_res_t;

int  cxlp_reserve(size_t len, const cxlp_hints_t *hints, cxlp_res_t *out);   /* 0, or -1 (no space / too big) */
void cxlp_commit(const cxlp_res_t *r);
void cxlp_abort(const cxlp_res_t *r);            /* reserved but never committed              */
void cxlp_release(const cxlp_res_t *r);          /* committed data is dead                    */
void cxlp_copy_in(void *dst, const void *src, size_t n);   /* always NT stores                */
void cxlp_thread_seal(void);                     /* close this thread's open segments         */
uint64_t cxlp_seg_live(int dev, uint32_t seg);

/* Placement hook: returns the device for the next segment of this thread. Component B installs
 * the real policy; the default takes the first CXL device that has a free segment. */
typedef int (*cxlp_pick_fn)(uint32_t klass);
void cxlp_set_pick(cxlp_pick_fn fn);

/* --- Component A, object index (A4) ---
 * An object is a list of committed extents, kept in the SHARED metadata: it belongs to the
 * node-level store, not to the process that wrote it, so the drain process and a restarted
 * application can find it. One writer per object; readers look it up after obj_commit. */
typedef uint64_t cxlp_key_t;                       /* 0 and UINT64_MAX are reserved */
int  cxlp_obj_begin(cxlp_key_t key, uint32_t klass, uint32_t *handle);
int  cxlp_obj_append(uint32_t handle, const cxlp_res_t *committed);
int  cxlp_obj_commit(uint32_t handle);
/* Fills up to `max` extents (pointers valid in this process). Returns the number of extents,
 * or -1 if the object does not exist or is not committed. */
int  cxlp_obj_lookup(cxlp_key_t key, cxlp_res_t *ext, int max, uint64_t *bytes);
int  cxlp_obj_release(cxlp_key_t key);
/* Convenience: whole-buffer put/get built on reserve/copy_in/commit/append. */
int  cxlp_put(cxlp_key_t key, uint32_t klass, const void *buf, size_t len);
int64_t cxlp_get(cxlp_key_t key, void *buf, size_t cap);
/* Crash cleanup (run by the background process, or by tests): objects never committed by a
 * dead writer are dropped, segments of dead writers are sealed with their live bytes
 * recomputed from the index, so reserved-but-uncommitted space is reclaimed. Returns the
 * number of objects dropped. */
int  cxlp_cleanup_dead(void);

/* --- Component A, buffer sets (A5) ---
 * For GPU checkpoint clients: a long-lived, VIRTUALLY contiguous buffer built from scattered
 * segments (mapped at adjacent addresses), registered with CUDA once by the client and
 * overwritten in place. A client owns two sets and alternates. A set may be overwritten only
 * when the version it holds is drained to NVMe AND the other set holds a committed version,
 * so one complete version is always on CXL. State lives in the shared metadata. */
#define CXLP_MAX_BUFSETS 16
typedef enum { CXLP_BS_EMPTY = 0, CXLP_BS_WRITING = 1, CXLP_BS_COMMITTED = 2 } cxlp_bsstate_t;

int   cxlp_bufset_create(cxlp_key_t client, int which /*0|1*/, int dev, size_t bytes);   /* idempotent */
void *cxlp_bufset_map(cxlp_key_t client, int which, size_t *bytes);    /* stitched mapping in this process */
/* Pick the set to write version `version` into, enforcing the overwrite rule. Returns 0/1,
 * or -1 if neither set may be overwritten yet (caller waits: back-pressure). */
int   cxlp_bufset_begin(cxlp_key_t client, uint64_t version);
int   cxlp_bufset_commit(cxlp_key_t client, int which);
int   cxlp_bufset_mark_drained(cxlp_key_t client, int which);
/* Newest committed version and the set holding it (-1 if none): used by recovery. */
int   cxlp_bufset_newest(cxlp_key_t client, uint64_t *version);
int   cxlp_bufset_destroy(cxlp_key_t client);

#ifdef __cplusplus
}
#endif
#endif
