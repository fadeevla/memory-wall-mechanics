#!/usr/bin/env python3
"""Source-tree entry point for the CPython free-threading comparison."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from duplicate_find.benchmark.free_threading import main


if __name__ == "__main__":
    main()
