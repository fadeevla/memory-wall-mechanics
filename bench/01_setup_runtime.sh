#!/bin/bash
# Запуск: sudo ./01_setup_runtime.sh

set -e # Остановка при любой ошибке

# Проверка прав root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Этот скрипт должен быть запущен от имени root (sudo)" 
   exit 1
fi

echo "🚀 Настройка системы для экстремального бенчмаркинга..."

# 1. Выделение 2 ГБ памяти под HugePages (1024 страницы по 2 МБ)
echo "📦 Выделение 1024 HugePages (2048 MB)..."
sysctl -w vm.nr_hugepages=1024

# 2. Снижение параноидальности perf, чтобы запускать замеры без sudo
echo "🔓 Разрешение доступа к аппаратным счетчикам (perf)..."
sysctl -w kernel.perf_event_paranoid=-1

# 3. Фиксация частоты процессора на максимуме (отключение энергосбережения)
# Проверяем, установлена ли утилита cpupower
if command -v cpupower &> /dev/null; then
    echo "⚡ Установка CPU Governor в режим 'performance'..."
    cpupower frequency-set -g performance > /dev/null
else
    echo "⚠️ Утилита cpupower не найдена. Установите: sudo apt install linux-cpupower"
fi

echo "✅ Среда успешно настроена!"
