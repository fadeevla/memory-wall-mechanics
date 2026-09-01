#!/usr/bin/env python3
"""Capture reproducible LLVM IR or assembly for a registered Numba implementation."""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from duplicate_find.algorithms import ALGORITHM_SPECS, warmup_numba_kernels
from duplicate_find.benchmark.runner import collect_environment


def main() -> None:
    compiled = [name for name, spec in ALGORITHM_SPECS.items() if spec.compiled]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("algorithm", choices=compiled)
    parser.add_argument("--kind", choices=["llvm", "asm"], default="llvm")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    warmup_numba_kernels()
    function = ALGORITHM_SPECS[args.algorithm].function
    signature = function.signatures[0]  # type: ignore[attr-defined]
    if args.kind == "llvm":
        evidence = function.inspect_llvm(signature)  # type: ignore[attr-defined]
        vector_markers = ["<2 x", "<4 x", "<8 x", "<16 x"]
    else:
        evidence = function.inspect_asm(signature)  # type: ignore[attr-defined]
        vector_markers = ["xmm", "ymm", "zmm", "vpopcnt", "vpadd", "vpsrl"]

    output_path = Path(args.output)
    output_path.write_text(evidence, encoding="utf-8")
    markers_found = sorted(marker for marker in vector_markers if marker in evidence.lower())
    metadata = {
        "schema_version": 1,
        "algorithm": args.algorithm,
        "kind": args.kind,
        "numba_signature": str(signature),
        "sha256": hashlib.sha256(evidence.encode()).hexdigest(),
        "vector_markers_found": markers_found,
        "interpretation_warning": (
            "Markers are a search aid, not proof that the hot loop vectorized; "
            "inspect the loop body and target instructions."
        ),
        "environment": collect_environment(),
    }
    Path(f"{args.output}.metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {args.kind} evidence to {output_path}")
    print(f"Vector search markers: {markers_found or 'none'}")


if __name__ == "__main__":
    main()
