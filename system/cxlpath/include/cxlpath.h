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

#ifdef __cplusplus
}
#endif
#endif
