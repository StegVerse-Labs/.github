#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path

from workers import control_plane_source_package as controlpkg

DEFAULT_PATHS = (
    "workers/control_plane_source_package.py",
    "workers/hil_intr_profiled_ingress.py",
    "workers/stegos_sovereign_relay_return_path_request_consumer.py",
    "handoffs/SHWP-STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001.json",
    "control/resident-execution-request.d/stegos-sovereign-relay-return-path-001.json",
    "scripts/dispatch_resident_execution_requests.py",
    "scripts/refresh_and_execute_resident_task.py",
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
