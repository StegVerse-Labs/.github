#!/usr/bin/env python3
"""Apply one committed, admitted CanonicalWork projection request on push.

This is the resident trigger for scripts/apply_admitted_canonical_work_projection.py.
A request committed under .stegverse/canonical-work-projection-requests/
(schema stegverse.canonical-work-projection-request/v1) carries the ingress and
consumption receipts the projection consumes, the registry generation the
request was prepared against, and a supplied hb_epoch. The push that lands it
on main starts .github/workflows/canonical-work-projection-trigger.yml, the
same way .stegverse/governance-decision-requests/** starts
organization-governance-decision.yml.

Subcommands:

* evaluate: decide one request. `--mode plan` writes nothing; `--mode apply`
  writes exactly the bytes apply_admitted_canonical_work_projection.py would
  write for the same inputs. Nothing here sets the generation: the projection
  script's own `generation + 1` is the only bump, and the existing generation
  fence (scripts/check_registry_generation_fence.py) must ALLOW it against the
  live registry generation before anything is written.
* record: append the decision (ALLOW or FAIL_CLOSED) as a repository receipt
  and its organization receipt on the declared organization ledger, the way
  resident-runtime/intr_destination_ingress.py records both levels.
* refuse: the six-field FAIL_CLOSED for a later workflow stage (the generation
  fence on the projection commit, or a publish that did not fast-forward).
* readback: confirm both receipts from a fresh fetch of the ledger ref.

Every refusal is `disposition: FAIL_CLOSED` with the six fields. It never
skips, never reads a clock for the epoch, and never edits a registry row by
hand. The authority boundary is the merge that lands the request on main.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REQUEST_DIR = ".stegverse/canonical-work-projection-requests"
REQUEST_SCHEMA = "stegverse.canonical-work-projection-request/v1"
RESULT_SCHEMA = "stegverse.canonical-work-projection-trigger-result/v1"
OWNING_GOAL = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"
RETRY_ENTRYPOINT = (".github/workflows/canonical-work-projection-trigger.yml: push a corrected "
                    "request under " + REQUEST_DIR + "/ (python scripts/canonical_work_projection_trigger.py evaluate)")
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")
ALLOW, FAIL_CLOSED = "ALLOW", "FAIL_CLOSED"
APPLIED_CLASS = "CANONICAL_WORK_PROJECTION_APPLIED"
REFUSED_CLASS = "CANONICAL_WORK_PROJECTION_REFUSED"
REQUEST_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")

MANIFEST_ABSENT = "CANONICAL_WORK_PROJECTION_MANIFEST_ABSENT"
BATCH_NOT_SINGULAR = "CANONICAL_WORK_PROJECTION_BATCH_NOT_SINGULAR"
REQUEST_INVALID = "CANONICAL_WORK_PROJECTION_REQUEST_INVALID"
NOT_ADMITTED = "CANONICAL_WORK_PROJECTION_NOT_ADMITTED"
FENCE_MISMATCH = "REGISTRY_GENERATION_FENCE_MISMATCH"
INTERNAL_ERROR = "CANONICAL_WORK_PROJECTION_TRIGGER_INTERNAL_ERROR"


def _module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


projection = _module("apply_admitted_canonical_work_projection", "scripts/apply_admitted_canonical_work_projection.py")
fence = _module("check_registry_generation_fence", "scripts/check_registry_generation_fence.py")
kernel = _module("kernel", "org-kernel/kernel.py")


def sha_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def serialize(value: dict[str, Any]) -> str:
    # Byte-identical to apply_admitted_canonical_work_projection.main().
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def refusal(code: str, predicate: str, repair: str, next_attempt: str, **evidence: Any) -> dict[str, Any]:
    return {"schema": RESULT_SCHEMA, "disposition": FAIL_CLOSED, "failure_code": code,
            "failed_predicate": predicate, "required_evidence_or_repair": repair,
            "retry_entrypoint": RETRY_ENTRYPOINT, "owning_existing_goal": OWNING_GOAL,
            "next_attempt": next_attempt, "consequence_committed": False,
            "authority_effect": "NONE_REFUSAL_ONLY", "evidence": evidence}


def _relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def load_request(path: Path) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """(request, None) or (None, refusal)."""
    if not path.is_file():
        return None, refusal(MANIFEST_ABSENT, "THE_PUSHED_PROJECTION_REQUEST_IS_PRESENT_AT_THE_PUSHED_COMMIT",
                             f"commit the request at {REQUEST_DIR}/<request_id>.json",
                             "on the next push that adds the request", request_path=str(path))
    try:
        request = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        return None, refusal(REQUEST_INVALID, "REQUEST_IS_A_JSON_OBJECT",
                             "commit the request as one JSON object", "on the next push of a corrected request",
                             request_path=str(path), detail=f"{type(exc).__name__}: {exc}")
    problems = []
    if not isinstance(request, dict):
        return None, refusal(REQUEST_INVALID, "REQUEST_IS_A_JSON_OBJECT", "commit the request as one JSON object",
                             "on the next push of a corrected request", request_path=str(path))
    if request.get("schema") != REQUEST_SCHEMA:
        problems.append("schema")
    rid = request.get("request_id")
    if not isinstance(rid, str) or not REQUEST_ID.match(rid) or path.stem != rid:
        problems.append("request_id (must match the file name)")
    if not isinstance(request.get("task_id"), str) or not request["task_id"]:
        problems.append("task_id")
    gen = request.get("observed_registry_generation")
    if isinstance(gen, bool) or not isinstance(gen, int) or gen < 0:
        problems.append("observed_registry_generation")
    for key in ("ingress_receipt", "consumption_receipt"):
        if not isinstance(request.get(key), dict):
            problems.append(key)
    if request.get("authority_effect") != "NONE_REQUEST_ONLY":
        problems.append("authority_effect (must be NONE_REQUEST_ONLY)")
    if not problems and request["consumption_receipt"].get("task_id") != request["task_id"]:
        problems.append("consumption_receipt.task_id != task_id")
    if problems:
        return None, refusal(REQUEST_INVALID, "REQUEST_DECLARES_EVERY_REQUIRED_FIELD_UNDER_" + REQUEST_SCHEMA.upper(),
                             "fix the request fields: " + ", ".join(problems),
                             "on the next push of a corrected request", request_path=str(path),
                             invalid_fields=problems)
    epoch_failure = kernel.supplied_epoch_failure(request.get("hb_epoch"))
    if epoch_failure is not None:
        code, detail = epoch_failure
        result = refusal(code, kernel.HB_EPOCH_PREDICATE,
                         "carry hb_epoch in the request as ASCII digits with value >= 32; no clock is read",
                         "on the next push of a request carrying a supplied epoch",
                         request_path=str(path), detail=detail)
        result["derived_from_clock"] = False
        return None, result
    return request, None


def already_projected(registry: dict[str, Any], request: dict[str, Any], task_shards: Path) -> bool:
    try:
        _, task, _ = projection.find_source(registry=registry, task_id=request["task_id"], task_shards=task_shards)
    except SystemExit:
        return False
    refs = task.get("runtime_refs") or {}
    ingress = request["ingress_receipt"]
    return (refs.get("materialization_id") == ingress.get("materialization_id")
            and refs.get("request_hash") == ingress.get("request_hash")
            and refs.get("ingress_state") == "INGRESS_ADMITTED")


def evaluate(paths: list[Path], *, registry_path: Path, task_shards: Path, apply: bool) -> dict[str, Any]:
    if not paths:
        return refusal(MANIFEST_ABSENT, "THE_PUSH_ADDS_OR_MODIFIES_ONE_PROJECTION_REQUEST",
                       f"commit exactly one request under {REQUEST_DIR}/", "on the next push that adds a request")
    if len(paths) != 1:
        return refusal(BATCH_NOT_SINGULAR, "ONE_PROJECTION_REQUEST_PER_PUSH",
                       "push each request on its own commit; each takes the next generation",
                       "after the requests are pushed one per push", request_paths=[str(p) for p in paths])
    request, refused = load_request(paths[0])
    if refused is not None:
        return refused
    base = {"request_id": request["request_id"], "task_id": request["task_id"],
            "request_path": _relative(paths[0])}
    try:
        registry_raw = registry_path.read_bytes()
        registry = json.loads(registry_raw)
        live = fence.parse_generation(registry_raw, "the checked-out main")
    except (OSError, ValueError, fence.GenerationUnreadable) as exc:
        return refusal(fence.UNREADABLE, "data/canonical-task-registry.json#generation readable as a non-negative integer",
                       "restore a readable registry; this trigger never edits it by hand",
                       "after the registry is readable", detail=f"{type(exc).__name__}: {exc}", **base)
    base["registry_sha256_before"] = sha_bytes(registry_raw)
    base["live_generation"] = live
    if already_projected(registry, request, task_shards):
        return {"schema": RESULT_SCHEMA, "disposition": ALLOW, "applicability": "REPLAY_ALREADY_PROJECTED",
                "written": False, "authority_effect": "NONE_REPLAY", **base}
    if request["observed_registry_generation"] != live:
        payload = fence.generation_fence_payload(request["observed_registry_generation"], live)
        return refusal(FENCE_MISMATCH,
                       f"request observed_registry_generation ({request['observed_registry_generation']}) == live registry generation ({live})",
                       f"re-prepare the request against the live main generation {live} and push it again",
                       "on the next push of a request prepared at the live generation",
                       session_mutation_generation_fence=payload, **base)
    try:
        source_kind, proposed, shard_path = projection.project(
            registry, request["ingress_receipt"], request["consumption_receipt"], task_shards=task_shards)
    except SystemExit as exc:
        reason = str(exc.code if exc.code is not None else exc)
        return refusal(NOT_ADMITTED, reason.removeprefix("FAIL_CLOSED: "),
                       "commit authentic ingress and consumption receipts for this task "
                       "(apply_admitted_canonical_work_projection.validate_receipts / project_task)",
                       "on the next push of a request carrying admitted receipts", projection_refusal=reason, **base)
    if source_kind == "MONOLITHIC_REGISTRY":
        decided = fence.evaluate_pull_request(int(proposed.get("generation", -1)), live)
        if decided.get("disposition") != ALLOW:
            return refusal(FENCE_MISMATCH, decided.get("failed_predicate", "projected generation == live + 1"),
                           decided.get("required_evidence_or_repair", "re-prepare at the live generation"),
                           decided.get("next_attempt", "on the next push"), fence=decided, **base)
        target = registry_path
        fence_result = {"disposition": ALLOW, "head_generation": decided["head_generation"],
                        "tip_generation": decided["tip_generation"]}
    else:
        target = shard_path
        fence_result = {"disposition": ALLOW, "applicability": "NOT_APPLICABLE",
                        "reason": "sharded projection does not change data/canonical-task-registry.json"}
    text = serialize(proposed)
    if apply:
        Path(target).write_text(text, encoding="utf-8")
    return {"schema": RESULT_SCHEMA, "disposition": ALLOW, "applicability": "PROJECTED",
            "source_kind": source_kind, "target": _relative(Path(target)), "written": apply,
            "projected_sha256": sha_bytes(text.encode("utf-8")),
            "projected_generation": proposed.get("generation") if source_kind == "MONOLITHIC_REGISTRY" else live,
            "generation_fence": fence_result, "generation_set_by": "apply_admitted_canonical_work_projection.project",
            "authority_effect": "CANONICAL_TASK_STATE_PROJECTION_FROM_ADMITTED_INGRESS", **base}


def record(result: dict[str, Any], hb_epoch: Any) -> dict[str, Any]:
    """Append the decision at the repository and organization levels; return both digests."""
    if kernel.supplied_epoch_failure(hb_epoch) is not None:
        raise ValueError("record_requires_a_supplied_hb_epoch")
    repository_ledger = _module("repo_transition_emit", ".stegverse/transition-ledger/emit.py")
    organization_ledger = _module("aggregate_repo_transition", "resident-runtime/aggregate_repo_transition.py")
    disposition = result.get("disposition")
    transition_class = APPLIED_CLASS if disposition == ALLOW else REFUSED_CLASS
    request_id = result.get("request_id") or result.get("evidence", {}).get("request_id") or "unidentified-request"
    evidence = {"request_id": request_id, "disposition": disposition,
                "result_sha256": sha_bytes(json.dumps(result, sort_keys=True).encode("utf-8"))}
    for key in SIX_FIELDS:
        if key in result:
            evidence[key] = result[key]
    for key in ("task_id", "applicability", "target", "projected_sha256", "projected_generation",
                "live_generation", "commit"):
        if key in result:
            evidence[key] = result[key]
    predecessor = result.get("registry_sha256_before") or evidence["result_sha256"]
    successor = result.get("projected_sha256") or predecessor
    epoch = int(str(hb_epoch))
    repository_receipt = repository_ledger.append(
        transition_class + ":" + request_id, transition_class, predecessor, successor, evidence, "NONE",
        hb_epoch=epoch, idempotent_on=("request_id", "disposition", "result_sha256"))
    organization_receipt = organization_ledger.aggregate_transition(
        receipt=repository_receipt, org_transition_class="REPO_STATE_PROPAGATION",
        predecessor_org_state_sha256=predecessor, successor_org_state_sha256=successor,
        boundary_evidence={"operation": transition_class, "request_id": request_id, "disposition": disposition},
        authority_effect="NONE", hb_epoch=repository_receipt["hb_reference"]["epoch"])
    return {"repository_receipt_sha256": repository_receipt["receipt_sha256"],
            "organization_receipt_sha256": organization_receipt["receipt_sha256"],
            "organization_receipt_preserves_repository_receipt":
                organization_receipt.get("repo_receipt_sha256") == repository_receipt["receipt_sha256"],
            "transition_class": transition_class}


def readback(location: str, namespace: str, recorded: dict[str, Any]) -> dict[str, Any]:
    ledger_store = _module("ledger_store", "resident-runtime/ledger_store.py")
    found = {}
    for label, store_location, key in (
            ("repository", f"{location}:{namespace}", "repository_receipt_sha256"),
            ("organization", location, "organization_receipt_sha256")):
        digest = recorded.get(key)
        node = ledger_store.open_store(store_location).get(ledger_store.receipt_key(digest)) if digest else None
        found[label] = isinstance(node, dict) and node.get("receipt_sha256") == digest
    if not all(found.values()):
        return refusal("CANONICAL_WORK_PROJECTION_RECEIPT_NOT_ON_READBACK",
                       "BOTH_RECEIPTS_ARE_ON_THE_FRESHLY_FETCHED_ORGANIZATION_LEDGER_REF",
                       "re-run the trigger; a decision whose receipt is not on the read-back chain is not observed",
                       "on the next run of the trigger", found=found, recorded=recorded)
    return {"schema": RESULT_SCHEMA, "disposition": ALLOW, "readback": found, **recorded}


def emit(result: dict[str, Any], out: str | None) -> int:
    if result.get("disposition") not in (ALLOW, FAIL_CLOSED):
        result = refusal(INTERNAL_ERROR, "the trigger returns ALLOW or FAIL_CLOSED",
                         "fix the trigger; an unexpected disposition is never a pass", "after the fix",
                         disposition_seen=str(result.get("disposition")))
    text = json.dumps(result, indent=2, sort_keys=True, default=str)
    print(text)
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(text + "\n", encoding="utf-8")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(f"### Canonical work projection trigger: {result['disposition']}\n\n")
            if result["disposition"] == FAIL_CLOSED:
                handle.write("| field | value |\n|---|---|\n")
                for key in SIX_FIELDS:
                    handle.write(f"| {key} | {str(result.get(key, '')).replace('|', '/')} |\n")
    if result["disposition"] == FAIL_CLOSED:
        for key in SIX_FIELDS:
            print(f"{key}={result.get(key, '')}", file=sys.stderr)
        return 1
    return 0


def changed_paths(changed_file: str | None, explicit: list[str]) -> list[Path]:
    names = list(explicit)
    if changed_file:
        names += [line.strip() for line in Path(changed_file).read_text(encoding="utf-8").splitlines() if line.strip()]
    return [Path(n) if Path(n).is_absolute() else ROOT / n for n in names]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    ev = sub.add_parser("evaluate")
    ev.add_argument("--mode", choices=("plan", "apply"), required=True)
    ev.add_argument("--changed", help="file listing the request paths the push added or modified")
    ev.add_argument("--request", action="append", default=[])
    ev.add_argument("--registry", default=str(ROOT / "data" / "canonical-task-registry.json"))
    ev.add_argument("--task-shards", default=str(ROOT / "data" / "canonical-task-records"))
    ev.add_argument("--allow-none", action="store_true",
                    help="pull_request validation: no changed request is NOT_APPLICABLE, not a refusal")
    ev.add_argument("--out")
    rc = sub.add_parser("record")
    rc.add_argument("--result", required=True)
    rc.add_argument("--request", help="request carrying the supplied hb_epoch")
    rc.add_argument("--out")
    rf = sub.add_parser("refuse", help="six-field FAIL_CLOSED for a workflow stage (fence on push, publish)")
    rf.add_argument("--decision", required=True, help="the evaluate result this stage refused to publish")
    rf.add_argument("--failure-code", required=True)
    rf.add_argument("--failed-predicate", required=True)
    rf.add_argument("--required-evidence-or-repair", required=True)
    rf.add_argument("--next-attempt", required=True)
    rf.add_argument("--detail-file")
    rf.add_argument("--out")
    rb = sub.add_parser("readback")
    rb.add_argument("--location", required=True)
    rb.add_argument("--namespace", required=True)
    rb.add_argument("--recorded", required=True)
    rb.add_argument("--out")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        if exc.code in (0, None):
            raise
        return emit(refusal(INTERNAL_ERROR, "the trigger arguments parse", "fix the invocation",
                            "after the invocation is fixed", argparse_exit=exc.code), None)
    out = getattr(args, "out", None)
    try:
        if args.command == "evaluate":
            paths = changed_paths(args.changed, args.request)
            if not paths and args.allow_none:
                return emit({"schema": RESULT_SCHEMA, "disposition": ALLOW, "applicability": "NOT_APPLICABLE",
                             "reason": "no projection request changed", "written": False}, out)
            return emit(evaluate(paths, registry_path=Path(args.registry), task_shards=Path(args.task_shards),
                                 apply=args.mode == "apply"), out)
        if args.command == "record":
            result = json.loads(Path(args.result).read_text(encoding="utf-8"))
            hb_epoch = None
            if args.request and Path(args.request).is_file():
                hb_epoch = json.loads(Path(args.request).read_text(encoding="utf-8")).get("hb_epoch")
            epoch_failure = kernel.supplied_epoch_failure(hb_epoch)
            if epoch_failure is not None:
                # No clock is read for an epoch, so a decision without a supplied
                # epoch cannot be stamped; it stays a run-level FAIL_CLOSED.
                return emit(refusal(epoch_failure[0], kernel.HB_EPOCH_PREDICATE,
                                    "the request must carry a supplied hb_epoch for its decision to be recorded",
                                    "on the next push of a request carrying a supplied epoch",
                                    decision=result, ledger_recorded=False), out)
            recorded = record(result, hb_epoch)
            recorded["decision_disposition"] = result.get("disposition")
            return emit({"schema": RESULT_SCHEMA, "disposition": ALLOW, **recorded}, out)
        if args.command == "refuse":
            decision = json.loads(Path(args.decision).read_text(encoding="utf-8"))
            detail = None
            if args.detail_file and Path(args.detail_file).is_file():
                detail = Path(args.detail_file).read_text(encoding="utf-8", errors="replace")[-4000:]
            result = refusal(args.failure_code, args.failed_predicate, args.required_evidence_or_repair,
                             args.next_attempt, decision=decision, detail=detail)
            for key in ("request_id", "task_id", "registry_sha256_before", "live_generation"):
                if key in decision:
                    result[key] = decision[key]
            return emit(result, out)
        recorded = json.loads(Path(args.recorded).read_text(encoding="utf-8"))
        return emit(readback(args.location, args.namespace, recorded), out)
    except Exception as exc:  # an error is never a pass
        return emit(refusal(INTERNAL_ERROR, "the trigger evaluates without an unexpected error",
                            "fix the trigger or its inputs", "after the error is fixed",
                            detail=f"{type(exc).__name__}: {exc}"), out)


if __name__ == "__main__":
    sys.exit(main())
