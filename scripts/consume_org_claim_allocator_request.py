#!/usr/bin/env python3
"""Resident consumption of organization claim-allocator requests.

Every allocation attempt is a manifest-bound state transition with a retained
terminal disposition: ORGANIZATION_WORKER_CLAIM_GRANTED (ALLOW),
ORGANIZATION_WORKER_CLAIM_REFUSED (DENY) or ORGANIZATION_WORKER_CLAIM_FAIL_CLOSED.
Each is appended through the existing repository emitter and organization
aggregation, at ledger roots supplied by the materializer and never derived.

The fence is reconciled from the verified Organization claim-receipt chain, not
from a checkout projection: next = max(chain_max, provenance_floor, runtime
generation) + 1, and a runtime generation behind the issued fences fails closed.
The Organization receipt is appended before the task's active projection and the
runtime claim registry are written, so a projection never exists without it.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Mapping

REQUEST_REL = Path("control/resident-execution-request.d/org-claim-allocator-001.json")
REQUEST_RELS = (
    REQUEST_REL,
    Path("control/resident-execution-request.d/org-claim-allocator-sdk-manifest-001.json"),
)
# Projection only: the write-once records under CONSUMPTION_DIR are the evidence.
RECEIPT_REL = Path("receipts/sovereign-host/org-claim-allocator-request-consumption.latest.json")
CONSUMPTION_DIR = Path("receipts/sovereign-host/org-claim-allocator-consumptions")
GRANT_DIR = Path("receipts/sovereign-host/org-claim-allocator-grants")
ALLOCATOR_REL = Path("scripts/allocate_claims.py")
PROVENANCE_FLOOR_REL = Path("tasks/TASK-2026-0012.json")
PROVENANCE_FLOOR_POINTER = "predecessor_provenance.allocator_fence"
GRANTED = "ORGANIZATION_WORKER_CLAIM_GRANTED"
REFUSED = "ORGANIZATION_WORKER_CLAIM_REFUSED"
FAIL_CLOSED = "ORGANIZATION_WORKER_CLAIM_FAIL_CLOSED"
DISPOSITION = {GRANTED: "ALLOW", REFUSED: "DENY", FAIL_CLOSED: "FAIL_CLOSED"}
RETRY_ENTRYPOINT = "scripts/consume_org_claim_allocator_request.py::consume"
TASK_ID = "SHWP-ORG-CLAIM-ALLOCATOR-001"
MODE = "CANONICAL_ORGANIZATION_CLAIM_ALLOCATION"
HOSTED_ENV = (
    "GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "VERCEL_ENV",
    "CF_PAGES", "CLOUDFLARE_WORKERS",
)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def validate_request(request: dict[str, Any]) -> None:
    required = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": TASK_ID,
        "mode": MODE,
        "entrypoint": "scripts/consume_org_claim_allocator_request.py",
        "canonical_allocator": "scripts/allocate_claims.py",
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, expected in required.items():
        if request.get(key) != expected:
            raise RuntimeError(f"organization allocator request {key} mismatch")
    if request.get("repeat_on_resident_dispatch") is not True:
        raise RuntimeError("organization allocator request must be repeatable on resident dispatch")
    if request.get("github_token_required") is not False:
        raise RuntimeError("organization allocator request may not require GitHub token")
    if request.get("network_source_fetch_allowed") is not False:
        raise RuntimeError("organization allocator request may not allow network source fetch")
    if request.get("second_machine_required") is not False:
        raise RuntimeError("organization allocator request may not require a second machine")
    if request.get("heartbeat_grants_execution_authority") is not False:
        raise RuntimeError("heartbeat may not grant organization allocator authority")
    if request.get("request_grants_claim_authority") is not False:
        raise RuntimeError("resident request may not grant claim authority")
    if request.get("allocator_remains_claim_authority") is not True:
        raise RuntimeError("canonical allocator must remain claim authority")
    target = request.get("target_task_id")
    if target is not None and (not isinstance(target, str) or not target.startswith("TASK-")):
        raise RuntimeError("organization allocator request target_task_id invalid")


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def clean_env(values: Mapping[str, str] | None = None) -> dict[str, str]:
    source = dict(os.environ if values is None else values)
    hosted = [name for name in HOSTED_ENV if truthy(source.get(name))]
    if hosted:
        raise RuntimeError("hosted environment may not execute resident organization allocator: " + ",".join(sorted(hosted)))
    env = {}
    for key in ("PATH", "HOME", "LANG", "LC_ALL"):
        if source.get(key):
            env[key] = source[key]
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env




def validate_source_catalog_floor(source: Path, request: dict[str, Any]) -> dict[str, Any]:
    floor = request.get("source_catalog_floor")
    if not isinstance(floor, dict):
        raise RuntimeError("organization allocator request source catalog floor missing")
    task_id = floor.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        raise RuntimeError("organization allocator source catalog floor task missing")
    task_path = source / "tasks" / f"{task_id}.json"
    if not task_path.is_file():
        raise RuntimeError(f"STALE_SOURCE_CATALOG: required task missing: {task_id}")
    task = load_json(task_path)
    if task.get("task_id") != task_id:
        raise RuntimeError("STALE_SOURCE_CATALOG: task identity mismatch")
    if task.get("requested_at") != floor.get("requested_at"):
        raise RuntimeError("STALE_SOURCE_CATALOG: requested_at floor mismatch")
    mandatory = (task.get("requirements") or {}).get("mandatory") or []
    repository = floor.get("repository_full_name")
    surface = floor.get("required_dependency_surface")
    matched = False
    matched_scope = None
    for requirement in mandatory:
        if not isinstance(requirement, dict):
            continue
        repo = (requirement.get("repository") or {}).get("full_name")
        scope = requirement.get("scope") or {}
        surfaces = (scope.get("dependency_surfaces") or [])
        if repo == repository and surface in surfaces:
            matched = True
            matched_scope = scope
            break
    if not matched or not isinstance(matched_scope, dict):
        raise RuntimeError("STALE_SOURCE_CATALOG: required repository/dependency surface missing")
    observed_scope_sha256 = stable_hash(matched_scope)
    expected_scope_sha256 = floor.get("scope_sha256")
    if not isinstance(expected_scope_sha256, str) or len(expected_scope_sha256) != 64:
        raise RuntimeError("source catalog floor scope digest missing")
    if observed_scope_sha256 != expected_scope_sha256:
        raise RuntimeError(
            "STALE_SOURCE_CATALOG: claim scope digest mismatch "
            + observed_scope_sha256 + " != " + expected_scope_sha256
        )
    if floor.get("purpose") != "MINIMUM_SOURCE_CATALOG_FRESHNESS_ONLY":
        raise RuntimeError("source catalog floor purpose mismatch")
    if floor.get("task_eligibility_effect") != "NONE":
        raise RuntimeError("source catalog floor may not determine task eligibility")
    return {
        "state": "SOURCE_CATALOG_FLOOR_SATISFIED",
        "task_id": task_id,
        "requested_at": task.get("requested_at"),
        "repository_full_name": repository,
        "required_dependency_surface": surface,
        "scope_sha256": observed_scope_sha256,
        "task_status_observed": task.get("status"),
        "task_eligibility_effect": "NONE",
        "network_fetch_performed": False,
        "authority_effect": "NONE_FRESHNESS_ONLY",
    }

def materialize_org_control_inputs(source: Path, runtime: Path) -> dict[str, Any]:
    """Append missing organization task definitions without overwriting runtime task state."""
    source_tasks = source / "tasks"
    runtime_tasks = runtime / "tasks"
    if not source_tasks.is_dir():
        raise RuntimeError("canonical organization task catalog missing")
    runtime_tasks.mkdir(parents=True, exist_ok=True)
    imported: list[str] = []
    preserved: list[str] = []
    superseded_queued: list[str] = []
    supersession_deferred_active: list[str] = []
    source_values: list[dict[str, Any]] = []
    for task_path in sorted(source_tasks.glob("TASK-*.json")):
        value = load_json(task_path)
        if value.get("task_id") != task_path.stem:
            raise RuntimeError(f"organization task identity mismatch: {task_path.name}")
        source_values.append(value)
        destination = runtime_tasks / task_path.name
        if destination.exists():
            preserved.append(task_path.name)
            continue
        destination.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        imported.append(task_path.name)

    for value in source_values:
        supersedes = value.get("supersedes")
        if not isinstance(supersedes, str) or not supersedes:
            continue
        prior_path = runtime_tasks / f"{supersedes}.json"
        if not prior_path.is_file():
            continue
        prior = load_json(prior_path)
        prior_status = prior.get("status")
        if prior_status in {"queued", "proposed"}:
            prior["status"] = "proposed"
            prior["flags"] = sorted(set((prior.get("flags") or []) + ["superseded"]))
            prior_path.write_text(json.dumps(prior, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            superseded_queued.append(supersedes)
        elif prior_status in {"active", "checkin_pending"}:
            supersession_deferred_active.append(supersedes)

    initialized: list[str] = []
    for rel in (Path("control/claims-active.json"), Path("control/queue.json")):
        destination = runtime / rel
        if destination.exists():
            continue
        source_path = source / rel
        if not source_path.is_file():
            raise RuntimeError(f"canonical organization control input missing: {rel}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source_path.read_bytes())
        initialized.append(rel.as_posix())

    return {
        "state": "CONTROL_INPUTS_READY",
        "imported_task_files": imported,
        "preserved_runtime_task_files": preserved,
        "superseded_queued_task_ids": superseded_queued,
        "supersession_deferred_active_task_ids": supersession_deferred_active,
        "initialized_control_files": initialized,
        "runtime_task_state_overwritten": False,
        "network_source_fetch_performed": False,
        "authority_effect": "NONE_LOCAL_MATERIALIZATION_ONLY",
    }


class ClaimFailClosed(Exception):
    """An allocation attempt that cannot reach ALLOW or DENY; no fence is issued."""

    def __init__(self, predicate: str, detail: str, repair: str):
        super().__init__(predicate + ": " + detail)
        self.predicate = predicate
        self.detail = detail
        self.repair = repair


def _load_module(name: str, path: Path):
    if not path.is_file():
        raise ClaimFailClosed("ORGANIZATION_EMITTER_MISSING", str(path), "materialize the canonical ledger emitters")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ledger_custody(source: Path, repo_ledger_root: Path, org_ledger_root: Path) -> dict[str, Any]:
    """The existing emitters, at the ledger roots this execution was supplied."""
    emitter = _load_module("org_claim_repository_ledger", source / ".stegverse/transition-ledger/emit.py")
    organization = _load_module("org_claim_organization_ledger", source / "resident-runtime/aggregate_repo_transition.py")
    return {
        "emitter": emitter,
        "organization_ledger": organization,
        "repository_store": emitter.ledger_store.PosixLedgerStore(Path(repo_ledger_root).expanduser().resolve()),
        "organization_root": Path(org_ledger_root).expanduser().resolve(),
    }


def verify_organization_chain(custody: Mapping[str, Any]) -> dict[str, Any]:
    """Walk the organization chain from HEAD, recomputing every receipt digest.

    A root that is absent, has receipts but no HEAD, or whose chain does not
    recompute is unverified, and an unverified chain cannot issue a fence.
    """
    org = custody["organization_ledger"]
    root = custody["organization_root"]

    def unverified(detail: str) -> ClaimFailClosed:
        return ClaimFailClosed("LEDGER_HEAD_UNVERIFIED", detail,
                               "supply an organization ledger root whose HEAD and chain verify")

    if not root.is_dir():
        raise unverified("organization ledger root absent")
    receipts = root / "receipts"
    head_path = root / "HEAD.json"
    if not head_path.is_file():
        if receipts.is_dir() and any(receipts.glob("*.json")):
            raise unverified("organization receipts present without HEAD")
        return {"head_sha256": None, "receipts": []}
    try:
        head = org.load(head_path)
    except Exception as exc:
        raise unverified("HEAD unreadable: " + type(exc).__name__) from exc
    if head.get("organization") != org.C["organization"]:
        raise unverified("HEAD organization mismatch")
    chain: list[dict[str, Any]] = []
    seen: set[str] = set()
    cursor = head.get("receipt_sha256")
    if not isinstance(cursor, str) or not cursor.startswith("sha256:"):
        raise unverified("HEAD receipt digest invalid")
    while cursor:
        if cursor in seen:
            raise unverified("organization chain cycle")
        seen.add(cursor)
        path = receipts / (cursor.split(":", 1)[1] + ".json")
        if not path.is_file():
            raise unverified("organization chain receipt missing: " + cursor)
        row = org.load(path)
        body = dict(row)
        claimed = body.pop("receipt_sha256", None)
        if claimed != cursor or org.sha(body) != claimed or row.get("organization") != org.C["organization"]:
            raise unverified("organization chain receipt does not recompute: " + cursor)
        chain.append(row)
        cursor = row.get("previous_receipt_sha256")
    chain.reverse()
    return {"head_sha256": head["receipt_sha256"], "receipts": chain}


def chain_grants(chain: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Organization claim grants in chain order, as their receipts carry them."""
    grants = []
    for row in chain["receipts"]:
        evidence = row.get("boundary_evidence") or {}
        if evidence.get("operation") != GRANTED:
            continue
        fence = evidence.get("fencing_token")
        if not isinstance(fence, int) or isinstance(fence, bool) or fence < 1:
            raise ClaimFailClosed("LEDGER_HEAD_UNVERIFIED", "granted receipt fence invalid",
                                  "repair the organization claim receipt chain")
        grants.append(row)
    return grants


def provenance_floor(source: Path) -> dict[str, Any]:
    """The fence already issued outside the chain, read from its provenance record."""
    path = source / PROVENANCE_FLOOR_REL
    try:
        task = load_json(path)
        provenance = task["predecessor_provenance"]
        fence = provenance["allocator_fence"]
    except Exception as exc:
        raise ClaimFailClosed("PROVENANCE_FLOOR_UNVERIFIED", str(PROVENANCE_FLOOR_REL),
                              "materialize " + PROVENANCE_FLOOR_REL.as_posix()) from exc
    if not isinstance(fence, int) or isinstance(fence, bool) or fence < 1:
        raise ClaimFailClosed("PROVENANCE_FLOOR_UNVERIFIED", "allocator_fence invalid",
                              "repair " + PROVENANCE_FLOOR_REL.as_posix())
    return {
        "fence": fence,
        "provenance": PROVENANCE_FLOOR_REL.as_posix() + "#" + PROVENANCE_FLOOR_POINTER,
        "allocator_task": provenance.get("allocator_task"),
        "allocator_generation": provenance.get("allocator_generation"),
        "provenance_record_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def task_cosv(source: Path, task: Mapping[str, Any]) -> str | None:
    ref = task.get("canonical_task_record")
    if ref is None:
        return None
    try:
        return load_json(source / str(ref)).get("cosv_task_vector")
    except Exception as exc:
        raise ClaimFailClosed("CANONICAL_TASK_RECORD_UNRESOLVED", str(ref),
                              "materialize the task's canonical task record") from exc


def write_once(path: Path, value: Mapping[str, Any]) -> Path:
    """Create `path` atomically if absent; the same bytes again is a no-op, different bytes refuse."""
    rendered = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".once-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(rendered)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(name, path)
        except FileExistsError:
            if path.read_bytes() != rendered:
                raise RuntimeError("write_once_collision: " + path.name)
    finally:
        os.unlink(name)
    return path


def write_projection(path: Path, value: Mapping[str, Any], evidence_ref: Path) -> None:
    """Latest-pointer projection for observers. It is not evidence; `evidence_ref` is."""
    path.parent.mkdir(parents=True, exist_ok=True)
    projected = {**value, "projection_only": True, "evidence_role": "PROJECTION_ONLY_NOT_EVIDENCE",
                 "evidence_ref": evidence_ref.as_posix()}
    path.write_text(json.dumps(projected, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@contextmanager
def claim_allocation_lock(root: Path):
    """Serialize verify, fence and append for one organization ledger.

    The aggregation takes the ledger's own append lock inside this one, so the
    fence decided here and the receipt that issues it cannot be interleaved by
    another allocator sharing the ledger.
    """
    with (root / ".claim-allocation.lock").open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


CARRIED = ("disposition", "task_id", "fencing_token", "failed_predicate", "request_sha256",
           "claim_scope_sha256", "organization_head_sha256", "cosv_task_vector")


def record_transition(custody: Mapping[str, Any], transition_class: str, transition_id: str,
                      predecessor: str, evidence: dict[str, Any], *, organization: bool,
                      identity: tuple[str, ...]) -> dict[str, Any]:
    """Append the repository receipt, then the organization receipt consuming it.

    The organization receipt is built from the returned repository receipt, so
    a retry of a recorded transition consumes the same source with the same
    context and the organization ledger returns the receipt it already holds.
    """
    successor = "sha256:" + stable_hash({"transition_id": transition_id, "evidence": evidence})
    repository_receipt = custody["emitter"].append(
        transition_id, transition_class, predecessor, successor, evidence, "NONE",
        store=custody["repository_store"], idempotent_on=identity)
    organization_receipt = None
    if organization:
        recorded = repository_receipt.get("evidence") or {}
        organization_receipt = custody["organization_ledger"].aggregate_transition(
            repository_receipt, org_transition_class="REPO_STATE_PROPAGATION",
            predecessor_org_state_sha256=repository_receipt["predecessor_state_sha256"],
            successor_org_state_sha256=repository_receipt["successor_state_sha256"],
            boundary_evidence={"operation": transition_class, **{key: recorded.get(key) for key in CARRIED}},
            authority_effect="NONE", ledger=custody["organization_root"])
    return {"repository_receipt": repository_receipt, "organization_receipt": organization_receipt}


def run_allocator(runner, runtime: Path, env: Mapping[str, str], *args: str) -> dict[str, Any]:
    completed = runner(
        [sys.executable, str(runtime / ALLOCATOR_REL), *args],
        cwd=runtime, capture_output=True, text=True, check=False, timeout=120, env=dict(env),
    )
    result = parse_last_json(completed.stdout or "")
    if not isinstance(result, dict):
        raise ClaimFailClosed("ALLOCATOR_NO_MACHINE_RESULT", "returncode " + str(completed.returncode),
                              "materialize the canonical allocator")
    if result.get("state") == "ALLOCATOR_BUSY":
        raise ClaimFailClosed("ALLOCATOR_BUSY", "allocator lock held by pid " + str(result.get("allocator_lock_owner_pid")),
                              "retry after the holding allocator exits")
    return result


def runtime_claim_projection(runtime: Path, task_id: str) -> tuple[int, list[dict[str, Any]], str | None]:
    claims_state = load_json(runtime / "control/claims-active.json")
    generation = claims_state.get("generation", 0)
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 0:
        raise ClaimFailClosed("RUNTIME_CLAIM_REGISTRY_INVALID", "generation invalid",
                              "repair the runtime claim registry")
    claims = [c for c in (claims_state.get("claims") or []) if isinstance(c, dict) and c.get("task_id") == task_id]
    task_path = runtime / "tasks" / f"{task_id}.json"
    status = load_json(task_path).get("status") if task_path.is_file() else None
    return generation, claims, status


def retain_claim_grant_evidence(runtime: Path, task_id: str, fence: int,
                                organization_receipt_sha256: str) -> dict[str, Any]:
    """Write-once observation of the projected claim, keyed by task and generation."""
    _generation, granted, _status = runtime_claim_projection(runtime, task_id)
    granted = [c for c in granted if (c.get("lease") or {}).get("fencing_token") == fence]
    if not granted:
        raise RuntimeError("selected task has no retained canonical claim")
    dependency_surfaces = sorted({
        str(value).strip() for claim in granted
        for value in ((claim.get("scope") or {}).get("dependency_surfaces") or []) if str(value).strip()
    })
    snapshot = {"task_id": task_id, "claim_registry_generation": fence, "claims": granted}
    receipt = {
        "schema": "stegverse.org-claim-grant-observation/v1",
        "state": "CLAIM_GRANT_OBSERVED",
        "task_id": task_id,
        "claim_registry_generation": fence,
        "fencing_tokens": [fence],
        "dependency_surfaces": dependency_surfaces,
        "claims": granted,
        "claim_snapshot_sha256": stable_hash(snapshot),
        "organization_receipt_sha256": organization_receipt_sha256,
        "allocator_remains_claim_authority": True,
        "observation_grants_claim_authority": False,
        "heartbeat_grants_claim_authority": False,
        "github_token_required": False,
        "network_source_fetch_performed": False,
        "credential_authority": "TV/TVC",
        "second_machine_required": False,
        "authority_effect": "NONE_OBSERVATION_ONLY",
    }
    generation_rel = GRANT_DIR / f"{task_id}-G{fence}.json"
    latest_rel = GRANT_DIR / f"{task_id}.latest.json"
    write_once(runtime / generation_rel, receipt)
    write_projection(runtime / latest_rel, receipt, generation_rel)
    return {
        "state": "CLAIM_GRANT_EVIDENCE_RETAINED",
        "task_id": task_id,
        "claim_registry_generation": fence,
        "generation_receipt": generation_rel.as_posix(),
        "latest_receipt": latest_rel.as_posix(),
        "latest_receipt_is_projection_only": True,
        "claim_snapshot_sha256": receipt["claim_snapshot_sha256"],
        "authority_effect": "NONE_OBSERVATION_ONLY",
    }


def _ledger_refusal(request: Mapping[str, Any] | None, detail: str) -> dict[str, Any]:
    return {
        "schema": "stegverse.resident-execution-request-consumption/v1",
        "state": "FAIL_CLOSED",
        "request_id": (request or {}).get("request_id"),
        "task_id": TASK_ID,
        "disposition": "FAIL_CLOSED",
        "failed_predicate": "LEDGER_LOCATION_REQUIRED_FROM_MATERIALIZER",
        "detail": detail,
        "required_evidence_or_repair": "supply --repo-ledger-root and --org-ledger-root",
        "retry_entrypoint": RETRY_ENTRYPOINT,
        "runtime_execution_attempted": False,
        "fence_issued": False,
        "consequence_committed": False,
        "authority_effect": "NONE_REFUSAL_ONLY",
    }


def consume_request(source: Path, runtime: Path, request_rel: Path, *, custody: Mapping[str, Any],
                    runner, safe_env: Mapping[str, str]) -> dict[str, Any]:
    request = load_json(runtime / request_rel)
    validate_request(request)
    request_hash = stable_hash(request)
    target = request.get("target_task_id")
    source_catalog_floor = validate_source_catalog_floor(source, request)
    control_inputs = materialize_org_control_inputs(source, runtime)
    if not (runtime / ALLOCATOR_REL).is_file():
        raise RuntimeError("canonical organization allocator not materialized")

    base = {
        "schema": "stegverse.resident-execution-request-consumption/v1",
        "request_id": request.get("request_id"),
        "request_ref": request_rel.as_posix(),
        "request_sha256": request_hash,
        "task_id": TASK_ID,
        "mode": MODE,
        "target_task_id": target,
        "runtime_execution_attempted": True,
        "source_catalog_floor": source_catalog_floor,
        "control_inputs": control_inputs,
        "request_granted_claim_authority": False,
        "allocator_remains_claim_authority": True,
        "heartbeat_grants_execution_authority": False,
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "network_source_fetch_performed": False,
        "credential_authority": "TV/TVC",
        "second_machine_required": False,
        "repeat_on_resident_dispatch": True,
    }

    def retained(transition_id: str, body: dict[str, Any]) -> dict[str, Any]:
        """The write-once record of this transition: the prior one if it exists."""
        rel = CONSUMPTION_DIR / f"{transition_id}.json"
        path = runtime / rel
        if path.is_file():
            prior = load_json(path)
        else:
            write_once(path, body)
            prior = body
        write_projection(runtime / RECEIPT_REL, prior, rel)
        return prior

    def non_allow(transition_class: str, claim_task: str, predicate: str, detail: str, repair: str | None,
                  *, organization: bool, head: str | None) -> dict[str, Any]:
        transition_id = (transition_class.replace("_", "-") + "-"
                         + stable_hash({"task_id": claim_task, "request_sha256": request_hash,
                                        "failed_predicate": predicate})[:16])
        evidence = {
            "disposition": DISPOSITION[transition_class],
            "task_id": claim_task,
            "request_id": request.get("request_id"),
            "request_sha256": request_hash,
            "target_task_id": target,
            "failed_predicate": predicate,
            "detail": detail,
            "organization_head_sha256": head,
            "fencing_token": None,
            "fence_issued": False,
            "required_evidence_or_repair": repair,
            "retry_entrypoint": RETRY_ENTRYPOINT if transition_class == FAIL_CLOSED else None,
            "consequence_committed": False,
        }
        receipts = record_transition(
            custody, transition_class, transition_id, "sha256:" + request_hash, evidence,
            organization=organization, identity=("task_id", "request_sha256", "failed_predicate"))
        organization_receipt = receipts["organization_receipt"]
        body = {
            **base,
            "state": "FAIL_CLOSED" if transition_class == FAIL_CLOSED else "ATTEMPT_RECORDED",
            "transition_class": transition_class,
            "transition_id": transition_id,
            "disposition": DISPOSITION[transition_class],
            "claim_task_id": claim_task,
            "failed_predicate": predicate,
            "detail": detail,
            "required_evidence_or_repair": repair,
            "retry_entrypoint": evidence["retry_entrypoint"],
            "fencing_token": None,
            "fence_issued": False,
            "selected_task_id": None,
            "claim_grant_occurred": False,
            "claim_grant_evidence": None,
            "repository_receipt_sha256": receipts["repository_receipt"]["receipt_sha256"],
            "organization_receipt_sha256": organization_receipt and organization_receipt["receipt_sha256"],
            "organization_receipt_appended": organization_receipt is not None,
            "authority_effect": "NONE_REFUSAL_ONLY",
        }
        return retained(transition_id, body)

    def allow(claim_task: str, grant_row: Mapping[str, Any], receipts: Mapping[str, Any] | None,
              *, replayed: bool) -> dict[str, Any]:
        """Project a recorded grant (committing it only if absent) and retain its record."""
        evidence = grant_row["boundary_evidence"]
        fence = evidence["fencing_token"]
        transition_id = grant_row["source_transition_id"]
        generation, claims, status = runtime_claim_projection(runtime, claim_task)
        projected = any((c.get("lease") or {}).get("fencing_token") == fence for c in claims)
        if not projected and status == "queued":
            if generation >= fence:
                raise ClaimFailClosed("PRIOR_GRANT_PROJECTION_UNRECONCILABLE",
                                      f"runtime generation {generation} already at or beyond granted fence {fence}",
                                      "rematerialize the runtime claim registry from the organization chain")
            commit = run_allocator(runner, runtime, safe_env, "--task", claim_task, "--fencing-token", str(fence))
            if commit.get("selected") != claim_task:
                raise ClaimFailClosed("PROJECTION_COMMIT_REFUSED",
                                      str(commit.get("refusal_predicate") or commit.get("state")),
                                      "retry; the organization grant receipt is retained and is replayed")
            projected = True
        grant_evidence = (retain_claim_grant_evidence(runtime, claim_task, fence, grant_row["receipt_sha256"])
                          if projected else None)
        body = {
            **base,
            "state": "ATTEMPT_RECORDED",
            "transition_class": GRANTED,
            "transition_id": transition_id,
            "disposition": "ALLOW",
            "claim_task_id": claim_task,
            "failed_predicate": None,
            "fencing_token": fence,
            "fence_issued": True,
            "organization_head_sha256": evidence.get("organization_head_sha256"),
            "claim_scope_sha256": evidence.get("claim_scope_sha256"),
            "cosv_task_vector": evidence.get("cosv_task_vector"),
            "selected_task_id": claim_task,
            "claim_grant_occurred": True,
            "claim_grant_evidence": grant_evidence,
            "replayed_prior_grant": replayed,
            "repository_receipt_sha256": receipts["repository_receipt"]["receipt_sha256"] if receipts else None,
            "organization_receipt_sha256": grant_row["receipt_sha256"],
            "organization_receipt_appended": True,
            "organization_receipt_precedes_projection": True,
            "authority_effect": "CANONICAL_ALLOCATOR_ONLY_IF_SELECTED",
        }
        return retained(transition_id, body)

    def prior_grant(grants: list[dict[str, Any]], claim_task: str | None) -> dict[str, Any] | None:
        rows = [row for row in grants if (row.get("boundary_evidence") or {}).get("task_id") == claim_task]
        return rows[-1] if rows else None

    org_root = custody["organization_root"]
    head: str | None = None
    claim_task = target or "NONE"
    try:
        if not org_root.is_dir():
            raise ClaimFailClosed("LEDGER_HEAD_UNVERIFIED", "organization ledger root absent",
                                  "supply an organization ledger root whose HEAD and chain verify")
        with claim_allocation_lock(org_root):
            chain = verify_organization_chain(custody)
            head = chain["head_sha256"]
            grants = chain_grants(chain)
            prior = prior_grant(grants, target) if target else None
            if prior is not None:
                return allow(target, prior, None, replayed=True)
            plan = run_allocator(runner, runtime, safe_env, "--plan", *(("--task", target) if target else ()))
            selected = plan.get("selected")
            if not isinstance(selected, str) or not selected:
                predicate = plan.get("refusal_predicate") or "NO_ELIGIBLE_TASK"
                return non_allow(REFUSED, claim_task, predicate,
                                 "allocator evaluated " + ("target " + target if target else "the ranked queue"),
                                 None, organization=True, head=head)
            claim_task = selected
            prior = prior_grant(grants, selected)
            if prior is not None:
                return allow(selected, prior, None, replayed=True)
            floor = provenance_floor(source)
            chain_max = max([row["boundary_evidence"]["fencing_token"] for row in grants], default=0)
            runtime_generation = plan.get("claim_registry_generation")
            if not isinstance(runtime_generation, int) or isinstance(runtime_generation, bool):
                raise ClaimFailClosed("RUNTIME_CLAIM_REGISTRY_INVALID", "generation invalid",
                                      "repair the runtime claim registry")
            issued = max(chain_max, floor["fence"])
            if runtime_generation < issued:
                # Never lowered and never reissued: a registry behind the fences
                # already issued is a stale projection, not a new origin.
                raise ClaimFailClosed(
                    "FENCE_GENERATION_BEHIND_ISSUED_FENCES",
                    f"runtime generation {runtime_generation} < issued fence {issued}",
                    "rematerialize the runtime claim registry at or beyond the issued fences")
            fence = max(chain_max, floor["fence"], runtime_generation) + 1
            task = load_json(runtime / "tasks" / f"{selected}.json")
            requested = plan.get("requested_claims") or task["requirements"]["mandatory"]
            evidence = {
                "disposition": "ALLOW",
                "task_id": selected,
                "cosv_task_vector": task_cosv(source, task),
                "claim_scope_sha256": stable_hash(requested),
                "claimed_repositories": sorted({(r.get("repository") or {}).get("full_name") for r in requested}),
                "fencing_token": fence,
                "organization_head_sha256": head,
                "chain_max_fence": chain_max,
                "provenance_floor": floor,
                "runtime_claims_generation_observed": runtime_generation,
                "request_id": request.get("request_id"),
                "request_sha256": request_hash,
                "target_task_id": target,
                "failed_predicate": None,
                "consequence_committed": True,
            }
            transition_id = f"ORGANIZATION-WORKER-CLAIM-GRANTED-{selected}-G{fence}"
            predecessor = "sha256:" + stable_hash({"organization_head_sha256": head, "task_id": selected})
            receipts = record_transition(
                custody, GRANTED, transition_id, predecessor, evidence, organization=True,
                identity=("task_id", "fencing_token", "claim_scope_sha256", "organization_head_sha256"))
            return allow(selected, receipts["organization_receipt"], receipts, replayed=False)
    except ClaimFailClosed as exc:
        verified = head is not None or (org_root.is_dir() and exc.predicate != "LEDGER_HEAD_UNVERIFIED")
        return non_allow(FAIL_CLOSED, claim_task, exc.predicate, exc.detail, exc.repair,
                         organization=verified, head=head)


def consume(
    source_root: Path,
    runtime_root: Path,
    *,
    repo_ledger_root: Path | None = None,
    org_ledger_root: Path | None = None,
    runner=subprocess.run,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    present = [rel for rel in REQUEST_RELS if (runtime / rel).is_file()]
    if not present:
        return {
            "schema": "stegverse.resident-execution-request-consumption/v1",
            "state": "NO_REQUEST",
            "task_id": TASK_ID,
            "runtime_execution_attempted": False,
            "authority_effect": "NONE",
        }
    if repo_ledger_root is None or org_ledger_root is None:
        # Supplied, never derived: nothing is materialized or allocated without both.
        return _ledger_refusal(load_json(runtime / present[0]), "ledger roots not supplied")
    safe_env = clean_env(env)
    try:
        custody = ledger_custody(source, repo_ledger_root, org_ledger_root)
    except ClaimFailClosed as exc:
        return _ledger_refusal(load_json(runtime / present[0]), exc.predicate + ": " + exc.detail)
    attempts = [consume_request(source, runtime, rel, custody=custody, runner=runner, safe_env=safe_env)
                for rel in present]
    if len(attempts) == 1:
        return attempts[0]
    state = "FAIL_CLOSED" if any(a["state"] == "FAIL_CLOSED" for a in attempts) else "ATTEMPT_RECORDED"
    return {
        "schema": "stegverse.resident-execution-request-consumption/v1",
        "state": state,
        "task_id": TASK_ID,
        "attempts": attempts,
        "runtime_execution_attempted": True,
        "request_granted_claim_authority": False,
        "allocator_remains_claim_authority": True,
        "authority_effect": "CANONICAL_ALLOCATOR_ONLY_IF_SELECTED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Invoke the canonical organization claim allocator from resident dispatch.")
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--repo-ledger-root", type=Path, default=None)
    parser.add_argument("--org-ledger-root", type=Path, default=None)
    args = parser.parse_args()
    try:
        receipt = consume(args.source_root, args.runtime_root,
                          repo_ledger_root=args.repo_ledger_root, org_ledger_root=args.org_ledger_root)
    except Exception as exc:
        receipt = {
            "schema": "stegverse.resident-execution-request-consumption/v1",
            "state": "BLOCKED",
            "task_id": TASK_ID,
            "runtime_execution_attempted": False,
            "reason": str(exc),
            "authority_effect": "NONE",
        }
        print(json.dumps(receipt, sort_keys=True))
        return 2
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["state"] in {"NO_REQUEST", "ATTEMPT_RECORDED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
