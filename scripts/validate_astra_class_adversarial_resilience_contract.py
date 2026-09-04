#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "control/astra-class-adversarial-resilience-contract.json"
CARRIER = ROOT / "control/canonical-resident-carrier-contract.json"
SEPARATION = ROOT / "control/runtime-separation-contract.json"


def validate(root: Path = ROOT) -> dict:
    contract = json.loads((root / CONTRACT.relative_to(ROOT)).read_text(encoding="utf-8"))
    carrier = json.loads((root / CARRIER.relative_to(ROOT)).read_text(encoding="utf-8"))
    separation = json.loads((root / SEPARATION.relative_to(ROOT)).read_text(encoding="utf-8"))

    assert contract["schema"] == "stegverse.astra-class-adversarial-resilience-contract/v1"
    assert contract["goal_id"] == "ASTRA-CLASS-RESILIENCE-001"
    assert contract["threat_class"] == "FRONTIER_AI_CRITICAL_CYBER_CAPABILITY"
    assert contract["runtime_claim"] is False
    assert contract["deployment_claim"] is False
    assert contract["absolute_security_claim"] is False

    auth = contract["authority_invariants"]
    assert auth["capability_confers_authority"] is False
    assert auth["heartbeat_authority"] == "REFERENCE_OBSERVABILITY_ONLY"
    assert auth["intr_interlock_role"] == "ADMISSIBLE_TRANSITION_BOUNDARY"
    assert auth["worker_runtime"] == "EXISTING_WORKERCOORDINATOR_ONLY"
    assert auth["credential_authority"] == "TV/TVC_ONLY"
    assert auth["github_token_runtime_authority"] == "NONE"
    assert auth["second_user_operated_machine_required"] is False
    assert auth["fail_closed_on_missing_or_contradictory_authority_evidence"] is True

    # The resilience directive must remain subordinate to the already-canonical
    # resident/runtime authority split rather than quietly introducing a new one.
    assert carrier["credential_authority"] == "TV/TVC"
    assert carrier["github_token_runtime_authority"] == "NONE"
    assert carrier["second_user_operated_machine_required"] is False
    assert carrier["worker_runtime"]["class"] == "WorkerCoordinator"
    assert carrier["worker_runtime"]["second_scheduler_allowed"] is False
    assert carrier["worker_runtime"]["second_worker_runtime_allowed"] is False
    assert separation["authority"]["heartbeat_grants_execution_authority"] is False
    assert separation["authority"]["credential_authority"] == "TV/TVC"

    expected_roles = {
        "StegVerse-001": "CONTINUITY_REPLAY_DRIFT",
        "StegVerse-002": "CANONICAL_THREAT_AND_ADMISSIBILITY_MODEL",
        "SV-011": "GOVERNED_AUTONOMOUS_HARDENING_REBUILD",
    }
    by_entity = {row["entity_id"]: row for row in contract["entities"]}
    assert set(by_entity) == set(expected_roles)
    for entity_id, role in expected_roles.items():
        assert by_entity[entity_id]["resilience_role"] == role
        assert by_entity[entity_id]["required_responsibilities"]

    assert by_entity["StegVerse-001"]["selector"] == "stegverse001_bounded_autonomy"
    assert by_entity["StegVerse-002"]["selector"] == "sv002_org_runtime_activation"
    assert by_entity["SV-011"]["selectors"] == [
        "sv011_phase5_source_materialization",
        "sv011_phase5",
    ]

    carrier_selectors = {row["selector"] for row in carrier["consumers"]}
    assert "stegverse001_bounded_autonomy" in carrier_selectors
    assert "sv002_org_runtime_activation" in carrier_selectors
    assert "sv011_phase5" in carrier_selectors
    assert any(
        row.get("predecessor_selector") == "sv011_phase5_source_materialization"
        for row in carrier["consumers"]
    )

    properties = set(contract["required_security_properties"])
    required_properties = {
        "AUTHORITY_EXTERNALIZATION",
        "LEAST_CONSEQUENCE",
        "COMPARTMENTALIZATION",
        "FRESH_ADMISSIBILITY",
        "REVOCABILITY",
        "REPLAYABILITY",
        "TAMPER_EVIDENCE",
        "UNKNOWN_STATE_PRESERVATION",
        "DEPENDENCY_MINIMIZATION",
        "DENIED_CONSEQUENCE_PROOF",
        "ADVERSARIAL_UPDATEABILITY",
        "NO_SELF_EXEMPTION",
    }
    assert properties == required_properties

    threat_assumptions = set(contract["threat_assumptions"])
    assert "UNKNOWN_VULNERABILITY_DISCOVERY" in threat_assumptions
    assert "NOVEL_EXPLOIT_CHAIN_CONSTRUCTION" in threat_assumptions
    assert "MONITORING_EVASION_ATTEMPTS" in threat_assumptions

    return {
        "schema": "stegverse.astra-class-adversarial-resilience-validation/v1",
        "state": "PASS",
        "goal_id": contract["goal_id"],
        "entity_count": len(by_entity),
        "security_property_count": len(properties),
        "threat_assumption_count": len(threat_assumptions),
        "credential_authority": "TV/TVC",
        "worker_runtime": "WorkerCoordinator",
        "runtime_claim": False,
        "authority_effect": "NONE_VALIDATION_ONLY",
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
