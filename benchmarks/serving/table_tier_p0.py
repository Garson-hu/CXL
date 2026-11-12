#!/usr/bin/env python3
"""CXL-vs-NVMe study (2026-11-12), phase P0: table of the path-validation runs (short single-request runs, KVTIER_VERIFY=1).
Per run: where LMCache placed the KV (L1 objects by medium, L2 stores), the residency check (verify_residency.py, run right after
the run), whether the Device-DAX arenas were registered with CUDA, the DRAM the cache server used against the KV it held (RSS:
anonymous + shared memory; a Device-DAX mapping is not part of the RSS), the page-cache growth during the run, and the bytes the
NVMe device itself read / wrote (/proc/diskstats of nvme1n1) against the bytes LMCache loaded from / stored to its L2.
usage: table_tier_p0.py <P0 dir> tag [tag ...]  -> <P0 dir>/tables-p0.md"""
import collections, json, os, sys
P0 = sys.argv[1]; G = 2**30
rows = ["# P0 — validation of the real data paths (c28, 2026-11-12)", "",
        "| run | tier | KV stored GiB | L1 objects written DRAM / DAX (chunks) | L1 reads DRAM / DAX | L2 stored / loaded GiB | DAX arenas (GiB, CUDA-registered) | residency check | LMCache RSS max GiB: anon / shmem | page cache growth GiB | NVMe device read / written GiB | GPU memory max MiB |", "|" + "---|" * 12]
for tag in sys.argv[2:]:
    meta = open(f"{P0}/{tag}-meta.txt").read(); cfg = json.loads(meta.split("M config ", 1)[1].split("\n", 1)[0].split(" ", 2)[2])
    w = collections.Counter(); r = collections.Counter(); st = ld = 0; arenas = []; mem = []; nb = 0; open_load = {}
    for l in open(f"{P0}/{tag}-kvevents.jsonl"):
        d = json.loads(l); e = d["ev"]
        if e == "l1.write.finished": w.update(d.get("bk", "")); nb += d.get("nb", 0)
        elif e == "l1.read.reserved": r.update(d.get("bk", ""))
        elif e == "l2.store.completed": st += d.get("bytes_transferred") or 0
        elif e == "l2.load_task.submitted": open_load[(d.get("adapter_index"), d.get("task_id"))] = d.get("total_bytes") or 0
        elif e == "l2.load_task.completed": ld += open_load.pop((d.get("adapter_index"), d.get("task_id")), 0)
        elif e == "l1dax.arena": arenas.append(f"{d['dev'].split('/')[-1]} {d['size'] / G:g} {'yes' if d['pinned'] else 'NO'}")
        elif e == "mem": mem.append(d)
    res = "-"; p = f"{P0}/{tag}-residency.txt"
    if os.path.exists(p):
        t = open(p).read(); last = [x for x in t.splitlines() if x.startswith("RESULT")][-1]; m = int(last.split("dax_match=")[1].split()[0]); mm = int(last.split("dax_mismatch=")[1])
        fl = [x for x in t.splitlines() if x.startswith("files")]
        res = (f"{m} of {m + mm} hashes equal through an independent read-only mapping" if m + mm else "") + (("; " if m + mm else "") + "files: " + fl[0].split("page-cache residency of the sampled files: ")[1] + " in the page cache" if fl else "") or "no Device-DAX object in this run"
    gmax = 0; p = f"{P0}/{tag}-gpu.txt"
    if os.path.exists(p):
        for l in open(p):
            if l.startswith("U "): gmax = max(gmax, int(l.split()[4]))
    pc = (max(m["Cached"] - m["Shmem"] for m in mem) - (mem[0]["Cached"] - mem[0]["Shmem"])) / 2**20
    rows.append(f"| {tag} | {cfg['tier']}{' (buffered I/O: control)' if not cfg.get('ssd_odirect', True) else ''} | {nb / G:.2f} | {w['D']} / {w['X']} | {r['D']} / {r['X']} | {st / G:.2f} / {ld / G:.2f} | {'; '.join(arenas) or '-'} | {res} | "
                f"{max(m['RssAnon'] for m in mem) / 2**20:.2f} / {max(m['RssShmem'] for m in mem) / 2**20:.2f} | {pc:.2f} | {(mem[-1]['rd_sec'] - mem[0]['rd_sec']) * 512 / G:.2f} / {(mem[-1]['wr_sec'] - mem[0]['wr_sec']) * 512 / G:.2f} | {gmax} |")
open(f"{P0}/tables-p0.md", "w").write("\n".join(rows) + "\n"); print("\n".join(rows))
