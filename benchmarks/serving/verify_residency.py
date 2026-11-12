#!/usr/bin/env python3
"""Residency check of the CXL-vs-NVMe study (2026-11-12): is the KV data LMCache says it placed on a Device-DAX device really in
that device's memory?  An independent process (this one, not the LMCache server) maps the device read-only and compares the SHA-1
of the bytes at the recorded offsets with the SHA-1 the kvtier hook (KVTIER_VERIFY=1) computed inside the server:
   dax.w     one chunk written to a slot of the DAX L2 adapter (hash of the L1 source object at the time of the write)
   l1dax.obj a sampled object of the Device-DAX L1 arena, hashed 3 s after its allocation (after the KV write from the GPU)
A slot or an object that was freed and reused afterwards holds other data; only the LAST record per (device, offset) is checked,
so run this on a validation run that did not evict (or right after the run).
For the file tiers (--files <dir>): every cache file is read with O_DIRECT and hashed (the hash of what is on the NVMe device), the
number of its pages resident in the page cache is reported with mincore().
usage: verify_residency.py <tag>-kvevents.jsonl [--max N] [--files <dir>]      -> prints one summary line per device and "RESULT ..." """
import ctypes, hashlib, json, mmap, os, sys

ALIGN = 2 << 20
def check_dax(path, max_n):
    last = {}; arenas = []
    for line in open(path):
        if '"dax.w"' not in line and '"l1dax.obj"' not in line and '"l1dax.arena"' not in line and '"l1dax.add"' not in line: continue
        try: d = json.loads(line)
        except Exception: continue
        if d["ev"] in ("l1dax.arena", "l1dax.add"): arenas.append(d); continue
        if "sha1" in d: last[(d["dev"], d["off"])] = d
    for a in arenas: print("arena", json.dumps(a))
    bydev = {}
    for (dev, off), d in last.items(): bydev.setdefault(dev, []).append(d)
    tot_ok = tot_bad = 0
    for dev, recs in sorted(bydev.items()):
        recs.sort(key=lambda d: d["off"])
        if max_n and len(recs) > max_n: recs = recs[:: max(1, len(recs) // max_n)][:max_n]
        fd = os.open(dev, os.O_RDONLY); ok = bad = 0; nbytes = 0; kinds = {}
        for d in recs:
            off, n = d["off"], d["n"]; lo = off // ALIGN * ALIGN; hi = -(-(off + n) // ALIGN) * ALIGN
            m = mmap.mmap(fd, hi - lo, flags=mmap.MAP_SHARED, prot=mmap.PROT_READ, offset=lo)
            h = hashlib.sha1(m[off - lo: off - lo + n]).hexdigest(); m.close()
            kinds[d["ev"]] = kinds.get(d["ev"], 0) + 1; nbytes += n
            if h == d["sha1"]: ok += 1
            else:
                bad += 1
                if bad <= 5: print(f"  MISMATCH {dev} off={off} n={n} ev={d['ev']} recorded={d['sha1'][:12]} device={h[:12]}")
        os.close(fd); tot_ok += ok; tot_bad += bad
        print(f"device {dev}: {ok + bad} records checked ({kinds}), {nbytes / 2**30:.2f} GiB read from the device mapping, match {ok}, mismatch {bad}")
    return tot_ok, tot_bad

def check_files(dirpath, max_n):
    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    libc.mmap.restype = ctypes.c_void_p; libc.mmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_long]
    libc.mincore.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_ubyte)]; libc.munmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    names = sorted(os.path.join(root, f) for root, _, fs in os.walk(dirpath) for f in fs if not f.endswith(".tmp"))
    total = sum(os.path.getsize(p) for p in names); sample = names if not max_n else names[:: max(1, len(names) // max_n)][:max_n]
    cached = pages = nbytes = 0
    for p in sample:
        n = os.path.getsize(p)
        if n == 0: continue
        fd = os.open(p, os.O_RDONLY); npg = -(-n // 4096); vec = (ctypes.c_ubyte * npg)()
        ptr = libc.mmap(None, n, mmap.PROT_READ, mmap.MAP_SHARED, fd, 0)      # mapping a file does not read it; mincore reports what is cached
        if ptr and ptr != ctypes.c_void_p(-1).value:
            if libc.mincore(ptr, n, vec) == 0: cached += sum(v & 1 for v in vec); pages += npg
            libc.munmap(ptr, n)
        os.close(fd)
        if n % 4096 == 0:                                                      # the bytes on the device (O_DIRECT bypasses the page cache)
            fd = os.open(p, os.O_RDONLY | os.O_DIRECT); mm = mmap.mmap(-1, n); f = os.fdopen(fd, "rb", buffering=0); got = f.readinto(mm); f.close()
            nbytes += got; mm.close()
    print(f"files {dirpath}: {len(names)} files, {total / 2**30:.2f} GiB; sampled {len(sample)}: {nbytes / 2**30:.2f} GiB read back with O_DIRECT; "
          f"page-cache residency of the sampled files: {cached} of {pages} pages ({100.0 * cached / max(1, pages):.2f} %)")
    return len(names), total, cached, pages

if __name__ == "__main__":
    args = sys.argv[1:]; max_n = 0; files = None
    if "--max" in args: i = args.index("--max"); max_n = int(args[i + 1]); del args[i:i + 2]
    if "--files" in args: i = args.index("--files"); files = args[i + 1]; del args[i:i + 2]
    ok = bad = 0
    if args: ok, bad = check_dax(args[0], max_n)
    if files: check_files(files, max_n)
    print(f"RESULT dax_match={ok} dax_mismatch={bad}")
