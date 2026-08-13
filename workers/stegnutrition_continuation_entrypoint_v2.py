#!/usr/bin/env python3
"""Entrypoint v2: preserve canonical preflights, then use unified-proof worker v2."""
from __future__ import annotations

from pathlib import Path

import stegnutrition_continuation_entrypoint as base

ROOT = Path(__file__).resolve().parents[1]
base.WORKER = ROOT / "workers/stegnutrition_continuation_worker_v2.py"


if __name__ == "__main__":
    raise SystemExit(base.main())
