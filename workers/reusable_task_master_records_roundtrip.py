from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


def execute(request_path: Path) -> dict[str, Any]:
    raw_roots = os.getenv("STEGVERSE_REPO_ROOTS_JSON", "").strip()
    runtime_raw = os.getenv("STEGVERSE_HEARTBEAT_ROOT", "").strip()
    if not raw_roots or not runtime_raw:
        return {"state":"BOUNDARY","reason":"MASTER_RECORDS_RUNTIME_BINDING_MISSING","authority_effect":"NONE"}
    roots = json.loads(raw_roots)
    if not isinstance(roots, dict):
        return {"state":"BOUNDARY","reason":"MASTER_RECORDS_REPOSITORY_MAP_INVALID","authority_effect":"NONE"}
    root_raw = roots.get("master-records/orchestration")
    if not isinstance(root_raw, str) or not root_raw:
        return {"state":"BOUNDARY","reason":"MASTER_RECORDS_ORCHESTRATION_ROOT_MISSING","authority_effect":"NONE"}
    mr_root = Path(root_raw).expanduser().resolve()
    ingest = mr_root / "scripts/ingest_reusable_task_lifecycle.py"
    reconstruct = mr_root / "scripts/reconstruct_reusable_task_lifecycle.py"
    if not ingest.is_file() or not reconstruct.is_file():
        return {"state":"BOUNDARY","reason":"MASTER_RECORDS_REUSABLE_LIFECYCLE_SOURCE_MISSING","authority_effect":"NONE"}
    runtime_root = Path(runtime_raw).expanduser().resolve()
    custody_root = runtime_root / "master-records" / "reusable-task-lifecycle"
    reconstructed = request_path.with_name(request_path.stem + ".reconstructed.json")
    env = {key: os.environ[key] for key in ("PATH","PYTHONPATH","LANG","LC_ALL") if key in os.environ}
    first = subprocess.run([sys.executable, str(ingest), "--request", str(request_path), "--custody-root", str(custody_root)], cwd=mr_root, env=env, text=True, capture_output=True, check=False, timeout=60)
    if first.returncode != 0:
        return {"state":"BOUNDARY","reason":"MASTER_RECORDS_LIFECYCLE_INGEST_FAILED","returncode":first.returncode,"stderr_tail":first.stderr[-1200:],"authority_effect":"NONE"}
    try:
        ingest_result = json.loads(first.stdout.strip().splitlines()[-1])
        custody_ref = Path(str(ingest_result["custody_ref"]))
    except Exception:
        return {"state":"BOUNDARY","reason":"MASTER_RECORDS_LIFECYCLE_INGEST_RESULT_INVALID","authority_effect":"NONE"}
    second = subprocess.run([sys.executable, str(reconstruct), "--record", str(custody_ref), "--custody-root", str(custody_root), "--output", str(reconstructed)], cwd=mr_root, env=env, text=True, capture_output=True, check=False, timeout=60)
    if second.returncode != 0 or not reconstructed.is_file():
        return {"state":"BOUNDARY","reason":"MASTER_RECORDS_LIFECYCLE_RECONSTRUCTION_FAILED","returncode":second.returncode,"stderr_tail":second.stderr[-1200:],"authority_effect":"NONE"}
    if reconstructed.read_bytes() != request_path.read_bytes():
        return {"state":"BOUNDARY","reason":"MASTER_RECORDS_LIFECYCLE_RECONSTRUCTION_BYTES_MISMATCH","authority_effect":"NONE"}
    record = json.loads(custody_ref.read_text(encoding="utf-8"))
    return {"state":"RETURNED","custody_ref":str(custody_ref),"reconstructed_ref":str(reconstructed),"record":record,"authority_effect":"NONE"}
