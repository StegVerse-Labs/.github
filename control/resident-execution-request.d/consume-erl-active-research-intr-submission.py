#!/usr/bin/env python3
"""Invoke the bounded resident-local ERL loopback InTr submitter from the existing dispatcher.

The consumer is independently source-complete for selected-subset dispatch: it
may copy only its exact ERL source dependencies from the already-local canonical
source root, verify byte/hash parity, and apply/check the idempotent ERL source
preparation before delegating to the resident-local input materializer/submitter.
It performs no network source fetch and grants no authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

SUBMITTER = Path("scripts/submit_erl_active_research_intr_binding_local.py")
MATERIALIZER = Path("scripts/materialize_erl_active_research_intr_resident_local_input.py")
PREP = Path("scripts/prepare_erl_active_research_intr_runtime_source.py")
INPUT_REL = Path("runtime-state/erl-active-research/intr-submission-input.json")
SOURCE_DEPENDENCIES = (
    Path("scripts/install_sovereign_heartbeat_service.py"),
    Path("scripts/prepare_erl_active_research_intr_runtime_source.py"),
    Path("scripts/install_erl_active_research_universal_intr_route.py"),
    Path("scripts/install_erl_device_kv_prior_lineage.py"),
    Path("scripts/install_erl_resident_request_wiring.py"),
    Path("scripts/materialize_erl_active_research_intr_resident_local_input.py"),
    Path("scripts/submit_erl_active_research_intr_binding.py"),
    Path("scripts/submit_erl_active_research_intr_binding_local.py"),
    Path("workers/erl_active_research_transport.py"),
)


def parse_last_json(stdout: str) -> dict:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    raise RuntimeError("ERL submission result JSON missing")


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_copy_exact(source: Path, target: Path) -> bool:
    raw = source.read_bytes()
    expected = hashlib.sha256(raw).hexdigest()
    if target.is_file() and file_sha256(target) == expected:
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name("." + target.name + ".erl-source.tmp")
    tmp.write_bytes(raw)
    if file_sha256(tmp) != expected:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"source_dependency_temp_readback_mismatch:{target}")
    os.replace(tmp, target)
    if file_sha256(target) != expected:
        raise RuntimeError(f"source_dependency_readback_mismatch:{target}")
    return True


def materialize_source_dependencies(source_root: Path, runtime_root: Path) -> dict:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    if not source.is_dir():
        raise RuntimeError("canonical_local_source_root_missing")
    copied: list[str] = []
    verified: list[str] = []
    for rel in SOURCE_DEPENDENCIES:
        src = source / rel
        if not src.is_file():
            raise RuntimeError(f"canonical_local_source_dependency_missing:{rel.as_posix()}")
        dst = runtime / rel
        if source == runtime:
            verified.append(rel.as_posix())
        elif atomic_copy_exact(src, dst):
            copied.append(rel.as_posix())
        else:
            verified.append(rel.as_posix())
        if not dst.is_file() or file_sha256(dst) != file_sha256(src):
            raise RuntimeError(f"source_dependency_parity_failed:{rel.as_posix()}")
    return {
        "copied": copied,
        "verified": verified,
        "network_source_fetch_attempted": False,
        "authority_effect": "NONE_LOCAL_SOURCE_MATERIALIZATION_ONLY",
    }


def run_json(command: list[str], runtime: Path, *, runner=subprocess.run, timeout: int = 30) -> dict:
    completed = runner(command, cwd=runtime, capture_output=True, text=True, check=False, timeout=timeout)
    if completed.returncode != 0:
        raise RuntimeError("ERL loopback submission consumer failed: " + (completed.stderr or completed.stdout).strip())
    return parse_last_json(completed.stdout)


def run_prep(prep: Path, runtime: Path, *, runner=subprocess.run) -> None:
    applied = runner([sys.executable, str(prep)], cwd=runtime, capture_output=True, text=True, check=False, timeout=120)
    if applied.returncode != 0:
        raise RuntimeError("ERL source preparation apply failed: " + (applied.stderr or applied.stdout).strip())
    checked = runner([sys.executable, str(prep), "--check"], cwd=runtime, capture_output=True, text=True, check=False, timeout=120)
    if checked.returncode != 0:
        raise RuntimeError("ERL source preparation check failed: " + (checked.stderr or checked.stdout).strip())


def consume(source_root: Path, runtime_root: Path, *, runner=subprocess.run) -> dict:
    runtime = runtime_root.expanduser().resolve()
    source_materialization = materialize_source_dependencies(source_root, runtime)
    prep = runtime / PREP
    submitter = runtime / SUBMITTER
    materializer = runtime / MATERIALIZER
    if not prep.is_file() or not submitter.is_file() or not materializer.is_file():
        return {
            "schema": "stegverse.erl-active-research-intr-submission-dispatch/v1",
            "state": "SOURCE_NOT_MATERIALIZED",
            "source_materialization": source_materialization,
            "runtime_execution_attempted": False,
            "authority_effect": "NONE_WAIT_STATE",
        }
    run_prep(prep, runtime, runner=runner)
    input_path = runtime / INPUT_REL
    input_materialization = None
    if not input_path.is_file():
        input_materialization = run_json(
            [sys.executable, str(materializer), "--runtime-root", str(runtime)],
            runtime,
            runner=runner,
        )
        if input_materialization.get("input_materialized") is not True:
            return {
                "schema": "stegverse.erl-active-research-intr-submission-dispatch/v1",
                "state": input_materialization.get("state"),
                "source_materialization": source_materialization,
                "source_preparation_applied": True,
                "source_preparation_check_passed": True,
                "input_materialization": input_materialization,
                "runtime_execution_attempted": False,
                "transport_submission_attempted": False,
                "provider_operation_attempted": False,
                "authority_effect": "NONE_WAIT_STATE",
            }
    result = run_json(
        [sys.executable, str(submitter), "--runtime-root", str(runtime), "--input", str(INPUT_REL)],
        runtime,
        runner=runner,
    )
    return {
        "schema": "stegverse.erl-active-research-intr-submission-dispatch/v1",
        "state": result.get("state"),
        "source_materialization": source_materialization,
        "source_preparation_applied": True,
        "source_preparation_check_passed": True,
        "input_materialization": input_materialization,
        "submission_result": result,
        "runtime_execution_attempted": result.get("transport_submission_attempted") is True,
        "provider_operation_attempted": False,
        "authority_effect": "NONE_DISPATCH_ONLY" if result.get("transport_submission_attempted") is not True else "INGRESS_SUBMISSION_DELEGATED_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(consume(args.source_root, args.runtime_root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
