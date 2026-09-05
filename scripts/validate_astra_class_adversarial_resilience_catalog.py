#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "control/astra-class-adversarial-resilience-test-catalog.json"
REQUIRED_CLASSES = {
    "UNKNOWN_VULNERABILITY",
    "AUTHORITY_ESCALATION",
    "STALE_STATE",
    "REPLAY_DIVERGENCE",
    "COMPROMISED_DEPENDENCY_INPUT",
    "DENIED_CONSEQUENCE_REACHABILITY",
}
REQUIRED_ENTITIES = {"StegVerse-001", "StegVerse-002", "SV-011"}


def validate(payload: dict) -> dict:
    assert payload["schema"] == "stegverse.astra-class-adversarial-resilience-test-catalog/v1"
    assert payload["goal_id"] == "ASTRA-CLASS-RESILIENCE-001"
    assert payload["authority_effect"] == "NONE_TEST_DEFINITION"
    assert payload["credential_authority"] == "TV/TVC"
    assert payload["heartbeat_grants_execution_authority"] is False
    assert payload["capability_confers_authority"] is False
    assert payload["second_machine_required"] is False
    tests = payload["tests"]
    assert len({row["id"] for row in tests}) == len(tests)
    classes = {row["class"] for row in tests}
    entities = {row["entity"] for row in tests}
    assert REQUIRED_CLASSES <= classes
    assert REQUIRED_ENTITIES <= entities
    authority = next(row for row in tests if row["class"] == "AUTHORITY_ESCALATION")
    assert "credential_mint_denied" in authority["required_assertions"]
    assert "transition_admission_denied" in authority["required_assertions"]
    assert "consequence_reachable_false" in authority["required_assertions"]
    denied = next(row for row in tests if row["class"] == "DENIED_CONSEQUENCE_REACHABILITY")
    assert "consumed_false" in denied["required_assertions"]
    assert "consequence_reachable_false" in denied["required_assertions"]
    unknown = next(row for row in tests if row["class"] == "UNKNOWN_VULNERABILITY")
    assert "not_known_vulnerable_not_equal_secure" in unknown["required_assertions"]
    return {"status":"PASS","test_count":len(tests),"classes":sorted(classes),"entities":sorted(entities),"authority_effect":"NONE"}


def main() -> int:
    payload = json.loads(CATALOG.read_text(encoding="utf-8"))
    print(json.dumps(validate(payload), sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
