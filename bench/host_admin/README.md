# Optional host administration

These scripts change machine-wide Linux settings and are deliberately separated
from the normal benchmark path. Timing and correctness experiments do not require
them. Review each script and its saved-state or backup path before running it on a
machine you control.

- `runtime_settings.sh status|apply|restore` manages HugePages, perf permissions,
  and the CPU governor.
- `grub_isolation.sh preview|apply|restore` manages an explicitly selected CPU
  isolation configuration and requires a reboot after apply or restore.
