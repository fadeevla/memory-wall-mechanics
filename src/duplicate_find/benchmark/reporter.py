"""Formatting and reporting benchmark results."""

import math
from typing import Dict, List, Optional, Tuple


def format_table_cli(
    results: Dict[str, List[Tuple[int, float]]],
    sizes: List[int],
) -> str:
    """Formats benchmark results into an aligned, colored terminal table."""
    lines = []
    separator_width = 34 + 18 * len(sizes)
    sep_line = "=" * separator_width
    sub_sep = "-" * separator_width

    lines.append(sep_line)
    header = f"{'Алгоритм / Algorithm':<32} |"
    for N in sizes:
        eng_n = f"10^{int(math.log10(N))}" if N >= 10 else str(N)
        header += f" N={eng_n:<13} |"
    lines.append(header)
    lines.append(sub_sep)

    # Find best times per N
    best_times: Dict[int, float] = {}
    for N in sizes:
        valid = [
            t for func_name, res in results.items() for n, t in res if n == N and t >= 0
        ]
        best_times[N] = min(valid) if valid else -1.0

    # Sort algorithms by time on max N
    max_N = max(sizes)

    def sort_key(name: str) -> float:
        t = next((val for n, val in results[name] if n == max_N), -1)
        return t if t >= 0 else float("inf")

    sorted_names = sorted(results.keys(), key=sort_key)

    for name in sorted_names:
        row = f"{name:<32} |"
        for N in sizes:
            time_val = next((t for n, t in results[name] if n == N), -1)
            if time_val < 0:
                row += f" {'ERROR / N/A':>15} |"
            else:
                is_best = abs(time_val - best_times[N]) < 1e-6 and time_val > 0
                formatted = f"{time_val:>12.2f} ms"
                if is_best:
                    row += f" \033[1;32m{formatted}\033[0m |"
                else:
                    row += f" {formatted} |"
        lines.append(row)

    lines.append(sep_line)
    return "\n".join(lines)


def export_csv(
    results: Dict[str, List[Tuple[int, float]]],
    sizes: List[int],
    file_path: str,
):
    """Exports benchmark results to a CSV file."""
    with open(file_path, "w", encoding="utf-8") as f:
        headers = ["Algorithm"] + [f"N_{n}" for n in sizes]
        f.write(",".join(headers) + "\n")
        for algo, timings in results.items():
            timing_map = {n: t for n, t in timings}
            row = [algo] + [f"{timing_map.get(n, -1):.4f}" for n in sizes]
            f.write(",".join(row) + "\n")


def export_markdown(
    results: Dict[str, List[Tuple[int, float]]],
    sizes: List[int],
) -> str:
    """Generates a Markdown table of benchmark results."""
    headers = ["**Algorithm**"] + [
        f"**N=10^{int(math.log10(n))}**" if n >= 10 else f"**N={n}**" for n in sizes
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    max_N = max(sizes)
    sorted_names = sorted(
        results.keys(),
        key=lambda k: next(
            (t for n, t in results[k] if n == max_N and t >= 0), float("inf")
        ),
    )

    for name in sorted_names:
        row = [f"`{name}`"]
        timing_map = {n: t for n, t in results[name]}
        for n in sizes:
            t = timing_map.get(n, -1)
            row.append(f"{t:.2f} ms" if t >= 0 else "N/A")
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)
