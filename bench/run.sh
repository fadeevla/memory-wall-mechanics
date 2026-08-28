#!/bin/bash
# Запуск: ./bench/run.sh [SCRIPT_NAME]

SCRIPT_NAME=${1:-"main.py"} # По умолчанию запускаем main.py
TARGET_CORE=${TARGET_CORE:-"10,8,6,4,2"}     # Логические ядра для NUMBA/процесса

echo "🔬 Запуск бенчмарка в лабораторных условиях..."
echo "📄 Скрипт: $SCRIPT_NAME"
echo "🧠 Привязка к ядру (CPU Pinning): Cores $TARGET_CORE"
echo "🛡️  Отключение ASLR: Включено"

# setarch x86_64 -R: Отключает рандомизацию адресного пространства
# taskset -c: Привязывает выполнение к конкретным ядрам
# stdbuf -oL: Делает вывод в консоль немедленным (без буферизации)

setarch x86_64 -R taskset -c $TARGET_CORE stdbuf -oL python3 "$SCRIPT_NAME" "${@:2}"
