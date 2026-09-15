#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RESIDENT = Path("/tmp/stegverse-resident")
EPHEMERAL = Path("/tmp/stegverse-ephemeral")
BUNDLE = ROOT / "execution-bundles/stegbrowser-stegos"
OUTPUT = ROOT / "build/stegbrowser-manifest-invocation"
RUNNER = ROOT / "scripts/run_stegbrowser_manifest_bound_runtime.py"


def main() -> int:
    shutil.rmtree(RESIDENT, ignore_errors=True)
    shutil.rmtree(EPHEMERAL, ignore_errors=True)
    shutil.rmtree(OUTPUT, ignore_errors=True)
    RESIDENT.mkdir(parents=True)
    EPHEMERAL.mkdir(parents=True)
    OUTPUT.mkdir(parents=True)
    params = {
        "sovereign_source_root": str(ROOT),
        "runtime_root": str(RESIDENT),
        "stegos_source_root": str(BUNDLE),
        "runtime_base": str(EPHEMERAL),
    }
    env = {
        **os.environ,
        "STEGVERSE_REUSABLE_TASK_PARAMETERS_JSON": json.dumps(params, separators=(",", ":")),
        "STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY": "TV/TVC",
        "STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY": "NONE",
    }
    completed = subprocess.run(
        [sys.executable, str(RUNNER)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    (OUTPUT / "invocation.stdout.jsonl").write_text(completed.stdout, encoding="utf-8")
    (OUTPUT / "invocation.stderr.log").write_text(completed.stderr, encoding="utf-8")
    (OUTPUT / "invocation.exit-code.txt").write_text(f"{completed.returncode}\n", encoding="utf-8")
    if RESIDENT.exists():
        shutil.copytree(RESIDENT, OUTPUT / "retained", dirs_exist_ok=True)
    summary = {
        "schema": "stegverse.stegbrowser-callable-execution-carrier-result/v1",
        "carrier": "RENDER_BUILD_EVENT_EPHEMERAL",
        "carrier_authority_effect": "NONE",
        "persistent_runtime_dependency": False,
        "attached_user_device_required": False,
        "runner": "scripts/run_stegbrowser_manifest_bound_runtime.py",
        "runner_exit_code": completed.returncode,
        "expected_boundary_exit_code": 2,
        "source_branch_execution_only": True,
    }
    (OUTPUT / "carrier-result.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    # The StegBrowser runtime runner intentionally returns 2 when it reaches the
    # next authentic boundary. Preserve that as a successful carrier build so
    # the receipts can be inspected; all other non-zero exits fail the build.
    return 0 if completed.returncode in (0, 2) else completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
