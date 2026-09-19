#!/usr/bin/env bash
# F1: all three clients at once on one store for <seconds> (default 600), with a DRAM aggressor burst
# every minute. Invariants: every client verifies its own data (VeloC restart byte-exact, PyTorch reload
# equal, every KV hit checked word by word), no failed store, and after a sweep no segment is left.
# usage: f1_all.sh <outdir> [seconds]
set -u; OUT=$1; SECS=${2:-600}; mkdir -p "$OUT"; cd "$(dirname "$0")/../.."; B=$PWD/build; W=$PWD/../../workloads; FAILS=0
V=$HOME/apps/veloc-cxlpath-inst; export LD_LIBRARY_PATH=$V/lib64:$HOME/checkpoint/veloc_lib/lib64:${LD_LIBRARY_PATH:-} PATH=$V/bin:$PATH
ok() { if [ "$1" = 0 ]; then echo "  ok   $2"; else echo "  FAIL $2"; FAILS=$((FAILS+1)); fi; }
SCR=/dev/shm/cxlp_veloc_scratch; META=/dev/shm/cxlp_veloc_meta; PER=/mnt/local/ghu4/cxlp_veloc_persistent
pkill -x veloc-backend 2>/dev/null; rm -f /dev/shm/*veloc-* /dev/shm/*queue* 2>/dev/null; rm -rf $SCR $META $PER; mkdir -p $SCR $META $PER
CFG=$OUT/veloc.cfg; printf 'scratch = %s\npersistent = %s\nmeta = %s\nmax_versions = 8\nscratch_versions = 8\nmode = async\n' $SCR $PER $META > $CFG
CXLP_OBJ_SLOTS=65536 $B/cxlp_mkstore f1 16384 4096 /dev/dax0.0 /dev/dax1.0 | sed 's/^/    /'
$B/cxlpathd f1 --cpu 16 --log $OUT/F1-daemon.csv & DPID=$!; for i in $(seq 100); do sleep 0.05; $B/cxlp_admin f1 view 2>/dev/null | grep -q alive=1 && break; done
END=$(( $(date +%s) + SECS )); export VELOC_CXLPATH_STORE=f1
( n=0; e=0; while [ $(date +%s) -lt $END ]; do $B/veloc_roundtrip write $CFG > /dev/null 2>&1 || e=$((e+1)); $B/veloc_roundtrip check $CFG 3 2>/dev/null | grep -q "byte-exact" || e=$((e+1)); n=$((n+1)); done; echo "VELOC round_trips=$n ERRORS=$e" ) > $OUT/F1-veloc.txt &
( n=0; e=0; cd $HOME/apps/lulesh-veloc; while [ $(date +%s) -lt $END ]; do LULESH_VELOC_CFG=$CFG LULESH_CKPT_EVERY=5 OMP_NUM_THREADS=16 OMP_PROC_BIND=close OMP_PLACES=cores timeout 300 mpirun --bind-to none -np 1 -x PATH -x LD_LIBRARY_PATH -x VELOC_CXLPATH_STORE ./lulesh2.0.veloc -s 100 -i 100 2>&1 | grep -q "Elapsed" || e=$((e+1)); n=$((n+1)); done; echo "LULESH runs=$n ERRORS=$e" ) > $OUT/F1-lulesh.txt &
python3 -u clients/pytorch/loop_dcp.py f1 $SECS /mnt/local/ghu4/cxlpath_test/f1dcp 2>/dev/null | grep -E "^DCP" > $OUT/F1-dcp.txt &
( while [ $(date +%s) -lt $END ]; do for t in conversation toolagent; do [ $(date +%s) -lt $END ] && $B/cxlp_kv_replay f1 $W/mooncake_${t}_trace.jsonl 4096 1500 10 | grep -E "^KV requests"; done; done ) > $OUT/F1-kv.txt &
( while [ $(date +%s) -lt $((END-10)) ]; do sleep 55; $B/dram_aggressor 64 32 5 | grep AGGRESSOR; done ) > $OUT/F1-aggressor.txt &
wait %2 %3 %4 %5 %6 2>/dev/null; sleep 5
echo "  after ${SECS} s:"; for f in veloc lulesh dcp; do sed 's/^/    /' $OUT/F1-$f.txt; done
awk '{r+=1; split($3,a,"="); b+=a[2]; split($4,h,"="); hh+=h[2]; for(i=1;i<=NF;i++){ if($i ~ /^VERIFY_ERRORS=/){split($i,v,"="); ve+=v[2]} if($i ~ /^put_failures=/){split($i,pf,"="); p+=pf[2]} } } END{printf "    KV replays=%d blocks=%d hits=%d put_failures=%d VERIFY_ERRORS=%d\n", r, b, hh, p, ve}' $OUT/F1-kv.txt | tee $OUT/F1-kv-sum.txt
echo "    aggressor bursts: $(wc -l < $OUT/F1-aggressor.txt)"
grep -q "ERRORS=0" $OUT/F1-veloc.txt; ok $? "VeloC: every round trip restarted byte-exact"
grep -q "ERRORS=0" $OUT/F1-lulesh.txt; ok $? "LULESH + VeloC: every run completed"
grep -q "ERRORS=0" $OUT/F1-dcp.txt; ok $? "PyTorch: every reload equal to the checkpoint-time tensors (from CXL and from NVMe)"
grep -q "put_failures=0 VERIFY_ERRORS=0" $OUT/F1-kv-sum.txt; ok $? "KV: every hit byte-exact, no failed store"
$B/cxlp_admin f1 view | sed 's/^/    /'
HALV=$(grep -c HALVE $OUT/F1-daemon.csv); echo "    policy: $HALV fast decreases, $(awk -F, '$1+0>0 && $6>0' $OUT/F1-daemon.csv | wc -l) epochs with GPU chunks on the staged path"
sleep 3; $B/cxlp_admin f1 sweep | sed 's/^/    /'; $B/cxlp_admin f1 sweep > /dev/null; ok $? "no segment left after releasing every object and buffer set (no leak)"
kill -TERM $DPID; wait $DPID 2>/dev/null; $B/cxlp_admin f1 destroy; pkill -x veloc-backend 2>/dev/null
[ $FAILS = 0 ] && echo PASS || echo "FAIL ($FAILS)"; exit $FAILS
