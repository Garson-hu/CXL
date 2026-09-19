/* B4 gate, deterministic part: the controller and the baseline tracker with injected signals. */
#include "cxlpath_daemon.h"
#include <stdio.h>
static int fails;
#define CHECK(c, msg) do { if (!(c)) { printf("  FAIL: %s\n", msg); fails++; } } while (0)
int main(void) {
    cxlp_ctl_t c; cxlp_ctl_init(&c, 1.10, 1.05); const double B = 138.0;
    puts("B4.1 slow increase: +1/16 per epoch only when the path is full AND DRAM is calm");
    for (int e = 0; e < 5; e++) cxlp_ctl_epoch(&c, 0, 0, B, B);
    CHECK(c.cpu == 0 && c.gpu == 0, "path not full: stays at 0");
    for (int e = 0; e < 5; e++) cxlp_ctl_epoch(&c, 1, 0, 1.07 * B, B);
    CHECK(c.cpu == 0, "full but mean5 = 1.07x base (above the 1.05 margin): hold");
    for (int e = 0; e < 20; e++) { cxlp_ctl_epoch(&c, 1, 0, 1.02 * B, B); if (e == 3) CHECK(c.cpu == 4, "4 epochs -> 4/16"); }
    CHECK(c.cpu == 16 && c.gpu == 0, "saturates at 16/16; the GPU value is independent");
    for (int e = 0; e < 3; e++) cxlp_ctl_epoch(&c, 0, 1, B, B);
    CHECK(c.cpu == 16 && c.gpu == 3, "GPU path full -> staged share rises");

    { cxlp_ctl_t d; cxlp_ctl_init(&d, 1.10, 1.05); d.cpu = 6;
      cxlp_ctl_epoch(&d, 0, 0, B, B); CHECK(d.cpu == 6, "between 70% and 90% of the CXL capacity: hold");
      cxlp_ctl_epoch(&d, -1, 0, B, B); cxlp_ctl_epoch(&d, -1, 0, 3 * B, B); CHECK(d.cpu == 4, "CXL has slack: -1/16 per epoch, even while DRAM is busy"); }

    puts("B4.2 fast decrease: two CONSECUTIVE probes above 1.10x base halve everything");
    CHECK(cxlp_ctl_probe(&c, 1.30 * B, B) == 0 && cxlp_ctl_probe(&c, 1.00 * B, B) == 0 && c.cpu == 16, "one probe above the bound, then calm: nothing");
    CHECK(cxlp_ctl_probe(&c, 1.09 * B, B) == 0 && cxlp_ctl_probe(&c, 1.09 * B, B) == 0 && c.cpu == 16, "1.09x is inside the bound");
    CHECK(cxlp_ctl_probe(&c, 1.2 * B, B) == 0 && cxlp_ctl_probe(&c, 1.2 * B, B) == 1 && c.cpu == 8 && c.gpu == 1, "two in a row: 16 -> 8 (and 3 -> 1)");
    int n = 0; while (c.cpu && n < 100) { cxlp_ctl_probe(&c, 5 * B, B); n++; }
    CHECK(n == 8 && c.cpu == 0 && c.gpu == 0, "sustained pressure: 8 -> 4 -> 2 -> 1 -> 0 in 8 probes (80 ms at 10 ms per probe)");
    cxlp_ctl_epoch(&c, 1, 1, 5 * B, B); CHECK(c.cpu == 0, "no increase while DRAM is under pressure");

    puts("B4.3 per-stream memory");
    for (int e = 0; e < 6; e++) cxlp_ctl_epoch(&c, 1, 0, B, B);
    cxlp_ctl_stream_idle(&c, 3); CHECK(c.mem_cpu[3] == 6, "stream 3 remembers 6/16 when its burst ends");
    c.cpu = 0; cxlp_ctl_burst_start(&c, 1u << 3, B, B); CHECK(c.cpu == 6, "next burst of stream 3 starts at 6/16");
    cxlp_ctl_burst_start(&c, 1u << 5, B, B); CHECK(c.cpu == 0, "a stream with no history starts at 0");
    cxlp_ctl_burst_start(&c, 1u << 3, 1.2 * B, B); CHECK(c.cpu == 0, "DRAM busy at burst start: start at 0 whatever was remembered");
    cxlp_ctl_probe(&c, 2 * B, B); cxlp_ctl_probe(&c, 2 * B, B); CHECK(c.mem_cpu[3] == 3, "pressure while idle halves the remembered value too");

    puts("B4.4 reference levels (median; idle: 60 s window; active: 2 s window, known after 5 epochs, frozen while we spill)");
    cxlp_ref_t idle, act; cxlp_ref_init(&idle, 60000); cxlp_ref_init(&act, 2000); double v = 0; uint64_t t = 1000000;
    double noisy[] = { 100, 131, 158, 126, 135, 140, 129, 152, 133, 137, 99 };      /* idle c28: 100-160 ns from probe to probe */
    for (int i = 0; i < 11; i++) { v = cxlp_ref_feed(&idle, noisy[i], t); t += 200; }
    CHECK(v == 133, "idle reference = MEDIAN of the idle epoch means (133), not their minimum (99)");
    CHECK(cxlp_ref_value(&act, 5) == 0, "active reference unknown before 5 no-spill epochs");
    double burst[] = { 112, 126, 134, 135, 136, 133, 139, 135 };                     /* ramp-up, then the no-spill level */
    for (int i = 0; i < 4; i++) { cxlp_ref_feed(&act, burst[i], t); t += 50; }
    CHECK(cxlp_ref_value(&act, 5) == 0, "still unknown after 4");
    for (int i = 4; i < 8; i++) { v = cxlp_ref_feed(&act, burst[i], t); t += 50; }
    CHECK(cxlp_ref_value(&act, 5) == 135, "known after 5: median 135 although the window still holds the ramp-up samples");
    t += 100000; CHECK(cxlp_ref_value(&act, 5) == 135, "100 s of spill later (no feeding): frozen at 135, our own spill cannot ratchet it up");
    CHECK(135 <= 2.0 * idle.low, "reference 135 vs lowest idle reference: headroom (guard 2.0)");
    CHECK(!(290 <= 2.0 * idle.low), "reference 290 (others load DRAM to ~73%): no headroom, nothing may spill");
    cxlp_ctl_t g; cxlp_ctl_init(&g, 1.10, 1.05); g.cpu = 8;
    cxlp_ctl_epoch(&g, 1, 0, 290, 0); CHECK(g.cpu == 8, "no headroom (reference passed as 0): no increase");
    cxlp_ctl_probe(&g, 290, 0); cxlp_ctl_probe(&g, 290, 0); CHECK(g.cpu == 4, "no headroom: every probe counts as over the bound");
    g.cpu = 8; cxlp_ctl_probe_b(&g, 1.4 * 133, 133, 1.5); cxlp_ctl_probe_b(&g, 1.4 * 133, 133, 1.5); CHECK(g.cpu == 8, "idle state, loose bound 1.5: a noisy 1.4x reading does not halve the remembered ratios");
    cxlp_ctl_probe_b(&g, 3 * 133, 133, 1.5); cxlp_ctl_probe_b(&g, 3 * 133, 133, 1.5); CHECK(g.cpu == 4, "idle state: obvious pressure (3x) does");
    puts(fails ? "FAIL" : "PASS"); return fails != 0;
}
