#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTITY_REGISTRY = ROOT / "control" / "system-ai-entity-registry.json"
HB_REGISTRY = ROOT / "control" / "repo-heartbeat-federation.json"

VALID_STATES = {
    "DECLARED",
    "FEDERATION_REGISTERED",
    "HEARTBEAT_PRESENT",
    "INFERENCE_PROVEN",
    "SYSTEM_AI_ACTIVE",
    "DEGRADED",
    "RETIRED",
}

def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1

def main() -> int:
    registry = load(ENTITY_REGISTRY)
    hb = load(HB_REGISTRY)

    if registry.get("schema") != "stegverse.system-ai-entity-registry/v0.1":
        return fail("invalid system AI entity registry schema")
    if hb.get("schema") != "stegverse.repo-heartbeat-federation/v0.1":
        return fail("invalid repo heartbeat federation schema")

    participants = {
        row["repository"]: row
        for row in hb.get("required_participants", [])
        if isinstance(row, dict) and isinstance(row.get("repository"), str)
    }

    entities = registry.get("entities")
    if not isinstance(entities, list) or not entities:
        return fail("system AI entity registry is empty")

    seen: set[str] = set()
    for entity in entities:
        entity_id = entity.get("entity_id")
        if not isinstance(entity_id, str) or not entity_id:
            return fail("entity_id missing")
        if entity_id in seen:
            return fail(f"duplicate entity_id: {entity_id}")
        seen.add(entity_id)

        if entity.get("schema") != "stegverse.system-ai-entity/v0.1":
            return fail(f"{entity_id}: invalid entity schema")
        if entity.get("entity_class") != "SOVEREIGN_AI_RUNTIME_ENTITY":
            return fail(f"{entity_id}: invalid entity class")
        state = entity.get("lifecycle_state")
        if state not in VALID_STATES:
            return fail(f"{entity_id}: invalid lifecycle state")

        runtime_repo = entity.get("runtime_repository")
        participant = participants.get(runtime_repo)
        activation = entity.get("activation") or {}
        heartbeat = entity.get("heartbeat") or {}
        authority = entity.get("authority") or {}

        if activation.get("federation_membership_established") is True:
            if participant is None:
                return fail(f"{entity_id}: federation membership claimed but runtime is absent")
            if participant.get("participant_class") != "RUNTIME" or participant.get("required") is not True:
                return fail(f"{entity_id}: system AI runtime must be a required RUNTIME participant")
            if heartbeat.get("participant_class") != "RUNTIME" or heartbeat.get("required_participant") is not True:
                return fail(f"{entity_id}: heartbeat binding disagrees with federation registry")

        if heartbeat.get("grants_execution_authority") is not False:
            return fail(f"{entity_id}: heartbeat may not grant execution authority")
        if authority.get("credential_authority") != "TV/TVC":
            return fail(f"{entity_id}: credential authority must remain TV/TVC")
        if authority.get("policy_authority") != "StegVerse-Labs/TV":
            return fail(f"{entity_id}: policy authority mismatch")
        if authority.get("route_authority") != "StegVerse-Labs/TVC":
            return fail(f"{entity_id}: route authority mismatch")
        if authority.get("model_output_authority") != "NONE":
            return fail(f"{entity_id}: model output may not grant authority")
        if authority.get("heartbeat_authority_effect") != "NONE":
            return fail(f"{entity_id}: heartbeat authority effect must be NONE")
        if authority.get("github_token_runtime_authority") != "NONE":
            return fail(f"{entity_id}: GitHub token runtime authority prohibited")

        if state == "HEARTBEAT_PRESENT" and activation.get("heartbeat_presence_proven") is not True:
            return fail(f"{entity_id}: HEARTBEAT_PRESENT requires heartbeat proof")
        if state == "INFERENCE_PROVEN":
            if activation.get("heartbeat_presence_proven") is not True or activation.get("governed_inference_proven") is not True:
                return fail(f"{entity_id}: INFERENCE_PROVEN requires heartbeat and governed inference proof")
        if state == "SYSTEM_AI_ACTIVE":
            required = (
                "federation_membership_established",
                "heartbeat_presence_proven",
                "governed_inference_proven",
                "same_execution_reconstruction_proven",
                "active",
            )
            missing = [key for key in required if activation.get(key) is not True]
            if missing:
                return fail(f"{entity_id}: SYSTEM_AI_ACTIVE missing {','.join(missing)}")
        elif activation.get("active") is True:
            return fail(f"{entity_id}: active=true is reserved for SYSTEM_AI_ACTIVE")

    print(f"PASS: {len(entities)} system AI entity record(s) valid")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
