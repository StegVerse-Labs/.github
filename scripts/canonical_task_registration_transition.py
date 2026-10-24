#!/usr/bin/env python3
"""Manifest-directed canonical Goal Task registration transition.

Registering a new canonical Goal Task used to be a hand edit: a session wrote
the canonical record, appended the identical row to the aggregate Registry,
bumped the generation, hand-wrote the COSV task vector and index entry, and
added a bespoke per-task test (for example
tests/test_sdk_cost_derived_tier_pricing_registration.py). Nothing derived those
four surfaces from one declared input, so nothing could prove the edit was the
registration it claimed to be.

This transition derives them from one committed manifest,
``control/canonical-task-registration-requests/<request_id>.json``
(``stegverse.canonical-task-registration-request/v1``):

* ``plan``   reads the manifest against a predecessor tree and returns the
             disposition and the receipt it would carry; it writes nothing.
* ``apply``  performs the derivation into a working tree and writes nothing
             else. The receipt is its observation.
* ``verify`` re-derives from the predecessor tree (the live base) and requires
             the successor tree (the PR head) to hold exactly those bytes; a
             hand edit that differs is refused.

Predicates (every non-ALLOW carries the six standard fields):
  REGISTRATION_REQUEST_SCHEMA_INVALID, REGISTRY_GENERATION_NOT_OBSERVED_TIP
  (data/task-coordination-policy.json#session_mutation_generation_fence),
  TASK_IDENTITY_NOT_UNIQUE (adjacent_task_derivation_contract
  duplicate_task_creation_prohibited), CANONICAL_RECORD_SCHEMA_INVALID
  (schemas/canonical-task-record.schema.json), WORKER_CLAIM_NOT_PROJECTION_ONLY
  (TASK_REGISTRY_CANONICAL_INVARIANTS.md "Worker-claim field invariant"),
  UNQUALIFIED_COMPLETION_PROHIBITED (data/task-registry-global-invariants.json
  completion_language_requires_evidence_class), COSV_NOT_DERIVABLE
  (scripts/cosv.py encode_task over the declared exact_metrics; no manual
  vector), ALLOCATION_REQUEST_NOT_BOUND (control/goal-task-allocation-requests/;
  a proposal is checked against the derivation, never adopted),
  REGISTRY_COLLISION_CHECKIN_NOT_CONTINUE (plan and apply: the existing check-in,
  scripts/check_registry_collision_checkin.py, Labs#3254, over base -> successor),
  EXISTING_IDENTITY_NOT_ADMISSIBLE (registration_mode EXISTING_IDENTITY),
  REGISTRATION_NOT_APPLIED / REGISTRATION_BYTES_DIVERGE (verify).

registration_mode EXISTING_IDENTITY (default NEW_IDENTITY) registers the
aggregate Registry row for a canonical record shard that already exists and has
no row (CHECKED_OUT_SHARD_OMITTED_FROM_AGGREGATE). The shard is identity
evidence, not a collision. Declared invariants it settles:

* row == record: the manifest record must equal the shard; the appended row is
  the shard record verbatim and the shard bytes are not rewritten; generation
  tip -> tip + 1.
* COSV source: encode_task over declared exact_metrics (must equal any vector the
  shard already records), else the shard's own recorded task.v1 vector (its
  missing metrics stay a six-field residual), else FAIL_CLOSED
  COSV_NOT_DERIVABLE. No vector is ever chosen by the manifest.
* schema conformance: the current record schema is reported, not enforced, on an
  existing identity (the Registry already holds legacy rows); the authority
  floor is enforced; nonconformance is a residual whose repair is the record-data
  successor transition.
* state: the recorded coordination_state is projected as recorded; a state that
  asserts a claim (CLAIMED, IN_PROGRESS, COMPLETION_CLAIMED) or a worker_claim
  with a claim_ref/fence_ref is refused. ACTIVE with no WorkerCoordinator claim
  is a residual, not a claim; the receipt carries a claim *request*.

Every ALLOW receipt carries a WorkerCoordinator claim request
(workercoordinator_claim_request): a request only, claim_ref and fence_ref null,
request_grants_claim_authority false. Lowest supported mode: E0 (ecosystem only,
no LLM): every predicate is mechanical over committed files.

Authority: NONE_REGISTRATION_ONLY. Registration mints no WorkerCoordinator
claim or fence, no InTr admission and no execution authority
(TASK_REGISTRY_DOES_NOT_MINT_EXECUTION_AUTHORITY). No clock is read: the vector
``observed_at`` comes from the manifest and the successor generation is the
observed tip + 1. Appending the receipt to the organization ledger is the
existing emitter's job (.stegverse/transition-ledger/emit.py through
organization-ledger-transition.yml); this script never appends or dispatches.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "StegVerse-Labs/.github"
REQUEST_SCHEMA = "stegverse.canonical-task-registration-request/v1"
RECEIPT_SCHEMA = "stegverse.canonical-task-registration-transition-receipt/v1"
RECORD_SCHEMA_PATH = "schemas/canonical-task-record.schema.json"
REQUEST_SCHEMA_PATH = "schemas/canonical-task-registration-request.schema.json"
REGISTRY = "data/canonical-task-registry.json"
RECORDS = "data/canonical-task-records"
VECTORS = "control/task-vectors"
INDEX = "control/task-vector-index.json"
INDEX_SHARDS = "control/task-vector-index.d"
REQUESTS = "control/canonical-task-registration-requests"
ENTRYPOINT = "scripts/canonical_task_registration_transition.py"
WORKFLOW = ".github/workflows/canonical-task-registration-transition.yml"
OWNING_GOAL = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"
NEXT_ATTEMPT = "on the next registration request event after the repair is recorded"
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")
AUTHORITY_EFFECT = "NONE_REGISTRATION_ONLY"
ALLOWED_INITIAL_STATES = {"PROPOSED"}
NEW_IDENTITY, EXISTING_IDENTITY = "NEW_IDENTITY", "EXISTING_IDENTITY"
CLAIM_ASSERTING_STATES = {"CLAIMED", "IN_PROGRESS", "COMPLETION_CLAIMED"}
ALLOCATION_REQUESTS = "control/goal-task-allocation-requests"
ALLOCATION_REQUEST_SCHEMA = "stegverse.goal-task-allocation-request/v0.1"
COLLISION_CHECKIN = "scripts/check_registry_collision_checkin.py"
RECORD_DATA_SUCCESSOR = "apply_task_record_data record-data successor transition (StegVerse-Labs/.github#3257)"
LOWEST_SUPPORTED_MODE = "E0"
VECTOR_KEYS = ("exact_metrics", "metric_evidence", "evidence_refs", "observed_at")


class Refusal(Exception):
    def __init__(self, predicate: str, detail: str, repair: str):
        super().__init__(f"{predicate}: {detail}")
        self.predicate, self.detail, self.repair = predicate, detail, repair


def _cosv() -> Any:
    spec = importlib.util.spec_from_file_location("cosv_for_registration", ROOT / "scripts" / "cosv.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _parent_existence() -> Any:
    spec = importlib.util.spec_from_file_location("registration_parent_existence",
                                                  ROOT / "scripts" / "registration_parent_existence.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def dump(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(ok: bool, predicate: str, detail: str, repair: str) -> None:
    if not ok:
        raise Refusal(predicate, detail, repair)


# --- stdlib subset of JSON Schema used by schemas/canonical-task-record.schema.json
_TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}


def _type_ok(value: Any, name: str) -> bool:
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, _TYPES[name])


def schema_errors(value: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []
    if "type" in schema:
        names = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_type_ok(value, n) for n in names):
            return [f"{path}: type {names}"]
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: const {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: enum")
    if isinstance(value, str) and len(value) < schema.get("minLength", 0):
        errors.append(f"{path}: minLength")
    if isinstance(value, (int, float)) and not isinstance(value, bool) and "minimum" in schema and value < schema["minimum"]:
        errors.append(f"{path}: minimum")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{path}: minItems")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path}: maxItems")
        if schema.get("uniqueItems") and len({canon(v) for v in value}) != len(value):
            errors.append(f"{path}: uniqueItems")
        if isinstance(schema.get("items"), dict):
            for i, item in enumerate(value):
                errors += schema_errors(item, schema["items"], f"{path}[{i}]")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: required {key}")
        props = schema.get("properties", {})
        for key, item in value.items():
            if key in props:
                errors += schema_errors(item, props[key], f"{path}.{key}")
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: additional property {key}")
            elif isinstance(schema.get("additionalProperties"), dict):
                errors += schema_errors(item, schema["additionalProperties"], f"{path}.{key}")
    return errors


# --- the transition
def validate_request(request: Any) -> dict[str, Any]:
    fix = f"commit a {REQUEST_SCHEMA} manifest under {REQUESTS}/ (see contracts/canonical-task-registration-transition.v1.json)"
    require(isinstance(request, dict), "REGISTRATION_REQUEST_SCHEMA_INVALID", "manifest is not an object", fix)
    errors = schema_errors(request, load(ROOT / REQUEST_SCHEMA_PATH))
    require(not errors, "REGISTRATION_REQUEST_SCHEMA_INVALID", "; ".join(errors[:8]), fix)
    require(request.get("schema") == REQUEST_SCHEMA, "REGISTRATION_REQUEST_SCHEMA_INVALID", f"schema {request.get('schema')!r}", fix)
    for key in ("request_id", "task_id", "observed_registry_generation", "record", "vector", "authority_effect"):
        require(key in request, "REGISTRATION_REQUEST_SCHEMA_INVALID", f"missing {key}", fix)
    require(isinstance(request["observed_registry_generation"], int) and not isinstance(request["observed_registry_generation"], bool),
            "REGISTRATION_REQUEST_SCHEMA_INVALID", "observed_registry_generation must be an integer", fix)
    require(request["authority_effect"] == AUTHORITY_EFFECT, "REGISTRATION_REQUEST_SCHEMA_INVALID",
            f"authority_effect must be {AUTHORITY_EFFECT}", fix)
    vector = request["vector"]
    require(isinstance(vector, dict) and all(k in vector for k in VECTOR_KEYS), "REGISTRATION_REQUEST_SCHEMA_INVALID",
            f"vector must carry {list(VECTOR_KEYS)}", fix)
    require(isinstance(vector["evidence_refs"], list) and vector["evidence_refs"], "REGISTRATION_REQUEST_SCHEMA_INVALID",
            "vector.evidence_refs must be non-empty", fix)
    mode = request.get("registration_mode", NEW_IDENTITY)
    require(mode in (NEW_IDENTITY, EXISTING_IDENTITY), "REGISTRATION_REQUEST_SCHEMA_INVALID",
            f"registration_mode {mode!r}", fix)
    recorded_vector_allowed = mode == EXISTING_IDENTITY  # the shard's own value, checked against the shard
    require("vector" not in vector and (recorded_vector_allowed or "cosv_task_vector" not in request["record"]),
            "COSV_NOT_DERIVABLE",
            "a manifest may not carry a vector value; the transition derives it",
            "remove the vector value; declare exact_metrics only (no manual vector assignment)")
    task_id = request["task_id"]
    require(isinstance(task_id, str) and task_id and "/" not in task_id and task_id == task_id.strip(),
            "REGISTRATION_REQUEST_SCHEMA_INVALID", "task_id must be a bare identifier", fix)
    return request


def collisions(root: Path, task_id: str, registry: dict[str, Any]) -> list[str]:
    found = [f"{REGISTRY}#tasks" for row in registry.get("tasks", []) if row.get("task_id") == task_id]
    for rel in (f"{RECORDS}/{task_id}.json", f"{VECTORS}/{task_id}.json", f"{INDEX_SHARDS}/{task_id}.json"):
        if (root / rel).exists():
            found.append(rel)
    index = root / INDEX
    if index.exists() and any(row.get("task_id") == task_id for row in load(index).get("tasks", [])):
        found.append(INDEX)
    return found


def residual(code: str, klass: str, repair: str, entrypoint: str, goal: str = OWNING_GOAL) -> dict[str, Any]:
    """A six-field item the ALLOW leaves open; it blocks nothing this transition decides."""
    return {"failure_code": code, "failed_predicate": code, "class": klass,
            "required_evidence_or_repair": repair, "retry_entrypoint": entrypoint,
            "owning_existing_goal": goal, "next_attempt": NEXT_ATTEMPT}


def has_metrics(metrics: Any, cosv: Any) -> bool:
    return isinstance(metrics, dict) and any(k in metrics for k in cosv.TASK_FIELDS)


def encode(cosv: Any, metrics: dict[str, Any]) -> str:
    try:
        vector = cosv.encode_task(metrics)
    except (KeyError, ValueError, TypeError) as exc:
        raise Refusal("COSV_NOT_DERIVABLE", f"encode_task failed: {exc!r}",
                      "declare every task.v1 exact_metrics field (scripts/cosv.py TASK_FIELDS)") from exc
    require(metrics.get("symbol_order") == "LRUIVGOCMTBEAP", "COSV_NOT_DERIVABLE", "exact_metrics.symbol_order missing",
            "set exact_metrics.symbol_order to LRUIVGOCMTBEAP")
    return vector


def vector_record_of(request: dict[str, Any], task_id: str, vector: str, cosv: Any) -> dict[str, Any]:
    vector_record = {
        "identity": f"{REPOSITORY}:task:{task_id}",
        "profile": "task.v1",
        "level": "task",
        "vector": vector,
        "evidence_refs": request["vector"]["evidence_refs"],
        "observed_at": request["vector"]["observed_at"],
        "exact_metrics": request["vector"]["exact_metrics"],
        "metric_evidence": request["vector"]["metric_evidence"],
        "authority_effect": "NONE",
    }
    require(cosv.validate_record(vector_record), "COSV_NOT_DERIVABLE", "derived vector record fails cosv.validate_record",
            "correct exact_metrics so the derived vector validates as task.v1")
    return vector_record


def index_shard_of(task_id: str, vector: str) -> dict[str, Any]:
    return {
        "schema": "stegverse.cosv-task-vector-index-entry/v1",
        "task_id": task_id,
        "repository": REPOSITORY,
        "registry_ref": f"{RECORDS}/{task_id}.json",
        "source_state_vector_ref": f"{VECTORS}/{task_id}.json",
        "vector": vector,
        "vector_state": "EMITTED",
        "profile": "task.v1",
        "authority_effect": "NONE",
    }


def bind_allocation(root: Path, request: dict[str, Any], vector: str | None) -> dict[str, Any] | None:
    """Check an allocation proposal against this derivation. A proposal never supplies the identity or the vector."""
    ref = request.get("allocation_request_ref")
    if ref is None:
        return None
    fix = f"point allocation_request_ref at a committed {ALLOCATION_REQUEST_SCHEMA} under {ALLOCATION_REQUESTS}/ whose proposal matches"
    require(isinstance(ref, str) and ref.startswith(ALLOCATION_REQUESTS + "/") and ".." not in ref and (root / ref).is_file(),
            "ALLOCATION_REQUEST_NOT_BOUND", f"allocation request {ref!r} not committed on the predecessor", fix)
    proposal = load(root / ref)
    require(isinstance(proposal, dict) and proposal.get("schema") == ALLOCATION_REQUEST_SCHEMA, "ALLOCATION_REQUEST_NOT_BOUND",
            f"{ref} is not {ALLOCATION_REQUEST_SCHEMA}", fix)
    require(proposal.get("proposed_task_id") == request["task_id"], "ALLOCATION_REQUEST_NOT_BOUND",
            f"{ref} proposes {proposal.get('proposed_task_id')!r}, manifest registers {request['task_id']!r}", fix)
    proposed = proposal.get("cosv_task_vector")
    require(proposed is None or vector is None or proposed == vector, "COSV_NOT_DERIVABLE",
            f"{ref} proposes vector {proposed!r}; the derivation is {vector!r}",
            "correct exact_metrics or the proposal; the derived vector is the only one registered")
    return {"allocation_request_ref": ref, "allocation_request_sha256": sha((root / ref).read_bytes()),
            "proposed_task_id_matches": True,
            "proposed_cosv_task_vector": proposed,
            "proposal_adopted": False}


def claim_request(task_id: str, row: dict[str, Any], generation: int) -> dict[str, Any]:
    """The request WorkerCoordinator consumes. It names no claim and grants nothing."""
    return {
        "schema": "stegverse.workercoordinator-claim-request/v1",
        "requested_of": "WORKERCOORDINATOR",
        "state": "REQUESTED",
        "task_id": task_id,
        "registry_row_sha256": sha(canon(row)),
        "registry_generation": generation,
        "canonical_allocator": "scripts/allocate_claims.py",
        "consumer_entrypoint": "scripts/consume_org_claim_allocator_request.py",
        "claim_ref": None,
        "fence_ref": None,
        "request_grants_claim_authority": False,
        "allocator_remains_claim_authority": True,
        "authority_effect": "NONE_REQUEST_ONLY",
    }


def derive(root: Path, request: dict[str, Any]) -> tuple[dict[str, bytes], dict[str, Any]]:
    """Return the successor bytes for each derived path, and the receipt evidence."""
    validate_request(request)
    _parent_existence().require_registry_readable(root, Refusal)  # REGISTRATION_PARENT_REGISTRY_UNREADABLE
    registry_path = root / REGISTRY
    registry_bytes = registry_path.read_bytes()
    registry = json.loads(registry_bytes)
    tip = registry.get("generation")
    require(isinstance(tip, int) and tip == request["observed_registry_generation"], "REGISTRY_GENERATION_NOT_OBSERVED_TIP",
            f"manifest observed generation {request['observed_registry_generation']!r}, predecessor tip is {tip!r}",
            "re-read data/canonical-task-registry.json on the live base and set observed_registry_generation to its generation")
    if request.get("registration_mode", NEW_IDENTITY) == EXISTING_IDENTITY:
        return derive_existing(root, request, registry, registry_bytes, tip)
    return derive_new(root, request, registry, registry_bytes, tip)


def derive_new(root: Path, request: dict[str, Any], registry: dict[str, Any], registry_bytes: bytes,
               tip: int) -> tuple[dict[str, bytes], dict[str, Any]]:
    task_id = request["task_id"]
    found = collisions(root, task_id, registry)
    require(not found, "TASK_IDENTITY_NOT_UNIQUE", f"{task_id} already present in {found}",
            "reuse the existing task (adjacent_task_derivation_contract reuse_existing_equivalent_task_first) or choose a distinct task_id")
    _parent_existence().check(root, request, Refusal)  # REGISTRATION_PARENT_NOT_REGISTERED

    record = copy.deepcopy(request["record"])
    errors = schema_errors(record, load(root / RECORD_SCHEMA_PATH))
    require(not errors, "CANONICAL_RECORD_SCHEMA_INVALID", "; ".join(errors[:8]),
            f"make the manifest record conform to {RECORD_SCHEMA_PATH}")
    require(record["task_id"] == task_id, "CANONICAL_RECORD_SCHEMA_INVALID", "record.task_id differs from manifest task_id",
            "set record.task_id to the manifest task_id")
    require(record["coordination_state"] in ALLOWED_INITIAL_STATES, "CANONICAL_RECORD_SCHEMA_INVALID",
            f"initial coordination_state {record['coordination_state']!r}", "register as PROPOSED; later states are separate transitions")
    claim = record["worker_claim"]
    require(claim == {"authority": "WORKERCOORDINATOR", "claim_ref": None, "fence_ref": None, "projection_only": True},
            "WORKER_CLAIM_NOT_PROJECTION_ONLY", "registration cannot carry a claim or fence",
            "set worker_claim claim_ref/fence_ref null; WorkerCoordinator mints claims separately")
    require(record["completion"]["claimed"] is False and record["completion"]["validated"] is False,
            "UNQUALIFIED_COMPLETION_PROHIBITED", "registration cannot carry a completion claim",
            "register with completion.claimed/validated false; completion is reconciled later with an evidence class")
    require(record.get("authority_model", {}).get("task_registry_mints_execution_authority") is False,
            "CANONICAL_RECORD_SCHEMA_INVALID", "authority_model.task_registry_mints_execution_authority must be false",
            "set it false (TASK_REGISTRY_DOES_NOT_MINT_EXECUTION_AUTHORITY)")

    cosv = _cosv()
    vector = encode(cosv, request["vector"]["exact_metrics"])
    vector_rel = f"{VECTORS}/{task_id}.json"
    vector_record = vector_record_of(request, task_id, vector, cosv)
    allocation = bind_allocation(root, request, vector)

    record["cosv_task_vector"] = vector
    record["source_state_vector_ref"] = vector_rel
    record_rel = f"{RECORDS}/{task_id}.json"
    successor = copy.deepcopy(registry)
    successor["generation"] = tip + 1
    successor.setdefault("tasks", []).append(copy.deepcopy(record))
    shard = index_shard_of(task_id, vector)
    outputs = {
        REGISTRY: dump(successor),
        record_rel: dump(record),
        vector_rel: dump(vector_record),
        f"{INDEX_SHARDS}/{task_id}.json": dump(shard),
    }
    evidence = {
        "task_id": task_id,
        "cosv_task_vector": vector,
        "cosv_derivation": "scripts/cosv.py encode_task(exact_metrics)",
        "predecessor_registry_generation": tip,
        "successor_registry_generation": tip + 1,
        "predecessor_registry_sha256": sha(registry_bytes),
        "row_equals_record": True,
        "registration_mode": NEW_IDENTITY,
        "lowest_supported_mode": LOWEST_SUPPORTED_MODE,
        "allocation": allocation,
        "workercoordinator_claim_request": claim_request(task_id, record, tip + 1),
    }
    return outputs, evidence


def derive_existing(root: Path, request: dict[str, Any], registry: dict[str, Any], registry_bytes: bytes,
                    tip: int) -> tuple[dict[str, bytes], dict[str, Any]]:
    """Register the aggregate row for an existing shard (row == shard record, generation tip -> tip + 1)."""
    task_id = request["task_id"]
    record_rel = f"{RECORDS}/{task_id}.json"
    gate = "EXISTING_IDENTITY_NOT_ADMISSIBLE"
    shard_path = root / record_rel
    require(shard_path.is_file(), gate, f"{record_rel} does not exist on the predecessor",
            "register a new identity with registration_mode NEW_IDENTITY (the default)")
    shard_bytes = shard_path.read_bytes()
    try:
        shard = json.loads(shard_bytes)
    except json.JSONDecodeError as exc:
        raise Refusal(gate, f"{record_rel} is not JSON: {exc}", "repair the shard through the record-data successor transition") from exc
    rows = [row for row in registry.get("tasks", []) if row.get("task_id") == task_id]
    require(not rows, "TASK_IDENTITY_NOT_UNIQUE", f"{task_id} already has {len(rows)} aggregate row(s) at generation {tip}",
            "nothing to register; reconcile the existing row through its own transition")
    require(request["record"] == shard, gate, f"manifest record differs from {record_rel} ({sha(shard_bytes)})",
            f"copy {record_rel} verbatim into the manifest record")
    require(shard.get("task_id") == task_id, gate, "shard task_id differs from manifest task_id",
            "the shard file name and its task_id must name the same identity")

    # authority floor: enforced on every existing identity, whatever schema generation the shard predates
    authority = shard.get("authority_model") if isinstance(shard.get("authority_model"), dict) else {}
    require(authority.get("task_registry_mints_execution_authority") is False, "CANONICAL_RECORD_SCHEMA_INVALID",
            "authority_model.task_registry_mints_execution_authority must be false",
            "set it false through the record-data successor transition (TASK_REGISTRY_DOES_NOT_MINT_EXECUTION_AUTHORITY)")
    require(authority.get("worker_claim_authority", "WORKERCOORDINATOR") == "WORKERCOORDINATOR"
            and authority.get("source_state_proves_execution", False) is False, "CANONICAL_RECORD_SCHEMA_INVALID",
            "authority_model names a claim authority other than WORKERCOORDINATOR or lets source state prove execution",
            "repair authority_model through the record-data successor transition")
    completion = shard.get("completion") if isinstance(shard.get("completion"), dict) else {}
    require(completion.get("claimed", False) is False and completion.get("validated", False) is False,
            "UNQUALIFIED_COMPLETION_PROHIBITED", "the shard carries a completion claim",
            "reconcile completion with an evidence class before the row is registered")
    state = shard.get("coordination_state")
    require(isinstance(state, str) and state, "CANONICAL_RECORD_SCHEMA_INVALID", "coordination_state missing",
            "record a coordination_state through the record-data successor transition")
    claim = shard.get("worker_claim")
    require(state not in CLAIM_ASSERTING_STATES and (claim is None or (isinstance(claim, dict)
            and claim.get("claim_ref") is None and claim.get("fence_ref") is None)),
            "WORKER_CLAIM_NOT_PROJECTION_ONLY", f"state {state!r} / worker_claim {claim!r} asserts a claim WorkerCoordinator did not issue",
            "WorkerCoordinator mints claims (scripts/allocate_claims.py); register the identity without the claim")

    residuals: list[dict[str, Any]] = []
    schema_errors_found = schema_errors(shard, load(root / RECORD_SCHEMA_PATH))
    if schema_errors_found:
        residuals.append(residual(
            "CANONICAL_RECORD_SCHEMA_SUCCESSOR_REQUIRED", "A",
            f"conform {record_rel} to {RECORD_SCHEMA_PATH} through the {RECORD_DATA_SUCCESSOR}; the row follows the record",
            f"{RECORD_DATA_SUCCESSOR} / python {ENTRYPOINT} verify"))
    if state not in ALLOWED_INITIAL_STATES or claim is None:
        residuals.append(residual(
            "CLAIM_NOT_ISSUED_BY_WORKERCOORDINATOR", "A",
            f"coordination_state {state!r} is projected as recorded and is not a claim; WorkerCoordinator consumes "
            "evidence.workercoordinator_claim_request and alone issues claim_ref/fence_ref",
            "scripts/consume_org_claim_allocator_request.py -> scripts/allocate_claims.py", "SHWP-ORG-CLAIM-ALLOCATOR-001"))

    cosv = _cosv()
    metrics = request["vector"]["exact_metrics"]
    recorded = shard.get("cosv_task_vector")
    outputs: dict[str, bytes] = {}
    vector_rel, index_rel = f"{VECTORS}/{task_id}.json", f"{INDEX_SHARDS}/{task_id}.json"
    if has_metrics(metrics, cosv):
        vector = encode(cosv, metrics)
        require(recorded is None or recorded == vector, "COSV_NOT_DERIVABLE",
                f"exact_metrics derive {vector}, the shard records {recorded}",
                "declare the exact_metrics the shard's vector was derived from, or repair the shard's vector by its successor")
        derived = {vector_rel: dump(vector_record_of(request, task_id, vector, cosv)), index_rel: dump(index_shard_of(task_id, vector))}
        for rel, data in derived.items():
            require(not (root / rel).exists() or (root / rel).read_bytes() == data, "TASK_IDENTITY_NOT_UNIQUE",
                    f"{rel} exists with other bytes", f"reconcile {rel} with the derivation before registering the row")
        outputs.update(derived)
        cosv_source = "scripts/cosv.py encode_task(exact_metrics)"
    elif isinstance(recorded, str) and cosv.validate_vector("task.v1", recorded):
        vector = recorded
        cosv_source = f"{record_rel}#cosv_task_vector (recorded on the existing identity; not re-derived)"
        residuals.append(residual(
            "COSV_EXACT_METRICS_NOT_OBSERVED", "A",
            f"declare the task.v1 exact_metrics of {task_id} in a manifest; this transition then emits {vector_rel} "
            f"and {index_rel} and requires them to derive {recorded}",
            f"{WORKFLOW} / python {ENTRYPOINT} plan"))
    else:
        raise Refusal("COSV_NOT_DERIVABLE",
                      f"no exact_metrics declared and {record_rel} records no valid task.v1 vector ({recorded!r})",
                      "declare every task.v1 exact_metrics field (scripts/cosv.py TASK_FIELDS); no vector is assigned by hand")
    allocation = bind_allocation(root, request, vector)

    row = copy.deepcopy(shard)  # row == record: the shard verbatim
    successor = copy.deepcopy(registry)
    successor["generation"] = tip + 1
    successor.setdefault("tasks", []).append(row)
    outputs[REGISTRY] = dump(successor)
    outputs[record_rel] = shard_bytes  # identity evidence: verify requires it unchanged
    evidence = {
        "task_id": task_id,
        "registration_mode": EXISTING_IDENTITY,
        "lowest_supported_mode": LOWEST_SUPPORTED_MODE,
        "existing_record_ref": record_rel,
        "existing_record_sha256": sha(shard_bytes),
        "record_rewritten": False,
        "cosv_task_vector": vector,
        "cosv_derivation": cosv_source,
        "predecessor_registry_generation": tip,
        "successor_registry_generation": tip + 1,
        "predecessor_registry_sha256": sha(registry_bytes),
        "row_equals_record": True,
        "record_schema_conformance": "CONFORMS" if not schema_errors_found else "PREDATES_CURRENT_SCHEMA",
        "record_schema_errors": schema_errors_found[:16],
        "projected_coordination_state": state,
        "existing_record_preflight": "StegVerse-Labs/.github#3306 requires exactly one aggregate row equal to the shard "
                                     "with a matching COSV; this successor supplies exactly that row",
        "allocation": allocation,
        "residuals": residuals,
        "workercoordinator_claim_request": claim_request(task_id, row, tip + 1),
    }
    return outputs, evidence


def checkin_on_successor(base: Path, outputs: dict[str, bytes]) -> str:
    """Run the check-in on a scratch successor (predecessor + derived bytes); nothing is written to base."""
    scratch = Path(tempfile.mkdtemp(prefix="registration-successor-"))
    try:
        for rel in ("data", "scripts"):
            if (base / rel).is_dir():
                shutil.copytree(base / rel, scratch / rel)
        for rel, data in outputs.items():
            (scratch / rel).parent.mkdir(parents=True, exist_ok=True)
            (scratch / rel).write_bytes(data)
        collision_checkin(base, scratch)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    return f"ALLOW ({COLLISION_CHECKIN} over predecessor -> derived successor)"


def collision_checkin(base: Path, head: Path) -> None:
    """Apply predicate: the existing check-in (Labs#3254) over predecessor -> successor."""
    script = base / COLLISION_CHECKIN
    require(script.is_file(), "REGISTRY_COLLISION_CHECKIN_NOT_CONTINUE", f"{COLLISION_CHECKIN} absent on the predecessor",
            f"run apply on a tree that carries {COLLISION_CHECKIN} (StegVerse-Labs/.github#3254)")
    spec = importlib.util.spec_from_file_location("collision_checkin_for_registration", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    load_evaluator = module.load_evaluator

    def clock_free_evaluator(root: Path) -> Any:
        # The check-in points its event ledger at an empty scratch path, so its recent-event
        # window is empty whatever "now" is. Pin "now" to the epoch so no clock is read.
        evaluator = load_evaluator(root)
        real = evaluator.datetime

        class _Pinned(real):  # type: ignore[misc, valid-type]
            @classmethod
            def now(cls, tz=None):
                return real.fromtimestamp(0, tz)

        evaluator.datetime = _Pinned
        return evaluator

    module.load_evaluator = clock_free_evaluator
    result = module.check(base, head)
    failed = [r for r in result.get("results", []) if r.get("disposition") != "ALLOW"]
    require(result.get("disposition") == "ALLOW", "REGISTRY_COLLISION_CHECKIN_NOT_CONTINUE",
            json.dumps([{k: r.get(k) for k in ("task_id", "head_disposition", "failure_code", "evidence")} for r in failed])[:900],
            "; ".join(str(r.get("required_evidence_or_repair")) for r in failed)[:600]
            or "coordinate the colliding tasks the check-in names, then re-run plan")


def receipt(request: dict[str, Any], request_bytes: bytes, mode: str, disposition: str,
            evidence: dict[str, Any] | None = None, outputs: dict[str, bytes] | None = None,
            refusal: Refusal | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema": RECEIPT_SCHEMA,
        "transition": "CANONICAL_TASK_REGISTRATION",
        "mode": mode,
        "request_id": request.get("request_id") if isinstance(request, dict) else None,
        "request_sha256": sha(request_bytes),
        "disposition": disposition,
        "authority_effect": AUTHORITY_EFFECT,
        "workercoordinator_claim_or_fence_minted": False,
        "intr_admission_minted": False,
        "execution_authority_minted": False,
        "clock_read": False,
        "organization_ledger_appended": False,
        "organization_ledger_entrypoint": ".stegverse/transition-ledger/emit.py via .github/workflows/organization-ledger-transition.yml",
    }
    if evidence is not None:
        body["evidence"] = evidence
    if outputs is not None:
        body["derived_files"] = {path: sha(data) for path, data in sorted(outputs.items())}
    if refusal is not None:
        body.update({
            "failure_code": refusal.predicate,
            "failed_predicate": refusal.predicate,
            "detail": refusal.detail,
            "required_evidence_or_repair": refusal.repair,
            "retry_entrypoint": f"{WORKFLOW} / python {ENTRYPOINT} {mode}",
            "owning_existing_goal": OWNING_GOAL,
            "next_attempt": NEXT_ATTEMPT,
            "consequence_committed": False,
        })
    return body


def run(mode: str, request_path: Path, base: Path, head: Path | None = None) -> dict[str, Any]:
    request_bytes = request_path.read_bytes()
    try:
        request = json.loads(request_bytes)
    except json.JSONDecodeError as exc:
        return receipt({}, request_bytes, mode, "FAIL_CLOSED",
                       refusal=Refusal("REGISTRATION_REQUEST_SCHEMA_INVALID", f"not JSON: {exc}", "commit valid JSON"))
    try:
        outputs, evidence = derive(base, request)
        if mode in ("plan", "apply"):
            evidence["collision_checkin"] = checkin_on_successor(base, outputs)
        if mode == "apply":
            target = head or base
            for rel, data in outputs.items():
                path = target / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        elif mode == "verify":
            assert head is not None
            missing = [rel for rel in outputs if not (head / rel).exists()]
            require(not missing, "REGISTRATION_NOT_APPLIED", f"successor lacks {missing}",
                    f"run python {ENTRYPOINT} apply --request <manifest> on the live base and commit its output unchanged")
            diverged = [rel for rel, data in outputs.items() if (head / rel).read_bytes() != data]
            require(not diverged, "REGISTRATION_BYTES_DIVERGE", f"successor differs from the derivation at {diverged}",
                    f"replace hand edits with the output of python {ENTRYPOINT} apply on the live base")
        return receipt(request, request_bytes, mode, "ALLOW", evidence, outputs)
    except Refusal as refusal:
        return receipt(request, request_bytes, mode, "FAIL_CLOSED", refusal=refusal)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", choices=("plan", "apply", "verify"))
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--base", type=Path, default=ROOT, help="predecessor tree (live base)")
    parser.add_argument("--head", type=Path, help="successor tree (verify) or apply target")
    parser.add_argument("--receipt-out", type=Path)
    args = parser.parse_args(argv)
    if args.mode == "verify" and args.head is None:
        parser.error("verify needs --head")
    body = run(args.mode, args.request, args.base.resolve(), args.head.resolve() if args.head else None)
    text = json.dumps(body, indent=2, sort_keys=True) + "\n"
    if args.receipt_out:
        args.receipt_out.write_text(text, encoding="utf-8")
    (sys.stdout if body["disposition"] == "ALLOW" else sys.stderr).write(text)
    return 0 if body["disposition"] == "ALLOW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
