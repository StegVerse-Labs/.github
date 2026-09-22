#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path

from workers import control_plane_source_package as controlpkg

# Bootstrap-critical control-plane delta. Keep this set sufficient to recover a
# stale resident into the current autonomous refresh -> scheduler path without
# requiring the stale runtime to already contain the repair that refreshes it.
#
# The StegBrowser A0-A4 implementation was already merged/validated before the
# one-shot request at commit 19935454.... The only new canonical-source byte set
# required for that invocation is the unchanged resident request itself. Carrying
# the entire pre-existing runner chain would duplicate already-canonical source and
# exceed the existing relay envelope.
DEFAULT_PATHS = (
    "workers/control_plane_source_package.py",
    "workers/hil_intr_profiled_ingress.py",
    "workers/stegos_sovereign_relay_return_path_request_consumer.py",
    "handoffs/SHWP-STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001.json",
    "control/resident-execution-request.d/stegos-sovereign-relay-return-path-001.json",
    "control/resident-execution-request.d/healer-sovereign-scheduler-001.json",
    "control/resident-execution-request.d/sdk-tt-richard-seam-authentic-runtime-001.json",
    "heartbeat_runtime/worker_runtime.py",
    "heartbeat_runtime/admitted_worker_runtime.py",
    "heartbeat_runtime/worker_assignment_functional_memory.py",
    "workers/canonical_state_transition_custody.py",
    ".stegverse/transition-ledger/org-contract.json",
    "resident-runtime/aggregate_repo_transition.py",
    "control/worker-registry.d/stegfin-live-entry-003.json",
    "heartbeat_runtime/worker_runtime_legacy.py",
    "heartbeat_runtime/process_adapter.py",
    "workers/stegagents_governed_runtime_worker.py",
    "handoffs/SDK-TT-RICHARD-SEAM-AUTHENTIC-RUNTIME-001.json",
    "control/worker-registry.d/sdk-tt-richard-seam-authentic-runtime-001.json",
    "control/resident-execution-request.d/canonical-work-stegbrowser-runtime-consumption-001.json",
    "scripts/build_control_plane_source_package.py",
    "scripts/build_control_plane_source_package_reusable.py",
    "scripts/refresh_sovereign_worker_runtime_source.py",
    "scripts/install_sovereign_worker_source_refresh_service.py",
    "scripts/dispatch_resident_execution_requests.py",
    "scripts/refresh_and_dispatch_resident_requests.py",
    "scripts/refresh_and_execute_resident_task.py",
    "scripts/consume_healer_sovereign_scheduler_request.py",
    "scripts/consume_sdk_tt_richard_seam_authentic_runtime_request.py",
    "source-bundles/reusable-task-registry.d/RT-SOVEREIGN-SOURCE-REFRESH-001.json",
    "source-bundles/reusable-task-registry.d/RT-REUSABLE-TASK-SCHEDULER-001.json",
    "source-bundles/reusable-task-registry.d/RT-CONTROL-PLANE-SOURCE-PACKAGE-001.json",
)


def build(source_root: Path, paths: tuple[str, ...]) -> dict:
    root = source_root.expanduser().resolve()
    rows = []
    files = []
    for rel in sorted(set(paths)):
        safe = controlpkg._safe_rel(rel)
        path = root / safe
        if not path.is_file():
            raise RuntimeError(f"required control-plane package file missing: {safe}")
        raw = path.read_bytes()
        row = {"path": safe, "sha256": controlpkg.sha256_bytes(raw), "size": len(raw)}
        rows.append(row)
        files.append({**row, "content_base64": base64.b64encode(raw).decode("ascii")})
    manifest_digest = controlpkg.digest(rows)
    package = {
        "schema": controlpkg.PACKAGE_SCHEMA,
        "package_version": controlpkg.PACKAGE_VERSION,
        "component_id": controlpkg.COMPONENT_ID,
        "source_identity": "sha256:" + manifest_digest,
        "credential_material_included": False,
        "manifest": {"file_count": len(rows), "source_bundle_sha256": manifest_digest, "files": rows},
        "files": files,
        "provenance": {
            "source_identity_scheme": "sha256-content-manifest",
            "external_platform_required": False,
            "package_scope": "ALLOWLISTED_CONTROL_PLANE_DELTA",
        },
        "authority_effect": controlpkg.AUTHORITY_EFFECT,
    }
    controlpkg.validate_package(package)
    return package


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an allowlisted StegVerse control-plane source delta package.")
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--path", action="append", dest="paths")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    package = build(args.source_root, tuple(args.paths or DEFAULT_PATHS))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(package, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "schema": "stegverse.control-plane-source-package-build-receipt/v1",
        "state": "BUILT_VERIFIED",
        "component_id": controlpkg.COMPONENT_ID,
        "source_identity": package["source_identity"],
        "file_count": package["manifest"]["file_count"],
        "output": str(args.out),
        "credential_material_included": False,
        "network_source_fetch_performed": False,
        "execution_authority": "NONE",
        "authority_effect": "NONE_SOURCE_PACKAGE_BUILD_ONLY",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
