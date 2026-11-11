#!/bin/bash
# Wait until the given replay tags are listed as finished in <results dir>/done.txt (queue_adm.sh), run the per-run analysis for each
# (post_adm.sh) and print the one-row-per-configuration table of the overloaded tool-agent replay.
# usage: wait_adm.sh <results dir> <tag> [<tag> ...]
S=$(dirname "$(readlink -f "$0")"); PY=${PY:-/mnt/local/ghu4/envs/agent/bin/python}; R=$1; shift
for tag in "$@"; do
  until grep -q "^end $tag " "$R/done.txt" 2>/dev/null; do sleep 20; done
  grep "^end $tag " "$R/done.txt"; "$S/post_adm.sh" "$R" "$tag"
done
$PY "$S/table_adm_variants.py" "$R" tool08-320-base tool08-320-base2 tool08-320-sync tool08-320-lpt1024 tool08-320-priohits tool08-320-storefix tool08-320-tokfast11 tool08-320-tokfast12 tool08-320-p1 tool08-320-p2 tool08-320-p2-r2 tool08-320-p3 tool08-320-p2-skip10 tool08-320-p2-skip30 tool08-320-skip tool08-320-p1-a20 tool08-320-p2-sync 2>/dev/null | cut -c1-330
