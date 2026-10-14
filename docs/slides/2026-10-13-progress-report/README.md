# Research progress deck — 2026-10-13 (sources of `docs/slides/SLIDES_2026-10-13-progress-report.pptx`)

Progress report for Dr. Mueller: from the original CXL-first write isolation idea, through the unified DRAM/CXL
management suggestion, to the current direction (interference-aware capacity and bandwidth management).

| file | what |
|---|---|
| `../SLIDES_2026-10-13-progress-report.pptx` | the editable deck (26 slides, 16:9, Calibri; speaker notes on every slide) |
| `deck-preview.pdf`, `preview/slide-NN.png` | a preview drawn by matplotlib from the same slide data, for layout checks only — no LibreOffice/PowerPoint on c28, so this is NOT PowerPoint's rendering (text is set in DejaVu Sans, which is wider than Calibri; what fits here fits in PowerPoint) |
| `scripts/figs_deck_2026-10-13.py` (tracked) | every data figure, drawn from the raw result files in `experimental_results/` (matplotlib default colours, fixed per category: DRAM blue, CXL orange, static split purple, budget-gated green, existing controller gray) |
| `figs/*.png`, `figs/*.svg` | the figures (PNG 200 dpi for the deck, SVG for editing) |
| `figs/SOURCES.md` | figure → raw data files |
| `scripts/deck_2026-10-13.py` (tracked) | the slide data (titles, statements, takeaways, notes) and the PPTX / preview / outline builders |
| `outline.md` | one line per slide: title, part, evidence tag, figure |

## Regenerate
```
cd /home/ghu4/CXL
python3 scripts/figs_deck_2026-10-13.py   # ~1 min; needs matplotlib; reads experimental_results/
python3 scripts/deck_2026-10-13.py        # needs python-pptx, Pillow
```
`figs_deck_2026-10-13.py` draws the bucket-depth and varying-load figures only when their result directories exist
(`experimental_results/2026-10-12-budget-gated-admission/{depth,varying,longrun}/summary.csv`); until then
`deck_2026-10-13.py` puts a "PENDING" panel on those two slides. The evaluation slide reports the number of independent
runs it averages (`REPS`).

## Evidence tags
Each slide carries one or more tags: **Hardware measurement** (membench / topo / readcost on c28, Optane on c35),
**Real application** (vLLM + LMCache on the RTX 4060 Ti; checkpoint producers beside real victims),
**Trace-driven emulation** (host memory traffic emulation: CPU non-temporal copies driven by the Mooncake traces,
calibrated on the real runs — not GPU DMA, not multi-GPU serving), **Trace simulation** (exact LRU stack distances on
the traces), **Estimate** (H100 throughput, recompute cost), **Proposal (not implemented)**.

## Style
Written in Simplified Technical English style (short sentences, one idea each, active voice, consistent terms);
one conclusion-style title, one figure, two to four statements and one takeaway per slide; speaker notes carry the
setup, the data source and the limits.

`docs/slides/` is local-only (gitignored since 2026-09, commit c5676fd): the deck, figures and preview live here on c28; the two generator scripts are tracked in `scripts/`.
