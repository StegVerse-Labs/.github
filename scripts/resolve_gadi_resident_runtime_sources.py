#!/usr/bin/env python3
"""Resolve authentic local GADI runtime evidence into the canonical staging directory.

The resolver is local-only and non-authorizing. It never invents evidence values and never
performs network access. When a runtime source-locator manifest exists, it copies the exact
referenced bytes into the canonical GADI source staging paths. Without a locator manifest,
existing staged files are preserved and missing inputs remain missing for the materializer
to report fail-closed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

TASK_ID = "GADI-RESIDENT-EXECUTION-001"
PARENT_TASK_ID = "GADI-001"
LOCATOR_REL = Path("state/gadi-resident-execution/source-locators.json")
SOURCE_DIR = Path("state/gadi-resident-execution/source")
OUTPUT_REL = Path("state/gadi-resident-execution/source-resolution.json")
TARGETS = {
    "stegos_command": SOURCE_DIR / "stegos-command.json",
    "intr_admission": SOURCE_DIR / "intr-admission.json",
    "worker_claim": SOURCE_DIR / "worker-claim.json",
    "actuator_observation": SOURCE_DIR / "actuator-observation.json",
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def safe_relative(value: Any) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    rel = Path(value)
    if rel.is_absolute() or ".." in rel.parts:
        return None
    return rel


def resolve(runtime_root: Path) -> dict[str, Any]:
    runtime = runtime_root.expanduser().resolve()
    locator_path = runtime / LOCATOR_REL
    blockers: list[str] = []
    resolved: dict[str, dict[str, str]] = {}

    if locator_path.is_file():
        try:
            manifest = load(locator_path)
        except Exception:
            manifest = {}
            blockers.append("SOURCE_LOCATOR_INVALID_JSON")
        if manifest:
            if manifest.get("schema") != "stegverse.gadi-resident-runtime-source-locators/v1":
                blockers.append("SOURCE_LOCATOR_SCHEMA_INVALID")
            if manifest.get("task_id") != TASK_ID:
                blockers.append("SOURCE_LOCATOR_TASK_MISMATCH")
            if manifest.get("parent_task_id") not in (None, PARENT_TASK_ID):
                blockers.append("SOURCE_LOCATOR_PARENT_MISMATCH")
            if manifest.get("network_fetch_allowed") is not False:
                blockers.append("NETWORK_SOURCE_FETCH_FORBIDDEN")
            sources = manifest.get("sources")
            if not isinstance(sources, dict):
                blockers.append("SOURCE_LOCATOR_SOURCES_INVALID")
                sources = {}
            for name, target_rel in TARGETS.items():
                rel = safe_relative(sources.get(name))
                if rel is None:
                    blockers.append(f"{name.upper()}_LOCATOR_MISSING_OR_UNSAFE")
                    continue
                source_path = (runtime / rel).resolve()
                try:
                    source_path.relative_to(runtime)
                except ValueError:
                    blockers.append(f"{name.upper()}_LOCATOR_ESCAPES_RUNTIME")
                    continue
                if not source_path.is_file():
                    blockers.append(f"{name.upper()}_LOCATED_SOURCE_MISSING")
                    continue
                try:
                    load(source_path)
                except Exception:
                    blockers.append(f"{name.upper()}_LOCATED_SOURCE_INVALID_JSON")
                    continue
                target = runtime / target_rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source_path, target)
                resolved[name] = {
                    "source": str(rel),
                    "target": str(target_rel),
                    "sha256": digest(target),
                }
    else:
        # No locator manifest is not itself an error: legacy/existing authentic staged
        # source files remain valid. Missing staged inputs are left for the materializer
        # to identify deterministically.
        for name, target_rel in TARGETS.items():
            target = runtime / target_rel
            if target.is_file():
                try:
                    load(target)
                    resolved[name] = {
                        "source": str(target_rel),
                        "target": str(target_rel),
                        "sha256": digest(target),
                    }
                except Exception:
                    blockers.append(f"{name.upper()}_STAGED_SOURCE_INVALID_JSON")

    result = {
        "schema": "stegverse.gadi-resident-runtime-source-resolution/v1",
        "task_id": TASK_ID,
        "parent_task_id": PARENT_TASK_ID,
        "state": "SOURCE_RESOLUTION_COMPLETE" if not blockers else "SOURCE_RESOLUTION_BLOCKED_FAIL_CLOSED",
        "locator_manifest_observed": locator_path.is_file(),
        "resolved_count": len(resolved),
        "resolved": dict(sorted(resolved.items())),
        "blockers": sorted(set(blockers)),
        "network_fetch_performed": False,
        "authority_minted": False,
        "execution_claimed": False,
        "activation_claimed": False,
    }
    write(runtime / OUTPUT_REL, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    result = resolve(args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] == "SOURCE_RESOLUTION_COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
