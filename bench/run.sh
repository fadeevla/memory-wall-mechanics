#!/usr/bin/env bash
# Usage: CPU_SET=2,4 NUMBA_NUM_THREADS=2 ./bench/run.sh [SCRIPT] [ARGS...]

set -euo pipefail

script_name=${1:-main.py}
cpu_set=${CPU_SET:-}
python_bin=${PYTHON_BIN:-python3}
command=("$python_bin" "$script_name" "${@:2}")

echo "Running benchmark: script=$script_name cpus=${cpu_set:-current-affinity}"
if [[ -n "$cpu_set" ]]; then
    taskset -c "$cpu_set" "${command[@]}"
else
    "${command[@]}"
fi
