#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.cwd().resolve()
CONFIG = ROOT / "control" / "formalism-manifold-orchestration.json"
RECEIPT_ROOT = (ROOT / "receipts" / "formalism-manifold-orchestration").resolve()
CURRENT_AUTHORITY = "TV/TVC"

TASKS = {
    "SHWP-FORMALISM-INVENTORY-001": ("FORMALISM-INVENTORY", "formalism_inventory_reconciliation"),
    "SHWP-FORMALISM-HANDOFF-NORMALIZATION-001": ("HANDOFF-NORMALIZATION", "formalism_handoff_normalization_analysis"),
    "SHWP-FORMALISM-MATHEMATICAL-CROSSWALK-001": ("MATHEMATICAL-CROSSWALK", "formalism_mathematical_crosswalk"),
    "SHWP-MANIFOLD-GOVERNANCE-MAPPING-001": ("GOVERNANCE-MAPPING", "manifold_governance_mapping"),
    "SHWP-FORMALISM-MANIFOLD-RECONCILIATION-001": ("RECONCILIATION", "formalism_manifold_reconciliation"),
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = handle.name
    os.replace(temporary, path)


def roots_from_environment() -> dict[str, Path]:
    raw = os.environ.get("STEGVERSE_FORMALISM_ROOTS_JSON", "")
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    result: dict[str, Path] = {}
    for repo, value in parsed.items():
        if isinstance(repo, str) and isinstance(value, str):
            path = Path(value).expanduser().resolve()
            result[repo] = path
    return result


def handoff_files(repo_root: Path) -> list[Path]:
    candidates: list[Path] = []
    for base in (repo_root, repo_root / "docs"):
        if not base.is_dir():
            continue
        for path in sorted(base.glob("*_MIRROR_HANDOFF.md")):
            if path.is_file():
                candidates.append(path)
    return candidates


def relative(repo_root: Path, path: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def inventory(config: dict, roots: dict[str, Path]) -> dict:
    rows = []
    for spec in config["required_repositories"]:
        repo = spec["repository"]
        root = roots.get(repo)
        present = bool(root and root.is_dir())
        handoffs = handoff_files(root) if present and root else []
        rows.append({
            "repository": repo,
            "required": bool(spec.get("required")),
            "materialized": present,
            "handoffs": [relative(root, p) for p in handoffs] if root else [],
            "handoff_present": bool(handoffs),
        })
    missing = [r["repository"] for r in rows if r["required"] and not r["materialized"]]
    missing_handoff = [r["repository"] for r in rows if r["required"] and r["materialized"] and not r["handoff_present"]]
    return {"repositories": rows, "missing_materialization": missing, "missing_handoff": missing_handoff}


def normalization(config: dict, roots: dict[str, Path]) -> dict:
    required = config["relationship_contract"]["required_handoff_fields"]
    aliases = {
        "formal_role": ["formal role", "role", "purpose"],
        "inputs": ["inputs", "source refs", "dependencies"],
        "outputs": ["outputs", "receipts", "artifacts"],
        "upstream_dependencies": ["upstream", "dependencies"],
        "downstream_consumers": ["downstream", "consumer", "propagation"],
        "authority_boundary": ["authority boundary", "authority", "non-claims"],
        "composition_relations": ["composition", "compositional", "relationship"],
        "resolution_relationship": ["resolution", "admissible resolution"],
        "continuity_relationship": ["continuity", "reconstruction", "reconstruct"],
        "mathematical_maturity": ["mathematical maturity", "theorem", "axiom", "formalism"],
        "functional_maturity": ["functional maturity", "status", "validation"],
        "collision_rules": ["collision", "do not", "claims"],
    }
    rows = []
    for spec in config["required_repositories"]:
        repo = spec["repository"]
        root = roots.get(repo)
        handoffs = handoff_files(root) if root and root.is_dir() else []
        text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in handoffs).lower()
        fields = {}
        for field in required:
            fields[field] = any(token in text for token in aliases.get(field, [field.replace("_", " ")]))
        rows.append({
            "repository": repo,
            "handoff_present": bool(handoffs),
            "field_presence": fields,
            "missing_fields": [key for key, value in fields.items() if not value],
        })
    return {"repositories": rows, "normalization_complete": all(r["handoff_present"] and not r["missing_fields"] for r in rows)}


def crosswalk(config: dict, roots: dict[str, Path]) -> dict:
    known = {spec["repository"] for spec in config["required_repositories"]}
    ref_pattern = re.compile(r"\b([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\b")
    nodes = []
    edges = set()
    for spec in config["required_repositories"]:
        repo = spec["repository"]
        root = roots.get(repo)
        handoffs = handoff_files(root) if root and root.is_dir() else []
        refs = set()
        for path in handoffs:
            refs.update(match for match in ref_pattern.findall(path.read_text(encoding="utf-8", errors="replace")) if match in known and match != repo)
        nodes.append({"repository": repo, "handoff_count": len(handoffs), "declared_related_repositories": sorted(refs)})
        for target in refs:
            edges.add((repo, target))
    return {
        "nodes": nodes,
        "edges": [{"source": source, "target": target, "relation": "DECLARED_REFERENCE_UNTYPED"} for source, target in sorted(edges)],
        "authority_effect": "NONE_RELATIONSHIP_EVIDENCE_ONLY",
    }


def governance_mapping(config: dict, roots: dict[str, Path]) -> dict:
    ae = roots.get("Admissible-Existence/AE")
    stegcore = roots.get("StegVerse-Labs/StegCore")
    ae_handoffs = handoff_files(ae) if ae and ae.is_dir() else []
    core_handoffs = handoff_files(stegcore) if stegcore and stegcore.is_dir() else []
    bridge_ready = bool(ae_handoffs and core_handoffs)
    return {
        "bridge_ready_for_analysis": bridge_ready,
        "formalism_authority": config["formalism_authority"],
        "runtime_authority": config["runtime_authority"],
        "formalism_handoffs": [relative(ae, p) for p in ae_handoffs] if ae else [],
        "runtime_handoffs": [relative(stegcore, p) for p in core_handoffs] if stegcore else [],
        "mapping_contract": [
            "AE/RTG/TT/STCM/GTG constructs are upstream mathematical inputs.",
            "StegCore canonical StegGate remains the execution/admissibility runtime authority.",
            "Manifold/coherence/gradient observations remain evidence and cannot independently grant execution authority.",
            "Runtime mappings may reference/version mathematical constructs but may not silently redefine them."
        ],
        "authority_effect": "NONE_MAPPING_EVIDENCE_ONLY",
    }


def reconciliation() -> dict:
    required = [
        "SHWP-FORMALISM-INVENTORY-001.json",
        "SHWP-FORMALISM-HANDOFF-NORMALIZATION-001.json",
        "SHWP-FORMALISM-MATHEMATICAL-CROSSWALK-001.json",
        "SHWP-MANIFOLD-GOVERNANCE-MAPPING-001.json",
    ]
    rows = []
    for name in required:
        path = RECEIPT_ROOT / name
        if not path.is_file():
            rows.append({"receipt": name, "present": False, "state": None, "sha256": None})
            continue
        value = load(path)
        rows.append({"receipt": name, "present": True, "state": value.get("state"), "sha256": canonical_hash(value)})
    complete = all(row["present"] and row["state"] == "COMPLETED" for row in rows)
    return {"inputs": rows, "reconciled": complete, "authority_effect": "NONE_RECONCILIATION_EVIDENCE_ONLY"}


def main() -> int:
    try:
        invocation = json.load(sys.stdin)
    except Exception as exc:
        print(f"invalid invocation: {exc}", file=sys.stderr)
        return 2
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return 3
    epoch = invocation.get("heartbeat_epoch")
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    task_id = task.get("task_id")
    if not isinstance(epoch, int) or task_id not in TASKS:
        return 4
    lane_id, capability = TASKS[task_id]
    timing = task.get("heartbeat_timing") or {}
    claim_id = task.get("claim_id")
    fence = timing.get("fencing_token")
    if not claim_id or not isinstance(fence, int):
        return 5
    execution = handoff.get("execution") or {}
    if capability not in set(execution.get("required_capabilities") or []):
        return 6
    allowed = f"receipts/formalism-manifold-orchestration/**"
    if allowed not in set(execution.get("allowed_paths") or []):
        return 7

    config = load(CONFIG)
    if config.get("schema") != "stegverse.formalism-manifold-orchestration/v0.1":
        return 8
    if config.get("credential_authority") != CURRENT_AUTHORITY or config.get("github_token_required") is not False:
        return 9

    roots = roots_from_environment()
    if lane_id == "FORMALISM-INVENTORY":
        result = inventory(config, roots)
        complete = not result["missing_materialization"] and not result["missing_handoff"]
    elif lane_id == "HANDOFF-NORMALIZATION":
        result = normalization(config, roots)
        complete = bool(result["normalization_complete"])
    elif lane_id == "MATHEMATICAL-CROSSWALK":
        result = crosswalk(config, roots)
        complete = all(node["handoff_count"] > 0 for node in result["nodes"])
    elif lane_id == "GOVERNANCE-MAPPING":
        result = governance_mapping(config, roots)
        complete = bool(result["bridge_ready_for_analysis"])
    else:
        result = reconciliation()
        complete = bool(result["reconciled"])

    state = "COMPLETED" if complete else "BLOCKED"
    transition_id = f"{lane_id.replace('-', '_')}_{'COMPLETE' if complete else 'COVERAGE_GAP'}"
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    blocker = None if complete else {
        "dependency_class": "INTERNAL_CAPABILITY",
        "problem_statement": "Required local formalism/runtime evidence is absent or incomplete for this lane.",
        "solution_required": True,
        "may_remain_blocked": True,
        "next_solution_action": "MATERIALIZE_OR_RECONCILE_REQUIRED_FORMALISM_INPUTS"
    }
    receipt = {
        "schema": "stegverse.formalism-manifold-orchestration-receipt/v0.1",
        "goal_id": config["goal_id"],
        "task_id": task_id,
        "lane_id": lane_id,
        "claim_id": claim_id,
        "worker_id": task.get("worker_id"),
        "worker_instance_id": task.get("worker_instance_id"),
        "heartbeat_epoch": epoch,
        "fencing_token": fence,
        "generated_at": now,
        "state": state,
        "transition_id": transition_id,
        "result": result,
        "fail_closed": True,
        "credential_authority": CURRENT_AUTHORITY,
        "github_token_required": False,
        "heartbeat_grants_execution_authority": False,
        "authority_effect": "NONE_EVIDENCE_ONLY",
        "blocker": blocker,
    }
    receipt_path = RECEIPT_ROOT / f"{task_id}.json"
    atomic_write(receipt_path, receipt)

    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition_id,
        "transition_sequence": 1,
        "expected_next_transition": None if complete else f"{lane_id.replace('-', '_')}_RECHECK",
        "expected_next_earliest_epoch": None if complete else epoch + 1,
        "expected_next_latest_epoch": None if complete else epoch + 1,
        "checkpoint_ref": f"receipts/formalism-manifold-orchestration/{task_id}.json",
        "evidence_refs": [
            "control/formalism-manifold-orchestration.json",
            f"receipts/formalism-manifold-orchestration/{task_id}.json"
        ],
        "blocker": blocker,
        "cost_observation": {"hb_transition_count": 1, "compute_units": 1, "external_cost_usd": 0, "task_class": "formalism_manifold_orchestration"}
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
