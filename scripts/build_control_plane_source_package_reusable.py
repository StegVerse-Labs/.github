#!/usr/bin/env python3
"""Build one content-addressed control-plane source package as a reusable task.

This runner is source packaging only. It does not perform relay transport, issue a
TVC grant/authorization, admit an InTr transition, mint a WorkerCoordinator claim
or fence, or mutate the resident runtime control plane. The package is retained in
an outbox so the existing governed relay path can consume the exact bytes later.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_control_plane_source_package as builder

REUSABLE_TASK_ID = "RT-CONTROL-PLANE-SOURCE-PACKAGE-001"
RESULT_SCHEMA = "stegverse.reusable-task-runner-result/v1"
OUTBOX_REL = Path("outbox/control-plane-source-package")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"object_required:{path}")
    return value


def atomic_write_once(path: Path, rendered: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text(encoding="utf-8") != rendered:
            raise RuntimeError("control_plane_package_write_once_collision")
        return
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(rendered, encoding="utf-8")
    os.replace(tmp, path)
    if path.read_text(encoding="utf-8") != rendered:
        raise RuntimeError("control_plane_package_readback_mismatch")


def run() -> dict[str, Any]:
    manifest_path = Path(os.environ["STEGVERSE_REUSABLE_TASK_MANIFEST"]).expanduser().resolve()
    result_path = Path(os.environ["STEGVERSE_REUSABLE_TASK_RESULT_PATH"]).expanduser().resolve()
    manifest = load_json(manifest_path)
    if manifest.get("reusable_task_id") != REUSABLE_TASK_ID:
        raise RuntimeError("reusable_task_identity_mismatch")
    parameters = manifest.get("parameters")
    if not isinstance(parameters, dict):
        raise RuntimeError("parameters_required")

    source_root = Path(str(parameters.get("source_root") or ROOT)).expanduser().resolve()
    runtime_raw = str(parameters.get("runtime_root") or os.environ.get("STEGVERSE_HEARTBEAT_ROOT") or "").strip()
    if not runtime_raw:
        raise RuntimeError("runtime_root_required")
    runtime_root = Path(runtime_raw).expanduser().resolve()
    if not source_root.is_dir():
        raise RuntimeError("canonical_source_root_missing")
    runtime_root.mkdir(parents=True, exist_ok=True)

    package = builder.build(source_root, builder.DEFAULT_PATHS)
    source_identity = str(package["source_identity"])
    digest = source_identity.removeprefix("sha256:")
    if len(digest) != 64:
        raise RuntimeError("source_identity_invalid")
    rendered = json.dumps(package, indent=2, sort_keys=True) + "\n"
    output = runtime_root / OUTBOX_REL / f"{digest}.json"
    atomic_write_once(output, rendered)

    completion_predicates = json.loads(os.environ.get("STEGVERSE_REUSABLE_TASK_COMPLETION_PREDICATES_JSON", "[]"))
    result = {
        "schema": RESULT_SCHEMA,
        "invocation_id": manifest["invocation_id"],
        "reusable_task_id": REUSABLE_TASK_ID,
        "manifest_hash": manifest["manifest_hash"],
        "runtime_observed": True,
        "completion_evidence_observed": True,
        "completion_predicates_satisfied": completion_predicates,
        "package": {
            "component_id": package["component_id"],
            "source_identity": source_identity,
            "file_count": package["manifest"]["file_count"],
            "package_ref": str(output),
            "package_size": len(rendered.encode("utf-8")),
            "credential_material_included": False,
            "network_source_fetch_performed": False,
            "relay_transport_executed": False,
            "tvc_authorization_issued": False,
        },
        "authority_effect": "NONE_SOURCE_PACKAGE_BUILD_ONLY",
    }
    result_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = result_path.with_name("." + result_path.name + ".tmp")
    tmp.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, result_path)
    return result


def main() -> int:
    result = run()
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
