#!/usr/bin/env python3
"""CLI entrypoint for Duplicate Find benchmarking."""

import os
import sys

# Ensure src is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from duplicate_find.benchmark.runner import main

if __name__ == "__main__":
    main()
