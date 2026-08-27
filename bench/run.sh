#!/bin/bash
# Запуск: ./bench/run.sh benchmark_memory_wall.py 

SCRIPT_NAME=${1:-"benchmark_memory_wall.py"} # Если скрипт не указан, по умолчанию ищем 287.py
TARGET_CORE=10,8,6,4,2     # Логическое ядро, на котором запускаем код

echo "🔬 Запуск бенчмарка в лабораторных условиях..."
echo "📄 Скрипт: $SCRIPT_NAME"
echo "🧠 Привязка к ядру (CPU Pinning): Core $TARGET_CORE"
echo "🛡️  Отключение ASLR: Включено"

# setarch x86_64 -R: Отключает рандомизацию адресного пространства
# taskset -c: Привязывает выполнение к конкретному потоку
# stdbuf -oL: Делает вывод в консоль немедленным (без буферизации)

setarch x86_64 -R taskset -c $TARGET_CORE stdbuf -oL python3 "$SCRIPT_NAME"
