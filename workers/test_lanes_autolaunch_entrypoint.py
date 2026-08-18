#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

ROOT = Path.cwd().resolve()
SPEC = importlib.util.spec_from_file_location("autolaunch_worker", ROOT / "workers" / "test_lanes_autolaunch_worker.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def runtime_safe_source_validation(tvc_root: Path | None, lanes_root: Path | None) -> tuple[bool, list[dict[str, Any]]]:
    checks: list[dict[str, Any]] = []

    for test in (
        "tests/test_test_lanes_autolaunch_matrix.py",
        "tests/test_test_lanes_autolaunch_worker.py",
    ):
        result = MODULE.run([sys.executable, test], cwd=ROOT, timeout=45)
        checks.append({"name": ".github:" + test, **result})

    if lanes_root is None:
        checks.append({"name": "test_lanes", "returncode": 127, "stderr_tail": "TEST_LANES_ROOT_NOT_MATERIALIZED", "stdout_tail": ""})
    else:
        lane_dir = lanes_root / "experiments" / "stegverse-test-lanes"
        for test in (
            "tests/test_plan_test_lanes.py",
            "tests/test_compare_test_lanes.py",
            "tests/test_run_stegverse_primary_candidate.py",
            "tests/test_build_lane_evidence.py",
        ):
            result = MODULE.run([sys.executable, test], cwd=lane_dir, timeout=45)
            checks.append({"name": "test_lanes:" + test, **result})

    if tvc_root is None:
        checks.append({"name": "tvc", "returncode": 127, "stderr_tail": "TVC_ROOT_NOT_MATERIALIZED", "stdout_tail": ""})
    else:
        surfaces = (
            "tvc_provider_capsule.py",
            "scripts/tvc_materialize_provider_capsule_bindings.py",
            "scripts/tvc_resolve_test_lane_capsules.py",
            "scripts/tvc_issue_test_lane_lease.py",
            "scripts/tvc_run_test_lane_external_candidate.py",
        )
        compile_result = MODULE.run([sys.executable, "-m", "py_compile", *surfaces], cwd=tvc_root, timeout=45)
        checks.append({"name": "tvc:py_compile", **compile_result})
        for script in surfaces[1:]:
            result = MODULE.run([sys.executable, script, "--help"], cwd=tvc_root, timeout=30)
            checks.append({"name": "tvc:help:" + script, **result})

    return all(item.get("returncode") == 0 for item in checks), checks


MODULE.source_validation = runtime_safe_source_validation
raise SystemExit(MODULE.main())
