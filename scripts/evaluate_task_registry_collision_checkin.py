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
    load_events,
    parse_time,
)
from validate_task_registration_substrate_resolution import validate_resolution


def _load_object(path: Path):
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def load_registry():
    registry = _load_object(REGISTRY)
    generation = registry.get("generation")
    if not isinstance(generation, int) or generation < 0:
        raise ValueError("canonical Task Registry generation must be a non-negative integer")
    return registry


def load_records():
    """Resolve canonical identities from the Task Registry; shards only enrich."""
    registry = load_registry()
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


def load_missing_checked_out_shards(registered: dict) -> dict:
    """Guard collision evaluation against checked-out shards omitted from aggregate.

    An omitted shard is NEVER admitted as a task, minted a COSV, or silently
    inserted into the canonical Registry. It is collision evidence only.
    The canonical Registry producer must separately reconcile valid identities.
    """
    missing = {}
    for path in sorted(RECORDS.glob("*.json")):
        shard = _load_object(path)
        # Auxiliary session notes live alongside canonical shards; they lack a
        # canonical task identity and must not impersonate a checked-out owner.
        if ("task_id" not in shard and shard.get("schema") != "stegverse.canonical-task-record/v1"
                and "checkout_state" not in shard):
            continue
        tid = shard.get("task_id")
        if not isinstance(tid, str) or tid != path.stem:
            raise ValueError(f"canonical task shard path identity mismatch: {path.name}")
        if tid in registered:
            canonical = registered[tid]
            for key in ("correlation_id", "root_correlation_id", "parent_task_id"):
                left, right = canonical.get(key), shard.get(key)
                if left is not None and right is not None and left != right:
                    raise ValueError(f"canonical task shard {key} mismatch: {tid}")
            continue
        if (str(shard.get("coordination_state") or "").upper() in ACTIVEISH
                and str(shard.get("checkout_state") or "").upper() == "CHECKED_OUT"):
            missing[tid] = shard
    return missing


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


def resolve_observed_registry_generation(req: dict, caller_surface: str, current_generation: int) -> int | None:
    raw = req.get("observed_registry_generation")
    if raw is None:
        if caller_surface == "TEST_HARNESS" and os.environ.get("PYTEST_CURRENT_TEST"):
            return current_generation
        return None
    if isinstance(raw, bool):
        raise SystemExit("observed_registry_generation must be an integer")
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise SystemExit("observed_registry_generation must be an integer")
    if value < 0:
        raise SystemExit("observed_registry_generation must be non-negative")
    return value


def generation_fence_payload(observed_generation: int | None, current_generation: int) -> dict:
    return {
        "observed_registry_generation": observed_generation,
        "current_registry_generation": current_generation,
        "coordination_generation_current": observed_generation == current_generation,
        "write_pr_merge_handoff_claim_admissible": observed_generation == current_generation,
        "stale_session_prohibited_mutations": [
            "SOURCE_WRITE",
            "PULL_REQUEST_CREATE_OR_UPDATE",
            "PULL_REQUEST_MERGE",
            "NEW_HANDOFF_CLAIM",
        ],
        "reconciliation_required_before_mutation": observed_generation != current_generation,
    }


def _clean_user_action_surface(row, expected_owner_task_id=None):
    if not isinstance(row, dict):
        raise SystemExit("user action surface must be an object")
    required = ("surface_id", "url_route", "device_browser_context_class", "runtime_surface", "action_type", "owner_task_id", "sharing")
    out = {}
    for key in required:
        value = row.get(key)
        if not isinstance(value, str) or not value.strip():
            raise SystemExit(f"user action surface {key} must be a non-empty string")
        out[key] = value.strip()
    request_id = row.get("request_id")
    if request_id is not None:
        if not isinstance(request_id, str) or not request_id.strip():
            raise SystemExit("user action surface request_id must be null or non-empty string")
        request_id = request_id.strip()
    out["request_id"] = request_id
    out["sharing"] = out["sharing"].upper()
    if out["sharing"] not in {"SHAREABLE", "EXCLUSIVE"}:
        raise SystemExit("user action surface sharing must be SHAREABLE or EXCLUSIVE")
    if expected_owner_task_id and out["owner_task_id"] != expected_owner_task_id:
        raise SystemExit("user action surface owner_task_id must equal task_id")
    return out


def _surface_identity(row):
    return (
        row["url_route"],
        row["device_browser_context_class"],
        row["runtime_surface"],
        row["action_type"],
    )


def canonical_user_action_surfaces(record):
    task_id = str(record.get("task_id") or "").strip()
    rows = record.get("user_action_surfaces") or []
    if not isinstance(rows, list):
        raise SystemExit("canonical user_action_surfaces must be an array")
    return [_clean_user_action_surface(row, task_id) for row in rows]


def user_action_surface_overlap(a, b, request_context=None):
    a_rows = canonical_user_action_surfaces(a)
    if request_context:
        a_rows.extend(request_context.get("user_action_surfaces_under_mutation") or [])
    b_rows = canonical_user_action_surfaces(b)
    conflicts, shareable = [], []
    for left in a_rows:
        for right in b_rows:
            if _surface_identity(left) != _surface_identity(right):
                continue
            row = {
                "identity": {
                    "url_route": left["url_route"],
                    "device_browser_context_class": left["device_browser_context_class"],
                    "runtime_surface": left["runtime_surface"],
                    "action_type": left["action_type"],
                },
                "left_surface_id": left["surface_id"],
                "right_surface_id": right["surface_id"],
                "left_owner_task_id": left["owner_task_id"],
                "right_owner_task_id": right["owner_task_id"],
                "left_request_id": left.get("request_id"),
                "right_request_id": right.get("request_id"),
                "left_sharing": left["sharing"],
                "right_sharing": right["sharing"],
            }
            if "EXCLUSIVE" in {left["sharing"], right["sharing"]}:
                row["compatibility"] = "INCOMPATIBLE_EXCLUSIVE"
                conflicts.append(row)
            else:
                row["compatibility"] = "SHAREABLE"
                shareable.append(row)
    return conflicts, shareable


def clean_context(req, caller_surface, task_id):
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
    surfaces = context.get("user_action_surfaces_under_mutation")
    if surfaces is not None:
        if not isinstance(surfaces, list):
            raise SystemExit("checkin_context.user_action_surfaces_under_mutation must be an array")
        out["user_action_surfaces_under_mutation"] = [_clean_user_action_surface(row, task_id) for row in surfaces]
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
    # Missing parent/root identity is not shared lineage. In particular, two
    # independent root tasks both have parent_task_id=None; counting None as a
    # common ancestor spuriously STOP_COLLISIONs unrelated checked-out goals.
    a_lineage = {v.strip() for v in (a.get("task_id"), a.get("parent_task_id"), a.get("root_correlation_id")) if isinstance(v, str) and v.strip()}
    b_lineage = {v.strip() for v in (b.get("task_id"), b.get("parent_task_id"), b.get("root_correlation_id")) if isinstance(v, str) and v.strip()}
    lineage = bool(a_lineage & b_lineage)
    adjacent = b.get("task_id") in (a.get("adjacent_task_refs") or []) or a.get("task_id") in (b.get("adjacent_task_refs") or [])
    a_substrate = selected_substrate(a)
    b_substrate = selected_substrate(b)
    substrates = [a_substrate] if a_substrate and a_substrate == b_substrate else []
    action_conflicts, action_shareable = user_action_surface_overlap(a, b, request_context)
    return repos, comps, lineage, adjacent, substrates, action_conflicts, action_shareable


def repository_only_overlap_is_component_distinguished(a, b, repos, comps, lineage, adjacent, substrates):
    """Treat shared repository ownership as nonblocking only when component scope proves separation.

    Repository identity is intentionally conservative when component scope is absent. A
    repository-only overlap may be distinguished only when both canonical tasks declare
    non-empty component sets, those sets do not intersect, and there is no stronger
    lineage/adjacency/shared-substrate signal. The overlap remains visible in the
    disposition as nonblocking coordination evidence.
    """
    a_components = set((a.get("targets") or {}).get("components") or [])
    b_components = set((b.get("targets") or {}).get("components") or [])
    return bool(
        repos
        and not comps
        and not lineage
        and not adjacent
        and not substrates
        and a_components
        and b_components
        and not (a_components & b_components)
    )


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



def project_session_status(envelope: dict, context: dict) -> dict:
    """Project session-level collision evidence; never replace a registry disposition.

    The existing ledger proves a retained hash chain, NOT authenticated chat
    origin. Unknown/unavailable origin cannot become DUPLICATE: CONFIRMED.
    """
    task_id = str(envelope.get("task_id") or "")
    session_id = str(context.get("session_id") or "")
    hard_ids = list(envelope.get("hard_collision_task_ids") or [])
    candidates = envelope.get("collision_candidates") or []
    result = {
        "schema": "stegverse.task-registry-session-status-projection/v1",
        "task_lifecycle_state": None,
        "duplicate": "UNVERIFIED",
        "collision": "CONJOIN_REQUIRED" if hard_ids else "UNVERIFIED",
        "colliding_task_ids": hard_ids,
        "same_task_active_session_candidates": [],
        "evidence_class": "REGISTRY_CHECKIN_PROJECTION_NOT_SESSION_ORIGIN_ATTESTATION",
        "source_disposition": envelope.get("disposition"),
        "authority_effect": "NONE",
    }
    # Distinguish a known cross-task, exclusive mutation from mere repo overlap.
    if hard_ids:
        result["collision_reason"] = "EXISTING_REGISTRY_HARD_COLLISION"
    elif envelope.get("disposition") == "COORDINATE_CONVERGENCE":
        result["collision"] = "REVIEW_REQUIRED"
        result["collision_reason"] = "OVERLAP_NOT_YET_PROVEN_EXCLUSIVE"
    elif envelope.get("disposition") == "CONTINUE":
        result["collision"] = "NO_REGISTERED_COLLISION_OBSERVED"
        result["collision_reason"] = "EXTERNAL_SESSION_CENSUS_NOT_ATTESTED"

    # A shared task ID in two independently retained active check-ins is an
    # observed duplicate candidate. The current source does not attest origin.
    if session_id:
        ledger = event_ledger_path()
        events = load_events(ledger)
        latest = {}
        for event in events:
            latest[(event["task_id"], event["session_id"])] = event
        clock = context.get("checked_in_at")
        now = parse_time(clock) if isinstance(clock, str) and clock.strip() else datetime.now(timezone.utc)
        cutoff = now.timestamp() - 1800
        own_comps = set(context.get("components_under_mutation") or [])
        own_repos = set(context.get("repositories_under_mutation") or [])
        for (other_task, other_session), event in latest.items():
            if other_task != task_id or other_session == session_id or event.get("event_type") != "CHECK_IN":
                continue
            if parse_time(event["event_at"]).timestamp() < cutoff:
                continue
            other_context = event.get("context") or {}
            same_component = sorted(own_comps & set(other_context.get("components") or []))
            same_repository = sorted(own_repos & set(other_context.get("repositories") or []))
            same_branch = bool(context.get("branch") and context.get("branch") == other_context.get("branch"))
            same_pr = bool(context.get("pull_request") and str(context.get("pull_request")) == str(other_context.get("pull_request")))
            if same_component or same_branch or same_pr:
                result["same_task_active_session_candidates"].append({
                    "task_id": task_id, "session_id": other_session,
                    "event_sha256": event["event_sha256"],
                    "matching_components": same_component,
                    "matching_repositories": same_repository,
                    "same_branch": same_branch, "same_pull_request": same_pr,
                    "session_origin_attested": False,
                })
        if result["same_task_active_session_candidates"]:
            result["collision"] = "CONJOIN_REQUIRED"
            result["collision_reason"] = "SAME_TASK_ACTIVE_CHECKIN_OVERLAP_UNATTESTED"
            result["evidence_class"] = "HASH_CHAIN_VALIDATED_SESSION_ORIGIN_UNVERIFIED"
    return result

def emit(payload, request_context):
    envelope = dict(payload)
    envelope["session_status_projection"] = project_session_status(envelope, request_context)
    envelope["registry_global_invariants"] = load_global_invariants()
    envelope["checkin_context"] = request_context
    envelope["caller_surface"] = request_context.get("caller_surface")
    envelope["caller_surface_attestation_proven"] = False
    envelope["checkin_context_sha256"] = stable_hash(request_context)
    envelope["checkin_disposition_sha256"] = stable_hash({k: v for k, v in envelope.items() if k != "checkin_disposition_sha256"})
    checkin = record_event(envelope, request_context, "CHECK_IN")
    if checkin:
        envelope["checkin_event_sha256"] = checkin["event_sha256"]
        envelope["checkin_event_predecessor_sha256"] = checkin["predecessor_event_sha256"]
    if str(envelope.get("disposition") or "").startswith("STOP_"):
        stopped = record_event(envelope, request_context, "STOPPED")
        if stopped:
            envelope["stopped_event_sha256"] = stopped["event_sha256"]
            envelope["stopped_event_predecessor_sha256"] = stopped["predecessor_event_sha256"]
    print(json.dumps(envelope, sort_keys=True))


def main():
    req = json.load(sys.stdin)
    caller_surface = resolve_caller_surface(req)
    tid = str(req.get("task_id") or "").strip()
    context = clean_context(req, caller_surface, tid)
    registry = load_registry()
    current_generation = int(registry["generation"])
    observed_generation = resolve_observed_registry_generation(req, caller_surface, current_generation)
    fence = generation_fence_payload(observed_generation, current_generation)
    if observed_generation is None:
        emit({
            "schema":"stegverse.task-registry-checkin-disposition/v1",
            "task_id":tid,
            "disposition":"STOP_COORDINATION_GENERATION_REQUIRED",
            "session_action":"RECONCILE_CANONICAL_GITHUB_STATE_BEFORE_MUTATION",
            **fence,
            "authority_effect":"NONE",
        }, context)
        return
    if observed_generation != current_generation:
        disposition = "STOP_STALE_COORDINATION" if observed_generation < current_generation else "STOP_COORDINATION_GENERATION_MISMATCH"
        emit({
            "schema":"stegverse.task-registry-checkin-disposition/v1",
            "task_id":tid,
            "disposition":disposition,
            "session_action":"RECONCILE_CANONICAL_GITHUB_STATE_BEFORE_MUTATION",
            **fence,
            "authority_effect":"NONE",
        }, context)
        return
    records = load_records()
    missing_checked_out = load_missing_checked_out_shards(records)
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
    repository_only_scope_distinctions=[]
    shareable_user_action_surface_distinctions=[]
    controller_exclusions=[]
    for oid, o in [*records.items(), *missing_checked_out.items()]:
        if oid == tid:
            continue
        if progression_controller_for_same_goal(r, o):
            controller_exclusions.append(oid)
            continue
        os = str(o.get("coordination_state") or "").upper()
        oc = str(o.get("checkout_state") or "").upper()
        if os not in ACTIVEISH and oc not in ACTIVEISH and oc != "CHECKED_OUT":
            continue
        repos, comps, lineage, adjacent, substrates, action_conflicts, action_shareable = overlap(r, o, context)
        if repos or comps or lineage or adjacent or substrates or action_conflicts:
            overlap_row = {
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
                    "user_action_surface_conflicts":action_conflicts,
                },
                "source":"CHECKED_OUT_SHARD_OMITTED_FROM_AGGREGATE" if oid in missing_checked_out else "CANONICAL_TASK_REGISTRY",
            }
            if repository_only_overlap_is_component_distinguished(r, o, repos, comps, lineage, adjacent, substrates):
                overlap_row["scope_disposition"] = "DISTINGUISHED_COMPONENT_SCOPE"
                overlap_row["blocking"] = False
                repository_only_scope_distinctions.append(overlap_row)
            else:
                collisions.append(overlap_row)
        if action_shareable and not (repos or comps or lineage or adjacent or substrates or action_conflicts):
            shareable_user_action_surface_distinctions.append({
                "task_id": oid,
                "handoff": handoff(o),
                "coordination_state": os,
                "checkout_state": oc,
                "overlap": {"user_action_surface_shareable": action_shareable},
                "scope_disposition": "SHAREABLE_USER_ACTION_SURFACE",
                "blocking": False,
                "source": "CANONICAL_TASK_REGISTRY",
            })

    recent = recent_events_for(tid, r, context)
    known = {(c["task_id"], "CANONICAL_TASK_REGISTRY") for c in collisions}
    for row in recent:
        marker = (row["task_id"], "RECENT_EVENT_HISTORY")
        if marker not in known:
            collisions.append(row)
            known.add(marker)

    hard=[c for c in collisions if c.get("source") in {"CANONICAL_TASK_REGISTRY", "CHECKED_OUT_SHARD_OMITTED_FROM_AGGREGATE"} and c.get("checkout_state")=="CHECKED_OUT" and (c["overlap"].get("components") or c["overlap"].get("lineage") or c["overlap"].get("user_action_surface_conflicts"))]
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
        "unregistered_checked_out_shard_ids":sorted(missing_checked_out),
        "unregistered_shards_are_collision_guards_only":True,
        "repository_only_scope_distinctions":repository_only_scope_distinctions,
        "shareable_user_action_surface_distinctions":shareable_user_action_surface_distinctions,
        "repository_only_overlap_policy":"NONBLOCKING_ONLY_WHEN_BOTH_TASKS_DECLARE_NONEMPTY_DISJOINT_COMPONENT_SCOPES_AND_NO_STRONGER_OVERLAP_SIGNAL",
        "hard_collision_task_ids":[c["task_id"] for c in hard],
        "recent_event_window_seconds":1800,
        **fence,
        "authority_effect":"NONE",
    }, context)

if __name__ == "__main__":
    main()
