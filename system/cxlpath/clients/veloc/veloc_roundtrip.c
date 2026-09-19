/* E1 gate helper: byte-exact VeloC round trip through cxlpath.
 *   veloc_roundtrip write <cfg>   three versions of three protected regions (80 MiB + 12 MiB + 777 B)
 *   veloc_roundtrip check <cfg> <expected_version>   Restart_test + Restart in a NEW process, compare */
#include <veloc.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define NA (10u << 20)
#define NB (3u << 20)
static double *a; static int *b; static unsigned char c[777];
static void fill(int v) { for (size_t i = 0; i < NA; i++) a[i] = (double)i * 1.5 + v; for (size_t i = 0; i < NB; i++) b[i] = (int)(i * 2654435761u) ^ v; for (int i = 0; i < 777; i++) c[i] = (unsigned char)(i * 7 + v); }
int main(int argc, char **argv) {
    if (argc < 3) return 2;
    a = malloc(NA * sizeof *a); b = malloc(NB * sizeof *b);
    if (VELOC_Init_single(0, argv[2]) != VELOC_SUCCESS) { puts("VELOC_Init_single failed"); return 1; }
    VELOC_Mem_protect(0, a, NA, sizeof *a); VELOC_Mem_protect(1, b, NB, sizeof *b); VELOC_Mem_protect(2, c, 777, 1);
    int rc = 0;
    if (!strcmp(argv[1], "write")) {
        for (int v = 1; v <= 3; v++) { fill(v); if (VELOC_Checkpoint("rt", v) != VELOC_SUCCESS) { printf("checkpoint v%d failed\n", v); rc = 1; } }
        VELOC_Checkpoint_wait();
        printf("wrote versions 1..3 rc=%d\n", rc);
    } else {
        int want = atoi(argv[3]), v = VELOC_Restart_test("rt", 0);
        double *ra = malloc(NA * sizeof *ra); int *rb = malloc(NB * sizeof *rb); unsigned char rcc[777];
        fill(want); memcpy(ra, a, NA * sizeof *a); memcpy(rb, b, NB * sizeof *b); memcpy(rcc, c, 777);
        memset(a, 0, NA * sizeof *a); memset(b, 0, NB * sizeof *b); memset(c, 0, 777);
        int r = v > 0 ? VELOC_Restart("rt", v) : VELOC_FAILURE;
        int same = !memcmp(ra, a, NA * sizeof *a) && !memcmp(rb, b, NB * sizeof *b) && !memcmp(rcc, c, 777);
        printf("Restart_test -> version %d (expected %d), Restart rc=%d, regions %s\n", v, want, r, same ? "byte-exact" : "DIFFER");
        rc = !(v == want && r == VELOC_SUCCESS && same);
    }
    VELOC_Finalize(0);
    puts(rc ? "FAIL" : "PASS"); return rc;
}
