#!/usr/bin/env python3
"""Entrypoint v2: preserve canonical preflights, then use unified-proof worker v2."""
from __future__ import annotations

from pathlib import Path

import stegnutrition_continuation_entrypoint as base

ROOT = Path(__file__).resolve().parents[1]
base.WORKER = ROOT / "workers/stegnutrition_continuation_worker_v2.py"

# The v2 worker depends on these StegNutrition-owned surfaces in addition to the
# base current-surface contract. Require them before worker execution so a stale
# resident tree fails at deterministic preflight rather than halfway through the
# unified validation, real-data candidate projection, or release projection.
_V2_REQUIRED_SURFACES = (
    "scripts/run_full_validation_no_network.py",
    "src/stegnutrition/release.py",
    "src/stegnutrition/release_projection.py",
    "src/stegnutrition/real_data_qualification.py",
    "scripts/run_real_data_qualification_no_network.py",
    "tests/test_full_validation_orchestrator.py",
    "tests/test_release.py",
    "tests/test_release_projection.py",
    "tests/test_real_data_qualification.py",
    "tasks/STEGNUTRITION-RELEASE-PROPAGATION-017.json",
    "tasks/STEGNUTRITION-REAL-DATA-QUALIFICATION-HANDOFF-021.json",
)
base.CURRENT_REQUIRED_SURFACES = tuple(dict.fromkeys(base.CURRENT_REQUIRED_SURFACES + _V2_REQUIRED_SURFACES))


if __name__ == "__main__":
    raise SystemExit(base.main())
