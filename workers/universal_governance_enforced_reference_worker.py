#!/usr/bin/env python3
"""Sovereign Universal Governance ENFORCED reference-boundary observer."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

TASK_ID = "SHWP-UNIVERSAL-GOVERNANCE-ENFORCED-REFERENCE-001"
WORKER_ID = "universal-governance-enforced-reference-worker"
STEGCORE_ENV = "STEGVERSE_STEGCORE_SOURCE_ROOT"
MASTER_RECORDS_ENV = "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT"
BOUND_STATE_ENV = "STEGVERSE_BOUND_STATE_ROOT"
REPO_ROOTS_ENV = "STEGVERSE_REPO_ROOTS_JSON"
NODE_MARKERS = (Path("/etc/stegverse/node.json"), Path.home() / ".stegverse" / "node.json")
HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
FORBIDDEN_CREDENTIAL_ENV = ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GIT_ASKPASS", "OAUTH_TOKEN")
CANONICAL_REPO_BASES = (
    Path.home() / ".stegverse" / "repos",
    Path("/var/lib/stegverse/source"),
    Path("/srv/stegverse/repos"),
    Path("/opt/stegverse/repos"),
)

STEGCORE_REQUIRED = (
    Path("scripts/run_universal_governance_reference_boundary.py"),
    Path("src/stegcore/external_governance_adapter.py"),
    Path("src/stegcore/external_adapter_steggate_execution.py"),
    Path("src/stegcore/universal_governance_consequence_evidence.py"),
)
MR_REQUIRED = (
    Path("tools/validate_universal_governance_consequence_custody.py"),
    Path("contracts/stegcore_universal_governance_consequence_source.json"),
)


class SourceUnavailable(RuntimeError):
    pass


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def find_node() -> tuple[Path, dict[str, Any]]:
    for path in NODE_MARKERS:
        if path.is_file():
            node = read_json(path)
            if node.get("declared") is not True:
                raise RuntimeError("sovereign node is not declared")
            if node.get("credential_authority") != "TV/TVC":
                raise RuntimeError("credential authority must be TV/TVC")
            if node.get("github_token_required") is not False:
                raise RuntimeError("sovereign worker may not require GitHub token")
            return path, node
    raise RuntimeError("no declared sovereign StegVerse node marker is available")


def validate_invocation(invocation: Mapping[str, Any]) -> None:
    task = invocation.get("task") or {}
    if task.get("task_id") != TASK_ID:
        raise RuntimeError("unexpected task_id")
    if task.get("worker_id") != WORKER_ID:
        raise RuntimeError("unexpected worker_id")
    if not task.get("claim_id"):
        raise RuntimeError("canonical scheduler claim is required")
    authority = (invocation.get("handoff") or {}).get("authority") or {}
    if authority.get("credential_authority") != "TV/TVC":
        raise RuntimeError("handoff credential authority drift")
    for key in ("repository_writeback_authority", "publication_authority", "continuity_mint_authority"):
        if authority.get(key) is not False:
            raise RuntimeError(f"worker authority escalation: {key}")
    if authority.get("github_token_required") is not False:
        raise RuntimeError("GitHub token may not be required")


def repository_roots() -> dict[str, Path]:
    raw = str(os.getenv(REPO_ROOTS_ENV) or "").strip()
    roots: dict[str, Path] = {}
    if raw:
        try:
            value = json.loads(raw)
        except Exception:
            return {}
        if not isinstance(value, dict):
            return {}
        for repository, path_value in value.items():
            if not isinstance(repository, str) or "/" not in repository or not isinstance(path_value, str):
                continue
            try:
                path = Path(path_value).expanduser().resolve()
            except Exception:
                continue
            if path.is_dir():
                roots[repository] = path
        return roots

    ambiguous: set[str] = set()
    for base in CANONICAL_REPO_BASES:
        if not base.is_dir():
            continue
        for owner in sorted(x for x in base.iterdir() if x.is_dir()):
            for candidate in sorted(x for x in owner.iterdir() if x.is_dir()):
                repository = f"{owner.name}/{candidate.name}"
                resolved = candidate.resolve()
                prior = roots.get(repository)
                if prior is not None and prior != resolved:
                    ambiguous.add(repository)
                else:
                    roots[repository] = resolved
    for repository in ambiguous:
        roots.pop(repository, None)
    return roots


def candidate_roots(env_name: str, names: tuple[str, ...], repository: str) -> list[Path]:
    roots: list[Path] = []
    explicit = str(os.getenv(env_name) or "").strip()
    if explicit:
        roots.append(Path(explicit))
    mapped = repository_roots().get(repository)
    if mapped is not None:
        roots.append(mapped)
    for name in names:
        roots.extend([
            Path.cwd() / "workloads" / name,
            Path.home() / ".stegverse" / "workloads" / name,
            Path("/var/lib/stegverse/workloads") / name,
            Path.home() / ".stegverse" / "source" / name,
            Path("/var/lib/stegverse/source") / name,
        ])
    return roots


def find_source(env_name: str, names: tuple[str, ...], repository: str, required: tuple[Path, ...]) -> Path | None:
    seen: set[str] = set()
    for candidate in candidate_roots(env_name, names, repository):
        try:
            root = candidate.expanduser().resolve()
        except Exception:
            continue
        key = str(root)
        if key in seen:
            continue
        seen.add(key)
        if root.is_dir() and all((root / rel).is_file() for rel in required):
            return root
    return None


def require_sources() -> tuple[Path, Path]:
    stegcore = find_source(STEGCORE_ENV, ("StegCore", "stegcore"), "StegVerse-Labs/StegCore", STEGCORE_REQUIRED)
    master = find_source(MASTER_RECORDS_ENV, ("core-lite", "master-records-core-lite"), "master-records/core-lite", MR_REQUIRED)
    if stegcore is None or master is None:
        missing = []
        if stegcore is None:
            missing.append("StegCore")
        if master is None:
            missing.append("master-records/core-lite")
        raise SourceUnavailable("missing locally materialized source: " + ", ".join(missing))
    return stegcore, master


def bound_root() -> Path:
    raw = str(os.getenv(BOUND_STATE_ENV) or "").strip()
    if not raw:
        raise RuntimeError("bounded state root unavailable")
    root = Path(raw).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def execute(invocation: Mapping[str, Any]) -> dict[str, Any]:
    if any(truthy(os.getenv(name)) for name in HOSTED_ENV):
        raise RuntimeError("hosted environments cannot execute sovereign reference observation")
    present = [name for name in FORBIDDEN_CREDENTIAL_ENV if truthy(os.getenv(name))]
    if present:
        raise RuntimeError("forbidden credential-bearing environment: " + ",".join(sorted(present)))

    node_path, node = find_node()
    validate_invocation(invocation)
    stegcore, master = require_sources()
    root = bound_root()
    steg_state = root / "stegcore-reference"

    child = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PYTHONPATH": str(stegcore / "src"),
        "HOME": os.environ.get("HOME", ""),
    }
    proc = subprocess.run(
        [sys.executable, "scripts/run_universal_governance_reference_boundary.py",
         "--bound-state-root", str(steg_state)],
        cwd=stegcore,
        env=child,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError("StegCore reference runner failed: " + (proc.stdout + proc.stderr)[-4000:])

    runner_receipt = read_json(steg_state / "receipts" / "reference-boundary.latest.json")
    required_true = ("reference_enforced_boundary_observed", "bypass_negative_control_passed")
    if any(runner_receipt.get(k) is not True for k in required_true):
        raise RuntimeError("reference-boundary predicates not observed")
    if runner_receipt.get("governed_target_mutation_count") != 1:
        raise RuntimeError("reference target did not mutate exactly once")
    if runner_receipt.get("real_external_system_enforced_activation") is not False:
        raise RuntimeError("reference runner overclaimed real external activation")
    if runner_receipt.get("credential_authority") != "TV/TVC":
        raise RuntimeError("reference runner credential authority drift")

    evidence = steg_state / "evidence" / "consequence.json"
    projection = steg_state / "evidence" / "master-records-projection.json"
    mr_proc = subprocess.run(
        [sys.executable, "tools/validate_universal_governance_consequence_custody.py",
         str(evidence), str(projection)],
        cwd=master,
        env={"PATH": child["PATH"], "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    if mr_proc.returncode != 0:
        raise RuntimeError("Master Records custody validation failed: " + (mr_proc.stdout + mr_proc.stderr)[-4000:])
    lines = [line.strip() for line in mr_proc.stdout.splitlines() if line.strip()]
    if not lines or lines[0] != "MASTER RECORDS UNIVERSAL GOVERNANCE CUSTODY: PASS":
        raise RuntimeError("Master Records custody PASS marker missing")
    custody = json.loads(lines[-1])
    effect = custody.get("custody_effect") or {}
    if effect.get("destination_custody_accepted") is not True:
        raise RuntimeError("Master Records custody not accepted")
    if effect.get("runtime_activation") is not False or effect.get("execution_authority_granted") is not False:
        raise RuntimeError("Master Records custody authority escalation")
    if effect.get("credential_authority") != "TV/TVC":
        raise RuntimeError("Master Records credential authority drift")

    custody_path = root / "master-records" / "custody.json"
    custody_path.parent.mkdir(parents=True, exist_ok=True)
    custody_path.write_text(json.dumps(custody, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    receipt = {
        "schema": "stegverse.universal-governance-enforced-reference-observation/v1",
        "task_id": TASK_ID,
        "state": "OBSERVED",
        "transition_id": "UNIVERSAL_GOVERNANCE_REFERENCE_ENFORCED_BOUNDARY_OBSERVED",
        "claim_id": (invocation.get("task") or {}).get("claim_id"),
        "worker_id": WORKER_ID,
        "node_declaration_ref": str(node_path),
        "node_declaration_source": node.get("declaration_source"),
        "stegcore_source_root": str(stegcore),
        "master_records_source_root": str(master),
        "reference_enforced_boundary_observed": True,
        "bypass_negative_control_passed": True,
        "governed_target_mutation_count": 1,
        "master_records_custody_accepted": True,
        "real_external_system_enforced_activation": False,
        "runner_receipt_ref": "stegcore-reference/receipts/reference-boundary.latest.json",
        "custody_record_ref": "master-records/custody.json",
        "credential_authority": "TV/TVC",
        "github_token_used": False,
        "network_used": False,
        "repository_writeback_performed": False,
        "continuity_receipt_minted": False,
        "publication_authority_granted": False,
        "authority_effect": "REFERENCE_ENFORCED_BOUNDARY_OBSERVATION_ONLY",
    }
    out = root / "receipts" / "latest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt["local_receipt_ref"] = "receipts/latest.json"
    return receipt


def completed_response(receipt: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "COMPLETED",
        "transition_id": "UNIVERSAL_GOVERNANCE_REFERENCE_ENFORCED_BOUNDARY_OBSERVED",
        "transition_sequence": 2,
        "expected_next_transition": None,
        "evidence_refs": [str(receipt["local_receipt_ref"])],
        "credential_authority": "TV/TVC",
        "github_token_used": False,
        "repository_writeback_performed": False,
    }


def handoff_response(exc: Exception) -> dict[str, Any]:
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "HANDOFF_READY",
        "transition_id": "UNIVERSAL_GOVERNANCE_REFERENCE_SOURCE_MATERIALIZATION_PENDING",
        "transition_sequence": 1,
        "expected_next_transition": "UNIVERSAL_GOVERNANCE_REFERENCE_ENFORCED_BOUNDARY_OBSERVED",
        "error": str(exc),
        "evidence_refs": [],
        "credential_authority": "TV/TVC",
        "github_token_used": False,
        "repository_writeback_performed": False,
    }


def blocked_response(exc: Exception) -> dict[str, Any]:
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "BLOCKED",
        "transition_id": "UNIVERSAL_GOVERNANCE_REFERENCE_ENFORCED_BOUNDARY_BLOCKED",
        "transition_sequence": 1,
        "expected_next_transition": "UNIVERSAL_GOVERNANCE_REFERENCE_ENFORCED_BOUNDARY_OBSERVED",
        "error": str(exc),
        "evidence_refs": [],
        "credential_authority": "TV/TVC",
        "github_token_used": False,
        "repository_writeback_performed": False,
    }


def main() -> int:
    try:
        invocation = json.loads(sys.stdin.readline())
        if not isinstance(invocation, dict):
            raise RuntimeError("worker invocation must be object")
        receipt = execute(invocation)
        print(json.dumps(completed_response(receipt), sort_keys=True))
    except SourceUnavailable as exc:
        print(json.dumps(handoff_response(exc), sort_keys=True))
    except Exception as exc:
        print(json.dumps(blocked_response(exc), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
