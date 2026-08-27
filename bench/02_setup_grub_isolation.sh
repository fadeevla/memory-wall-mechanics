#!/bin/bash
# Запуск: sudo ./03_setup_grub_isolation.sh

set -e

if [[ $EUID -ne 0 ]]; then
   echo "❌ Требуются права root" 
   exit 1
fi

GRUB_FILE="/etc/default/grub"
ISOL_PARAMS="isolcpus=10,11 nohz_full=10,11 rcu_nocbs=10,11"

echo "🛑 Настройка жесткой изоляции ядер 10 и 11..."

# Проверяем, не добавлены ли параметры уже
if grep -q "isolcpus" "$GRUB_FILE"; then
    echo "⚠️ Параметры изоляции уже присутствуют в $GRUB_FILE. Отредактируйте вручную."
    exit 1
fi

# Делаем бэкап на всякий случай
cp "$GRUB_FILE" "${GRUB_FILE}.bak"
echo "💾 Создан бэкап: ${GRUB_FILE}.bak"

# Добавляем параметры в строку GRUB_CMDLINE_LINUX_DEFAULT
sed -i "s/GRUB_CMDLINE_LINUX_DEFAULT=\"[^\"]*/& $ISOL_PARAMS/" "$GRUB_FILE"

echo "🔄 Обновление GRUB..."
update-grub

echo "✅ Готово. Чтобы изменения вступили в силу, необходимо ПЕРЕЗАГРУЗИТЬ систему."
echo "После перезагрузки используйте 02_run_benchmark.sh для запуска кода на изолированных ядрах."
