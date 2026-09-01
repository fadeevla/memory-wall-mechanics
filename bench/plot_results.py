#!/usr/bin/env python3
"""Render timing JSON as a dependency-free SVG with seed-level confidence bars."""

import argparse
import html
import json
import math
from pathlib import Path
from typing import Dict, List, Tuple


COLORS = ["#2563eb", "#dc2626", "#059669", "#7c3aed", "#d97706", "#0891b2"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_json")
    parser.add_argument("output_svg")
    parser.add_argument("--algorithms", nargs="+")
    parser.add_argument("--title", default="Controlled Python performance matrix")
    args = parser.parse_args()

    payload = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    measurements = payload["measurements"]
    selected = args.algorithms or sorted({item["algorithm"] for item in measurements})
    points: Dict[str, List[Tuple[float, float, float, float]]] = {name: [] for name in selected}
    for item in measurements:
        if item["algorithm"] not in points or not item["statistics"]:
            continue
        stats = item["statistics"]
        points[item["algorithm"]].append(
            (
                float(item["n"]),
                float(stats["median_ms"]),
                float(stats["median_ci95_low_ms"]),
                float(stats["median_ci95_high_ms"]),
            )
        )
    points = {name: sorted(values) for name, values in points.items() if values}
    if not points:
        raise SystemExit("no matching measurements")

    width, height = 960, 560
    left, right, top, bottom = 90, 300, 55, 75
    plot_width, plot_height = width - left - right, height - top - bottom
    all_points = [point for values in points.values() for point in values]
    x_values = [math.log10(point[0]) for point in all_points]
    y_values = [math.log10(value) for point in all_points for value in point[2:4] if value > 0]
    x_min, x_max = math.floor(min(x_values)), math.ceil(max(x_values))
    y_min, y_max = math.floor(min(y_values)), math.ceil(max(y_values))
    if x_min == x_max:
        x_max += 1
    if y_min == y_max:
        y_max += 1

    def x_coord(value: float) -> float:
        return left + (math.log10(value) - x_min) / (x_max - x_min) * plot_width

    def y_coord(value: float) -> float:
        return top + (y_max - math.log10(max(value, 1e-12))) / (y_max - y_min) * plot_height

    lines = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" viewBox="0 0 {width} {height}">'
        ),
        '<rect width="100%" height="100%" fill="white"/>',
        (
            f'<text x="{left}" y="30" font-family="sans-serif" font-size="20" '
            f'font-weight="bold">{html.escape(args.title)}</text>'
        ),
        (
            f'<line x1="{left}" y1="{top + plot_height}" '
            f'x2="{left + plot_width}" y2="{top + plot_height}" stroke="#111827"/>'
        ),
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#111827"/>',
    ]
    for exponent in range(x_min, x_max + 1):
        x = x_coord(10**exponent)
        lines.extend(
            [
                (
                    f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" '
                    f'y2="{top + plot_height}" stroke="#e5e7eb"/>'
                ),
                (
                    f'<text x="{x:.1f}" y="{top + plot_height + 24}" '
                    f'text-anchor="middle" font-family="sans-serif" font-size="12">'
                    f'10^{exponent}</text>'
                ),
            ]
        )
    for exponent in range(y_min, y_max + 1):
        y = y_coord(10**exponent)
        lines.extend(
            [
                (
                    f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_width}" '
                    f'y2="{y:.1f}" stroke="#e5e7eb"/>'
                ),
                (
                    f'<text x="{left - 12}" y="{y + 4:.1f}" text-anchor="end" '
                    f'font-family="sans-serif" font-size="12">10^{exponent}</text>'
                ),
            ]
        )

    for index, (name, values) in enumerate(points.items()):
        color = COLORS[index % len(COLORS)]
        coordinates = " ".join(
            f"{x_coord(n):.1f},{y_coord(median):.1f}" for n, median, _, _ in values
        )
        lines.append(
            f'<polyline points="{coordinates}" fill="none" stroke="{color}" '
            'stroke-width="2"/>'
        )
        for n, median, low, high in values:
            x, y = x_coord(n), y_coord(median)
            low_y, high_y = y_coord(max(low, 1e-12)), y_coord(max(high, 1e-12))
            lines.append(
                f'<line x1="{x:.1f}" y1="{high_y:.1f}" x2="{x:.1f}" '
                f'y2="{low_y:.1f}" stroke="{color}"/>'
            )
            lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{color}"/>')
        legend_y = top + 20 + index * 28
        lines.append(
            f'<line x1="{left + plot_width + 25}" y1="{legend_y}" '
            f'x2="{left + plot_width + 50}" y2="{legend_y}" '
            f'stroke="{color}" stroke-width="3"/>'
        )
        lines.append(
            f'<text x="{left + plot_width + 58}" y="{legend_y + 4}" '
            f'font-family="sans-serif" font-size="12">{html.escape(name)}</text>'
        )
    lines.extend(
        [
            (
                f'<text x="{left + plot_width / 2}" y="{height - 20}" '
                'text-anchor="middle" font-family="sans-serif" font-size="14">'
                'Input size N (log scale)</text>'
            ),
            (
                f'<text x="22" y="{top + plot_height / 2}" '
                f'transform="rotate(-90 22 {top + plot_height / 2})" '
                'text-anchor="middle" font-family="sans-serif" font-size="14">'
                'Median latency, ms (log scale)</text>'
            ),
            (
                '<text x="660" y="535" font-family="sans-serif" font-size="11" '
                'fill="#4b5563">Bars: bootstrap 95% CI across data-seed medians</text>'
            ),
            "</svg>",
        ]
    )
    Path(args.output_svg).write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
