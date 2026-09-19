/* cxlp_admin <store> view | force <n|-1> | destroy | sweep
 * sweep (tests): release every committed object and destroy every buffer set, then report free
 * segments — whatever is still not free after that is a leak. */
#include "../../src/internal.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
int main(int argc, char **argv) {
    if (argc < 3) return 2;
    if (!strcmp(argv[2], "destroy")) { char p[256]; snprintf(p, sizeof p, "/dev/shm/cxlpath.%s.drampool", argv[1]); unlink(p); return cxlp_destroy(argv[1]); }
    if (cxlp_attach(argv[1])) { fprintf(stderr, "no such store\n"); return 1; }
    if (!strcmp(argv[2], "force") && argc > 3) cxlp_policy_force(atoi(argv[3]));
    if (!strcmp(argv[2], "sweep")) {
        unsigned objs = 0, sets = 0;
        for (uint32_t i = 0; i < cxlp_g.meta->nobj; i++) if (atomic_load(&cxlp_g.obj[i].state) == OBJ_COMMITTED) { while (cxlp_obj_release(atomic_load(&cxlp_g.obj[i].key)) == -2) usleep(1000); objs++; }
        for (int i = 0; i < CXLP_MAX_BUFSETS; i++) { uint64_t c = atomic_load(&cxlp_g.meta->bufset[i].client); if (c) { cxlp_bufset_destroy(c); sets++; } }
        cxlp_thread_seal(); unsigned fr = 0, tot = 0; for (int d = 0; d < cxlp_ndev(); d++) { fr += cxlp_dev_free(d); tot += cxlp_dev_nseg(d); }
        printf("sweep: released %u objects, destroyed %u buffer sets; free segments %u/%u%s\n", objs, sets, fr, tot, fr == tot ? "" : "  <-- LEAK");
        cxlp_close(); return fr == tot ? 0 : 3;
    }
    cxlp_policy_view_t v; cxlp_policy_view(0, &v);
    printf("alive=%d spill16=%u staged16=%u dram_ok=%u cxl_full=%u gpu_full=%u probe=%.1f base=%.1f bound=%.2f epoch=%llu\n", v.daemon_alive, v.spill16, v.staged16, v.dram_ok, v.cxl_full, v.gpu_full, v.probe_ns, v.base_ns, v.bound, (unsigned long long)v.epoch);
    for (int d = 0; d < cxlp_ndev(); d++) printf("dev %d %s free %u/%u written %.2f GiB\n", d, cxlp_dev_kind(d) == CXLP_DEV_CXL ? "CXL " : "DRAM", cxlp_dev_free(d), cxlp_dev_nseg(d), v.dev_bytes[d] / 1073741824.0);
    cxlp_close(); return 0;
}
