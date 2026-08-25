# Study Guide (Detailed): ObjPlace, membench, and the CXL Experiments

*Written 2026-05-20. A code-level companion to `STUDY_GUIDE_OBJPLACE.md`. Goal: after
reading this you can open the source yourself and know what every function does.
Nothing here changes code or runs experiments. Uncertain points are marked
**(uncertain)**; subtle/risky code is marked **(watch)**.*

Files referenced: `system/placement/objplace.{h,c}`, `test_objplace.c`, `bwbench.c`,
`gnnbench.c`, `sensbench.c`, `mixbench.c`, `obench.c`; `benchmarks/memory/membench.c`;
`benchmarks/embedding/embbench.py`; the orchestrators in `benchmarks/`.

---

## 1. Uncommon Linux / NUMA / threading functions

These are the library and system calls the project leans on. For each: what it does,
why we use it, args, return, failure modes, a tiny example, and where it appears.

### `numa_available()` — libnuma
- **Does:** checks whether the NUMA API is usable on this machine.
- **Why:** every benchmark refuses to run if NUMA is unavailable (we *need* node 0 vs
  node 1 to mean DRAM vs CXL).
- **Args:** none. **Returns:** `-1` if NUMA is not available, `0`/≥0 otherwise.
- **Goes wrong:** on a non-NUMA kernel it returns −1; we then `die()`/exit.
- **Example:** `if (numa_available() < 0) { fprintf(stderr,"no numa\n"); exit(2); }`
- **In code:** `membench.c:check_node_or_die`, `objplace.c:node_usable`,
  `test_objplace.c:main`, every bench's `main`.

### `numa_max_node()` — libnuma
- **Does:** returns the highest NUMA node id (so node count = `numa_max_node()+1`).
- **Why:** validate that a requested `--node` exists (e.g., node 1 must exist for CXL).
- **Returns:** highest node id (e.g., `1` on c28).
- **In code:** `membench.c:check_node_or_die`, `objplace.c:node_usable`.

### `numa_node_size64(node, &freep)` — libnuma
- **Does:** returns the total bytes of memory on `node`; optionally writes free bytes
  to `*freep`.
- **Why:** detect whether a node has **online** memory. CXL node 1 returns 0 until an
  admin onlines `dax2.0`; we use this to refuse fake CXL runs and to fall back.
- **Args:** `node` id; `long long *freep` (may be `NULL`). **Returns:** total bytes
  (`<= 0` means no usable memory).
- **Goes wrong:** returns 0 if the node exists but has no online memory → our code
  prints the `daxctl online-memory dax2.0` hint.
- **In code:** `membench.c:check_node_or_die`, `objplace.c:node_usable`.

### `numa_alloc_onnode(size, node)` — libnuma
- **Does:** allocates `size` bytes whose pages are **bound to a specific NUMA node**.
- **Why:** this is *the* mechanism for "put this buffer on DRAM (node 0) or CXL
  (node 1)". It sets the memory policy; pages are physically placed on first touch.
- **Args:** `size_t size`, `int node`. **Returns:** pointer, or `NULL` on failure.
- **Goes wrong:** can return `NULL` if the node can't satisfy the request. **Crucially,
  setting a policy does not guarantee placement** — the kernel can fall back to
  another node; that is why we verify with `move_pages` (below).
- **Example:** `void *p = numa_alloc_onnode(1<<30, 1); /* 1 GiB on CXL */`
- **In code:** `membench.c:alloc_on_node`, `objplace.c:alloc_node`, the C benches.

### `numa_alloc_interleaved(size)` — libnuma
- **Does:** allocates memory whose pages are striped round-robin across all nodes.
- **Why:** the **interleave** baseline (uses DRAM+CXL bandwidth in parallel).
- **In code:** `bwbench.c` / `gnnbench.c` interleave policy; `objplace.c:alloc_node`
  when `node<0` (used by the PLACE_INTERLEAVE path, which the planner does not yet
  select — see §5 Example 4).

### `numa_free(ptr, size)` — libnuma
- **Does:** frees memory from `numa_alloc_*`. **Must pass the same size.**
- **Goes wrong:** wrong size → corruption; double-free → crash. **(watch)** the C
  benches that mix `obj_*` and raw `numa_*` must free with the matching API.
- **In code:** every bench cleanup; `objplace.c:obj_destroy`, `obj_free_hint`.

### `mbind()` — not called directly
- We rely on libnuma's `numa_alloc_onnode`, which uses `mbind(2)`/`set_mempolicy`
  under the hood. We never call `mbind` ourselves. **(So you won't find it in our
  code; libnuma is the wrapper.)**

### `mmap()` — not called directly by us
- libnuma allocates via `mmap` internally. We do not `mmap` `/dev/dax*` directly
  (those are root-only and, once `dax2.0` is system-ram, are managed by the kernel as
  node 1). **(So no raw `mmap` in our sources.)**

### `memset(ptr, val, size)` — page touching
- **Does:** writes `val` to every byte — which **faults in every page**.
- **Why:** `numa_alloc_onnode` only reserves address space + policy; the physical
  page (on the chosen node) is allocated on **first touch**. We `memset` before
  timing so (a) page faults are excluded from measurements and (b) `move_pages` has
  real pages to query.
- **In code:** `membench.c:alloc_on_node` (`memset(p,0,bytes)`), every bench's
  pre-touch, `obench.c`.

### `move_pages(pid, count, pages[], nodes, status[], flags)` — syscall
- **Does:** in *query mode* (`nodes == NULL`) it fills `status[i]` with the **NUMA
  node of the physical page** backing virtual address `pages[i]`. (In move mode it
  migrates pages — we never use that.)
- **Why:** to *verify* a "CXL" buffer really landed on node 1, not silently on node 0.
- **Args:** `pid=0` (self), `count`, `pages[]` (page-aligned addresses), `nodes=NULL`
  for query, `status[]` (output), `flags=0`. **Returns:** `0` on success; `status[i]`
  is the node id, or negative on per-page error.
- **Detail (must understand):**
  - *Why it queries placement:* the kernel knows the physical frame → its node; query
    mode just reports it.
  - *Why pages must be touched first:* an untouched page has **no physical frame yet**
    (lazy allocation), so `status[i]` would be an error (e.g. `-ENOENT`), not a node.
    We `memset` first.
  - *What `status[i]` means:* the node id the page lives on. We compare to the
    expected node.
  - *Why `wrong=0` matters:* `wrong` counts sampled pages **not** on the expected
    node. `wrong=0` means the placement policy actually took effect — the measurement
    is trustworthy.
  - *Why `--strict-placement` matters:* it makes the program **exit non-zero** if any
    sampled page is misplaced, so a Phase-1 run **aborts** instead of silently
    reporting DRAM numbers as if they were CXL.
- **In code:** `membench.c:query_move_pages` + `verify_buffer_placement`;
  `test_objplace.c:node_of`.

### `syscall(SYS_move_pages, ...)`
- **Does:** invokes `move_pages` by syscall number directly.
- **Why:** avoids depending on a particular glibc/numaif prototype; the wrapper isn't
  always exposed. We define a thin `query_move_pages()` around it.
- **In code:** `membench.c`, `test_objplace.c`.

### `sched_setaffinity(pid, size, cpuset)` — CPU pinning
- **Does:** restricts a thread to run only on the CPUs in `cpuset`.
- **Why (central to the whole project):** **CPU pinning** nails each worker to a fixed
  core so the OS scheduler can't move it. For a memory benchmark this matters because:
  - it removes scheduler noise, and
  - it lets us put a **victim** and an **aggressor** on **disjoint physical cores**, so
    they contend on **memory**, not on **CPU time**.
- **Why disjoint cores matter:** if victim and aggressor share a core, the slowdown
  you measure mixes CPU contention (time-slicing, hyperthread sharing) with memory
  contention. **This is exactly what made Phase 2 wrong** — victim and aggressor both
  started at CPU 0, so the dramatic "8.75×" was largely CPU contention. The
  `--cpu-offset` flag (victim at 0.., aggressor at 64..) fixed it; the true
  memory-only number is 2.0–2.13× (Phase 2.2).
- **Args:** `pid=0` (self), `sizeof(cpu_set_t)`, `&set`. **Returns:** `0` or `-1`.
- **In code:** `membench.c:pin_self`, `bwbench.c:pin`, `sensbench.c:pin`,
  `mixbench.c:pin`.

### `CPU_ZERO(&set)` / `CPU_SET(cpu, &set)` — cpuset macros
- **Do:** clear a `cpu_set_t`; add a CPU id to it. Used to build the mask for
  `sched_setaffinity`.
- **Example:** `cpu_set_t s; CPU_ZERO(&s); CPU_SET(7,&s); sched_setaffinity(0,sizeof s,&s);`
- **In code:** all `pin*` helpers.

### `pthread_create` / `pthread_join`
- **Do:** start a worker thread running a function; wait for it to finish.
- **Why:** multi-threaded bandwidth (each thread streams its own buffer) and the
  victim/aggressor model inside one process (loaded-latency).
- **In code:** `membench.c:main`, `bwbench.c`, `sensbench.c`, `mixbench.c`.

### `pthread_barrier_init(&b, NULL, N)` / `pthread_barrier_wait(&b)`
- **Do:** create a barrier for `N` threads; block until all `N` arrive.
- **Why:** all workers pin themselves, then **wait at the barrier**, then start timing
  together. Without it, thread 32 might begin a millisecond after thread 0 and skew
  the aggregate bandwidth.
- **In code:** `membench.c:main`+`thread_main`, `bwbench.c`, `sensbench.c`, `mixbench.c`.

### `clock_gettime(CLOCK_MONOTONIC, &ts)`
- **Does:** reads a steadily-increasing clock unaffected by wall-clock adjustments.
- **Why:** all timing. We convert to ns: `sec*1e9 + nsec`.
- **In code:** `now_ns()` in every C file.

### `volatile`
- **Means:** "this variable may change unpredictably; do not optimize away reads/writes
  to it." We mark benchmark pointers/accumulators `volatile` so the compiler actually
  performs the memory accesses we're trying to measure (otherwise it could delete a
  read whose result is unused).
- **In code:** `volatile uint64_t *p` in the kernels; `volatile double sink`.

### `asm volatile("" :: "r"(x))` — compiler barrier
- **Means:** a no-op that *uses* `x`, forcing the compiler to compute it and keep the
  loop. Prevents dead-code elimination of an accumulator without the cost of real I/O.
- **In code:** end of `run_latency`/`run_stream_read`/etc. (`asm volatile("" :: "r"(acc));`).

### `dlopen` — not used directly
- We do not call `dlopen`; Python's `ctypes.CDLL` does the dynamic loading for us.

### `ctypes.CDLL(path)` — Python
- **Does:** loads a shared library (`libobjplace.so`) into the Python process so its C
  functions can be called.
- **Why:** `embbench.py` (Python/NumPy) needs to call the C ObjPlace runtime.
- **In code:** `embbench.py:get_objplace`.

### ctypes `argtypes` / `restype`
- **Do:** declare a C function's parameter types and return type so ctypes marshals
  values correctly. **Forgetting `restype` for a pointer-returning function defaults
  to `int`, truncating 64-bit pointers on 64-bit systems → crashes.** We set, e.g.,
  `lib.obj_create.restype = c_void_p` and `argtypes = [POINTER(ObjAttr)]`.
- **In code:** `embbench.py:get_objplace`.

### NumPy array backed by external C memory
- **Pattern:** `(c_uint8*size).from_address(ptr)` wraps a raw C pointer as a ctypes
  buffer; `np.frombuffer(buf, dtype=…)` makes a NumPy **view** over it (no copy). The
  C side (ObjPlace) **owns** that memory.
- **Memory-ownership pitfall (watch):** the Python view does **not** keep the C
  allocation alive and must not be freed by Python. `embbench.py` keeps a module-level
  `_NUMA_KEEPALIVE` list holding the `(ptr, size, buf)` so the buffer object isn't
  garbage-collected while NumPy is using it. If you drop that reference (or if C frees
  the memory while NumPy still points at it), you get a **segfault** or garbage data.
- **In code:** `embbench.py:buf_from_ptr` / `numa_alloc`.

---

## 2. The CXL memory path, in detail

```
   C code:  float *row = table + i*dim;   row[k] = ...
        |                                     (just a normal pointer)
        v
   VIRTUAL ADDRESS  (process address space)
        |
        v
   first access to an un-faulted page  ->  PAGE FAULT (trap into kernel)
        |
        v
   Linux memory policy for this VMA  (set by numa_alloc_onnode -> mbind)
        |   "allocate this page on node N"
        v
   PHYSICAL PAGE ALLOCATION on node N
        |
        v
   the physical address falls in node N's address range:
        node 0 range -> local DDR5 DRAM
        node 1 range -> the CXL window (dax2.0)
        |
        v
   CPU load/store is routed by physical address:
        node 0 -> DRAM memory controller (fast, ~300+ GiB/s aggregate)
        node 1 -> CXL root port -> PCIe 5.0 x8 -> CXL.mem transaction
        |
        v
   Micron CZ120  (one device, ~35.5 GiB/s ceiling, ~1.5x DRAM latency)
```

- **Why the program never computes a "CXL offset":** there is none. CXL memory is just
  a *physical address range* that the CPU reaches with ordinary loads/stores. Software
  only chooses a **NUMA node**; hardware routes by physical address. You write normal
  C; the placement is entirely in *where the page was allocated*.
- **Why node 1 = CXL here:** when the admin ran `daxctl … --mode=system-ram` + `online`
  on `dax2.0`, Linux created a new memory-only NUMA node (node 1) for that CZ120
  capacity. So on c28, "node 1" *is* the CXL device.
- **`dax2.0` online as system-ram:** `dax2.0` is a *device-DAX* character device
  exposing the CZ120 capacity. `--mode=system-ram` converts it from a raw device into
  ordinary kernel-managed RAM, which creates the NUMA node.
- **DAX** = Direct Access: a mode where memory/storage is exposed for direct CPU access
  without going through the page cache (`/dev/daxN.M`).
- **FAMFS** = Fabric-Attached Memory File System: a way to expose CXL memory as files.
  `dax0.0` and `dax1.0` are mounted as FAMFS (in use by others), so we **must not**
  touch them — only `dax2.0` is ours as system-ram. This is why we have **one** CXL
  NUMA node, not four.
- **PCI locality vs memory NUMA node:** a CXL device is a PCIe function with a "device
  NUMA node" (which socket it physically attaches to — often reported near node 0 by
  `lspci`/sysfs). The *memory* it exposes becomes its **own** node (node 1). These are
  two different ideas: *where the device hangs* vs *the memory pool the OS created*.
  Our code only cares about the latter (node 1 = the CXL memory). **(uncertain — the
  exact lspci/sysfs locality value isn't load-bearing for us; we rely on `move_pages`
  to confirm node 1 = CXL.)**

---

## 3. `membench.c` — function by function

`membench` measures DRAM vs CXL with controlled access patterns. Structure:

### `now_ns()`
Reads `CLOCK_MONOTONIC`, returns nanoseconds. Used for all timing.

### `die(msg)`
Prints to stderr and `exit(2)`. Used for unrecoverable setup errors.

### `query_move_pages(pid,count,pages,nodes,status,flags)`
Thin wrapper over `syscall(SYS_move_pages,…)` (see §1). Query mode (`nodes=NULL`).

### `check_node_or_die(node)`
- **Purpose:** validate the requested node before doing anything.
- **Steps:** `numa_available()<0` → die; `node` out of `[0, numa_max_node()]` → exit 3;
  `numa_node_size64(node,NULL) <= 0` → print the `daxctl online-memory` hint, exit 4.
- **Pitfall:** this is what prevents "measuring CXL" when node 1 has no online memory.

### `alloc_on_node(node, bytes)`
- **Purpose:** allocate a node-bound buffer and **pre-touch** it.
- **Steps:** `numa_alloc_onnode(bytes,node)`; on NULL → exit 5; `memset(p,0,bytes)` to
  fault every page onto the node.
- **Output:** the pointer.

### `verify_buffer_placement(buf, bytes, expected_node, tid)`
- **Purpose:** confirm the buffer's pages are on `expected_node`.
- **Important locals:** `page_size = sysconf(_SC_PAGESIZE)`; samples up to
  `VERIFY_SAMPLE_MAX = 1024` pages, stride = `n_pages/target`.
- **Steps:** build `pages[]` of sampled page addresses → `query_move_pages` →
  count `wrong` where `status[i] != expected_node`; print up to 5 wrong samples and the
  summary line.
- **Returns:** number of wrong pages (`-1` if the syscall failed). `main` turns this
  into a strict-mode abort.

### `pin_self(cpu)`
`CPU_ZERO`/`CPU_SET`/`sched_setaffinity` to pin the calling thread to one CPU.

### `build_chase(buf, bytes)`
- **Purpose:** build a **random permutation cycle** of 64-byte slots for the latency
  kernel.
- **How:** treat the buffer as `n = bytes/64` slots; create a permutation `perm[]` of
  slot indices (shuffled, keeping slot 0 as start); write each slot's pointer to point
  at the *next slot in the permutation*, forming one big cycle.
- **Why this defeats prefetching:** the next address is *data-dependent* (you must load
  the current slot to learn the next), and the order is random, so the hardware
  prefetcher cannot guess it. Each load waits for the previous → you measure **true
  dependent-load latency**, not bandwidth.

### Kernels (each runs for `--duration`, then records bytes/ops/seconds)
- `run_latency`: warm up, then `p = (uint64_t**)*p;` ×8 unrolled in a loop; counts
  `ops`; `avg_latency_ns = elapsed/ops`. Reports tiny "bandwidth" (`ops*64/time`) —
  **do not overinterpret it**; latency mode is about ns/access, not GiB/s.
- `run_stream_read`: sums every 8th `uint64_t` over the whole buffer, repeatedly;
  `bytes += buf_bytes` each pass. Sequential → measures **read bandwidth**.
- `run_stream_write`: writes a constant to every 8th `uint64_t`. **Writes are subtler
  than reads:** a write to a not-cached line typically triggers a *write-allocate*
  (read the line first) and later a *dirty writeback*, so a "write" can cost a read +
  a write of bandwidth. So **write bandwidth is not directly comparable to read
  bandwidth**; interpret carefully.
- `run_random_read`: picks a random cache-line index (LCG RNG) and reads the whole
  line. Unlike pointer-chase, successive accesses are **independent** (no dependency
  chain), so the CPU can have several outstanding — it represents **gather**-like
  workloads (embedding/feature lookups). Bandwidth is low because it's latency/queue
  bound, not because of dependencies.
- `run_mixed`: per access, draw a random line; with probability `read_pct/100` read it,
  else write it. Models read/write mixes (e.g., DLRM with updates).

### `thread_main(arg)`
Pins to its CPU, **waits on the barrier**, then dispatches to the kernel for its mode.
For `loaded-latency`: `tid==0` runs `run_latency` (the victim), all others run
`run_stream_read` (the aggressors).

### Option parsing
- `parse_mode(s)`: maps a string to the `enum mode`.
- `parse_size(s)`: parses a number with optional `K/M/G/T` suffix (so `--size=512M`
  works); rejects junk suffixes.
- `parse_rw(s)`: `sscanf(s,"%d:%d%c")` — requires exactly `R:W` with `R+W==100`;
  rejects anything else. (Earlier `atoi("70:30")` "worked" only by accident.)

### `main`
1. Parse options into `struct opts` (node, mode, size, threads, rw, duration, csv,
   verify/strict, cpu_offset, tag).
2. `check_node_or_die(node)`.
3. **CPU list construction:** read node-0's CPU mask (`numa_node_to_cpus(0,…)`) into
   `cpu_list[]` — the pool of CPUs we pin to (node 1 has no CPUs).
4. **CPU offset logic:** thread *i* pins to `cpu_list[(cpu_offset + i) % cpu_count]`.
   Victim uses offset 0; an aggressor process uses offset 64 → disjoint cores.
5. **Buffer allocation + pre-touch:** one `alloc_on_node` per thread.
6. **Placement verification** (if `--verify-placement`): per buffer; in strict mode a
   wrong page → exit 6/7. Runs **after** memset, **before** timing.
7. **Barrier** init for `threads`; create threads; join.
8. **Timing:** `global_t0/t1` wrap create→join (global wall time); each thread also
   records its own kernel `seconds`.
9. **Aggregation + CSV** (next).

### Loaded-latency aggregation (the three fields)
- `victim_latency_ns` = thread 0's `avg_latency_ns` only.
- `aggressor_bandwidth_gib_s` = (sum of bytes from threads 1..N-1) / `max_kernel_sec`.
- `total_bandwidth_gib_s` = (sum of **all** threads' bytes) / the **same**
  `max_kernel_sec`.
- `max_kernel_sec` = the longest per-thread kernel-loop time (excludes
  create/join/barrier overhead).
- **Why `max_kernel_sec` not global wall time:** global wall time includes thread
  setup/teardown, so it slightly *understates* bandwidth and (the original bug) made
  `total < aggressor` when the two used different denominators. Using one common
  `max_kernel_sec` for both new fields guarantees **`total_bw ≥ aggressor_bw`** (total
  adds the victim's tiny pointer-chase traffic on the same time base). The legacy
  `bandwidth_gib_s` column still uses global wall time for backward comparability.

---

## 4. ObjPlace — code in detail (`objplace.h` / `objplace.c`)

### Enums (every value)
- `obj_type_t`: `OBJ_GENERIC, OBJ_EMBEDDING, OBJ_FEATURE, OBJ_KV, OBJ_BUFFER`. Mostly
  documentation/intent; does not directly drive the formula. *Example:* an embedding
  table → `OBJ_EMBEDDING`.
- `access_pattern_t`: `ACC_STREAMING` (sequential, high CXL penalty), `ACC_RANDOM`
  (gather, low penalty), `ACC_MIXED` (in between). Sets `base_penalty`.
- `sensitivity_t`: `SENS_BANDWIDTH` (mult 1.0), `SENS_LATENCY` (0.5), `SENS_CAPACITY`
  (0.1). How much DRAM placement is "worth".
- `phase_t`: `PHASE_ACTIVE, INACTIVE, PREFILL, DECODE, GATHER`. Only `INACTIVE` lowers
  the multiplier (0.1); the rest are 1.0. *Example:* an idle KV region → `INACTIVE`.
- `placement_t`: `PLACE_DRAM, PLACE_CXL, PLACE_SPLIT, PLACE_INTERLEAVE`. The planner's
  output. Note **the planner never outputs `PLACE_INTERLEAVE` today** (no candidate);
  `materialize` handles it if set, but nothing sets it — see §5 Example 4.

### `obj_attr_t` (every field; who sets/reads it)
| field | set by | read by | effect | default |
|---|---|---|---|---|
| `type` | caller | (docs) | none in formula | — |
| `size` | caller | planner + materialize | budget accounting, partition sizes | — |
| `access` | caller | `base_penalty` | CXL penalty (1.10/0.60/0.25) | — |
| `sensitivity` | caller | `sens_mult` | benefit weight (1.0/0.5/0.1) | — |
| `hot_fraction` | caller / `obj_update_hotset` | `is_skewed`, partition sizes | split point | 0 |
| `skew_alpha` | caller / `obj_update_hotset` | `hot_access_share`, `is_skewed` | access concentration | 0 |
| `phase` | caller / `obj_update_phase` | `phase_mult` | 1.0 or 0.1 | — |

### `struct objplace_obj` (internal registry record, ~104 bytes)
Fields: `in_use`, `id`, `attr` (the metadata), `planned` (placement_t), `materialized`
(0/1), `would_migrate` (set if a rebalance changed a plan after materialization — but
we never migrate), `hot_buf`/`cold_buf` (allocated buffers), `hot_bytes`/`cold_bytes`.
Stored in a fixed array `g_objs[MAX_OBJS=4096]`. Set by `obj_create`/`materialize`;
read by the planner and the accessors.

### Config globals
`g_dram_node`/`g_cxl_node` (0/1), `g_dram_budget` (default 2 GiB), `g_cxl_load`
(<0 means "assume saturated"), `g_dram_used` (running budget accounting).

### Public API (signature → behavior)
- **`obj_handle_t obj_create(const obj_attr_t *attr)`**
  - Finds a free slot, copies `attr`, assigns an `id`, runs **incremental** `plan(o)`.
  - **No memory allocated. No pages touched. Placement decided (tentatively).**
  - Returns a handle (opaque pointer to the record).
  - *Example:* `obj_handle_t h = obj_create(&attr);`
- **`void obj_rebalance(void)`**
  - Recomputes the **global** plan over all *unmaterialized* objects (re-counts DRAM
    used by materialized ones first). Needed when you created several objects and want
    the budget shared globally rather than first-come-first-served. No allocation.
- **`void *obj_ptr(obj_handle_t h)`**
  - **Materializes** on first call (one `numa_alloc_onnode`), returns the whole-object
    buffer. **Returns NULL for a SPLIT object** (use hot/cold ptr). Placement is fixed
    after this. *Pages are not touched by ObjPlace* — the caller touches them.
- **`void *obj_hot_ptr(h)` / `void *obj_cold_ptr(h)`**
  - Materialize (for SPLIT: hot buffer on DRAM, cold buffer on CXL) and return the
    partition pointer. For non-split, `hot_ptr` returns the single buffer and
    `cold_ptr` returns NULL.
- **`size_t obj_hot_bytes(h)` / `obj_cold_bytes(h)`** — partition sizes (for routing).
- **`void obj_update_phase(h, phase)` / `obj_update_hotset(h, frac, alpha)`**
  - Edit metadata. Re-planned on the next `obj_rebalance` **if not yet materialized**.
- **`void obj_destroy(h)`** — frees buffers (`numa_free`), frees the slot, adjusts
  `g_dram_used`. **(watch:** the DRAM-used decrement is hand-rolled and could drift
  across many create/destroy/rebalance cycles.)
- **`void *obj_alloc_hint(size, hint)`** — compatibility wrapper: builds an `obj_attr_t`
  from the coarse hint, `obj_create`s it, **forces** `planned` to the hinted tier
  (bypassing the budget), and returns `obj_ptr`. `obj_free_hint(ptr,size)` = `numa_free`.

### Concepts
- **Object registry / id / handle:** the array `g_objs`; each object has a unique `id`
  and is referenced by an opaque `obj_handle_t` (= `struct objplace_obj *`).
- **Lazy materialization:** memory is allocated only at first `obj_ptr`/`obj_hot_ptr`/
  `obj_cold_ptr`, per the planned placement. *Create-all → rebalance → materialize →
  run.*
- **No-migration guarantee:** once materialized, placement is fixed; ObjPlace never
  moves pages. A post-materialization re-plan only sets `would_migrate` (advisory).
- **DRAM fast-tier budget:** how many DRAM bytes the planner may spend; models DRAM
  being smaller than the working set (the reason CXL exists).
- **CXL pressure value / ceiling:** `objplace_set_pressure(load)` vs
  `CXL_BW_CEILING_GIB=35.5`; `pressure_factor = clamp(load/35.5, 0, 1.2)`.
- **current placement / split / manual oracle / compatibility wrapper:** the
  `placement_t`; SPLIT = hot→DRAM + cold→CXL; manual oracle = a hand-set placement we
  treat as best; the wrapper = `obj_alloc_hint`.

---

## 5. The planner, with numbers

```
benefit_per_byte = sens_mult × phase_mult × (cxl_penalty − 1) × density
  sens_mult   : BANDWIDTH 1.0 | LATENCY 0.5 | CAPACITY 0.1
  phase_mult  : INACTIVE 0.1  | else 1.0
  cxl_penalty : 1 + base_penalty(access) × pressure_factor
                 base_penalty: STREAMING 1.10 | MIXED 0.60 | RANDOM 0.25
  pressure_factor : clamp(cxl_load / 35.5, 0, 1.2)   (default load=35.5 → 1.0)
  density     : access_share / partition_fraction
                 whole uniform object = 1.0
                 skewed hot partition: share = hot_fraction^(1/(1+alpha)), density = share/hot_fraction
```
- **sensitivity** — how much we care that this object is fast (bandwidth ≫ latency ≫
  capacity). Range 0.1–1.0.
- **phase** — deprioritize idle data. Range 0.1–1.0.
- **cxl_penalty − 1** — how much *worse* CXL is than DRAM for this access type, scaled
  by pressure. At full pressure: streaming ≈ 1.10, random ≈ 0.25.
- **density** — accesses per byte relative to uniform; >1 for a skewed hot partition,
  so concentrated-hot bytes are very valuable on DRAM.

The planner sorts all candidates (whole objects or hot/cold partitions) by
`benefit_per_byte` descending and fills the DRAM budget greedily.

### Example 1 — hotness-only picks wrong (full pressure, pf=1.0)
- **A**: hot, latency-bound, random. `bpb_A = 0.5 × 1.0 × (1.25−1) × 1.0 = 0.125`.
- **B**: less hot, bandwidth-bound, streaming. `bpb_B = 1.0 × 1.0 × (2.10−1) × 1.0 = 1.10`.
- DRAM fits one. **Hotness-only** ranks by hotness → picks A → B stranded on CXL → B
  (bandwidth) suffers ~2× under a co-runner. **ObjPlace** ranks by bpb: B (1.10) ≫ A
  (0.125) → **B on DRAM**. ObjPlace wins because it weighs *sensitivity × CXL-penalty*,
  not hotness. (This is `sensbench`; measured +118%.)

### Example 2 — low pressure: decision does NOT flip (be precise)
- At `cxl_load = 3.55` → `pf = 0.1`: `bpb_A = 0.5×(0.025) = 0.0125`,
  `bpb_B = 1.0×(0.11) = 0.11`. B still ≫ A.
- **Key honest point (watch):** `pressure_factor` is a **common multiplier** of every
  candidate's `(cxl_penalty−1)`, so it **does not change the ranking** between objects
  — it only scales the absolute benefit (here ~10× smaller). So the planner makes the
  *same* DRAM/CXL choice at low and high pressure; what changes is *how much that
  choice is worth in real throughput*. The measured "pressure-aware" win (+67%→+116%)
  comes from the **real workload** suffering more contention at higher load, not from
  the planner re-deciding. A genuinely pressure-sensitive *decision* would need pressure
  to gate a threshold (e.g., DRAM-vs-interleave), which the current planner lacks.
  **(This is the single most over-claimable part of the design — state it carefully.)**

### Example 3 — skewed object → SPLIT (hot 10%, alpha 1.0, full pressure)
- `share = 0.1^(1/2) = 0.316`. Hot partition: `density = 0.316/0.1 = 3.16` →
  `bpb_hot = 1.0×1.0×(1.25−1)×3.16 = 0.79` (random, bandwidth). Cold partition:
  `density = (1−0.316)/(1−0.1) = 0.76` → `bpb_cold = 0.19`.
- Hot bpb (0.79) ≫ cold (0.19): the greedy fill puts the **small dense hot partition
  on DRAM** and the large cold tail on **CXL** → `PLACE_SPLIT`. The caller uses
  `obj_hot_ptr` (DRAM, hot rows = low ids) and `obj_cold_ptr` (CXL), routing accesses
  by index. (This is the embedding/GNN win, ~15% / +8.3%.)

### Example 4 — uniform object → planner can lose to interleave
- Uniform means `skew_alpha=0` → `is_skewed` false → one whole-object candidate. If it
  is bandwidth-bound and **exceeds the DRAM budget**, the greedy fill can't put it on
  DRAM, so it goes **all-CXL**. But the optimal choice for a uniform bandwidth object
  is **interleave** (use DRAM+CXL bandwidth in parallel). The planner has **no
  INTERLEAVE candidate**, so it loses (measured: GNN uniform −11.6% vs interleave).
  Adding an INTERLEAVE candidate with a benefit estimate is the next planner change.

---

## 6. Workload integrations

### `bwbench.c`
- **Allocates:** a 1 GiB **hot** working set (streamed by all worker threads) + a
  larger **cold** capacity region (allocated, lightly touched).
- **Policies:** `allcxl` (both on CXL via `obj_alloc_hint(COLD_CAPACITY)`), `interleave`
  (`numa_alloc_interleaved`), `hint` (hot via `HINT_BW_SENSITIVE`→DRAM, cold via
  `HINT_COLD_CAPACITY`→CXL), `objplace` (register both, `obj_rebalance`, planner picks
  hot→DRAM/cold→CXL with a budget sized to the hot region).
- **Aggressor:** the orchestrator launches a separate `membench --mode=stream-read
  --node=1 --cpu-offset=64` process saturating CXL on disjoint cores; `bwbench` workers
  pin to cores 0..N-1.
- **Throughput:** sum of bytes each worker streamed over wall time → GiB/s.
- **Why it shows protection:** under the aggressor, hot-on-CXL collapses (~17 GiB/s);
  hot-on-DRAM stays ~69 GiB/s → **+315%**.
- **Why +315% is useful but not the whole story:** it is a clean *bandwidth-protection*
  demonstration, but `hint`/`objplace`/`manual` all make the same correct choice here
  (hot=bandwidth=DRAM). The harder, more interesting case is `sensbench`, where
  hotness and sensitivity *disagree*.

### `embbench.py`
- **Embedding table:** a `[rows, row_dim]` array (memory-bound config: `row_dim=2048`,
  ≈8 GiB). `rows` = number of vectors; `row_dim` = vector length.
- **Zipf alpha:** access skew; low `alpha` ≈ uniform, high `alpha` concentrates on
  low-id rows. (Sampled by a bounded inverse-CDF, supports `alpha ≤ 1`.)
- **Hot fraction:** the fraction of (low-id) rows treated as hot.
- **Hot/cold split:** in skew modes, hot rows = a DRAM buffer, cold rows = a CXL buffer;
  the gather routes index `< hot_rows` to hot, else to cold.
- **Placements:** `dram`/`cxl`/`interleave`; `skew` (manual `numa_alloc_onnode`);
  `skew-hint` (same split via `obj_alloc_hint`); `objplace` (register the table as one
  `OBJ_EMBEDDING` object; planner returns SPLIT; use `obj_hot_ptr`/`obj_cold_ptr`).
- **ctypes path:** `get_objplace()` loads `libobjplace.so`, sets `restype`/`argtypes`,
  declares an `ObjAttr` ctypes struct mirroring `obj_attr_t`; `alloc_table_objplace`
  calls `obj_create(byref(attr))`, `obj_rebalance()`, then `obj_hot_ptr`/`obj_cold_ptr`.
- **Passing pointer addresses / NumPy over C memory:** the C calls return `c_void_p`
  addresses; `buf_from_ptr(ptr,size)` wraps them as NumPy uint8 views (no copy).
- **Memory ownership / segfault causes:** ObjPlace owns the buffers; Python must keep
  `_NUMA_KEEPALIVE` references so the views stay valid. A segfault would come from:
  dropping the keepalive while NumPy still reads it; mismatched struct layout (wrong
  `ObjAttr` fields → wrong sizes/placement); or missing `restype=c_void_p` (truncated
  pointer).
- **Why "objplace matches manual" matters:** it proves the runtime/ctypes path adds no
  measurable overhead and reproduces the hand-optimal split → any win is the *policy*.

### `gnnbench.c`
- **GNN feature gather:** each step gathers `batch` neighbor **feature rows** from a
  large `[nodes, feat]` table; vertices sampled degree-skewed (Zipf), low ids = hot.
- **Feature table / vertex batch:** the table is the per-vertex feature store; a batch
  is the set of neighbor vertices gathered in one step.
- **Uniform vs skewed:** uniform (`alpha=0`) has no hot set → placement can't exploit
  skew; skewed (`alpha=1.2`) concentrates on low-id vertices → hot-on-DRAM helps.
- **Why the first version was compute-bound:** it summed each row's floats — arithmetic
  that hides memory latency (~5 GiB/s), so placement barely showed.
- **Why memcpy is memory-bound:** a real GNN *materializes* features into a buffer;
  `memcpy(dst,row,row_bytes)` is pure memory traffic (~20 GiB/s) → placement matters.
- **Skewed win / uniform loss:** skewed +8.3% vs interleave (= manual); uniform −11.6%
  (no INTERLEAVE candidate — §5 Example 4).

### `sensbench.c`
- **Objects:** a bandwidth-bound **stream** object and a latency-bound **chase** object,
  equal size and equal hotness, DRAM budget fits one.
- **hotness-only choice:** equal hotness → it has no way to prefer stream → it protects
  chase (DRAM) and strands stream (CXL).
- **ObjPlace choice:** `bpb_stream ≫ bpb_chase` (sensitivity × penalty) → stream→DRAM.
- **Why +118% supports the thesis:** under a CXL aggressor the bandwidth object's
  throughput is +118% higher with ObjPlace — the cleanest evidence that *sensitivity*,
  not hotness, is the right signal. (Pressure sweep extends this to +67%→+116%.)

---

## 7. Experiments as a debugging story

| Phase | What we thought | What we ran | Result | Right/Wrong | Direction change |
|---|---|---|---|---|---|
| Smoke | "CXL maybe 2× DRAM latency" | membench on node 0/1 | latency 1.5×, BW 35.5 | right | CXL usable; bandwidth is the constraint |
| Phase 1 | confirm baseline | `run-dram-cxl-baseline.sh` (strict placement) | 1.53×, 35.5 GiB/s, 630/630 verified | right | go/no-go passed |
| Phase 2 | "interference is huge" | victim+aggressor **shared cores** | up to 8.75× | **WRONG** | inflated by CPU contention |
| Phase 2.1 | re-measure clean | disjoint cores, **1-thread** victim | ≤1.41× | right but **misleading** | made interference look mild → thesis wobbled |
| Phase 2.2 | "maybe victim must be bandwidth-hungry" | multi-thread victim | **2.0–2.13×** (bandwidth), ≤1.23× (latency) | right | **revived** the thesis, correctly scoped |
| Confirm | reproduce | median-of-5 | 2.01×/2.13×; embedding ~15% | right | locked direction |
| Integration | "does the API match hand placement?" | embbench/bwbench via API | <1% diff; +315% recovery | right | runtime validated |
| Block2 pressure | "is it pressure-aware?" | sensbench × aggressor threads | +67%→+116% (workload-driven) | right (with §5 caveat) | pressure story |
| Block2 budget | "does planner quality matter?" | mixbench × budget | +18–22% at 40–60% | right | benefit-guided > hotness under scarcity |
| Block2 GNN | "does it generalize?" | gnnbench skewed/uniform | +8.3% / −11.6% | mixed | generalizes on skew; needs INTERLEAVE |
| Block2 overhead | "is it cheap?" | obench | create ~10.8 µs, steady ~0% | right | cheap |

**Stable conclusions:** CXL latency ≈1.5× DRAM; CXL BW ≈35.5 GiB/s; bandwidth-bound
CXL victim 2.0–2.13× under co-runner; DRAM not similarly slowed; latency-bound random
victim ≤1.23×; ObjPlace matches manual; ObjPlace beats hotness-only when bandwidth
sensitivity matters; ObjPlace overhead is low.

**Rejected / limited:** not all workloads see severe CXL interference (only
bandwidth-bound); no KV benefit; object-level placement is not new by itself; no
automatic profiling; no page migration.

---

## 8. Result numbers (table)

| Result | Number | Source | Supports | Does NOT prove | Caveat |
|---|---|---|---|---|---|
| CXL latency | 1.53× DRAM | Phase 1 (`…-phase1`) | "latency is fine" | not "as fast as DRAM" | single device |
| CXL bandwidth | 35.5 GiB/s | Phase 1 | "bandwidth is scarce" | not aggregate/multi-device | one CZ120 |
| CXL stream victim slowdown | 2.0–2.13× | Phase 2.2 / confirm | multi-tenant motivation | not "all workloads" | synthetic aggressor |
| random victim slowdown | ≤1.23× | Phase 2.2 | scoping (latency tolerant) | — | — |
| ObjPlace vs manual | <1% | integ / eval T1 | API faithful, low overhead | not a policy *win* | noise band |
| embedding ObjPlace vs interleave | +14.3% (~15%) | eval T2 | skew-aware placement helps | not 38% | memory-bound config |
| bandwidth recovery | +315% vs all-CXL | eval T3 | bandwidth protection | hint=objplace here | not the hard case |
| ObjPlace vs hotness-only | +118% | eval T4 / sensbench | sensitivity > hotness | only when they disagree | constructed scenario |
| DRAM budget sweep | +18–22% | block2 budget | planner quality under scarcity | degenerate ≤20% | mixbench synthetic |
| pressure sweep | +67%→+116% | block2 pressure | win grows with load | planner ranking is pf-invariant (§5) | workload-driven |
| GNN skewed | +8.3% | block2 gnn | generalization | — | memcpy gather |
| GNN uniform | −11.6% | block2 gnn | honest limitation | — | no INTERLEAVE candidate |
| overhead | create ~10.8 µs; rebalance ~0.26 µs/obj; 104 B/obj; steady ~0% | obench | cheap | — | coarse objects |

---

## 9. Baselines

| Baseline | What it does | Represents | Why included | Handles | Misses | Status |
|---|---|---|---|---|---|---|
| DRAM-only | all on node 0 | "fits in DRAM" upper bound | reference ceiling | small data | capacity beyond DRAM | implemented |
| CXL-only | all on node 1 | naive offload | worst case for bandwidth | capacity | bandwidth protection | implemented |
| interleave | `numa_alloc_interleaved` | Linux default for spreading BW | strong, hard to beat for uniform | uniform bandwidth | skew/sensitivity | implemented |
| hotness-only | rank by hotness | classic tiering signal | the thing we beat | hot/cold | bandwidth sensitivity | implemented (strawman in mixbench/sensbench) |
| sensitivity-only | rank by sensitivity class | "sensitivity but ignore skew/density" | isolates the skew term | sensitivity | density/skew | implemented (mixbench) |
| manual oracle | hand-set best placement | upper bound for our policy | shows ObjPlace ≈ optimal | the chosen scenario | generality | implemented |
| **ObjPlace** | benefit-per-byte planner | our system | — | sensitivity+skew+phase+pressure | interleave option, migration | implemented |
| profile-guided | offline AOL-style profiling | SoarAlto-style | claim "online beats offline" | bandwidth/MLP | online adaptivity | **planned** |
| TPP-like | kernel page hotness tiering | established page baseline | reviewer expectation | hotness | objects/bandwidth | **planned** |
| SoarAlto-like | object profile-guided beyond-hotness | closest prior art | must compare | bandwidth sensitivity | online/multi-tenant | **planned** |

---

## 10. Related-work risk (plain words)

Read `Related.md`. The honest situation:
- **Our idea is not obviously new** because every *single* axis already exists in print.
- **SoarAlto (OSDI'25) is dangerous** — it already published "object-level placement
  beyond hotness" using a bandwidth/MLP metric. If we say "first object-level
  sensitivity-aware tiering," a reviewer who knows SoarAlto rejects it. Our difference:
  *online hint-driven (not offline-profiled), multi-tenant, on real CXL.*
- **Memstrata (OSDI'24) is dangerous** — multi-tenant CXL sensitivity isolation on real
  hardware, but at **VM/page** granularity and transparent. Our difference:
  *intra-application object granularity + application hints.*
- **TPP / TMTS / HeMem matter** — they are the established page-level / production
  tiering baselines reviewers expect us to compare against; we currently do not.
- **CXL-KV papers matter** — Beluga/TraCT/Mooncake/LMCache show the LLM-serving framing
  is active; they treat CXL as a flat pool or need custom silicon, so multi-tenant
  commodity-CXL serving placement is open — but it also means "CXL + LLM" alone is not
  novel.

> **Our novelty is NOT "object-level placement."**
> **Our possible novelty is "online, pressure-aware object placement using bandwidth
> sensitivity, skew, and phase under CXL co-tenant pressure, on real commodity CXL."**
> And even that must be argued against SoarAlto + Memstrata, and is currently weakened
> by the synthetic aggressor and the missing baselines.

---

## 11. Limitations and the fix for each

| Limitation | Why it matters | What would fix it |
|---|---|---|
| Single CXL device | can't show aggregate-bandwidth or cross-device contention | free a FAMFS device → ≥2 system-ram CXL nodes |
| Other devices on FAMFS | only one CXL NUMA node available | admin reconfigures `dax0/1` (coordination needed) |
| Synthetic aggressor | the multi-tenant claim isn't from real co-located apps | build a real two-tenant workload (e.g., embedding serve + bandwidth job) |
| No real two-tenant workload | headline novelty rests on a microbenchmark | same as above (highest priority) |
| No INTERLEAVE candidate | loses on uniform bandwidth objects (GNN −11.6%) | add INTERLEAVE to the planner candidate set + a benefit estimate |
| GNN uniform negative | a visible failure case | the INTERLEAVE fix |
| No profile-guided baseline | can't claim "online beats offline" (SoarAlto) | build/borrow an offline AOL-style profiler |
| No TPP/SoarAlto-like baseline | reviewers expect established baselines | port or wrap TPP / a SoarAlto-style policy |
| No KV benefit | layer-split was null | redesign KV bench around request/recency skew |
| No migration | can't adapt to phase changes after materialization | (future) add a measured, bounded migration path |
| No auto profiling | metadata is hand-supplied | (future) lightweight online classification |

**Next steps (rationale only; not started):** 1) INTERLEAVE candidate; 2) profile-guided
baseline; 3) real two-tenant workload; 4) stronger baselines (TPP/MEMTIS/Colloid/
SoarAlto); 5) multi-device once FAMFS freed; 6) KV recency/request-skew redesign.

---

## 12. How to read the code (manual checklist)

Read in this order; for each file, focus + questions to ask yourself.

1. **`docs/DESIGN_OBJPLACE.md`** — focus: the benefit formula and lifecycle. *Ask: why
   object-level? what does each formula term do?*
2. **`system/placement/objplace.h`** — focus: enums, `obj_attr_t`, the API list. *Ask:
   which fields drive the formula vs are documentation?*
3. **`system/placement/objplace.c`** — focus: `partition_bpb`, `hot_access_share`,
   `plan()`, `materialize()`, `obj_alloc_hint()`. *Ask: when is memory allocated? does
   pressure change the ranking? (no — §5). how does SPLIT get chosen?*
4. **`system/placement/test_objplace.c`** — focus: `node_of` (move_pages) + the planner
   assertions. *Ask: what does each PASS prove?*
5. **`benchmarks/memory/membench.c`** — focus: `verify_buffer_placement`, `pin_self`,
   the kernels, loaded-latency aggregation. *Ask: why disjoint cores? why max_kernel_sec?*
6. **`system/placement/bwbench.c`** — focus: the four policies + the aggressor launch.
   *Ask: why do hint and objplace agree here?*
7. **`benchmarks/embedding/embbench.py`** — focus: `get_objplace`, `ObjAttr`,
   `alloc_table_objplace`, `_NUMA_KEEPALIVE`. *Ask: who owns the memory? what causes a
   segfault?*
8. **`system/placement/gnnbench.c`** — focus: the memcpy gather + Zipf sampler +
   policies. *Ask: why was the float-sum version compute-bound?*
9. **eval scripts** (`benchmarks/eval_objplace.py`, `eval_block2.py`, `phase22.py`) —
   focus: how aggressors are launched, median-of-5, what each CSV column is. *Ask:
   which result maps to which claim in `docs/RESULTS.md`?*

---

## 13. Glossary

- **CXL** — Compute Express Link; lets the CPU use device memory over PCIe with normal
  load/store.
- **CXL.mem** — the CXL sub-protocol for memory access.
- **Type 3 device** — a CXL memory expander (just memory; our CZ120).
- **DAX** — Direct Access; memory exposed as a character device for direct CPU access.
- **FAMFS** — Fabric-Attached Memory File System; CXL memory exposed as files.
- **system-ram** — devdax reconfigured into kernel-managed RAM (creates a NUMA node).
- **NUMA node** — a memory locality domain. Node 0 = DRAM (has CPUs); node 1 = CXL (no CPUs).
- **virtual address** — the address a program sees.
- **physical address** — the real memory location; its range determines the node/tier.
- **page table** — maps virtual → physical pages.
- **page fault** — the trap when a process first touches a page; triggers allocation.
- **page placement** — which NUMA node a physical page lives on.
- **move_pages** — syscall; query mode reports each page's node (we use it to verify).
- **CPU pinning** — fixing a thread to specific CPUs (`sched_setaffinity`).
- **disjoint cores** — victim and aggressor on non-overlapping cores (so they contend
  on memory, not CPU).
- **pointer chase** — following `p=*p` through a randomized chain; dependent-load
  latency test.
- **stream read / write** — sequential read / fill; bandwidth test.
- **random read** — random independent cache-line gather; latency/queue-bound.
- **loaded latency** — latency measured while bandwidth is being consumed.
- **victim / aggressor** — measured workload / background load creating contention.
- **bandwidth-bound** — limited by memory bandwidth (suffers most on CXL).
- **latency-bound** — limited by access latency (tolerates CXL).
- **hotness** — access frequency (the classic tiering signal).
- **skew** — non-uniform access (a small hot subset dominates).
- **Zipf alpha** — the skew parameter; higher = more concentrated.
- **phase** — a workload stage (prefill/decode; active/inactive).
- **CXL pressure** — current CXL demand vs the ~35.5 GiB/s ceiling; scales the penalty.
- **benefit per byte** — ObjPlace's score: sensitivity × phase × (CXL-penalty−1) × density.
- **DRAM budget** — fast-tier bytes the planner may spend.
- **interleave** — striping pages across nodes (uses both tiers' bandwidth).
- **hotness-only** — baseline ranking by hotness alone (ignores sensitivity).
- **manual oracle** — hand-chosen best placement; the target ObjPlace matches.
- **profile-guided baseline** — (planned) offline-profiling placement, à la SoarAlto.

*End of detailed guide.*
