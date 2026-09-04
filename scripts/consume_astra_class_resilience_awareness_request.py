#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_REL = Path("control/astra-class-adversarial-resilience-contract.json")
REQUEST_DIR = Path("control/resident-execution-request.d")
AGGREGATE_RECEIPT_REL = Path("receipts/sovereign-host/astra-class-resilience-awareness.latest.json")
AWARENESS_STATE_DIR = Path("runtime-state/entity-awareness")
ENTITY_RECEIPT_DIR = Path("receipts/sovereign-host/astra-class-resilience")

ENTITY_SPECS = {
    "StegVerse-001": {
        "request": "astra-class-resilience-sv001-awareness-001.json",
        "task_id": "SHWP-ASTRA-CLASS-RESILIENCE-SV001-AWARENESS-001",
        "role": "CONTINUITY_REPLAY_DRIFT",
        "slug": "stegverse-001",
        "selector_field": "entity_selector",
        "selectors": ["stegverse001_bounded_autonomy"],
    },
    "StegVerse-002": {
        "request": "astra-class-resilience-sv002-awareness-001.json",
        "task_id": "SHWP-ASTRA-CLASS-RESILIENCE-SV002-AWARENESS-001",
        "role": "CANONICAL_THREAT_AND_ADMISSIBILITY_MODEL",
        "slug": "stegverse-002",
        "selector_field": "entity_selector",
        "selectors": ["sv002_org_runtime_activation"],
    },
    "SV-011": {
        "request": "astra-class-resilience-sv011-awareness-001.json",
        "task_id": "SHWP-ASTRA-CLASS-RESILIENCE-SV011-AWARENESS-001",
        "role": "GOVERNED_AUTONOMOUS_HARDENING_REBUILD",
        "slug": "sv-011",
        "selector_field": "entity_selectors",
        "selectors": ["sv011_phase5_source_materialization", "sv011_phase5"],
    },
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected object: {path}")
    return value


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def validate_contract(contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if contract.get("schema") != "stegverse.astra-class-adversarial-resilience-contract/v1":
        raise RuntimeError("resilience contract schema mismatch")
    if contract.get("goal_id") != "ASTRA-CLASS-RESILIENCE-001":
        raise RuntimeError("resilience goal mismatch")
    if contract.get("runtime_claim") is not False or contract.get("absolute_security_claim") is not False:
        raise RuntimeError("source contract may not pre-claim runtime or absolute security")
    auth = contract.get("authority_invariants") or {}
    required_auth = {
        "capability_confers_authority": False,
        "heartbeat_authority": "REFERENCE_OBSERVABILITY_ONLY",
        "intr_interlock_role": "ADMISSIBLE_TRANSITION_BOUNDARY",
        "worker_runtime": "EXISTING_WORKERCOORDINATOR_ONLY",
        "credential_authority": "TV/TVC_ONLY",
        "github_token_runtime_authority": "NONE",
        "second_user_operated_machine_required": False,
        "fail_closed_on_missing_or_contradictory_authority_evidence": True,
    }
    for key, expected in required_auth.items():
        if auth.get(key) != expected:
            raise RuntimeError(f"authority invariant mismatch: {key}")
    entities = {row.get("entity_id"): row for row in contract.get("entities", []) if isinstance(row, dict)}
    if set(entities) != set(ENTITY_SPECS):
        raise RuntimeError("contract entity set mismatch")
    for entity_id, spec in ENTITY_SPECS.items():
        if entities[entity_id].get("resilience_role") != spec["role"]:
            raise RuntimeError(f"resilience role mismatch: {entity_id}")
        if not entities[entity_id].get("required_responsibilities"):
            raise RuntimeError(f"missing responsibilities: {entity_id}")
    return entities


def validate_request(req: dict[str, Any], entity_id: str, spec: dict[str, Any]) -> None:
    expected = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": spec["task_id"],
        "mode": "TARGETED_INDEPENDENT_TASK_CONTROL",
        "entrypoint": "scripts/consume_astra_class_resilience_awareness_request.py",
        "entity_id": entity_id,
        "resilience_role": spec["role"],
        "contract_ref": str(CONTRACT_REL),
        "standing_directive": True,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "second_machine_required": False,
        "network_source_fetch_allowed": False,
        "request_granted_authority": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, value in expected.items():
        if req.get(key) != value:
            raise RuntimeError(f"request mismatch for {entity_id}: {key}")
    field = spec["selector_field"]
    actual = req.get(field)
    expected_selectors = spec["selectors"]
    if field == "entity_selector":
        if actual != expected_selectors[0]:
            raise RuntimeError(f"selector mismatch for {entity_id}")
    elif actual != expected_selectors:
        raise RuntimeError(f"selectors mismatch for {entity_id}")


def consume(source_root: Path, runtime_root: Path) -> dict[str, Any]:
    runtime = runtime_root.expanduser().resolve()
    contract_path = runtime / CONTRACT_REL
    if not contract_path.is_file():
        return {
            "schema": "stegverse.astra-class-resilience-awareness-consumption/v1",
            "state": "NO_REQUEST",
            "runtime_awareness_materialized": False,
            "authority_effect": "NONE",
        }

    contract = load(contract_path)
    entities = validate_contract(contract)
    contract_sha = canonical_sha256(contract)
    outputs: list[dict[str, Any]] = []

    for entity_id, spec in ENTITY_SPECS.items():
        request_path = runtime / REQUEST_DIR / spec["request"]
        if not request_path.is_file():
            raise RuntimeError(f"missing resident awareness request: {entity_id}")
        req = load(request_path)
        validate_request(req, entity_id, spec)
        request_sha = canonical_sha256(req)
        entity_contract = entities[entity_id]
        state_path = runtime / AWARENESS_STATE_DIR / f"{spec['slug']}.json"
        receipt_path = runtime / ENTITY_RECEIPT_DIR / f"{spec['slug']}.latest.json"

        prior = load(receipt_path) if receipt_path.is_file() else None
        already = bool(
            prior
            and prior.get("state") == "COMPLETED"
            and prior.get("request_sha256") == request_sha
            and prior.get("contract_sha256") == contract_sha
            and prior.get("standing_directive_active") is True
        )
        if already:
            outputs.append({
                "entity_id": entity_id,
                "state": "ALREADY_CONSUMED",
                "request_sha256": request_sha,
                "contract_sha256": contract_sha,
                "standing_directive_active": True,
            })
            continue

        awareness_state = {
            "schema": "stegverse.entity-frontier-resilience-awareness-state/v1",
            "state": "ACTIVE",
            "goal_id": contract["goal_id"],
            "entity_id": entity_id,
            "resilience_role": spec["role"],
            "standing_directive_active": True,
            "threat_class": contract["threat_class"],
            "threat_assumptions": contract["threat_assumptions"],
            "required_security_properties": contract["required_security_properties"],
            "required_responsibilities": entity_contract["required_responsibilities"],
            "bound_runtime_selectors": spec["selectors"],
            "contract_sha256": contract_sha,
            "request_sha256": request_sha,
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
            "capability_confers_authority": False,
            "heartbeat_grants_execution_authority": False,
            "intr_interlock_remains_transition_boundary": True,
            "worker_runtime": "WorkerCoordinator",
            "second_machine_required": False,
            "future_task_directive": "USE_THIS_STANDING_STATE_WHEN_PROPOSING_OR_EXECUTING_SECURITY_RELEVANT_WORK",
            "absolute_security_claim": False,
        }
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(awareness_state, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        receipt = {
            "schema": "stegverse.entity-frontier-resilience-awareness-receipt/v1",
            "state": "COMPLETED",
            "task_id": spec["task_id"],
            "entity_id": entity_id,
            "resilience_role": spec["role"],
            "request_sha256": request_sha,
            "contract_sha256": contract_sha,
            "awareness_state_ref": str(AWARENESS_STATE_DIR / f"{spec['slug']}.json"),
            "standing_directive_active": True,
            "runtime_awareness_materialized": True,
            "runtime_substrate": "HEARTBEAT_SEPARATED_NATIVE_WORKER_COORDINATOR",
            "bound_runtime_selectors": spec["selectors"],
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
            "heartbeat_grants_execution_authority": False,
            "request_granted_authority": False,
            "second_machine_required": False,
            "absolute_security_claim": False,
            "authority_effect": "NONE_AWARENESS_MATERIALIZATION_ONLY",
        }
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        outputs.append(receipt)

    completed = all(row.get("state") in {"COMPLETED", "ALREADY_CONSUMED"} for row in outputs)
    aggregate = {
        "schema": "stegverse.astra-class-resilience-awareness-consumption/v1",
        "state": "COMPLETED" if completed else "ATTEMPT_RECORDED",
        "goal_id": contract["goal_id"],
        "contract_sha256": contract_sha,
        "entity_count": len(outputs),
        "entities": outputs,
        "runtime_awareness_materialized": completed and len(outputs) == 3,
        "standing_directive_active": completed and len(outputs) == 3,
        "runtime_substrate": "HEARTBEAT_SEPARATED_NATIVE_WORKER_COORDINATOR",
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "second_machine_required": False,
        "absolute_security_claim": False,
        "authority_effect": "NONE_AWARENESS_MATERIALIZATION_ONLY",
    }
    aggregate_path = runtime / AGGREGATE_RECEIPT_REL
    aggregate_path.parent.mkdir(parents=True, exist_ok=True)
    aggregate_path.write_text(json.dumps(aggregate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return aggregate


def main() -> int:
    parser = argparse.ArgumentParser(description="Materialize Astra-class standing awareness for SV001, SV002, and SV-011.")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    result = consume(args.source_root, args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] in {"COMPLETED", "NO_REQUEST"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
