#!/usr/bin/env python3
"""Build a portable, non-secret StegVerse sovereign control-plane bundle.

The bundle is local transport only. It grants no runtime, claim, fence,
credential, route, heartbeat, or provider authority. It is designed so
StegDeploy can materialize the exact canonical resident control-plane source
without a network fetch or an incidental adjacent checkout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_NAME = "stegverse-control-plane-manifest.json"

INCLUDE_DIRS = (
    "heartbeat_runtime",
    "control",
    "handoffs",
    "authorizations",
    "workers",
    "schemas",
    "cost-basis",
    "management",
    "state_language",
    "scripts",
)
INCLUDE_FILES = (
    "README.md",
)
EXCLUDE_PARTS = {
    ".git",
    ".github",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}
EXCLUDE_PREFIXES = (
    "receipts/",
    "events/",
    "checkpoints/",
)
FORBIDDEN_NAME_FRAGMENTS = (
    ".env",
    "credential",
    "private_key",
    "private-key",
    "secret",
    "token",
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _included_files(root: Path) -> list[Path]:
    paths: set[Path] = set()
    for name in INCLUDE_FILES:
        path = root / name
        if path.is_file():
            paths.add(path)
    for rel in INCLUDE_DIRS:
        base = root / rel
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.is_symlink():
                continue
            relative = path.relative_to(root)
            if any(part in EXCLUDE_PARTS for part in relative.parts):
                continue
            posix = relative.as_posix()
            if any(posix.startswith(prefix) for prefix in EXCLUDE_PREFIXES):
                continue
            lower = posix.lower()
            if any(fragment in lower for fragment in FORBIDDEN_NAME_FRAGMENTS):
                # Canonical source references to credentials/tokens are valid code.
                # Only reject likely secret-bearing file classes, not source filenames.
                if path.suffix.lower() not in {".py", ".json", ".md", ".txt", ".yaml", ".yml"}:
                    continue
            paths.add(path)
    return sorted(paths, key=lambda p: p.relative_to(root).as_posix())


def build_bundle(root: Path, output: Path) -> dict:
    root = root.resolve()
    output = output.resolve()
    files = _included_files(root)
    required = root / "scripts" / "bootstrap_sovereign_runtime.py"
    if required not in files:
        raise RuntimeError("canonical bootstrap missing from bundle source")

    entries = []
    for path in files:
        rel = path.relative_to(root).as_posix()
        data = path.read_bytes()
        entries.append({
            "path": rel,
            "sha256": _sha256(data),
            "size": len(data),
        })

    manifest = {
        "schema": "stegverse.sovereign-control-plane-bundle/v1",
        "file_count": len(entries),
        "files": entries,
        "network_fetch_required": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "bundle_grants_authority": False,
        "authority_effect": "NONE_SOURCE_TRANSPORT_ONLY",
    }
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            rel = path.relative_to(root).as_posix()
            info = zipfile.ZipInfo(rel, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = path.stat().st_mode
            info.external_attr = ((stat.S_IMODE(mode) or 0o644) & 0xFFFF) << 16
            archive.writestr(info, path.read_bytes())
        info = zipfile.ZipInfo(MANIFEST_NAME, date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = (0o644 & 0xFFFF) << 16
        archive.writestr(info, manifest_bytes)

    bundle_bytes = output.read_bytes()
    receipt = {
        **manifest,
        "bundle_path": str(output),
        "bundle_sha256": _sha256(bundle_bytes),
        "bundle_size": len(bundle_bytes),
    }
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = build_bundle(args.source_root, args.output)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
