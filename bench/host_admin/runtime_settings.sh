#!/usr/bin/env bash
# Apply or restore optional, host-wide benchmark settings.

set -euo pipefail

action=${1:-status}
state_file=${BENCH_STATE_FILE:-/var/tmp/duplicate-find-runtime-state}
hugepages=${HUGEPAGES:-1024}

require_root() {
    if [[ ${EUID} -ne 0 ]]; then
        echo "This action changes host-wide settings and requires sudo." >&2
        exit 1
    fi
}

show_status() {
    echo "vm.nr_hugepages=$(sysctl -n vm.nr_hugepages)"
    echo "kernel.perf_event_paranoid=$(sysctl -n kernel.perf_event_paranoid)"
    if [[ -r /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]]; then
        echo "cpu0.governor=$(< /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor)"
    fi
}

case "$action" in
    status)
        show_status
        ;;
    apply)
        require_root
        if [[ -e "$state_file" || -L "$state_file" ]]; then
            echo "State file already exists: $state_file. Restore first." >&2
            exit 1
        fi
        {
            echo "HUGEPAGES_PREVIOUS=$(sysctl -n vm.nr_hugepages)"
            echo "PERF_PARANOID_PREVIOUS=$(sysctl -n kernel.perf_event_paranoid)"
            if [[ -r /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]]; then
                echo "GOVERNOR_PREVIOUS=$(< /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor)"
            fi
        } > "$state_file"
        chmod 600 "$state_file"
        sysctl -w "vm.nr_hugepages=$hugepages"
        sysctl -w kernel.perf_event_paranoid=-1
        if command -v cpupower >/dev/null; then
            cpupower frequency-set -g performance >/dev/null
        fi
        echo "Applied settings. Restore with: sudo $0 restore"
        ;;
    restore)
        require_root
        if [[ ! -r "$state_file" ]]; then
            echo "No saved state at $state_file" >&2
            exit 1
        fi
        if [[ -L "$state_file" ]] || [[ $(stat -c %u "$state_file") -ne 0 ]]; then
            echo "Refusing an untrusted state file: $state_file" >&2
            exit 1
        fi
        hugepages_previous=$(sed -n 's/^HUGEPAGES_PREVIOUS=//p' "$state_file")
        perf_previous=$(sed -n 's/^PERF_PARANOID_PREVIOUS=//p' "$state_file")
        governor_previous=$(sed -n 's/^GOVERNOR_PREVIOUS=//p' "$state_file")
        if [[ ! "$hugepages_previous" =~ ^[0-9]+$ ]] || [[ ! "$perf_previous" =~ ^-?[0-9]+$ ]]; then
            echo "Invalid saved runtime values; refusing restore." >&2
            exit 1
        fi
        sysctl -w "vm.nr_hugepages=$hugepages_previous"
        sysctl -w "kernel.perf_event_paranoid=$perf_previous"
        if [[ -n "$governor_previous" ]] && command -v cpupower >/dev/null; then
            cpupower frequency-set -g "$governor_previous" >/dev/null
        fi
        rm "$state_file"
        echo "Restored saved runtime settings."
        ;;
    *)
        echo "Usage: sudo $0 {status|apply|restore}" >&2
        exit 2
        ;;
esac
