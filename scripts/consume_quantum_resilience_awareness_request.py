#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_REL = Path("control/quantum-resilience-contract.json")
CENSUS_REL = Path("control/quantum-crypto-census.json")
REQUEST_DIR = Path("control/resident-execution-request.d")
STATE_DIR = Path("runtime-state/entity-quantum-awareness")
RECEIPT_DIR = Path("receipts/sovereign-host/quantum-resilience")
AGGREGATE_REL = Path("receipts/sovereign-host/quantum-resilience-awareness.latest.json")

ENTITY_SPECS = {
    "StegVerse-001": {"slug": "stegverse-001", "role": "CRYPTO_LINEAGE_REPLAY_CONTINUITY", "request": "quantum-resilience-sv001-awareness-001.json", "task": "SHWP-QUANTUM-RESILIENCE-SV001-AWARENESS-001", "selectors": ["stegverse001_bounded_autonomy"]},
    "StegVerse-002": {"slug": "stegverse-002", "role": "CRYPTO_CENSUS_STATUS_ADMISSIBILITY_PROPOSALS", "request": "quantum-resilience-sv002-awareness-001.json", "task": "SHWP-QUANTUM-RESILIENCE-SV002-AWARENESS-001", "selectors": ["sv002_org_runtime_activation"]},
    "SV-011": {"slug": "sv-011", "role": "HYBRID_PQC_HARDENING_EXPERIMENTS", "request": "quantum-resilience-sv011-awareness-001.json", "task": "SHWP-QUANTUM-RESILIENCE-SV011-AWARENESS-001", "selectors": ["sv011_phase5_source_materialization", "sv011_phase5"]},
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected object: {path}")
    return value


def sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def validate_inputs(contract: dict[str, Any], census: dict[str, Any]) -> None:
    if contract.get("schema") != "stegverse.quantum-resilience-contract/v1" or contract.get("goal_id") != "QUANTUM-RESILIENCE-001":
        raise RuntimeError("quantum contract mismatch")
    auth = contract.get("authority") or {}
    required = {
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "intr_interlock_transition_boundary": True,
        "quantum_capability_confers_authority": False,
        "pqc_validity_confers_transition_authority": False,
        "second_machine_required": False,
    }
    for key, expected in required.items():
        if auth.get(key) != expected:
            raise RuntimeError(f"quantum authority invariant mismatch: {key}")
    roles = {row.get("entity_id"): row.get("role") for row in contract.get("entity_roles", []) if isinstance(row, dict)}
    if roles != {entity: spec["role"] for entity, spec in ENTITY_SPECS.items()}:
        raise RuntimeError("quantum entity role mismatch")
    if census.get("schema") != "stegverse.quantum-crypto-census/v1" or census.get("goal_id") != "QUANTUM-RESILIENCE-001":
        raise RuntimeError("quantum census mismatch")
    if census.get("runtime_claim") is not False or census.get("deployment_claim") is not False:
        raise RuntimeError("source census may not pre-claim runtime/deployment")


def validate_request(req: dict[str, Any], entity: str, spec: dict[str, Any]) -> None:
    expected = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": spec["task"],
        "mode": "TARGETED_INDEPENDENT_TASK_CONTROL",
        "entrypoint": "scripts/consume_quantum_resilience_awareness_request.py",
        "entity_id": entity,
        "quantum_role": spec["role"],
        "contract_ref": str(CONTRACT_REL),
        "census_ref": str(CENSUS_REL),
        "standing_directive": True,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "second_machine_required": False,
        "request_granted_authority": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, value in expected.items():
        if req.get(key) != value:
            raise RuntimeError(f"request mismatch {entity}: {key}")
    if req.get("entity_selectors") != spec["selectors"]:
        raise RuntimeError(f"selector mismatch: {entity}")


def consume(source_root: Path, runtime_root: Path) -> dict[str, Any]:
    runtime = runtime_root.expanduser().resolve()
    contract_path, census_path = runtime / CONTRACT_REL, runtime / CENSUS_REL
    if not contract_path.is_file() or not census_path.is_file():
        return {"schema": "stegverse.quantum-resilience-awareness-consumption/v1", "state": "NO_REQUEST", "runtime_awareness_materialized": False, "authority_effect": "NONE"}
    contract, census = load(contract_path), load(census_path)
    validate_inputs(contract, census)
    contract_sha, census_sha = sha(contract), sha(census)
    outputs = []
    for entity, spec in ENTITY_SPECS.items():
        req_path = runtime / REQUEST_DIR / spec["request"]
        if not req_path.is_file():
            raise RuntimeError(f"missing quantum awareness request: {entity}")
        req = load(req_path)
        validate_request(req, entity, spec)
        request_sha = sha(req)
        state_path = runtime / STATE_DIR / f"{spec['slug']}.json"
        receipt_path = runtime / RECEIPT_DIR / f"{spec['slug']}.latest.json"
        prior = load(receipt_path) if receipt_path.is_file() else None
        if prior and prior.get("state") == "COMPLETED" and prior.get("request_sha256") == request_sha and prior.get("contract_sha256") == contract_sha and prior.get("census_sha256") == census_sha:
            outputs.append({"entity_id": entity, "state": "ALREADY_CONSUMED", "request_sha256": request_sha, "contract_sha256": contract_sha, "census_sha256": census_sha, "standing_directive_active": True})
            continue
        state = {
            "schema": "stegverse.entity-quantum-resilience-awareness-state/v1", "state": "ACTIVE", "goal_id": "QUANTUM-RESILIENCE-001",
            "entity_id": entity, "quantum_role": spec["role"], "standing_directive_active": True, "bound_runtime_selectors": spec["selectors"],
            "contract_sha256": contract_sha, "census_sha256": census_sha, "request_sha256": request_sha,
            "required_properties": contract.get("required_properties", []), "known_surface_count": len(census.get("surfaces", [])),
            "credential_authority": "TV/TVC", "github_token_runtime_authority": "NONE", "quantum_capability_confers_authority": False,
            "pqc_validity_confers_transition_authority": False, "heartbeat_grants_execution_authority": False, "intr_interlock_remains_transition_boundary": True,
            "worker_runtime": "WorkerCoordinator", "second_machine_required": False, "future_task_directive": "CONSULT_QUANTUM_STANDING_STATE_FOR_SECURITY_RELEVANT_WORK",
            "pqc_deployment_claim": False, "absolute_quantum_security_claim": False,
        }
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        receipt = {
            "schema": "stegverse.entity-quantum-resilience-awareness-receipt/v1", "state": "COMPLETED", "task_id": spec["task"], "entity_id": entity,
            "quantum_role": spec["role"], "request_sha256": request_sha, "contract_sha256": contract_sha, "census_sha256": census_sha,
            "awareness_state_ref": str(STATE_DIR / f"{spec['slug']}.json"), "standing_directive_active": True, "runtime_awareness_materialized": True,
            "runtime_substrate": "HEARTBEAT_SEPARATED_NATIVE_WORKER_COORDINATOR", "credential_authority": "TV/TVC", "github_token_runtime_authority": "NONE",
            "heartbeat_grants_execution_authority": False, "request_granted_authority": False, "second_machine_required": False,
            "pqc_deployment_claim": False, "absolute_quantum_security_claim": False, "authority_effect": "NONE_AWARENESS_MATERIALIZATION_ONLY",
        }
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        outputs.append(receipt)
    complete = len(outputs) == 3 and all(row.get("state") in {"COMPLETED", "ALREADY_CONSUMED"} for row in outputs)
    aggregate = {
        "schema": "stegverse.quantum-resilience-awareness-consumption/v1", "state": "COMPLETED" if complete else "ATTEMPT_RECORDED", "goal_id": "QUANTUM-RESILIENCE-001",
        "contract_sha256": contract_sha, "census_sha256": census_sha, "entity_count": len(outputs), "entities": outputs,
        "runtime_awareness_materialized": complete, "standing_directive_active": complete, "runtime_substrate": "HEARTBEAT_SEPARATED_NATIVE_WORKER_COORDINATOR",
        "credential_authority": "TV/TVC", "github_token_runtime_authority": "NONE", "heartbeat_grants_execution_authority": False,
        "second_machine_required": False, "pqc_deployment_claim": False, "absolute_quantum_security_claim": False, "authority_effect": "NONE_AWARENESS_MATERIALIZATION_ONLY",
    }
    path = runtime / AGGREGATE_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(aggregate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return aggregate


def main() -> int:
    parser = argparse.ArgumentParser(description="Materialize standing quantum-resilience awareness for SV001, SV002, and SV-011.")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    result = consume(args.source_root, args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] in {"COMPLETED", "NO_REQUEST"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
