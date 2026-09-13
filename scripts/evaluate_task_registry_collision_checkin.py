#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "data" / "canonical-task-records"
REGISTRY = ROOT / "data" / "canonical-task-registry.json"
GLOBAL_INVARIANTS = ROOT / "data" / "task-registry-global-invariants.json"
CALLER_POLICY = ROOT / "data" / "task-registry-general-checkin-caller-policy.json"
ACTIVEISH = {"ACTIVE", "CHECKED_OUT", "CLAIMED_INTEGRATION", "HANDOFF_READY_RUNTIME_PROOF_PENDING", "BLOCKED_RUNTIME_ACTIVATION"}
PROGRESSION_CONTROLLER_TASK_ID = "ENTITY-AUTONOMOUS-GOVERNED-PROGRESSION-RUNTIME-ADOPTION-001"
sys.path.insert(0, str(ROOT / "scripts"))
from task_registry_checkin_event_history import (
    DEFAULT_LEDGER,
    append_event,
    recent_collision_candidates,
)
from validate_task_registration_substrate_resolution import validate_resolution


def _load_object(path: Path):
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def load_records():
    """Resolve canonical identities from the Task Registry; shards only enrich."""
    registry = _load_object(REGISTRY)
    rows = registry.get("tasks")
    if not isinstance(rows, list):
        raise ValueError("canonical Task Registry tasks must be a list")
    out = {}
    for raw in rows:
        if not isinstance(raw, dict):
            raise ValueError("canonical Task Registry task rows must be objects")
        tid = str(raw.get("task_id") or "").strip()
        if not tid:
            raise ValueError("canonical Task Registry task row missing task_id")
        if tid in out:
            raise ValueError(f"duplicate canonical Task Registry task: {tid}")
        projected = dict(raw)
        shard_path = RECORDS / f"{tid}.json"
        if shard_path.is_file():
            shard = _load_object(shard_path)
            if shard.get("task_id") != tid:
                raise ValueError(f"canonical task shard identity mismatch: {tid}")
            for identity_key in ("correlation_id", "root_correlation_id", "parent_task_id"):
                registry_value = raw.get(identity_key)
                shard_value = shard.get(identity_key)
                if registry_value is not None and shard_value is not None and registry_value != shard_value:
                    raise ValueError(f"canonical task shard {identity_key} mismatch: {tid}")
            for key, value in shard.items():
                projected.setdefault(key, value)
        out[tid] = projected
    return out


def load_global_invariants():
    policy = json.loads(GLOBAL_INVARIANTS.read_text(encoding="utf-8"))
    if policy.get("schema") != "stegverse.task-registry-global-invariants/v1":
        raise SystemExit("task registry global invariant schema mismatch")
    if policy.get("applies_to") != "ALL_CANONICAL_TASKS_EXISTING_AND_NEW":
        raise SystemExit("task registry global invariant scope mismatch")
    return policy


def load_caller_policy():
    policy = json.loads(CALLER_POLICY.read_text(encoding="utf-8"))
    if policy.get("schema") != "stegverse.task-registry-general-checkin-caller-policy/v1":
        raise SystemExit("task registry general check-in caller policy schema mismatch")
    return policy


def resolve_caller_surface(req: dict) -> str:
    policy = load_caller_policy()
    declared = str(req.get("caller_surface") or "").strip().upper()
    admitted = set((policy.get("admitted_production_caller_surfaces") or {}).keys())
    if declared in admitted:
        return declared
    if not declared and os.environ.get("PYTEST_CURRENT_TEST"):
        return str((policy.get("test_harness") or {}).get("surface") or "TEST_HARNESS").strip().upper()
    if declared == str((policy.get("test_harness") or {}).get("surface") or "TEST_HARNESS").strip().upper() and os.environ.get("PYTEST_CURRENT_TEST"):
        return declared
    if not declared:
        raise SystemExit("caller_surface required for general Task Registry check-in")
    raise SystemExit(f"caller_surface not admitted by general check-in policy: {declared}")


def handoff(r):
    refs = r.get("handoff_projection_refs") or r.get("source_refs") or []
    for x in refs:
        if isinstance(x, str) and "HANDOFF" in x.upper():
            return x
    return None


def stable_hash(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def clean_context(req, caller_surface):
    context = req.get("checkin_context") or {}
    if not isinstance(context, dict):
        raise SystemExit("checkin_context must be an object")
    out = {}
    for key in ("session_id", "checked_in_at", "repository", "branch", "pull_request", "source_head", "first_unresolved_predicate"):
        value = context.get(key)
        if value is not None:
            if not isinstance(value, (str, int)):
                raise SystemExit(f"checkin_context.{key} must be scalar")
            out[key] = value
    for key in ("repositories_under_mutation", "components_under_mutation"):
        value = context.get(key)
        if value is not None:
            if not isinstance(value, list) or not all(isinstance(x, str) and x.strip() for x in value):
                raise SystemExit(f"checkin_context.{key} must be a string array")
            out[key] = sorted(set(x.strip() for x in value))
    out["caller_surface"] = caller_surface
    out["caller_surface_attestation_proven"] = False
    return out


def selected_substrate(record):
    resolution = record.get("execution_substrate_resolution")
    if not isinstance(resolution, dict):
        return None
    selected = resolution.get("selected_substrate_id")
    return str(selected).strip() if isinstance(selected, str) and selected.strip() else None


def overlap(a, b, request_context=None):
    at, bt = a.get("targets") or {}, b.get("targets") or {}
    a_repos = set(at.get("repositories") or [])
    a_comps = set(at.get("components") or [])
    if request_context:
        a_repos.update(request_context.get("repositories_under_mutation") or [])
        a_comps.update(request_context.get("components_under_mutation") or [])
        if request_context.get("repository"):
            a_repos.add(str(request_context["repository"]))
    repos = sorted(a_repos & set(bt.get("repositories") or []))
    comps = sorted(a_comps & set(bt.get("components") or []))
    lineage = bool({a.get("task_id"), a.get("parent_task_id"), a.get("root_correlation_id")} & {b.get("task_id"), b.get("parent_task_id"), b.get("root_correlation_id")})
    adjacent = b.get("task_id") in (a.get("adjacent_task_refs") or []) or a.get("task_id") in (b.get("adjacent_task_refs") or [])
    a_substrate = selected_substrate(a)
    b_substrate = selected_substrate(b)
    substrates = [a_substrate] if a_substrate and a_substrate == b_substrate else []
    return repos, comps, lineage, adjacent, substrates


def progression_controller_for_same_goal(candidate, other):
    if other.get("task_id") != PROGRESSION_CONTROLLER_TASK_ID:
        return False
    candidate_root = str(candidate.get("root_correlation_id") or candidate.get("correlation_id") or candidate.get("task_id") or "")
    controller_root = str(other.get("root_correlation_id") or "")
    claim = other.get("worker_claim") or {}
    authority = other.get("authority_model") or {}
    return (
        bool(candidate_root)
        and candidate_root == controller_root
        and claim.get("projection_only") is True
        and authority.get("task_registry_mints_execution_authority") is False
    )


def event_ledger_path() -> Path:
    configured = str(os.environ.get("STEGVERSE_TASK_REGISTRY_EVENT_LEDGER") or "").strip()
    return Path(configured).expanduser().resolve() if configured else DEFAULT_LEDGER


def recent_events_for(tid, task_record, context):
    targets = task_record.get("targets") or {}
    repositories = set(targets.get("repositories") or [])
    components = set(targets.get("components") or [])
    repositories.update(context.get("repositories_under_mutation") or [])
    components.update(context.get("components_under_mutation") or [])
    if context.get("repository"):
        repositories.add(str(context["repository"]))
    checked_in_at = context.get("checked_in_at")
    if isinstance(checked_in_at, str) and checked_in_at.strip():
        now = datetime.fromisoformat(checked_in_at.replace("Z", "+00:00"))
    else:
        now = datetime.now(timezone.utc)
    return recent_collision_candidates(
        event_ledger_path(), now=now, task_id=tid,
        repositories=sorted(repositories), components=sorted(components),
    )


def event_context(context):
    return {
        "repository": context.get("repository"),
        "branch": context.get("branch"),
        "pull_request": context.get("pull_request"),
        "source_head": context.get("source_head"),
        "first_unresolved_predicate": context.get("first_unresolved_predicate"),
        "repositories": context.get("repositories_under_mutation") or [],
        "components": context.get("components_under_mutation") or [],
        "caller_surface": context.get("caller_surface"),
        "caller_surface_attestation_proven": False,
    }


def record_event(envelope, context, event_type):
    session_id = str(context.get("session_id") or "").strip()
    if not session_id:
        return None
    return append_event(event_ledger_path(), {
        "event_type": event_type,
        "task_id": envelope["task_id"],
        "session_id": session_id,
        "event_at": context.get("checked_in_at") or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "context": event_context(context),
        "registry_disposition": envelope,
    })


def emit(payload, request_context):
    envelope = dict(payload)
    envelope["registry_global_invariants"] = load_global_invariants()
    envelope["checkin_context"] = request_context
    envelope["caller_surface"] = request_context.get("caller_surface")
    envelope["caller_surface_attestation_proven"] = False
    envelope["checkin_context_sha256"] = stable_hash(request_context)
    envelope["checkin_disposition_sha256"] = stable_hash({k: v for k, v in envelope.items() if k != "checkin_disposition_sha256"})
    checkin = record_event(envelope, request_context, "CHECK_IN")
    if checkin:
        envelope["checkin_event_sha256"] = checkin["event_sha256"]
    if str(envelope.get("disposition") or "").startswith("STOP_"):
        stopped = record_event(envelope, request_context, "STOPPED")
        if stopped:
            envelope["stopped_event_sha256"] = stopped["event_sha256"]
    print(json.dumps(envelope, sort_keys=True))


def main():
    req = json.load(sys.stdin)
    caller_surface = resolve_caller_surface(req)
    tid = str(req.get("task_id") or "").strip()
    context = clean_context(req, caller_surface)
    records = load_records()
    r = records.get(tid)
    if not r:
        emit({"schema":"stegverse.task-registry-checkin-disposition/v1","task_id":tid,"disposition":"STOP_NOT_REGISTERED","session_action":"END_OR_REGISTER_BEFORE_MUTATION","authority_effect":"NONE"}, context)
        return

    if isinstance(r.get("runtime_requirements"), dict):
        try:
            validate_resolution(r)
        except Exception as exc:
            emit({
                "schema":"stegverse.task-registry-checkin-disposition/v1",
                "task_id":tid,
                "task_handoff":handoff(r),
                "disposition":"STOP_SUBSTRATE_REVIEW_REQUIRED",
                "session_action":"END_AND_RECONCILE_EXECUTION_SUBSTRATE_REVIEW",
                "substrate_review_error":str(exc),
                "authority_effect":"NONE",
            }, context)
            return

    state = str(r.get("coordination_state") or "").upper()
    checkout = str(r.get("checkout_state") or "").upper()
    continuation = r.get("continuation_task_id")
    if state in {"SUPERSEDED","RETIRED","INACTIVE"} or checkout in {"SUPERSEDED","COMPLETED","RETIRED"}:
        emit({"schema":"stegverse.task-registry-checkin-disposition/v1","task_id":tid,"task_handoff":handoff(r),"disposition":"STOP_SUPERSEDED" if continuation else "STOP_INACTIVE","continuation_task_id":continuation,"continuation_handoff":handoff(records.get(continuation,{})) if continuation else None,"session_action":"END_SESSION_AND_CONTINUE_ONLY_AT_RETURNED_TASK" if continuation else "END_SESSION","authority_effect":"NONE"}, context)
        return

    collisions=[]
    controller_exclusions=[]
    for oid, o in records.items():
        if oid == tid:
            continue
        if progression_controller_for_same_goal(r, o):
            controller_exclusions.append(oid)
            continue
        os = str(o.get("coordination_state") or "").upper()
        oc = str(o.get("checkout_state") or "").upper()
        if os not in ACTIVEISH and oc not in ACTIVEISH and oc != "CHECKED_OUT":
            continue
        repos, comps, lineage, adjacent, substrates = overlap(r, o, context)
        if repos or comps or lineage or adjacent or substrates:
            collisions.append({
                "task_id":oid,
                "handoff":handoff(o),
                "coordination_state":os,
                "checkout_state":oc,
                "overlap":{
                    "repositories":repos,
                    "components":comps,
                    "lineage":lineage,
                    "adjacent":adjacent,
                    "execution_substrates":substrates,
                },
                "source":"CANONICAL_TASK_REGISTRY",
            })

    recent = recent_events_for(tid, r, context)
    known = {(c["task_id"], "CANONICAL_TASK_REGISTRY") for c in collisions}
    for row in recent:
        marker = (row["task_id"], "RECENT_EVENT_HISTORY")
        if marker not in known:
            collisions.append(row)
            known.add(marker)

    hard=[c for c in collisions if c.get("source") == "CANONICAL_TASK_REGISTRY" and c.get("checkout_state")=="CHECKED_OUT" and (c["overlap"]["components"] or c["overlap"]["lineage"])]
    disposition = "STOP_COLLISION" if hard else ("COORDINATE_CONVERGENCE" if collisions else "CONTINUE")
    action = "END_SESSION_AND_CONTINUE_IN_RETURNED_COLLISION_OWNER" if hard else ("COORDINATE_BEFORE_MUTATION" if collisions else "CONTINUE_CURRENT_TASK")
    emit({
        "schema":"stegverse.task-registry-checkin-disposition/v1",
        "task_id":tid,
        "task_handoff":handoff(r),
        "selected_execution_substrate":selected_substrate(r),
        "registry_identity_source":"CANONICAL_TASK_REGISTRY",
        "task_record_shards_are_optional_enrichment_only":True,
        "same_goal_progression_controller_collision_excluded":bool(controller_exclusions),
        "excluded_progression_controller_task_ids":controller_exclusions,
        "disposition":disposition,
        "session_action":action,
        "collision_candidates":collisions,
        "hard_collision_task_ids":[c["task_id"] for c in hard],
        "recent_event_window_seconds":1800,
        "authority_effect":"NONE",
    }, context)

if __name__ == "__main__":
    main()
