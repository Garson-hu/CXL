/* cxlp_mkstore <name> <cxl_MiB_per_device> <dram_MiB> <dev0> [dev1]  — (re)create a store. */
#include "cxlpath.h"
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
int main(int argc, char **argv) {
    if (argc < 5) { fprintf(stderr, "usage: %s name cxl_MiB dram_MiB dev0 [dev1]\n", argv[0]); return 2; }
    static char pool[256]; snprintf(pool, sizeof pool, "/dev/shm/cxlpath.%s.drampool", argv[1]);
    cxlp_config_t c = { .name = argv[1] }; uint64_t cb = (uint64_t)atol(argv[2]) << 20, db = (uint64_t)atol(argv[3]) << 20;
    for (int i = 4; i < argc && c.ndev < 2; i++) c.dev[c.ndev++] = (cxlp_devcfg_t){ argv[i], 0, cb, CXLP_DEV_CXL };
    if (db) c.dev[c.ndev++] = (cxlp_devcfg_t){ pool, 0, db, CXLP_DEV_DRAM };
    cxlp_destroy(argv[1]); unlink(pool);
    if (cxlp_open(&c)) { fprintf(stderr, "cannot create store\n"); return 1; }
    for (int d = 0; d < cxlp_ndev(); d++) printf("dev %d: %s %u segments\n", d, cxlp_dev_kind(d) == CXLP_DEV_CXL ? "CXL " : "DRAM", cxlp_dev_nseg(d));
    cxlp_close(); return 0;
}
