/*
 * ObjPlace — object-level sensitivity-aware CXL placement runtime.
 *
 * The application registers each memory object with semantic metadata
 * (type, access pattern, sensitivity, hot fraction, skew, phase). A
 * benefit-guided planner decides DRAM / CXL / split placement under a model of
 * CXL bandwidth pressure. See docs/DESIGN_OBJPLACE.md.
 *
 * Scope guard: no auto hot/cold detection, no page migration, no kernel module.
 * Memory is materialized lazily on first obj_ptr/obj_hot_ptr/obj_cold_ptr call.
 */
#ifndef OBJPLACE_H
#define OBJPLACE_H

#include <stddef.h>

/* ---- object metadata enums ---- */
typedef enum { OBJ_GENERIC, OBJ_EMBEDDING, OBJ_FEATURE, OBJ_KV, OBJ_BUFFER } obj_type_t;
typedef enum { ACC_STREAMING, ACC_RANDOM, ACC_MIXED } access_pattern_t;
typedef enum { SENS_BANDWIDTH, SENS_LATENCY, SENS_CAPACITY } sensitivity_t;
typedef enum { PHASE_ACTIVE, PHASE_INACTIVE, PHASE_PREFILL, PHASE_DECODE, PHASE_GATHER } phase_t;
typedef enum { PLACE_DRAM, PLACE_CXL, PLACE_SPLIT, PLACE_INTERLEAVE } placement_t;

typedef struct {
    obj_type_t       type;
    size_t           size;          /* total bytes */
    access_pattern_t access;
    sensitivity_t    sensitivity;
    double           hot_fraction;  /* 0..1; portion that is hot (for split) */
    double           skew_alpha;    /* >=0; 0 = uniform access */
    phase_t          phase;
} obj_attr_t;

typedef struct objplace_obj *obj_handle_t;

/* ---- runtime configuration ---- */
#define CXL_BW_CEILING_GIB 35.5      /* measured single-CZ120 ceiling (Phase 1) */

/* dram_node/cxl_node default to 0/1 (c28) or env OBJ_DRAM_NODE/OBJ_CXL_NODE. */
void   objplace_init(int dram_node, int cxl_node);
/* DRAM "fast tier" budget the planner may spend (bytes). Env OBJPLACE_DRAM_BUDGET. */
void   objplace_set_dram_budget(size_t bytes);
/* Current/assumed CXL demand in GiB/s; scales the CXL penalty. Default = ceiling. */
void   objplace_set_pressure(double cxl_load_gib_s);

/* ---- object lifecycle ---- */
obj_handle_t obj_create(const obj_attr_t *attr);
void   obj_update_phase(obj_handle_t h, phase_t phase);
void   obj_update_hotset(obj_handle_t h, double hot_fraction, double skew_alpha);
void   obj_rebalance(void);          /* global re-plan of all unmaterialized objects */
void   obj_destroy(obj_handle_t h);

/* ---- memory access (materializes on first call) ---- */
void  *obj_ptr(obj_handle_t h);      /* whole-object buffer; NULL if SPLIT */
void  *obj_hot_ptr(obj_handle_t h);  /* hot partition (DRAM under SPLIT) */
void  *obj_cold_ptr(obj_handle_t h); /* cold partition (CXL under SPLIT) */
size_t obj_hot_bytes(obj_handle_t h);
size_t obj_cold_bytes(obj_handle_t h);

/* ---- introspection (eval / logging) ---- */
placement_t obj_placement(obj_handle_t h);
double      obj_benefit_per_byte(obj_handle_t h);
const char *placement_name(placement_t p);
size_t      objplace_record_bytes(void);   /* per-object registry record size */
int         objplace_live_count(void);      /* registered objects in use */

/* ---- compatibility wrapper (old prototype API) ---- */
typedef enum {
    HINT_BW_SENSITIVE = 0,  /* -> obj_create{bandwidth, active} */
    HINT_COLD_CAPACITY,     /* -> obj_create{capacity, inactive} */
    HINT_SKEW_HOT,          /* -> DRAM */
    HINT_SKEW_COLD,         /* -> CXL */
    HINT__COUNT
} obj_hint_t;

void  *obj_alloc_hint(size_t size, obj_hint_t hint);  /* wraps obj_create */
void   obj_free_hint(void *ptr, size_t size);
int    obj_hint_node(obj_hint_t hint);
const char *obj_hint_name(obj_hint_t hint);

#endif /* OBJPLACE_H */
