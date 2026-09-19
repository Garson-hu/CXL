/* cxlp_admin <store> view | force <n|-1> | destroy */
#include "cxlpath.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
int main(int argc, char **argv) {
    if (argc < 3) return 2;
    if (!strcmp(argv[2], "destroy")) { char p[256]; snprintf(p, sizeof p, "/dev/shm/cxlpath.%s.drampool", argv[1]); unlink(p); return cxlp_destroy(argv[1]); }
    if (cxlp_attach(argv[1])) { fprintf(stderr, "no such store\n"); return 1; }
    if (!strcmp(argv[2], "force") && argc > 3) cxlp_policy_force(atoi(argv[3]));
    cxlp_policy_view_t v; cxlp_policy_view(0, &v);
    printf("alive=%d spill16=%u staged16=%u dram_ok=%u cxl_full=%u gpu_full=%u probe=%.1f base=%.1f bound=%.2f epoch=%llu\n", v.daemon_alive, v.spill16, v.staged16, v.dram_ok, v.cxl_full, v.gpu_full, v.probe_ns, v.base_ns, v.bound, (unsigned long long)v.epoch);
    for (int d = 0; d < cxlp_ndev(); d++) printf("dev %d %s free %u/%u written %.2f GiB\n", d, cxlp_dev_kind(d) == CXLP_DEV_CXL ? "CXL " : "DRAM", cxlp_dev_free(d), cxlp_dev_nseg(d), v.dev_bytes[d] / 1073741824.0);
    cxlp_close(); return 0;
}
