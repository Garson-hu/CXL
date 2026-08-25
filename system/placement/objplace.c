/*
 * ObjPlace — object-level sensitivity-aware CXL placement runtime.
 * See objplace.h and docs/DESIGN_OBJPLACE.md.
 */
#define _GNU_SOURCE
#include "objplace.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <numa.h>

#define MAX_OBJS 4096

struct objplace_obj {
    int          in_use;
    unsigned     id;
    obj_attr_t   attr;
    placement_t  planned;     /* planner output */
    int          materialized;
    int          would_migrate; /* planned != current after rebalance, no migration */
    void        *hot_buf;     /* materialized buffers */
    void        *cold_buf;
    size_t       hot_bytes;
    size_t       cold_bytes;
};

static struct objplace_obj g_objs[MAX_OBJS];
static unsigned g_next_id = 1;
static int g_dram_node = -1, g_cxl_node = -1;
static int g_init = 0;
static int g_cxl_warned = 0;
static size_t g_dram_budget = 0;
static size_t g_dram_used = 0;       /* incremental planner accounting */
static double g_cxl_load = -1.0;     /* <0 means "assume saturated" */

/* ---- config ---- */
static long env_long(const char *k, long d) {
    const char *v = getenv(k);
    if (!v || !*v) return d;
    char *e = NULL; long n = strtol(v, &e, 10);
    return (e == v) ? d : n;
}

static void ensure_init(void) {
    if (g_init) return;
    g_dram_node = (int)env_long("OBJ_DRAM_NODE", 0);
    g_cxl_node  = (int)env_long("OBJ_CXL_NODE", 1);
    g_dram_budget = (size_t)env_long("OBJPLACE_DRAM_BUDGET", (long)(2UL << 30)); /* 2 GiB */
    g_init = 1;
}

void objplace_init(int dram_node, int cxl_node) {
    g_dram_node = dram_node; g_cxl_node = cxl_node; g_init = 1;
    if (g_dram_budget == 0)
        g_dram_budget = (size_t)env_long("OBJPLACE_DRAM_BUDGET", (long)(2UL << 30));
}
void objplace_set_dram_budget(size_t bytes) { ensure_init(); g_dram_budget = bytes; }
void objplace_set_pressure(double cxl_load_gib_s) { ensure_init(); g_cxl_load = cxl_load_gib_s; }

static double pressure_factor(void) {
    double load = (g_cxl_load < 0) ? CXL_BW_CEILING_GIB : g_cxl_load; /* default saturated */
    double pf = load / CXL_BW_CEILING_GIB;
    if (pf < 0) pf = 0;
    if (pf > 1.2) pf = 1.2;
    return pf;
}

/* ---- benefit model ---- */
static double base_penalty(access_pattern_t a) {
    switch (a) {
    case ACC_STREAMING: return 1.10;  /* -> ~2.1x at full pressure */
    case ACC_MIXED:     return 0.60;
    case ACC_RANDOM:    return 0.25;  /* -> ~1.25x at full pressure */
    default:            return 0.50;
    }
}
static double sens_mult(sensitivity_t s) {
    switch (s) {
    case SENS_BANDWIDTH: return 1.0;
    case SENS_LATENCY:   return 0.5;
    case SENS_CAPACITY:  return 0.1;
    default:             return 0.5;
    }
}
static double phase_mult(phase_t p) {
    return (p == PHASE_INACTIVE) ? 0.1 : 1.0;
}

/* Access share captured by the top `hot_fraction` under Zipf(alpha). */
static double hot_access_share(double hot_fraction, double alpha) {
    if (hot_fraction >= 1.0) return 1.0;
    if (hot_fraction <= 0.0) return 0.0;
    return pow(hot_fraction, 1.0 / (1.0 + alpha));  /* alpha=0 -> = hot_fraction */
}

/* benefit per byte for a partition with given access share and size fraction. */
static double partition_bpb(const obj_attr_t *a, double access_share,
                            double partition_fraction) {
    if (partition_fraction <= 0) return 0;
    double cxl_pen = 1.0 + base_penalty(a->access) * pressure_factor();
    double density = access_share / partition_fraction;
    return sens_mult(a->sensitivity) * phase_mult(a->phase)
         * (cxl_pen - 1.0) * density;
}

static int is_skewed(const obj_attr_t *a) {
    return a->skew_alpha > 0.0 && a->hot_fraction > 0.0 && a->hot_fraction < 1.0;
}

double obj_benefit_per_byte(obj_handle_t h) {
    if (!h) return 0;
    const obj_attr_t *a = &h->attr;
    if (is_skewed(a)) {
        double share = hot_access_share(a->hot_fraction, a->skew_alpha);
        return partition_bpb(a, share, a->hot_fraction); /* hot-partition density */
    }
    return partition_bpb(a, 1.0, 1.0);
}

/* ---- planner ---- */
/* A candidate is a (object, partition) with size and benefit-per-byte. */
struct cand { struct objplace_obj *o; int is_hot; size_t bytes; double bpb; };

static int cand_cmp(const void *x, const void *y) {
    double a = ((const struct cand *)x)->bpb, b = ((const struct cand *)y)->bpb;
    return (a < b) - (a > b);   /* descending */
}

/* Re-plan a set of objects given the DRAM budget. If `single` non-NULL, only that
 * object is planned incrementally against current g_dram_used (create path). */
static void plan(struct objplace_obj *single) {
    ensure_init();
    struct cand cands[2 * MAX_OBJS];
    int nc = 0;

    for (int i = 0; i < MAX_OBJS; i++) {
        struct objplace_obj *o = &g_objs[i];
        if (!o->in_use) continue;
        if (single && o != single) continue;
        if (!single && o->materialized) continue; /* fixed; can't move */
        const obj_attr_t *a = &o->attr;
        if (is_skewed(a)) {
            double share = hot_access_share(a->hot_fraction, a->skew_alpha);
            size_t hot_b = (size_t)(a->size * a->hot_fraction);
            cands[nc++] = (struct cand){o, 1, hot_b,
                partition_bpb(a, share, a->hot_fraction)};
            cands[nc++] = (struct cand){o, 0, a->size - hot_b,
                partition_bpb(a, 1.0 - share, 1.0 - a->hot_fraction)};
        } else {
            cands[nc++] = (struct cand){o, 1, a->size,
                partition_bpb(a, 1.0, 1.0)};
        }
    }
    qsort(cands, nc, sizeof(cands[0]), cand_cmp);

    /* Greedy fill of DRAM budget. For the global path, reset accounting. */
    size_t used = single ? g_dram_used : 0;
    /* Track per-object hot/cold tier decision. */
    for (int i = 0; i < MAX_OBJS; i++) {
        if (g_objs[i].in_use && (!single || &g_objs[i] == single)) {
            /* default both partitions to CXL; planner promotes below */
            if (!g_objs[i].materialized) g_objs[i].planned = PLACE_CXL;
        }
    }
    /* Assign. Use small per-object flags via planned encoding:
       we accumulate hot_on_dram / cold_on_dram via temp arrays keyed by id. */
    static char hot_dram[MAX_OBJS], cold_dram[MAX_OBJS], has_hot[MAX_OBJS], has_cold[MAX_OBJS];
    for (int i = 0; i < MAX_OBJS; i++) { hot_dram[i]=cold_dram[i]=has_hot[i]=has_cold[i]=0; }

    for (int i = 0; i < nc; i++) {
        struct cand *c = &cands[i];
        int idx = (int)(c->o - g_objs);
        if (c->is_hot) has_hot[idx] = 1; else has_cold[idx] = 1;
        int fits = (c->bpb > 0.0) && (used + c->bytes <= g_dram_budget);
        if (fits) {
            used += c->bytes;
            if (c->is_hot) hot_dram[idx] = 1; else cold_dram[idx] = 1;
        }
    }
    if (single) g_dram_used = used;
    else        g_dram_used = used;

    /* Fold partition decisions into placement. */
    for (int i = 0; i < MAX_OBJS; i++) {
        struct objplace_obj *o = &g_objs[i];
        if (!o->in_use) continue;
        if (single && o != single) continue;
        if (o->materialized) continue;
        placement_t newp;
        if (has_hot[i] && has_cold[i]) {
            if (hot_dram[i] && cold_dram[i]) newp = PLACE_DRAM;
            else if (hot_dram[i] && !cold_dram[i]) newp = PLACE_SPLIT;
            else if (!hot_dram[i] && !cold_dram[i]) newp = PLACE_CXL;
            else newp = PLACE_SPLIT; /* cold on dram but not hot: unusual; treat as split */
        } else {
            newp = hot_dram[i] ? PLACE_DRAM : PLACE_CXL;
        }
        o->planned = newp;
    }
}

obj_handle_t obj_create(const obj_attr_t *attr) {
    ensure_init();
    int slot = -1;
    for (int i = 0; i < MAX_OBJS; i++) if (!g_objs[i].in_use) { slot = i; break; }
    if (slot < 0) { fprintf(stderr, "objplace: registry full\n"); return NULL; }
    struct objplace_obj *o = &g_objs[slot];
    memset(o, 0, sizeof(*o));
    o->in_use = 1;
    o->id = g_next_id++;
    o->attr = *attr;
    plan(o);                 /* incremental placement decision */
    return o;
}

void obj_update_phase(obj_handle_t h, phase_t phase) {
    if (h) h->attr.phase = phase;
}
void obj_update_hotset(obj_handle_t h, double hot_fraction, double skew_alpha) {
    if (!h) return;
    h->attr.hot_fraction = hot_fraction;
    h->attr.skew_alpha = skew_alpha;
}

void obj_rebalance(void) {
    g_dram_used = 0;
    /* Re-add already-materialized objects' DRAM usage so the budget is honest. */
    for (int i = 0; i < MAX_OBJS; i++) {
        struct objplace_obj *o = &g_objs[i];
        if (o->in_use && o->materialized) {
            if (o->planned == PLACE_DRAM) g_dram_used += o->attr.size;
            else if (o->planned == PLACE_SPLIT) g_dram_used += o->hot_bytes;
        }
    }
    plan(NULL);
}

/* ---- materialization ---- */
static int node_usable(int node) {
    if (numa_available() < 0) return 0;
    if (node < 0 || node > numa_max_node()) return 0;
    return numa_node_size64(node, NULL) > 0;
}
static int cxl_or_fallback(void) {
    if (node_usable(g_cxl_node)) return g_cxl_node;
    if (!g_cxl_warned) {
        fprintf(stderr, "objplace: CXL node %d unavailable; using DRAM node %d. "
                "(c28: sudo daxctl online-memory dax2.0)\n", g_cxl_node, g_dram_node);
        g_cxl_warned = 1;
    }
    return g_dram_node;
}

static void *alloc_node(int node, size_t bytes) {
    if (bytes == 0) return NULL;
    void *p;
    if (node < 0) p = numa_alloc_interleaved(bytes);   /* node<0 => interleave */
    else          p = numa_alloc_onnode(bytes, node);
    if (!p) { fprintf(stderr, "objplace: alloc %zu on node %d failed\n", bytes, node); }
    return p;
}

static void materialize(struct objplace_obj *o) {
    if (o->materialized) return;
    size_t hot_b = (size_t)(o->attr.size * o->attr.hot_fraction);
    int dram = g_dram_node, cxl = cxl_or_fallback();
    switch (o->planned) {
    case PLACE_DRAM:
        o->hot_buf = alloc_node(dram, o->attr.size);
        o->hot_bytes = o->attr.size; o->cold_buf = NULL; o->cold_bytes = 0;
        break;
    case PLACE_CXL:
        o->hot_buf = alloc_node(cxl, o->attr.size);
        o->hot_bytes = o->attr.size; o->cold_buf = NULL; o->cold_bytes = 0;
        break;
    case PLACE_INTERLEAVE:
        o->hot_buf = alloc_node(-1, o->attr.size);
        o->hot_bytes = o->attr.size; o->cold_buf = NULL; o->cold_bytes = 0;
        break;
    case PLACE_SPLIT:
        o->hot_buf  = alloc_node(dram, hot_b);
        o->cold_buf = alloc_node(cxl, o->attr.size - hot_b);
        o->hot_bytes = hot_b; o->cold_bytes = o->attr.size - hot_b;
        break;
    }
    o->materialized = 1;
}

void *obj_ptr(obj_handle_t h) {
    if (!h) return NULL;
    materialize(h);
    if (h->planned == PLACE_SPLIT) {
        fprintf(stderr, "objplace: obj_ptr on SPLIT object %u; use hot/cold ptr\n", h->id);
        return NULL;
    }
    return h->hot_buf;
}
void *obj_hot_ptr(obj_handle_t h)  { if (!h) return NULL; materialize(h); return h->hot_buf; }
void *obj_cold_ptr(obj_handle_t h) { if (!h) return NULL; materialize(h); return h->cold_buf; }
size_t obj_hot_bytes(obj_handle_t h)  { if (!h) return 0; materialize(h); return h->hot_bytes; }
size_t obj_cold_bytes(obj_handle_t h) { if (!h) return 0; materialize(h); return h->cold_bytes; }

placement_t obj_placement(obj_handle_t h) { return h ? h->planned : PLACE_CXL; }

size_t objplace_record_bytes(void) { return sizeof(struct objplace_obj); }
int objplace_live_count(void) {
    int n = 0;
    for (int i = 0; i < MAX_OBJS; i++) if (g_objs[i].in_use) n++;
    return n;
}

const char *placement_name(placement_t p) {
    switch (p) {
    case PLACE_DRAM: return "DRAM";
    case PLACE_CXL: return "CXL";
    case PLACE_SPLIT: return "SPLIT";
    case PLACE_INTERLEAVE: return "INTERLEAVE";
    default: return "?";
    }
}

void obj_destroy(obj_handle_t h) {
    if (!h || !h->in_use) return;
    if (h->hot_buf)  numa_free(h->hot_buf, h->hot_bytes);
    if (h->cold_buf) numa_free(h->cold_buf, h->cold_bytes);
    if (h->materialized) {
        if (h->planned == PLACE_DRAM) g_dram_used -= (g_dram_used >= h->attr.size) ? h->attr.size : g_dram_used;
        else if (h->planned == PLACE_SPLIT) g_dram_used -= (g_dram_used >= h->hot_bytes) ? h->hot_bytes : g_dram_used;
    }
    h->in_use = 0;
}

/* ---- compatibility wrapper ---- */
void obj_placement_init(int dram_node, int cxl_node) { objplace_init(dram_node, cxl_node); }

int obj_hint_node(obj_hint_t hint) {
    ensure_init();
    switch (hint) {
    case HINT_BW_SENSITIVE:
    case HINT_SKEW_HOT:    return g_dram_node;
    default:               return g_cxl_node;
    }
}
const char *obj_hint_name(obj_hint_t hint) {
    switch (hint) {
    case HINT_BW_SENSITIVE: return "BW_SENSITIVE";
    case HINT_COLD_CAPACITY: return "COLD_CAPACITY";
    case HINT_SKEW_HOT: return "SKEW_HOT";
    case HINT_SKEW_COLD: return "SKEW_COLD";
    default: return "UNKNOWN";
    }
}

/* Map a legacy hint to a one-object obj_create whose plan forces the intended
 * tier, then return its (whole-object) pointer. We bypass the DRAM budget so the
 * compat path always honors the literal hint (it is a hint, not a planner ask). */
void *obj_alloc_hint(size_t size, obj_hint_t hint) {
    ensure_init();
    obj_attr_t a; memset(&a, 0, sizeof(a));
    a.size = size;
    switch (hint) {
    case HINT_BW_SENSITIVE:
        a.type = OBJ_BUFFER; a.access = ACC_STREAMING;
        a.sensitivity = SENS_BANDWIDTH; a.phase = PHASE_ACTIVE; break;
    case HINT_COLD_CAPACITY:
        a.type = OBJ_GENERIC; a.access = ACC_RANDOM;
        a.sensitivity = SENS_CAPACITY; a.phase = PHASE_INACTIVE; break;
    case HINT_SKEW_HOT:
        a.type = OBJ_GENERIC; a.access = ACC_RANDOM;
        a.sensitivity = SENS_BANDWIDTH; a.phase = PHASE_ACTIVE; break;
    case HINT_SKEW_COLD:
    default:
        a.type = OBJ_GENERIC; a.access = ACC_RANDOM;
        a.sensitivity = SENS_CAPACITY; a.phase = PHASE_INACTIVE; break;
    }
    /* Force the literal hint tier regardless of budget. */
    obj_handle_t h = obj_create(&a);
    if (!h) return NULL;
    h->planned = (obj_hint_node(hint) == g_dram_node) ? PLACE_DRAM : PLACE_CXL;
    return obj_ptr(h);
}

void obj_free_hint(void *ptr, size_t size) {
    if (ptr) numa_free(ptr, size);
}
