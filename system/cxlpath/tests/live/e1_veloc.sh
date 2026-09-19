#!/usr/bin/env bash
# E1 live gate: VeloC (project copy ~/apps/veloc-src + clients/veloc/veloc-cxlpath.patch, installed in
# ~/apps/veloc-cxlpath-inst) checkpoints through cxlpath.
#  (a) API round trip: 3 versions -> restart in a new process from CXL, byte-exact; after the store is
#      destroyed (reboot) stock VeloC restarts from the drained NVMe file, byte-exact.
#  (b) LULESH: the checkpoint file cxlpathd drains to NVMe is byte-identical to the file stock VeloC
#      writes for the same version; LULESH restarts from CXL.
# usage: e1_veloc.sh <outdir>
set -u; OUT=$1; mkdir -p "$OUT"; cd "$(dirname "$0")/../.."; B=$PWD/build; FAILS=0
V=$HOME/apps/veloc-cxlpath-inst; export LD_LIBRARY_PATH=$V/lib64:$HOME/checkpoint/veloc_lib/lib64:${LD_LIBRARY_PATH:-} PATH=$V/bin:$PATH
ok() { if [ "$1" = 0 ]; then echo "  ok   $2"; else echo "  FAIL $2"; FAILS=$((FAILS+1)); fi; }
SCR=/dev/shm/cxlp_veloc_scratch; META=/dev/shm/cxlp_veloc_meta; PER=/mnt/local/ghu4/cxlp_veloc_persistent
reset_veloc() { pkill -x veloc-backend 2>/dev/null; sleep 1; rm -f /dev/shm/*veloc-* /dev/shm/*queue* 2>/dev/null; rm -rf $SCR $META; mkdir -p $SCR $META $PER; }
CFG=$OUT/veloc.cfg; printf 'scratch = %s\npersistent = %s\nmeta = %s\nmax_versions = 8\nscratch_versions = 8\nmode = async\n' $SCR $PER $META > $CFG
mpicc -O2 -o $B/veloc_roundtrip clients/veloc/veloc_roundtrip.c -I$V/include -L$V/lib64 -lveloc-client -Wl,-rpath,$V/lib64 || exit 1
start_daemon() { $B/cxlp_mkstore veloc 8192 0 /dev/dax0.0 /dev/dax1.0 > /dev/null; $B/cxlpathd veloc --cpu 16 --log $OUT/$1 & DPID=$!; for i in $(seq 100); do sleep 0.05; $B/cxlp_admin veloc view 2>/dev/null | grep -q alive=1 && break; done; }
stop_daemon() { kill -TERM $DPID; wait $DPID 2>/dev/null; }

echo "E1.a VeloC API round trip"
reset_veloc; rm -rf $PER/*; start_daemon E1a-daemon.csv
VELOC_CXLPATH_STORE=veloc $B/veloc_roundtrip write $CFG | tail -2 | sed 's/^/    /'
ls $SCR | grep -q . ; ok $((1-$?)) "no scratch file was written (the checkpoint went to CXL)"
VELOC_CXLPATH_STORE=veloc $B/veloc_roundtrip check $CFG 3 > $OUT/E1a-check-cxl.txt; R=$?; sed 's/^/    /' $OUT/E1a-check-cxl.txt | tail -2; ok $R "restart in a new process from CXL, newest version, byte-exact"
for i in $(seq 300); do [ -s $PER/rt-0-3.dat ] && $B/cxlp_admin veloc view | grep -q . && sleep 0.2 && break; sleep 0.1; done; sleep 2
ls -l $PER | awk 'NR>1{print "    drained: "$9" "$5" bytes"}'
stop_daemon; $B/cxlp_admin veloc destroy; reset_veloc                       # reboot: store and scratch gone, NVMe files stay
$B/veloc_roundtrip check $CFG 3 > $OUT/E1a-check-nvme.txt; R=$?; sed 's/^/    /' $OUT/E1a-check-nvme.txt | tail -2; ok $R "after the store is gone: STOCK VeloC path restarts from the drained NVMe file, byte-exact"

echo "E1.b LULESH -s 100 -i 20, checkpoint every 5 cycles"
L=$HOME/apps/lulesh-veloc; run_lulesh() { ( cd $L; LULESH_VELOC_CFG=$CFG LULESH_CKPT_EVERY=5 OMP_NUM_THREADS=16 OMP_PROC_BIND=close OMP_PLACES=cores timeout 600 mpirun --bind-to none -np 1 -x PATH -x LD_LIBRARY_PATH ${1:+-x VELOC_CXLPATH_STORE} ./lulesh2.0.veloc -s 100 -i 20 2>&1 | grep -E "LULESH\+VELOC|Elapsed|Final Origin" ); }
reset_veloc; rm -rf $PER/*; run_lulesh > $OUT/E1b-lulesh-stock.txt; sleep 8; pkill -x veloc-backend; mkdir -p $OUT/stock; cp $PER/lulesh-0-*.dat $OUT/stock/ 2>/dev/null; ls $OUT/stock | sed 's/^/    stock VeloC persistent: /'
reset_veloc; rm -rf $PER/*; start_daemon E1b-daemon.csv
export VELOC_CXLPATH_STORE=veloc; run_lulesh 1 > $OUT/E1b-lulesh-cxlpath.txt; grep -E "ckpt|Elapsed" $OUT/E1b-lulesh-cxlpath.txt | tail -3 | sed 's/^/    /'
sleep 6; SAME=1; N=0; for f in $OUT/stock/lulesh-0-*.dat; do b=$(basename $f); if [ -f $PER/$b ]; then N=$((N+1)); cmp -s $f $PER/$b || SAME=0; fi; done
echo "    compared $N checkpoint files (stock VeloC vs drained by cxlpathd)"; [ $N -gt 0 ] && [ $SAME = 1 ]; ok $? "drained checkpoint files byte-identical to stock VeloC's files"
run_lulesh 1 > $OUT/E1b-lulesh-restart.txt; grep -E "restart" $OUT/E1b-lulesh-restart.txt | sed 's/^/    /'; grep -q "restart v=.* rc=0" $OUT/E1b-lulesh-restart.txt; ok $? "LULESH restarts from the newest version on CXL (rc=0)"
unset VELOC_CXLPATH_STORE; stop_daemon; $B/cxlp_admin veloc destroy; pkill -x veloc-backend; rm -rf $OUT/stock
[ $FAILS = 0 ] && echo PASS || echo "FAIL ($FAILS)"; exit $FAILS
