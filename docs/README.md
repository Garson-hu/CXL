# docs/ — map and maintenance rules

*Reorganized 2026-08-25 (user-approved scheme). Entry point for the project is
`../WORKLOG.md` (status + session history); this file explains what lives in
`docs/` and how to maintain it.*

## Map
| File / dir | Role | Update style |
|---|---|---|
| `PAPER.md` | Thesis, claims, positioning — the paper skeleton | Living; every change appended to its Change History |
| `DESIGN.md` | CURRENT system design + API | Living; every change appended to its Change History |
| `experiments/INDEX.md` | One-row-per-experiment lookup: date, question, verdict, link | Living (table only) |
| `experiments/METHODOLOGY.md` | Measurement invariants that apply to every experiment | Living; append when a new invariant is learned |
| `experiments/YYYY-MM-DD-<content>.md` | One experiment (or campaign): question, setup, commands, numbers, verdict | ONE active at a time; **frozen** once its verdict lands in INDEX |
| `guides/` | Onboarding walkthroughs (rarely touched) | Frozen unless the code they describe changes |
| `slides/` | Presentation decks (dated filenames) | Add new; never edit past decks |
| `archive/` | Superseded docs, kept verbatim for reference | Never edited |

Raw data stays outside docs (rule added 2026-08-25):
**`../experimental_results/<experiment-name>/`** — one subdirectory per
experiment, SAME basename as its md file, holding that experiment's original
logs/CSVs/outputs; the md in `experiments/` is the summary. Machine inspections
(not tied to one experiment) stay in `../hardware/results/`; literature data in
`../benchmarks/results/`. Literature docs: `../Related.md` +
`../DEEP_RESEARCH_2026-07-08-cxl-landscape.html`.

## Rules
1. **Append-mode history.** `PAPER.md` and `DESIGN.md` each end with a
   `## Change history` section: one dated line per change (what + why). Edit the
   body freely to reflect the present; never rewrite or delete history entries.
2. **Experiment files are immutable after close.** While active, a file may be
   edited; when the verdict is recorded in `INDEX.md`, the file is frozen —
   corrections go in a new dated file that references the old one.
3. **Naming:** `YYYY-MM-DD-<content>.md`, date = when the experiment started.
4. **Precision.** Every number carries units, thread count, node, and date;
   every claim links its raw file in `../experimental_results/<name>/`.
   Machine-state changes (BIOS, reboot, remap) are recorded in the experiment
   file they affect.
5. **No new top-level docs.** New material is either an experiment file, a
   Change-History-tracked edit to PAPER/DESIGN, or it goes to WORKLOG.

## Naming (rule 2026-09-08 — do not use "Pair A"/"Pair B" in new text)
| historical label | what it is | use instead |
|---|---|---|
| Pair A | two cards at PCI c1:00.0 + e1:00.0, exposed as two firmware windows `/dev/dax0.0` (242.5 GiB) and `dax1.0` (= NUMA node 1, 269.5 GiB); root-level hashed interleave, not splittable | `dax0.0` / `node 1` (same two cards) |
| Pair B | two cards at PCI 01:00.0 + 02:00.0 behind host bridge pci0000:00, one window `/dev/dax2.0` (512 GiB); plain 256 B stripe, `card = (offset>>8)&1` | `dax2.0`; single cards "卡 01" / "卡 02" |
