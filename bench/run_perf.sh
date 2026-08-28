#!/bin/bash
# Запуск: ./bench/run_perf.sh [ALGORITHM] [N]
# Пример: ./bench/run_perf.sh findDuplicate_floyd_numba 10000000

set -e

ALGO=${1:-"findDuplicate_floyd_numba"}
N=${2:-"10000000"}
TARGET_CORE=${3:-"2"}

echo "📊 Профилирование аппаратных счетчиков с помощью perf stat..."
echo "🔹 Алгоритм: $ALGO"
echo "🔹 Размер N: $N"
echo "🔹 Ядро: $TARGET_CORE"

PERF_EVENTS="cycles,instructions,cache-references,cache-misses,L1-dcache-loads,L1-dcache-load-misses,dTLB-loads,dTLB-load-misses"

taskset -c "$TARGET_CORE" perf stat -e "$PERF_EVENTS" python3 -c "
import numpy as np, random, sys, os
sys.path.insert(0, os.path.abspath('src'))
from duplicate_find.algorithms import ALGORITHMS, warmup_numba_kernels

warmup_numba_kernels()
n = int($N)
arr = list(range(1, n + 1)) + [n]
random.shuffle(arr)
data = np.array(arr, dtype=np.int32)

func = ALGORITHMS['$ALGO']
res = func(data)
print(f'Done. Result: {res}')
"
