#!/usr/bin/env python3
"""Build the canonical StegVerse runtime-profile discovery projection.

The projection describes declared runtime/capability surfaces and explicit observations.
It never grants execution, admission, claim/fence, credential, deployment, or transition authority.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_CATALOG = Path("control/runtime-profile-sources.json")
OUTPUT = Path("control/runtime-profile-map.json")
DEFAULT_FRESHNESS_SECONDS = 900


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"object required: {path}")
    return value


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError("FAIL_CLOSED: " + reason)


def base_authority() -> dict[str, Any]:
    return {
        "availability_grants_authority": False,
        "match_grants_authority": False,
        "claim_fence_authority": "WORKERCOORDINATOR",
        "credential_authority": "TV/TVC",
        "hb_grants_authority": False,
    }


def carrier_substrate(contract: dict[str, Any]) -> dict[str, Any]:
    hb = contract.get("heartbeat", {})
    wr = contract.get("worker_runtime", {})
    intr = contract.get("intr_carrier", {})
    return {
        "hb_protocol": hb.get("protocol_anchor"),
        "oscillator": {
            "mechanism": hb.get("mechanism"),
            "reference_frequency_hz": hb.get("reference_frequency_hz"),
            "reference_increment_interval_ms": hb.get("reference_increment_interval_ms"),
            "progression_dependency": hb.get("progression_dependency"),
            "grants_authority": False,
        },
        "worker_runtime": {
            "class": wr.get("class"),
            "implementation_ref": wr.get("implementation_ref"),
            "dispatcher_ref": wr.get("dispatcher_ref"),
            "single_scheduler_required": wr.get("single_scheduler_required"),
        },
        "intr": {
            "profile_ref": intr.get("profile_ref"),
            "exact_byte_runtime_ref": intr.get("exact_byte_runtime_ref"),
            "authority_effect": intr.get("authority_effect"),
        },
        "runtime_root": "SYMBOLIC_RESIDENT_RUNTIME_ROOT",
    }


def declared_only_observation() -> dict[str, Any]:
    return {"state": "DECLARED_ONLY", "freshness_state": "UNKNOWN", "observed_at": None, "predicate_map": {}, "evidence_refs": []}


def resident_profile(contract: dict[str, Any]) -> dict[str, Any]:
    capabilities = [
        "hb_reference",
        "independent_phase_oscillator_reference",
        "intr_carrier_reference",
        "workercoordinator_runtime",
        "resident_request_dispatch",
    ]
    return {
        "profile_id": "canonical-resident-substrate-v1",
        "profile_class": "RESIDENT_SUBSTRATE",
        "component": "Canonical Resident Runtime",
        "repository": "StegVerse-Labs/.github",
        "declared": {
            "capabilities": capabilities,
            "effect_class": "resident_runtime_substrate",
            "mutation_allowed": False,
            "deployment_allowed": False,
            "environment_classes": ["SOVEREIGN_RESIDENT"],
            "directions": ["INTERNAL"],
        },
        "substrate": carrier_substrate(contract),
        "required_predicates": ["resident_process_alive_supervised"],
        "observed": declared_only_observation(),
        "task_selectors": [c.get("selector") for c in contract.get("consumers", []) if c.get("selector")],
        "authority": base_authority(),
        "provenance": {"source_refs": ["control/canonical-resident-carrier-contract.json"], "projection_method": "CANONICAL_JSON"},
    }


def worker_profiles(data: dict[str, Any], substrate: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for p in data.get("profiles", []):
        rows.append({
            "profile_id": str(p.get("profile_id")),
            "profile_class": "WORKER_CAPABILITY",
            "component": str(p.get("executor_type") or p.get("profile_id")),
            "repository": "StegVerse-Labs/.github",
            "declared": {
                "capabilities": sorted(set(p.get("allowed_capabilities", []))),
                "effect_class": p.get("effect_class"),
                "mutation_allowed": bool(p.get("mutation_allowed", False)),
                "deployment_allowed": bool(p.get("deployment_allowed", False)),
                "environment_classes": [],
                "directions": ["INTERNAL"],
            },
            "substrate": substrate,
            "required_predicates": [],
            "observed": declared_only_observation(),
            "task_selectors": [],
            "authority": base_authority(),
            "provenance": {"source_refs": ["control/worker-capability-profiles.json"], "projection_method": "WORKER_CAPABILITY_JSON"},
        })
    return rows


def intr_profiles(source: str, substrate: dict[str, Any]) -> list[dict[str, Any]]:
    m = re.search(r'"profiles"\s*:\s*\[([^\]]+)\]', source)
    names = re.findall(r'"([^"]+)"', m.group(1)) if m else []
    return [{
        "profile_id": "universal-intr-profiled-ingress-v1",
        "profile_class": "INGRESS_EGRESS",
        "component": "Universal InTr Profiled Ingress",
        "repository": "StegVerse-Labs/.github",
        "declared": {
            "capabilities": ["intr_ingress", "event_triggered_materialization"] + ["intr_profile:" + n for n in names],
            "effect_class": "ingress_materialization",
            "mutation_allowed": True,
            "deployment_allowed": False,
            "environment_classes": ["SOVEREIGN_RESIDENT"],
            "directions": ["INGRESS"],
        },
        "substrate": substrate,
        "required_predicates": ["shared_intr_listener_available"],
        "observed": declared_only_observation(),
        "task_selectors": [],
        "authority": base_authority(),
        "provenance": {"source_refs": ["workers/universal_intr_profiled_ingress.py"], "projection_method": "STATIC_PROFILE_DECLARATION"},
    }]


def coordination_profile(data: dict[str, Any], substrate: dict[str, Any]) -> dict[str, Any]:
    return {
        "profile_id": "canonical-work-coordination-runtime-v1",
        "profile_class": "COORDINATION_RUNTIME",
        "component": "Canonical Work Coordination",
        "repository": "StegVerse-Labs/.github",
        "declared": {
            "capabilities": ["task_registry_reconciliation", "master_records_reconciliation", "worker_claim_projection", "dependency_reevaluation", "intr_task_admission", "runtime_profile_discovery"],
            "effect_class": "coordination_runtime",
            "mutation_allowed": True,
            "deployment_allowed": False,
            "environment_classes": ["SOVEREIGN_RESIDENT"],
            "directions": ["INGRESS", "INTERNAL", "EGRESS"],
        },
        "substrate": substrate,
        "required_predicates": ["authentic_intr_ingress", "master_records_projection_available", "workercoordinator_state_available"],
        "observed": declared_only_observation(),
        "task_selectors": ["canonical_work_coordination"],
        "authority": base_authority(),
        "provenance": {"source_refs": ["control/canonical-work-runtime-profile.json"], "projection_method": "CANONICAL_WORK_JSON"},
    }


def parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def freshness(observed_at: Any, now: datetime, max_age_seconds: int) -> str:
    stamp = parse_time(observed_at)
    if stamp is None:
        return "UNKNOWN"
    age = (now - stamp).total_seconds()
    if age < -60:
        return "CONFLICT"
    return "CURRENT" if age <= max_age_seconds else "STALE"


def observability_profiles(directory: Path, substrate: dict[str, Any], now: datetime, max_age_seconds: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not directory.is_dir():
        return rows
    for path in sorted(directory.glob("*.json")):
        try:
            data = load(path)
        except Exception:
            continue
        profile_id = str(data.get("consumer_id") or data.get("profile_id") or path.stem)
        predicate_map = data.get("predicate_map") if isinstance(data.get("predicate_map"), dict) else {}
        observed_at = data.get("runtime_observed_at") or data.get("observed_at") or data.get("observed_repository_state_at")
        evidence = []
        for key in ("consumer_state_ref", "consumer_handoff", "runtime_receipt_ref", "evidence_ref"):
            if isinstance(data.get(key), str) and data.get(key):
                evidence.append(data[key])
        has_observation = bool(predicate_map or observed_at or evidence)
        fresh = freshness(observed_at, now, max_age_seconds) if has_observation else "UNKNOWN"
        state = "DECLARED_ONLY"
        if has_observation:
            state = "STALE" if fresh == "STALE" else ("CONFLICT" if fresh == "CONFLICT" else "OBSERVED")
        rows.append({
            "profile_id": "observability:" + profile_id,
            "profile_class": "OBSERVABILITY_CONSUMER",
            "component": str(data.get("consumer_id") or data.get("consumer_repository") or path.stem),
            "repository": str(data.get("consumer_repository") or "StegVerse-Labs/.github"),
            "declared": {
                "capabilities": ["runtime_observation", "predicate_projection"],
                "effect_class": "runtime_observability",
                "mutation_allowed": False,
                "deployment_allowed": False,
                "environment_classes": [],
                "directions": ["OBSERVATION"],
            },
            "substrate": substrate,
            "required_predicates": [],
            "observed": {
                "state": state,
                "freshness_state": fresh,
                "observed_at": observed_at,
                "predicate_map": predicate_map,
                "evidence_refs": sorted(set(evidence)),
            },
            "task_selectors": [],
            "authority": base_authority(),
            "provenance": {"source_refs": [path.relative_to(ROOT).as_posix()], "projection_method": "OBSERVABILITY_CONSUMER_JSON"},
        })
    return rows


def next_generation(root: Path) -> int:
    path = root / OUTPUT
    if not path.is_file():
        return 1
    try:
        current = load(path)
        value = int(current.get("generation", 0))
        return max(1, value + 1)
    except Exception:
        return 1


def build(root: Path, *, now: datetime | None = None, freshness_seconds: int = DEFAULT_FRESHNESS_SECONDS) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    catalog = load(root / SOURCE_CATALOG)
    required_refs = [s["ref"] for s in catalog.get("sources", []) if s.get("required")]
    for ref in required_refs:
        path = root / ref
        require(path.exists(), "required runtime-profile source missing: " + ref)

    contract = load(root / "control/canonical-resident-carrier-contract.json")
    substrate = carrier_substrate(contract)
    profiles = [resident_profile(contract)]
    profiles.extend(worker_profiles(load(root / "control/worker-capability-profiles.json"), substrate))
    profiles.extend(intr_profiles((root / "workers/universal_intr_profiled_ingress.py").read_text(encoding="utf-8"), substrate))
    profiles.append(coordination_profile(load(root / "control/canonical-work-runtime-profile.json"), substrate))
    profiles.extend(observability_profiles(root / "control/runtime-observability-consumers", substrate, now, freshness_seconds))

    ids = [p["profile_id"] for p in profiles]
    require(len(ids) == len(set(ids)), "duplicate runtime profile identity")
    return {
        "schema": "stegverse.runtime-profile-map/v1",
        "generation": next_generation(root),
        "status": "GENERATED_PROJECTION_NON_AUTHORIZING",
        "generated_at": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "freshness_policy": {"observation_max_age_seconds": freshness_seconds, "stale_is_unavailable": False, "unknown_is_false": False},
        "authority": {
            "map_grants_execution_authority": False,
            "capability_match_grants_authority": False,
            "worker_claim_authority": "WORKERCOORDINATOR",
            "credential_authority": "TV/TVC",
            "ingress_egress_authority": "INTERLOCK_INTR",
            "observed_reality_authority": "MASTER_RECORDS",
        },
        "profiles": profiles,
        "nonclaims": [
            "PROFILE_DECLARATION_DOES_NOT_PROVE_RUNTIME_EXECUTION",
            "RUNTIME_OBSERVATION_DOES_NOT_GRANT_EXECUTION_AUTHORITY",
            "STALE_OBSERVATION_IS_NOT_CURRENT_RUNTIME_PROOF",
            "UNKNOWN_OBSERVATION_IS_NOT_NEGATIVE_PROOF",
            "CAPABILITY_MATCH_DOES_NOT_GRANT_TASK_ADMISSION",
            "HB32_OSCILLATOR_REFERENCE_DOES_NOT_GRANT_AUTHORITY",
            "MAP_DOES_NOT_MINT_WORKERCOORDINATOR_CLAIM_OR_FENCE",
            "MAP_DOES_NOT_GRANT_CREDENTIAL_OR_DEPLOYMENT_AUTHORITY",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--freshness-seconds", type=int, default=DEFAULT_FRESHNESS_SECONDS)
    args = parser.parse_args()
    require(args.freshness_seconds > 0, "freshness seconds must be positive")
    root = args.root.expanduser().resolve()
    result = build(root, freshness_seconds=args.freshness_seconds)
    output = args.output if args.output.is_absolute() else root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"state": "BUILT", "generation": result["generation"], "profile_count": len(result["profiles"]), "output": str(output), "authority_effect": "NONE_PROJECTION_ONLY"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
