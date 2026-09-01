#!/usr/bin/env bash
# Usage: CPU_SET=2 NUMBA_NUM_THREADS=1 ./bench/run_perf.sh ALGORITHM N REPEATS

set -euo pipefail

algorithm=${1:-findDuplicate_floyd_numba}
n=${2:-10000000}
repeats=${3:-5}
cpu_set=${CPU_SET:-}
events=${PERF_EVENTS:-cycles,instructions,cache-references,cache-misses,L1-dcache-loads,L1-dcache-load-misses,dTLB-loads,dTLB-load-misses}
output=${PERF_OUTPUT:-}
python_bin=${PYTHON_BIN:-python3}

args=("$algorithm" "$n" --repeats "$repeats" --events "$events")
if [[ -n "$cpu_set" ]]; then
    args+=(--cpus "$cpu_set")
fi
if [[ -n "$output" ]]; then
    args+=(--output "$output")
fi

echo "Profiling only the warmed algorithm region"
echo "algorithm=$algorithm n=$n repeats=$repeats cpus=${cpu_set:-current-affinity}"
if [[ -n "$output" ]]; then
    echo "perf_csv=$output metadata=${output}.metadata.json"
fi
"$python_bin" bench/profile_target.py "${args[@]}"
