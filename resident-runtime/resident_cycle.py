#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "federation_cycle",
    ROOT / "resident-runtime" / "federation_cycle.py",
)
FC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FC)

if __name__ == "__main__":
    FC.main()
