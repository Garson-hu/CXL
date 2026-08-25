/*
 * obj_placement.h — compatibility shim.
 *
 * The original minimal prototype lived here. It has been refactored into the
 * ObjPlace runtime (objplace.h). This header now just forwards, so existing
 * includes of "obj_placement.h" keep working. obj_alloc_hint is a compatibility
 * wrapper over obj_create (see objplace.c).
 */
#ifndef OBJ_PLACEMENT_H
#define OBJ_PLACEMENT_H

#include "objplace.h"

/* Legacy init alias (maps to objplace_init). */
void obj_placement_init(int dram_node, int cxl_node);

#endif /* OBJ_PLACEMENT_H */
