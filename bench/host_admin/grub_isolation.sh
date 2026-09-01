#!/usr/bin/env bash
# Print or explicitly apply reversible GRUB CPU-isolation settings.

set -euo pipefail

action=${1:-preview}
isolated_cpus=${ISOLATED_CPUS:-}
grub_file=${GRUB_FILE:-/etc/default/grub}
backup_file="${grub_file}.duplicate-find.bak"

if [[ "$action" == "restore" ]]; then
    if [[ ${EUID} -ne 0 ]]; then
        echo "Restore requires sudo." >&2
        exit 1
    fi
    if [[ ! -r "$backup_file" ]]; then
        echo "Backup not found: $backup_file" >&2
        exit 1
    fi
    cp "$backup_file" "$grub_file"
    update-grub
    rm "$backup_file"
    echo "Restored $grub_file; reboot required."
    exit 0
fi

if [[ -z "$isolated_cpus" ]]; then
    echo "Set ISOLATED_CPUS after checking lscpu -e, for example:" >&2
    echo "  ISOLATED_CPUS=2,4 $0 preview" >&2
    exit 2
fi
if [[ ! "$isolated_cpus" =~ ^[0-9]+([,-][0-9]+)*$ ]]; then
    echo "ISOLATED_CPUS must contain only CPU numbers, commas, and ranges." >&2
    exit 2
fi

parameters="isolcpus=$isolated_cpus nohz_full=$isolated_cpus rcu_nocbs=$isolated_cpus"
echo "Proposed kernel parameters: $parameters"
if [[ "$action" == "preview" ]]; then
    echo "No changes made. Re-run with sudo and the apply argument after review."
    exit 0
fi
if [[ "$action" != "apply" ]]; then
    echo "Usage: ISOLATED_CPUS=... $0 {preview|apply|restore}" >&2
    exit 2
fi
if [[ ${EUID} -ne 0 ]]; then
    echo "Apply requires sudo." >&2
    exit 1
fi
if [[ -e "$backup_file" || -L "$backup_file" ]]; then
    echo "Backup already exists: $backup_file; restore it before another apply." >&2
    exit 1
fi
if grep -qE '(^|[[:space:]])isolcpus=' "$grub_file"; then
    echo "Existing isolcpus configuration found; refusing an automatic edit." >&2
    exit 1
fi

cp "$grub_file" "$backup_file"
sed -i "s/GRUB_CMDLINE_LINUX_DEFAULT=\"/GRUB_CMDLINE_LINUX_DEFAULT=\"$parameters /" "$grub_file"
if ! grep -q "isolcpus=$isolated_cpus" "$grub_file"; then
    cp "$backup_file" "$grub_file"
    rm "$backup_file"
    echo "Expected GRUB assignment was not found; no change retained." >&2
    exit 1
fi
update-grub
echo "Applied isolation settings; reboot required. Restore with: sudo $0 restore"
