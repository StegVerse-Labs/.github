#!/usr/bin/env python3
"""Project an organization claim-allocator GRANTED receipt into the WorkerCoordinator registry.

`scripts/consume_org_claim_allocator_request.py` appends an
ORGANIZATION_WORKER_CLAIM_GRANTED receipt to the Organization ledger (fence
domain: the Organization claim chain, provenance floor 7 at
tasks/TASK-2026-0012.json). The canonical Task Registry names
`control/worker-registry.json / WorkerCoordinator` as execution_claim_and_fence
authority, and `scripts/project_worker_claim_into_canonical_task.py` reads only
that registry. Without this transition a grant never reaches a canonical
task's worker_claim; a hand edit of the worker registry would be the only path.

This transition derives the worker-registry successor from one committed
manifest, ``control/worker-claim-grant-projection-requests/<request_id>.json``
(``stegverse.worker-claim-grant-projection-request/v1``), carrying the grant
receipt's exact bytes, and from a read of the Organization ledger:

* ``plan``   returns the disposition and receipt; writes nothing.
* ``apply``  writes the derived control/worker-registry.json into a tree.
* ``verify`` re-derives from the predecessor tree and requires the successor
             tree to hold exactly those bytes.
* ``guard``  for a change carrying no manifest: control/worker-registry.json may
             not add, change or remove a projected row.

Fence-domain reconciliation (cited in contracts/worker-claim-grant-projection-transition.v1.json):
* The allocator fence is carried verbatim, tagged ``fence_domain:
  ORGANIZATION_CLAIM_ALLOCATOR``, with the grant transition id as claim_id. It is
  never renumbered into the WorkerCoordinator generation domain, and this
  transition mints no WorkerCoordinator-domain fence.
* The worker registry generation advances to max(generation + 1, fence + 1):
  the existing cross-domain rule of heartbeat_runtime/worker_runtime_legacy.py
  (``minimum_fencing_token_exclusive``), so it never lowers and no later
  WorkerCoordinator mint can reuse an integer at or below a projected fence.
* A fence already projected from a different receipt is refused (no reissue);
  the same receipt again is an idempotent replay with no change.

No clock is read: ordering is the registry generation and the receipt's
carrier ``hb_reference.epoch``; a receipt whose epoch was derived from a host
clock is refused, and ``updated_at`` is left as found. Authority:
NONE_PROJECTION_ONLY. Projection into canonical records stays with the existing
projector, which requires an admitted task.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REQUEST_SCHEMA = "stegverse.worker-claim-grant-projection-request/v1"
RECEIPT_SCHEMA = "stegverse.worker-claim-grant-projection-transition-receipt/v1"
REQUEST_SCHEMA_PATH = "schemas/worker-claim-grant-projection-request.schema.json"
ORG_RECEIPT_SCHEMA = "stegverse.organization-transition-receipt/v1"
GRANTED = "ORGANIZATION_WORKER_CLAIM_GRANTED"
WORKER_REGISTRY = "control/worker-registry.json"
ORG_CONTRACT = ".stegverse/transition-ledger/org-contract.json"
REPO_CONTRACT = ".stegverse/transition-ledger/contract.json"
SOURCE_RECEIPT_SCHEMA = "stegverse.repo-transition-receipt/v1"
REQUESTS = "control/worker-claim-grant-projection-requests"
ENTRYPOINT = "scripts/worker_claim_grant_projection_transition.py"
WORKFLOW = ".github/workflows/worker-claim-grant-projection-transition.yml"
OWNING_GOAL = "STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001"
FENCE_DOMAIN = "ORGANIZATION_CLAIM_ALLOCATOR"
PROJECTED_STATE = "CLAIM_GRANTED_PROJECTED"
# What a verified Organization chain establishes (consume_org_claim_allocator_request.CUSTODY_AUTHENTICATION):
# hash-chain continuity only, never authenticated custody. A grant claiming more is refused, and every
# projected row carries this label so no reader takes the row for authenticated custody.
CUSTODY_AUTHENTICATION = "HASH_CHAIN_CONTINUITY_ONLY"
AUTHORITY_EFFECT = "NONE_PROJECTION_ONLY"
NEXT_ATTEMPT = "on the next projection request event after the repair is recorded"
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")


class Refusal(Exception):
    """A six-field FAIL_CLOSED. `failed_predicate` defaults to the failure code; a refusal passed
    through from an existing verifier names that verifier's own predicate and carries its refusal."""

    def __init__(self, predicate: str, detail: str, repair: str, *, failed_predicate: str | None = None,
                 readback_refusal: dict[str, Any] | None = None):
        super().__init__(f"{predicate}: {detail}")
        self.predicate, self.detail, self.repair = predicate, detail, repair
        self.failed_predicate = failed_predicate or predicate
        self.readback_refusal = readback_refusal


def require(ok: bool, predicate: str, detail: str, repair: str) -> None:
    if not ok:
        raise Refusal(predicate, detail, repair)


def canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha(value: Any) -> str:
    """The Organization ledger digest (resident-runtime/aggregate_repo_transition.py sha)."""
    return "sha256:" + hashlib.sha256(canon(value)).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def _module(name: str, rel: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _schema_errors(value: Any, schema: dict[str, Any]) -> list[str]:
    # Stdlib subset (required, additionalProperties, const, integer); no jsonschema dependency.
    errors = []
    if not isinstance(value, dict):
        return ["$: object required"]
    for key in schema.get("required", []):
        if key not in value:
            errors.append(f"$: required {key}")
    props = schema.get("properties", {})
    if schema.get("additionalProperties") is False:
        errors += [f"$: additional property {k}" for k in value if k not in props]
    for key, rule in props.items():
        if key in value and "const" in rule and value[key] != rule["const"]:
            errors.append(f"$.{key}: const {rule['const']!r}")
        if key in value and rule.get("type") == "integer" and (not isinstance(value[key], int) or isinstance(value[key], bool)):
            errors.append(f"$.{key}: integer")
    return errors


# --- Organization ledger read (same predicates as consume_org_claim_allocator_request._verify_store_chain)
def open_store(locator: str | None) -> Any:
    if not locator:
        return None
    ledger_store = _module("projection_ledger_store", "resident-runtime/ledger_store.py")
    return ledger_store.open_store(locator), ledger_store


def read_chain(opened: Any, organization: str) -> list[dict[str, Any]]:
    repair = "supply --org-ledger for the designated Organization ledger ref (refs/stegverse/organization-ledger) and retry"
    require(opened is not None, "ORGANIZATION_CHAIN_MEMBERSHIP_UNVERIFIED", "no Organization ledger supplied", repair)
    store, keys = opened
    head = store.get(keys.HEAD_KEY)
    require(isinstance(head, dict) and head.get("organization") == organization, "ORGANIZATION_CHAIN_MEMBERSHIP_UNVERIFIED",
            "Organization HEAD absent or for another organization", repair)
    chain, seen, cursor = [], set(), head.get("receipt_sha256")
    while cursor:
        require(cursor not in seen, "ORGANIZATION_CHAIN_MEMBERSHIP_UNVERIFIED", "chain cycle", repair)
        seen.add(cursor)
        row = store.get(keys.receipt_key(cursor))
        require(isinstance(row, dict), "ORGANIZATION_CHAIN_MEMBERSHIP_UNVERIFIED", f"receipt missing {cursor}", repair)
        body = dict(row)
        claimed = body.pop("receipt_sha256", None)
        require(claimed == cursor and sha(body) == cursor and row.get("organization") == organization,
                "ORGANIZATION_CHAIN_MEMBERSHIP_UNVERIFIED", f"receipt does not recompute {cursor}", repair)
        chain.append(row)
        cursor = row.get("previous_receipt_sha256")
    chain.reverse()
    require(bool(chain) and chain[0].get("previous_receipt_sha256") is None, "ORGANIZATION_CHAIN_MEMBERSHIP_UNVERIFIED",
            "chain not rooted", repair)
    return chain


def verify_grant_source(opened: Any, receipt: dict[str, Any], issuer: str, consumer: Any) -> dict[str, Any]:
    """The retained source of the GRANTED receipt, read back through the existing Organization verifier.

    organization_batch_custody.verified_organization_source_receipt binds the receipt to its
    source_transition_sha256 and transition id, reads the exact source bytes the Organization append
    retained, and recomputes their digest and schema (aggregate_repo_transition.verify_source). The
    source must then be the allocator's own repository receipt recording this grant. A chain that only
    recomputes is not enough. What this establishes is the recorded issuer evidence, never authenticated
    custody (readback_custody_basis is reported beside it), and it authorizes nothing.

    A verifier refusal keeps the verifier's own failed_predicate and travels verbatim as
    organization_readback_refusal. The source's evidence must equal the receipt's boundary_evidence on
    every key consume_org_claim_allocator_request.record_transition carries into it (CARRIED, and
    CARRIED_IF_RECORDED by presence and value), not only the fence, task and disposition.
    """
    repair = ("project a GRANTED receipt whose exact source receipt the Organization ledger retains "
              "(source-receipts/), as aggregate_transition recorded it")
    require(opened is not None, "ORGANIZATION_CHAIN_MEMBERSHIP_UNVERIFIED", "no Organization ledger supplied", repair)
    resident = str(ROOT / "resident-runtime")
    if resident not in sys.path:
        sys.path.insert(0, resident)
    custody = importlib.import_module("organization_batch_custody")
    try:
        row, source = custody.verified_organization_source_receipt(
            opened[0], receipt["receipt_sha256"], state_receipt_sha256=receipt.get("source_transition_sha256"),
            expected_transition_id=receipt.get("source_transition_id"))
    except custody.OrganizationReceiptRefused as exc:
        raise Refusal("GRANT_SOURCE_RECEIPT_UNVERIFIED", f"{exc.disposition} {exc.failed_predicate}: {exc.detail}",
                      repair, failed_predicate=exc.failed_predicate, readback_refusal=exc.refusal()) from exc
    ev, recorded = receipt["boundary_evidence"], source.get("evidence") or {}
    hb = source.get("hb_reference") or {}
    mismatched = [name for name, ok in (
        ("schema", source.get("schema") == SOURCE_RECEIPT_SCHEMA),
        ("repository", source.get("repository") == issuer),
        ("transition_id", source.get("transition_id") == receipt["source_transition_id"]),
        ("transition_class", source.get("transition_class") == GRANTED),
        *((f"evidence.{key}", recorded.get(key) == ev.get(key)) for key in ("disposition", "task_id", "fencing_token")),
        *((f"evidence.{key}", recorded.get(key) == ev.get(key)) for key in consumer.CARRIED
          if key not in ("disposition", "task_id", "fencing_token")),
        *((f"evidence.{key}", (key in recorded, recorded.get(key)) == (key in ev, ev.get(key)))
          for key in consumer.CARRIED_IF_RECORDED),
        ("hb_reference", isinstance(hb.get("epoch"), int) and not isinstance(hb.get("epoch"), bool)
         and hb.get("derived_from_clock") is False),
    ) if not ok]
    require(not mismatched, "GRANT_SOURCE_ISSUER_EVIDENCE_MISMATCH",
            f"retained source {receipt['source_transition_sha256']} does not record this grant: {mismatched}",
            f"project only a grant the allocator recorded in {issuer} with its carrier epoch; re-run the allocator")
    return {"source_transition_sha256": row["source_transition_sha256"], "source_repository": issuer,
            "organization_readback": "VERIFIED",
            "organization_readback_custody_basis": custody.readback_custody_basis(row)}


# --- the transition
def validate_request(root: Path, request: Any) -> dict[str, Any]:
    fix = f"commit a {REQUEST_SCHEMA} manifest under {REQUESTS}/ (contracts/worker-claim-grant-projection-transition.v1.json)"
    errors = _schema_errors(request, load(ROOT / REQUEST_SCHEMA_PATH))
    require(not errors, "PROJECTION_REQUEST_SCHEMA_INVALID", "; ".join(errors[:8]), fix)
    require(isinstance(request["organization_receipt"], dict), "PROJECTION_REQUEST_SCHEMA_INVALID",
            "organization_receipt must be the receipt object", fix)
    return request


def verify_grant(root: Path, request: dict[str, Any], chain: list[dict[str, Any]], floor: dict[str, Any]) -> dict[str, Any]:
    receipt = request["organization_receipt"]
    body = dict(receipt)
    claimed = body.pop("receipt_sha256", None)
    require(claimed == request["organization_receipt_sha256"] and sha(body) == claimed, "GRANT_RECEIPT_DIGEST_MISMATCH",
            "inline receipt bytes do not recompute to organization_receipt_sha256",
            "copy the GRANTED receipt byte-for-byte from the Organization ledger")
    ev = receipt.get("boundary_evidence") or {}
    allocator_task = request["allocator_task_id"]
    fence = ev.get("fencing_token")
    require(receipt.get("schema") == ORG_RECEIPT_SCHEMA and ev.get("operation") == GRANTED and ev.get("disposition") == "ALLOW"
            and ev.get("task_id") == allocator_task and isinstance(fence, int) and not isinstance(fence, bool),
            "RECEIPT_NOT_A_CLAIM_GRANT", f"receipt is not an {GRANTED} ALLOW for {allocator_task}",
            "project only an ORGANIZATION_WORKER_CLAIM_GRANTED receipt for the manifest's allocator task")
    label = ev.get("custody_authentication", CUSTODY_AUTHENTICATION)
    require(type(label) is str and label == CUSTODY_AUTHENTICATION, "GRANT_CUSTODY_AUTHENTICATION_OVERSTATED",
            f"grant boundary_evidence.custody_authentication is {label!r}, not {CUSTODY_AUTHENTICATION!r}",
            "the Organization chain proves hash-chain continuity only; project a grant the allocator recorded as such")
    require(receipt.get("source_transition_id") == f"ORGANIZATION-WORKER-CLAIM-GRANTED-{allocator_task}-G{fence}",
            "RECEIPT_NOT_A_CLAIM_GRANT", "source_transition_id does not name this grant and fence",
            "use the receipt the allocator appended for this grant")
    require(fence > floor["fence"], "FENCE_AT_OR_BELOW_PROVENANCE_FLOOR",
            f"fence {fence} <= provenance floor {floor['fence']} ({floor['provenance']})",
            "a grant fence must exceed the immutable provenance floor; re-run the allocator")
    hb = receipt.get("hb_reference") or {}
    require(isinstance(hb.get("epoch"), int) and not isinstance(hb.get("epoch"), bool) and hb.get("derived_from_clock") is False,
            "GRANT_EPOCH_NOT_CARRIER_SUPPLIED", "receipt hb_reference is absent or derived from a host clock",
            "the allocator appends the grant with the carrier hb_epoch (aggregate_transition hb_epoch=...), then re-request")
    digests = [row["receipt_sha256"] for row in chain]
    require(claimed in digests, "ORGANIZATION_CHAIN_MEMBERSHIP_UNVERIFIED", "grant receipt is not on the verified chain",
            "project a receipt read back from the designated Organization ledger")
    later = chain[digests.index(claimed) + 1:]
    superseding = [r["receipt_sha256"] for r in later
                   if (r.get("boundary_evidence") or {}).get("task_id") == allocator_task
                   and (r.get("boundary_evidence") or {}).get("operation") == GRANTED]
    require(not superseding, "GRANT_SUPERSEDED_ON_CHAIN", f"a later grant for {allocator_task} exists: {superseding[:1]}",
            "project the latest grant for the task")
    task_path = root / "tasks" / f"{allocator_task}.json"
    require(task_path.is_file(), "ALLOCATOR_TASK_UNRESOLVED", f"tasks/{allocator_task}.json absent",
            "materialize the allocator task projection")
    task = load(task_path)
    require(task.get("canonical_task_record") == f"data/canonical-task-records/{request['canonical_task_id']}.json",
            "ALLOCATOR_TASK_UNRESOLVED", "allocator task does not project the manifest's canonical task",
            "name the canonical task the allocator task's canonical_task_record points at")
    return {"fence": fence, "epoch": hb["epoch"], "evidence": ev}


def derive(root: Path, request: dict[str, Any], opened: Any) -> tuple[dict[str, bytes], dict[str, Any]]:
    validate_request(root, request)
    consumer = _module("projection_allocator_consumer", "scripts/consume_org_claim_allocator_request.py")
    try:
        floor = consumer.provenance_floor(root)
    except Exception as exc:  # ClaimFailClosed carries its own predicate
        raise Refusal("FENCE_FLOOR_UNVERIFIED", str(exc), "restore tasks/TASK-2026-0012.json predecessor_provenance") from exc
    organization = load(root / ORG_CONTRACT)["organization"]
    chain = read_chain(opened, organization)
    grant = verify_grant(root, request, chain, floor)
    source = verify_grant_source(opened, request["organization_receipt"], load(root / REPO_CONTRACT)["repository"],
                                 consumer)

    registry_bytes = (root / WORKER_REGISTRY).read_bytes()
    registry = json.loads(registry_bytes)
    generation = registry.get("generation")
    goal, fence, digest = request["canonical_task_id"], grant["fence"], request["organization_receipt_sha256"]
    rows = [r for r in registry.get("tasks", []) if r.get("task_id") == goal or r.get("goal_id") == goal]
    require(len(rows) <= 1, "WORKER_REGISTRY_TASK_AMBIGUOUS", f"{len(rows)} rows for {goal}", "resolve the duplicate rows")
    evidence = {
        "canonical_task_id": goal, "allocator_task_id": request["allocator_task_id"],
        "organization_receipt_sha256": digest, "fencing_token": fence, "fence_domain": FENCE_DOMAIN,
        "carrier_epoch": grant["epoch"], "provenance_floor_fence": floor["fence"],
        "predecessor_worker_registry_generation": generation,
        "predecessor_worker_registry_sha256": "sha256:" + hashlib.sha256(registry_bytes).hexdigest(),
        "organization_head_sha256": chain[-1]["receipt_sha256"],
        "custody_authentication": CUSTODY_AUTHENTICATION,
        **source,
    }
    if rows and (rows[0].get("assignment_timer") or {}).get("grant_receipt_sha256") == digest:
        evidence.update(successor_worker_registry_generation=generation, replayed=True)
        # Idempotent replay: the same receipt changes nothing, whatever the generation has since become.
        return {WORKER_REGISTRY: registry_bytes}, evidence
    require(isinstance(generation, int) and generation == request["observed_worker_registry_generation"],
            "WORKER_REGISTRY_GENERATION_NOT_OBSERVED_TIP",
            f"manifest observed {request['observed_worker_registry_generation']!r}, registry is {generation!r}",
            "re-read control/worker-registry.json and set observed_worker_registry_generation")
    require(not rows or (rows[0].get("claim_id") is None and rows[0].get("state") not in {"ACTIVE", "IN_PROGRESS", "RUNNING", PROJECTED_STATE}),
            "TASK_ALREADY_HELD_IN_WORKER_REGISTRY", f"{goal} already carries claim {rows[0].get('claim_id') if rows else None}",
            "release or retire the existing WorkerCoordinator claim through its own transition first")
    reissued = [r.get("task_id") for r in registry.get("tasks", [])
                if (r.get("assignment_timer") or {}).get("fence_domain") == FENCE_DOMAIN
                and (r.get("assignment_timer") or {}).get("fencing_token") == fence]
    require(not reissued, "FENCE_REISSUED", f"allocator fence {fence} already projected for {reissued}",
            "a fence is projected once; repair the Organization claim chain")

    successor = copy.deepcopy(registry)
    successor_generation = max(generation + 1, fence + 1)
    successor["generation"] = successor_generation
    ev = grant["evidence"]
    row = {
        "archive_eligible": False,
        "archive_reason_codes": [],
        "assignment_timer": {
            "allocator_task_id": request["allocator_task_id"],
            "claim_scope_sha256": ev.get("claim_scope_sha256"),
            "custody_authentication": CUSTODY_AUTHENTICATION,
            "fence_domain": FENCE_DOMAIN,
            "fencing_token": fence,
            "grant_receipt_sha256": digest,
            "organization_head_sha256": ev.get("organization_head_sha256"),
            "start_epoch": grant["epoch"],
        },
        "block_ref": None,
        "claim_id": request["organization_receipt"]["source_transition_id"],
        "cost_basis_ref": None,
        "evidence_refs": [f"StegVerse-Labs/.github:refs/stegverse/organization-ledger:receipts/{digest.split(':', 1)[1]}.json"],
        "executor_binding": "UNBOUND",
        "external_entity_job_ref": None,
        "goal_id": goal,
        "handoff_ref": None,
        "heartbeat_timing": None,
        "last_checkpoint_ref": None,
        "lease": None,
        "state": PROJECTED_STATE,
        "task_id": goal,
        "worker_id": None,
        "worker_instance_id": None,
    }
    if rows:
        successor["tasks"][registry["tasks"].index(rows[0])] = {**rows[0], **row}
    else:
        successor["tasks"].append(row)
    evidence.update(successor_worker_registry_generation=successor_generation, replayed=False,
                    generation_rule="max(generation + 1, fence + 1)")
    return {WORKER_REGISTRY: dump(successor)}, evidence


def projected_rows(registry: Any) -> dict[str, Any]:
    """Rows this transition owns: an allocator-domain fence or the projected state, keyed canonically."""
    require(isinstance(registry, dict) and isinstance(registry.get("tasks"), list), "PROJECTION_INTERNAL_ERROR",
            "worker registry is not an object with a tasks list", "restore control/worker-registry.json")
    owned = {}
    for index, row in enumerate(registry["tasks"]):
        require(isinstance(row, dict), "PROJECTION_INTERNAL_ERROR", f"worker registry row {index} is not an object",
                "restore control/worker-registry.json")
        timer = row.get("assignment_timer")
        if (isinstance(timer, dict) and timer.get("fence_domain") == FENCE_DOMAIN) or row.get("state") == PROJECTED_STATE:
            owned[canon(row).decode()] = row
    return owned


def guard(base: Path, head: Path) -> dict[str, Any]:
    """A head that changes control/worker-registry.json without a projection manifest.

    Projected rows (fence_domain ORGANIZATION_CLAIM_ALLOCATOR, or state
    CLAIM_GRANTED_PROJECTED) are written only by `apply` from a committed
    manifest, so such an edit may not add, change or remove one. Rows of any
    other writer are outside this transition and pass unchanged.
    """
    mode = "guard"
    request_bytes = b""
    try:
        before = projected_rows(json.loads((base / WORKER_REGISTRY).read_bytes()))
        after = projected_rows(json.loads((head / WORKER_REGISTRY).read_bytes()))
        added = sorted(str(after[k].get("task_id")) for k in after.keys() - before.keys())
        removed = sorted(str(before[k].get("task_id")) for k in before.keys() - after.keys())
        require(not added and not removed, "PROJECTED_ROW_WITHOUT_MANIFEST",
                f"projected rows changed without a manifest: added/changed {added}, removed/changed {removed}",
                f"commit a {REQUEST_SCHEMA} manifest under {REQUESTS}/ and write the row with python {ENTRYPOINT} apply")
        return receipt({}, request_bytes, mode, "ALLOW",
                       {"projected_rows_unchanged": len(after), "worker_registry": WORKER_REGISTRY}, {})
    except Refusal as refusal:
        return receipt({}, request_bytes, mode, "FAIL_CLOSED", refusal=refusal)
    except Exception as exc:
        return receipt({}, request_bytes, mode, "FAIL_CLOSED",
                       refusal=Refusal("PROJECTION_INTERNAL_ERROR", f"{type(exc).__name__}: {exc}",
                                       "restore a readable control/worker-registry.json on both trees"))


def receipt(request: Any, request_bytes: bytes, mode: str, disposition: str, evidence: dict[str, Any] | None = None,
            outputs: dict[str, bytes] | None = None, refusal: Refusal | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema": RECEIPT_SCHEMA,
        "transition": "WORKER_CLAIM_GRANT_PROJECTION",
        "mode": mode,
        "request_id": request.get("request_id") if isinstance(request, dict) else None,
        "request_sha256": "sha256:" + hashlib.sha256(request_bytes).hexdigest(),
        "disposition": disposition,
        "authority_effect": AUTHORITY_EFFECT,
        "workercoordinator_domain_fence_minted": False,
        "allocator_fence_reissued": False,
        "generation_lowered": False,
        "clock_read": False,
        "organization_ledger_appended": False,
    }
    if evidence is not None:
        body["evidence"] = evidence
    if outputs is not None:
        body["derived_files"] = {p: "sha256:" + hashlib.sha256(d).hexdigest() for p, d in sorted(outputs.items())}
    if refusal is not None:
        body.update({"failure_code": refusal.predicate, "failed_predicate": refusal.failed_predicate, "detail": refusal.detail,
                     "required_evidence_or_repair": refusal.repair,
                     "retry_entrypoint": f"{WORKFLOW} / python {ENTRYPOINT} {mode}",
                     "owning_existing_goal": OWNING_GOAL, "next_attempt": NEXT_ATTEMPT, "consequence_committed": False})
        if refusal.readback_refusal is not None:
            body["organization_readback_refusal"] = refusal.readback_refusal
    return body


def run(mode: str, request_path: Path, base: Path, head: Path | None = None, org_ledger: str | None = None) -> dict[str, Any]:
    request_bytes = request_path.read_bytes()
    try:
        request = json.loads(request_bytes)
    except json.JSONDecodeError as exc:
        return receipt({}, request_bytes, mode, "FAIL_CLOSED",
                       refusal=Refusal("PROJECTION_REQUEST_SCHEMA_INVALID", f"not JSON: {exc}", "commit valid JSON"))
    try:
        opened = open_store(org_ledger)
        outputs, evidence = derive(base, request, opened)
        if mode == "apply":
            target = head or base
            for rel, data in outputs.items():
                (target / rel).write_bytes(data)
        elif mode == "verify":
            assert head is not None
            diverged = [rel for rel, data in outputs.items() if not (head / rel).is_file() or (head / rel).read_bytes() != data]
            require(not diverged, "PROJECTION_BYTES_DIVERGE", f"successor differs from the derivation at {diverged}",
                    f"replace hand edits with the output of python {ENTRYPOINT} apply on the live base")
        return receipt(request, request_bytes, mode, "ALLOW", evidence, outputs)
    except Refusal as refusal:
        return receipt(request, request_bytes, mode, "FAIL_CLOSED", refusal=refusal)
    except Exception as exc:  # any unexpected failure is still a six-field refusal
        return receipt(request, request_bytes, mode, "FAIL_CLOSED",
                       refusal=Refusal("PROJECTION_INTERNAL_ERROR", f"{type(exc).__name__}: {exc}",
                                       "inspect the receipt detail and repair the input or the transition"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", choices=("plan", "apply", "verify", "guard"))
    parser.add_argument("--request", type=Path)
    parser.add_argument("--base", type=Path, default=ROOT)
    parser.add_argument("--head", type=Path)
    parser.add_argument("--org-ledger", help="Organization ledger locator, e.g. git+<repo>#refs/stegverse/organization-ledger")
    parser.add_argument("--receipt-out", type=Path)
    args = parser.parse_args(argv)
    if args.mode in ("verify", "guard") and args.head is None:
        parser.error(f"{args.mode} needs --head")
    if args.mode == "guard":
        body = guard(args.base.resolve(), args.head.resolve())
    else:
        if args.request is None:
            parser.error(f"{args.mode} needs --request")
        body = run(args.mode, args.request, args.base.resolve(), args.head.resolve() if args.head else None, args.org_ledger)
    text = json.dumps(body, indent=2, sort_keys=True) + "\n"
    if args.receipt_out:
        args.receipt_out.write_text(text, encoding="utf-8")
    (sys.stdout if body["disposition"] == "ALLOW" else sys.stderr).write(text)
    return 0 if body["disposition"] == "ALLOW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
