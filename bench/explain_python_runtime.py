#!/usr/bin/env python3
"""Source-tree entry point for the generated Python runtime report."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from duplicate_find.benchmark.runtime_explainer import main


if __name__ == "__main__":
    main()
