#!/usr/bin/env python3
"""Future-window prefetch simulator for training-data caches (Task B of the 2026-10-27 exploratory study).
Input: the access trace of a REAL training run collected by train_trace.py (<run>/reads.txt: 'R <t> <epoch> <pos> <id> <bytes>' = the
moment the input pipeline pulled a sample file; <run>/schedule.txt: 'E <epoch> <t_computed> ...' and 'S <epoch> <t_start>' = when the
epoch's order was computed and when the epoch started; <run>/files.txt: id, name, bytes). The simulator replays the demand stream
against one cache of capacity C bytes fed from storage over one channel of bandwidth B bytes/s (FIFO; a transfer in progress is not
preempted; a demand fetch goes ahead of queued prefetches), with a prefetcher that may fetch any sample whose demand lies within the next
W seconds — but only samples whose schedule is already AVAILABLE: --avail all (every epoch's order known from the seed at job start),
epoch (an epoch's order is known from its start), none (no prefetch). Prefetched data is pinned until its use (unless --no-pin); a
prefetch is issued only when the cache can hold it after evicting unpinned data (LRU), so the window is bounded by the capacity;
resident data whose demand lies inside the window is protected from eviction until that use (--no-protect disables this: the naive
prefetcher that evicts what it later needs); pins are COUNTS of pending in-window demands, so an entry demanded in two epochs
inside one window stays protected until the second use (fixed 2026-10-27 after the first sweep); a
demand that finds its prefetch queued or in flight is a MISS (late prefetch: no second fetch, the remaining wait is the stall); a demand
miss fetches on the channel and inserts the sample (LRU eviction of unpinned data); used data stays cached (retention hits across
epochs). Metrics per (W, C): hit rate, retention hits (data used in an earlier epoch), prefetch hits, cold and late misses, bytes
fetched from storage (demand / prefetch) = bytes written into the cache, late and wasted prefetches, stall time, mean occupancy,
evictions, prefetch lead time (p10 / p50). --speed k replays the demand timeline k times faster (a faster trainer, or several trainers
sharing one storage link); --score-epochs '1-' scores epochs >= 1 (epoch 0 is the cold start for retention), 'all' scores every epoch.
usage: train_prefetch_sim.py <run_dir> <out.csv> [--windows 0,5,10,25,50,100,150,200,300,600] [--caps-gib 30,60,120,180,360,inf]
       [--bw-gbps 0.49] [--avail all|epoch|none] [--speed 1] [--no-pin] [--score-epochs 1-] [--label x]"""
import argparse, collections, csv, os
ap = argparse.ArgumentParser(); ap.add_argument("run"); ap.add_argument("out")
ap.add_argument("--windows", default="0,5,10,25,50,100,150,200,300,600"); ap.add_argument("--caps-gib", default="30,60,120,180,360,inf")
ap.add_argument("--bw-gbps", type=float, default=0.49); ap.add_argument("--avail", default="all", choices=["all", "epoch", "none"])
ap.add_argument("--speed", type=float, default=1.0); ap.add_argument("--no-pin", action="store_true"); ap.add_argument("--score-epochs", default="1-")
ap.add_argument("--no-protect", action="store_true", help="naive prefetcher: resident data due inside the window is NOT protected from eviction")
ap.add_argument("--demand-bw-gbps", type=float, default=0.0, help="bandwidth of a demand fetch (0 = the channel's B)"); ap.add_argument("--label", default="")
ap.add_argument("--demand", default="batches", choices=["reads", "batches"], help="demand instants: the training step start that consumes the sample (batches, default) or the pipeline's file pull (reads)"); ap.add_argument("--batch-size", type=int, default=4)
A = ap.parse_args(); INF = float("inf")
size = {}
for l in open(os.path.join(A.run, "files.txt")): i, nm, b = l.split(); size[int(i)] = int(b)
dem = []
if A.demand == "reads":                                     # demand = the moment the input pipeline pulled the file
    for l in open(os.path.join(A.run, "reads.txt")):
        if l[0] != "R": continue
        _, t, e, pos, i, b = l.split(); dem.append((float(t) / A.speed, int(e), int(pos), int(i)))
else:                                                       # demand = the start of the training step that consumes the sample (end of the previous step; the epoch start for step 0)
    perms = {}; st_ = {}; bt = {}
    for l in open(os.path.join(A.run, "schedule.txt")):
        x = l.split()
        if x[0] == "E": perms[int(x[1])] = [int(v) for v in x[5:]]
        elif x[0] == "S": st_[int(x[1])] = float(x[2])
    for l in open(os.path.join(A.run, "batches.txt")):
        x = l.split(); bt[(int(x[2]), int(x[3]))] = float(x[1])
    for e, perm in perms.items():
        for pos, i in enumerate(perm):
            k = pos // A.batch_size
            t = bt.get((e, k - 1), st_.get(e)) if k > 0 else st_.get(e)
            if t is None or (e, k) not in bt: continue              # steps not run (end of a truncated epoch)
            dem.append((t / A.speed, e, pos, i))
dem.sort()
avail_t = {}; starts = {}
for l in open(os.path.join(A.run, "schedule.txt")):
    x = l.split()
    if x[0] == "E": avail_t[int(x[1])] = float(x[2]) / A.speed
    elif x[0] == "S": starts[int(x[1])] = float(x[2]) / A.speed
E = max(e for _, e, _, _ in dem) + 1
if A.avail == "epoch":
    for e in range(E): avail_t[e] = starts.get(e, avail_t.get(e, 0.0))
score_from = 0 if A.score_epochs == "all" else int(A.score_epochs.rstrip("-"))
B = A.bw_gbps * 1e9; Bd = (A.demand_bw_gbps * 1e9) if A.demand_bw_gbps > 0 else B
D = sum(size.values()); span = dem[-1][0] - dem[0][0]
print(f"{len(dem)} demands over {E} epochs, {len(size)} files, dataset {D / 2**30:.1f} GiB, span {span:.0f} s at speed {A.speed:g}x ({len(dem) / span:.1f} samples/s = {sum(size[i] for *_, i in dem) / span / 1e6:.1f} MB/s), channel {A.bw_gbps:g} GB/s, avail {A.avail}")

def run(W, C):
    ready = {}                      # id -> [bytes, t_ready, origin]  origin: 'prefetch' | 'used'
    lru = collections.OrderedDict() # evictable ready entries (no pending demand inside the window), LRU order
    pins = collections.Counter()    # id -> number of demands inside the prefetch window not yet served (a pinned entry is not in lru)
    inflight = {}                   # id -> completion time of a started transfer
    issue_t = {}                    # id -> issue time of a queued / started prefetch
    queue = collections.deque(); queued = set()
    occ = [0]; chan = [0.0]; st = collections.Counter(); occ_int = [0.0]; last_t = [dem[0][0]]; leads = []; stall = [0.0]; pf = [0]
    def evictable(i): return A.no_pin or pins[i] == 0
    def evict_for(nbytes):
        while occ[0] + nbytes > C and lru:
            v, _ = lru.popitem(last=False); b, _, org = ready.pop(v); occ[0] -= b; st["evict"] += 1
            if org == "prefetch": st["wasted_prefetch"] += 1
        return occ[0] + nbytes <= C
    def chan_run(now):
        while queue and chan[0] <= now:
            i, b = queue.popleft(); queued.discard(i); chan[0] = max(chan[0], issue_t[i]) + b / B; inflight[i] = chan[0]
    def settle(now):
        for i in [i for i, tc in inflight.items() if tc <= now]:
            tc = inflight.pop(i); issue_t.pop(i, None)
            if i in ready: continue
            ready[i] = [size[i], tc, "prefetch"]
            if evictable(i): lru[i] = True
    for (t, e, pos, i) in dem:
        chan_run(t); settle(t)
        occ_int[0] += occ[0] * (t - last_t[0]); last_t[0] = t
        if W > 0 and A.avail != "none":                                            # prefetch what is due within (t, t + W] and whose epoch order is known
            while pf[0] < len(dem) and dem[pf[0]][0] <= t + W:
                tp, ep, pp, ip = dem[pf[0]]
                if tp <= t: pf[0] += 1; st["window_passed"] += (ip not in ready and ip not in inflight and ip not in queued); continue
                if avail_t.get(ep, INF) > t: break
                if ip in ready:                                                     # resident: a pending demand inside the window protects it (unless --no-protect)
                    pins[ip] += 1
                    if not A.no_protect: lru.pop(ip, None)
                    pf[0] += 1; continue
                if ip in inflight or ip in queued: pins[ip] += 1; pf[0] += 1; continue
                b = size[ip]
                if not evict_for(b): break                                          # cache full of pinned / in-flight data: the window is capacity-bound
                pins[ip] += 1; occ[0] += b; issue_t[ip] = t; queue.append((ip, b)); queued.add(ip); pf[0] += 1
                if ep >= score_from: st["prefetch_n"] += 1; st["prefetch_bytes"] += b                  # storage traffic is counted for the scored epochs only, like the demand misses
            chan_run(t); settle(t)
        sc = e >= score_from
        if sc: st["acc"] += 1; st["acc_bytes"] += size[i]
        if pins[i] > 0: pins[i] -= 1
        if i in ready:
            ent = ready[i]
            if sc:
                st["hit"] += 1; st["hit_bytes"] += ent[0]
                if ent[2] == "prefetch": st["hit_prefetched"] += 1; leads.append(t - ent[1])
                else: st["hit_retained"] += 1
            ent[2] = "used"
            if evictable(i): lru[i] = True; lru.move_to_end(i)
            else: lru.pop(i, None)
        else:
            if sc: st["miss"] += 1
            b = size[i]
            if i in inflight:                                                       # late prefetch, in flight: wait for it
                tc = inflight.pop(i); issue_t.pop(i, None)
                if sc: st["miss_late"] += 1; stall[0] += max(0.0, tc - t)
                ready[i] = [b, t, "used"]
            elif i in queued:                                                       # late prefetch, not even started: cancel it, fetch on demand
                queued.discard(i); queue.remove((i, b)); issue_t.pop(i, None)
                if sc: st["prefetch_n"] -= 1; st["prefetch_bytes"] -= b
                done = max(chan[0], t) + b / Bd; chan[0] = done
                if sc: st["miss_late"] += 1; st["demand_bytes"] += b; stall[0] += done - t
                ready[i] = [b, t, "used"]                                           # occ already reserved at queueing
            else:                                                                   # cold miss: demand fetch ahead of queued prefetches
                done = max(chan[0], t) + b / Bd; chan[0] = done
                if sc: st["miss_cold"] += 1; st["demand_bytes"] += b; stall[0] += done - t
                if evict_for(b): occ[0] += b; ready[i] = [b, t, "used"]
                else: st["uncacheable"] += 1; continue
            if evictable(i): lru[i] = True
            else: lru.pop(i, None)
    occ_mean = occ_int[0] / max(1e-9, span); leads.sort()
    return dict(label=A.label, avail=A.avail, speed=A.speed, bw_gbps=A.bw_gbps, pin=int(not A.no_pin), protect=int(not A.no_protect), window_s=W, cap_gib=(C / 2**30 if C < INF else INF),
                acc=st["acc"], hits=st["hit"], hit_rate=round(st["hit"] / max(1, st["acc"]), 4), hit_retained=st["hit_retained"], hit_prefetched=st["hit_prefetched"],
                miss=st["miss"], miss_cold=st["miss_cold"], miss_late=st["miss_late"], read_GB=round(st["acc_bytes"] / 1e9, 2), served_from_cache_GB=round(st["hit_bytes"] / 1e9, 2),
                storage_GB=round((st["demand_bytes"] + st["prefetch_bytes"]) / 1e9, 2), prefetch_GB=round(st["prefetch_bytes"] / 1e9, 2), demand_GB=round(st["demand_bytes"] / 1e9, 2),
                prefetches=st["prefetch_n"], wasted_prefetches=st["wasted_prefetch"], evictions=st["evict"], stall_s=round(stall[0], 1),
                occupancy_mean_gib=round(occ_mean / 2**30, 1), lead_p10_s=(round(leads[len(leads) // 10], 2) if leads else None), lead_p50_s=(round(leads[len(leads) // 2], 2) if leads else None),
                uncacheable=st["uncacheable"], window_passed=st["window_passed"])
rows = []
for C in [(float(x) * 2**30 if x != "inf" else INF) for x in A.caps_gib.split(",")]:
    for W in [float(x) for x in A.windows.split(",")]:
        r = run(W, C); rows.append(r)
        print(f"C {r['cap_gib']:>6} GiB W {W:5g} s: hit {r['hit_rate']:.3f} (retained {r['hit_retained']}, prefetched {r['hit_prefetched']}) miss cold {r['miss_cold']} late {r['miss_late']} storage {r['storage_GB']:.1f} GB (prefetch {r['prefetch_GB']:.1f}) stall {r['stall_s']:.0f} s occ {r['occupancy_mean_gib']} GiB lead p50 {r['lead_p50_s']} wasted {r['wasted_prefetches']}", flush=True)
with open(A.out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("wrote", A.out)
