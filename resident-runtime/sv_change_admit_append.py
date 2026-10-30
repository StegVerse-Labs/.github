#!/usr/bin/env python3
"""``sv_change_admit`` -- record the SV_CHANGE_SUPERSEDE -> SV_CHANGE_VERIFY -> SV_CHANGE_ADMIT outcome for one change.

Authoring-Session: p1-ecosystem-ai-lane (StegVerse-org/.github#163; Lane D FAIL_CLOSED StegVerse-org/.github#167
c6513778290; Lane B owns this writer).

``resident-runtime/sv_work_items.py::transition("SV_CHANGE_ADMIT")`` is a library function whose ``record()`` hands every
outcome, refusals included, to "the existing repository emitter". Nothing called it. This operation is that caller, added to
the existing writer (``organization-ledger-transition.yml``, push to main, no new workflow, no dispatch, no schedule):

  * it evaluates the lifecycle on the committed request with the evaluator pinned for ``sv_check_receipt`` (P1 f28c3a76,
    ``sv_check_receipt_append.p1_readers``; one rule, not a copy): SV_CHANGE_SUPERSEDE (predecessor -> NATIVE successor),
    SV_CHANGE_VERIFY, SV_CHANGE_ADMIT;
  * it never invents evidence. The push receipts and the ledger head are READ from the declared ledger, never taken from the
    request: each declared push range is looked up as SV_PUSH_RECEIPT_APPEND:<range id> and passed on only if the ledger holds
    it; an unrecorded range stays unobserved, so branch-writer derivation fails closed. Required-check receipts, sign-offs and
    the resolved SV_ISSUEs are not supplied by this operation, so a change that needs them is refused by the evaluator, and
    that refusal is the outcome (nothing here turns a gap into ALLOW);
  * the outcome is recorded whatever it is (``record()``): one repository receipt (``transition_class`` SV_CHANGE_ADMIT,
    ``$.evidence`` = the lifecycle result with its six fields, the change record, the chain of step dispositions and what was
    observed) and one organization receipt naming it. A non-ALLOW outcome is a recorded fact that confers nothing;
  * exactly one admit per change: the transition id is ``<change_id>:SV_CHANGE_ADMIT`` (sv_work_items.record), so a second
    request for the same change, byte-identical or not, is a six-field FAIL_CLOSED SV_CHANGE_ADMIT_ALREADY_RECORDED and appends
    nothing; the lookup and the append share one exclusive two-level section under ORGANIZATION_LEDGER_LOCK;
  * the ledger of the organization that owns the repository (CHANGE_BINDS_TARGET_REPOSITORY_LEDGER): a change whose
    ``target_repository`` is not owned by this ledger's organization is refused before any write;
  * time is supplied: the request epoch (an int) must pass org-kernel/kernel.py::supplied_epoch_failure and equal the
    NATIVE successor's own hb_epoch (the push-receipt tie rule). No clock, no network, no key, no dependency.

Refusals before any write are six-field FAIL_CLOSED with consequence_committed false. The operation's own ``disposition`` is
ALLOW exactly when the pair was appended; ``admit_disposition`` is the lifecycle outcome that was recorded. Stdlib only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import importlib.util
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]

OPERATION_ID = "sv_change_admit"
TRANSITION_CLASS = "SV_CHANGE_ADMIT"
PROFILE_ID = "org-ledger-writer"
LEDGER_REF = "refs/stegverse/organization-ledger"
LEDGER_OWNER = "StegVerse-Labs"  # the organization whose ledger this checkout writes (CHANGE_BINDS_TARGET_REPOSITORY_LEDGER)
RESULT_SCHEMA = "stegverse.org-sv-change-admit-append-result/v1"
READBACK_SCHEMA = "stegverse.org-sv-change-admit-readback/v1"
OWNING_GOAL = "StegVerse-org/.github#163 (WORK_ITEMS_ARE_TASK_REGISTRY_NATIVE)"
RETRY = "resident-runtime/sv_change_admit_append.py::append_change_admit"
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")
ADMISSION_FIELDS = {"predicate_digest", "corpus_head", "actor_session", "change_commits", "push_ranges"}
CHANGE_ID = re.compile(r"^svc:[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
REGISTRY_PATH = "data/canonical-task-registry.json"


def _module(name: str, relative: str):
    if name in sys.modules:
        return sys.modules[name]
    runtime = str(ROOT / "resident-runtime")
    if runtime not in sys.path:
        sys.path.insert(0, runtime)
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# The same private instances the sv_check_receipt and sv_push_receipt operations append through: one declared store.
pa = _module("sv_push_receipt_append_for_change_admit", "resident-runtime/sv_push_receipt_append.py")
ingress = pa.ingress
sha = ingress.sha
SHARED_RULE_SHA256 = pa.SHARED_RULE_SHA256
_check = pa._check


def refusal(code: str, predicate: str, repair: str, next_attempt: str, **detail: Any) -> dict[str, Any]:
    return {"schema": RESULT_SCHEMA, "operation": OPERATION_ID, "disposition": "FAIL_CLOSED",
            "failure_code": code, "failed_predicate": predicate, "required_evidence_or_repair": repair,
            "retry_entrypoint": RETRY, "owning_existing_goal": OWNING_GOAL, "next_attempt": next_attempt,
            "consequence_committed": False, "authority_effect": "NONE_REFUSAL_ONLY", **detail}


def _epoch_refusal(successor: Mapping[str, Any], hb_epoch: Any) -> dict[str, Any] | None:
    """The supplied-epoch rule of the sibling operations (one shared rule, pinned): the request epoch is an int that passes
    org-kernel/kernel.py::supplied_epoch_failure and equals the NATIVE successor's own hb_epoch (ASCII digits)."""
    kernel = pa.kernel
    why = "supply the request epoch as an integer and carry the same supplied epoch in the successor's hb_epoch; both must pass " \
          "org-kernel/kernel.py::supplied_epoch_failure (SHARED_RULE_SHA256 " + SHARED_RULE_SHA256 + ")"
    if pa.KERNEL_RULE_SHA256 != SHARED_RULE_SHA256:
        return refusal("HB_EPOCH_SOURCE_UNOBSERVED", pa.EPOCH_SOURCE_PREDICATE, why, "after the shared rule is the pinned one; nothing was written",
                       detail="org-kernel/kernel.py::supplied_epoch_failure is not the pinned shared rule",
                       shared_rule_sha256=SHARED_RULE_SHA256)
    mine = successor.get("hb_epoch")
    for side, value in (("request epoch", hb_epoch), ("successor hb_epoch", mine)):
        if pa._unobserved_value(value):
            return refusal("HB_EPOCH_SOURCE_UNOBSERVED", pa.EPOCH_SOURCE_PREDICATE, why,
                           "after a supplied epoch is observed on both; nothing was written",
                           detail=side + " is absent, null, '', 'null' or " + pa.UNKNOWN_SENTINEL, side=side, value=repr(value), shared_rule_sha256=SHARED_RULE_SHA256)
    detail = None
    bad = kernel.supplied_epoch_failure(hb_epoch)
    if bad is not None or type(hb_epoch) is not int:
        detail = "request epoch " + repr(hb_epoch) + ": " + (bad[0] + ": " + bad[1] if bad else "not an int")
    else:
        bad = kernel.supplied_epoch_failure(mine)
        if bad is not None or not isinstance(mine, str):
            detail = "successor hb_epoch " + repr(mine) + ": " + (bad[0] + ": " + bad[1] if bad else "not ASCII text")
        elif int(mine) != hb_epoch:
            detail = "the successor's epoch differs from the request epoch"
    if detail is None:
        return None
    out = refusal(pa.EPOCH_MISMATCH, "SUCCESSOR_HB_EPOCH_EQUALS_REQUEST_HB_EPOCH",
                  "the request's hb_epoch (an int) equals the successor's hb_epoch (ASCII digits), both passing "
                  "org-kernel/kernel.py::supplied_epoch_failure", "commit the ingest request again with the successor's own supplied epoch; "
                  "nothing was written", detail=detail, shared_rule_sha256=SHARED_RULE_SHA256, hb_epoch=repr(hb_epoch), successor_hb_epoch=repr(mine))
    out["disposition"] = "DENY"
    return out


def _stored_epoch_refusal(row: Any, hb_epoch: int) -> dict[str, Any] | None:
    bad = pa._stored_epoch_refusal(row, hb_epoch)
    if bad is None:
        return None
    return {**bad, "schema": RESULT_SCHEMA, "operation": OPERATION_ID, "retry_entrypoint": RETRY, "owning_existing_goal": OWNING_GOAL}


def transition_id(change_id: str) -> str:
    """sv_work_items.record(): ``<change_id>:<transition_class>``. One admit per change."""
    return change_id + ":" + TRANSITION_CLASS


def _owned_by_this_ledger(repository: Any) -> bool:
    return isinstance(repository, str) and repository.startswith(LEDGER_OWNER + "/") and repository.count("/") == 1


def request_problem(predecessor: Any, successor: Any, admission: Any) -> dict[str, Any] | None:
    """The request's shape, before any evaluation (never a lifecycle result)."""
    if not (isinstance(predecessor, dict) and isinstance(successor, dict) and isinstance(admission, dict)):
        return refusal("SV_CHANGE_ADMIT_REQUEST_MALFORMED", "REQUEST_CARRIES_PREDECESSOR_SUCCESSOR_AND_ADMISSION",
                       "predecessor and successor as one stegverse.sv_change.v1 object each and admission as one object",
                       "commit the ingest request again with all three objects; nothing was written")
    if set(admission) != ADMISSION_FIELDS:
        return refusal("SV_CHANGE_ADMIT_REQUEST_MALFORMED", "ADMISSION_HAS_EXACTLY_THE_DECLARED_FIELDS",
                       "admission takes exactly " + ", ".join(sorted(ADMISSION_FIELDS)), "commit the ingest request again; nothing was written",
                       found=sorted(admission))
    cc = admission["change_commits"]
    ranges = admission["push_ranges"]
    bad = []
    if not (isinstance(admission["predicate_digest"], str) and DIGEST.match(admission["predicate_digest"])):
        bad.append("predicate_digest")
    if not (isinstance(admission["corpus_head"], str) and GIT_SHA.match(admission["corpus_head"])):
        bad.append("corpus_head")
    if not (isinstance(admission["actor_session"], str) and admission["actor_session"].strip()):
        bad.append("actor_session")
    if not (isinstance(cc, dict) and set(cc) == {"base_commit", "head_commit"}
            and all(isinstance(v, str) and GIT_SHA.match(v) for v in cc.values())):
        bad.append("change_commits")
    if not (isinstance(ranges, list) and ranges and all(isinstance(r, dict) and set(r) == set(pa.RANGE_FIELDS)
                                                       and all(isinstance(v, str) and v for v in r.values()) for r in ranges)):
        bad.append("push_ranges")
    if not (isinstance(successor.get("change_id"), str) and CHANGE_ID.match(successor["change_id"])):
        bad.append("successor.change_id")
    if bad:
        return refusal("SV_CHANGE_ADMIT_REQUEST_MALFORMED", "ADMISSION_FIELDS_ARE_WELL_FORMED",
                       "predicate_digest sha256:<64 hex>, corpus_head 40 hex, actor_session text, change_commits {base_commit, head_commit} "
                       "40 hex, push_ranges a non-empty list of {repository, ref, old_sha, new_sha}, and the successor's change_id "
                       "svc:<64 hex>; malformed: " + ", ".join(bad), "commit the ingest request again; nothing was written", malformed=bad)
    if not _owned_by_this_ledger(successor.get("target_repository")):
        return refusal("SV_CHANGE_TARGET_NOT_OWNED_BY_THIS_LEDGER", "CHANGE_BINDS_TARGET_REPOSITORY_LEDGER",
                       "an admit is recorded once, on the ledger of the organization that owns the change's target repository ("
                       + LEDGER_OWNER + " here); the successor targets " + repr(successor.get("target_repository")),
                       "send the request to the writer of the owning organization; nothing was written",
                       target_repository=successor.get("target_repository"))
    if successor.get("record_mode") != "NATIVE":
        return refusal("SV_CHANGE_ADMIT_SUCCESSOR_NOT_NATIVE", "ADMITTED_RECORDS_ARE_NATIVE",
                       "the successor is a NATIVE stegverse.sv_change.v1 record (a MIGRATED_HISTORICAL record is never admitted; "
                       "evaluate_admission refuses it as HISTORICAL_RECORD_NOT_ADMISSIBLE)",
                       "commit the ingest request again with the NATIVE successor; nothing was written",
                       record_mode=successor.get("record_mode"))
    if predecessor.get("target_repository") != successor.get("target_repository"):
        return refusal("SV_CHANGE_SUPERSEDE_CROSSES_REPOSITORIES", "CHANGE_BINDS_TARGET_REPOSITORY_LEDGER",
                       "predecessor and successor name the same target_repository", "commit the ingest request again; nothing was written",
                       predecessor=predecessor.get("target_repository"), successor=successor.get("target_repository"))
    return None


def ledger_head_commit(store: Any) -> str | None:
    """The git commit the declared organization-ledger ref points at (the store's own committed tip): observed, not supplied."""
    try:
        tip = store._tip()
    except Exception:  # noqa: BLE001 - an unreadable ledger is reported as an unobserved base
        return None
    return tip if isinstance(tip, str) and GIT_SHA.match(tip) else None


def registry_generation() -> int | None:
    """The task-registry generation of this checkout (the pushed main commit): observed."""
    try:
        value = json.loads((ROOT / REGISTRY_PATH).read_text(encoding="utf-8")).get("generation")
    except (OSError, UnicodeDecodeError, ValueError):
        return None
    return value if type(value) is int else None


def _step(result: Mapping[str, Any]) -> dict[str, Any]:
    keep = ("transition_class", "disposition") + SIX_FIELDS
    out = {k: result.get(k) for k in keep if k in result or k in ("transition_class", "disposition")}
    rec = result.get("record") or {}
    return out | {"record_sha256": sha(rec), "lifecycle_state": rec.get("lifecycle_state"), "superseded_by": rec.get("superseded_by")}


def evaluate(predecessor: dict[str, Any], successor: dict[str, Any], admission: Mapping[str, Any], push_receipts: list[dict[str, Any]],
             current_base: Mapping[str, Any], hb_epoch: int) -> dict[str, Any]:
    """The lifecycle over the supplied records and the observed ledger facts. Returns {result, chain}: `result` is the
    SV_CHANGE_ADMIT outcome (ALLOW, DENY or FAIL_CLOSED, six fields on every non-ALLOW), `chain` the step dispositions."""
    wi = _check.p1_readers()
    epoch = str(hb_epoch)
    commits = dict(admission["change_commits"])
    writer_ctx = {"push_receipts": push_receipts, "change_commits": commits}
    supersede = wi.transition("SV_CHANGE_SUPERSEDE", predecessor, hb_epoch=epoch, context={"successor": successor})
    verify = wi.transition("SV_CHANGE_VERIFY", successor, hb_epoch=epoch, context={**writer_ctx, "resolved_issues": []})
    state = verify["record"]
    admit_ctx = {**writer_ctx, "resolved_issues": [], "current_base": dict(current_base),
                 "predicate_digest": admission["predicate_digest"], "corpus_head": admission["corpus_head"],
                 "actor_session": admission["actor_session"]}
    admitted = wi.transition("SV_CHANGE_ADMIT", state, hb_epoch=epoch, context=admit_ctx)
    return {"result": admitted, "chain": [_step(supersede), _step(verify), _step(admitted)]}


def _duplicate(change_id: str, prior: Mapping[str, Any]) -> dict[str, Any]:
    evidence = prior.get("evidence") if isinstance(prior.get("evidence"), dict) else {}
    return refusal("SV_CHANGE_ADMIT_ALREADY_RECORDED", "ONE_ADMIT_PER_CHANGE",
                   "the ledger already holds the admit outcome for " + change_id + " (" + str(evidence.get("disposition")) + "); a second "
                   "request for the same change is a duplicate and is not minted, identical or not. The recorded outcome confers "
                   "nothing it did not already confer",
                   "none for this change: the recorded receipt is the evidence; a NATIVE successor on a newer base is a new change_id "
                   "and may be requested; nothing was written", appended=False, change_id=change_id,
                   recorded_repository_receipt_sha256=prior.get("receipt_sha256"),
                   recorded_disposition=evidence.get("disposition"), recorded_failure_code=evidence.get("failure_code"))


def append_change_admit(predecessor: Any, successor: Any, admission: Any, *, hb_epoch: Any) -> dict[str, Any]:
    """Evaluate the lifecycle for `successor` and record the outcome once per change."""
    bad = request_problem(predecessor, successor, admission) or _epoch_refusal(successor, hb_epoch)
    if bad is not None:
        return bad
    if _check.P1_PIN_FAILURE is not None:
        return refusal("P1_CONTRACT_PINS_UNVERIFIED", "VENDORED_P1_FILES_MATCH_THE_PINNED_CONTRACT_MANIFEST",
                       "re-vendor P1's files against data/sv-work-items/contract-pins.json (sha256 " + _check.P1_MANIFEST_SHA256 + ")",
                       "after the vendored files match the pinned manifest; nothing was written", detail=_check.P1_PIN_FAILURE)
    try:
        rl, org = ingress.repository_ledger, ingress.organization_ledger
        rl.repository_store()
        org.organization_store()
    except (Exception, SystemExit) as exc:  # noqa: BLE001 - every resolver refusal is reported, none is retried
        return refusal("ORGANIZATION_LEDGER_LOCATION_UNRESOLVED", "WRITER_LEDGER_LOCATIONS_ARE_SUPPLIED",
                       "supply the repository and organization ledger locations the writer workflow declares",
                       "after the ledger locations resolve; nothing was written", detail=f"{type(exc).__name__}: {exc}")
    change_id = successor["change_id"]
    tid = transition_id(change_id)
    wi = None
    try:
        with ingress._two_level_atomic():
            store = rl.repository_store()
            head = store.get(rl.ledger_store.HEAD_KEY)
            prior = rl.recorded(store, head, tid, TRANSITION_CLASS)
            if prior is not None:
                return _duplicate(change_id, prior)
            # Observed under the lock, from the declared ledger and this checkout: never from the request.
            ledger_head, generation = ledger_head_commit(store), registry_generation()
            if ledger_head is None or generation is None:
                return refusal("CURRENT_BASE_UNOBSERVED", "BASE_IS_CURRENT",
                               "the writer reads the ledger ref commit (" + LEDGER_REF + " in the declared store) and "
                               + REGISTRY_PATH + " generation itself; one of them is unreadable",
                               "after both are readable in the writer checkout; nothing was written",
                               ledger_head=ledger_head, registry_generation=generation)
            found, unrecorded = [], []
            for rng in admission["push_ranges"]:
                row = rl.recorded(store, head, pa.transition_id(rng), pa.TRANSITION_CLASS)
                evidence = row.get("evidence") if isinstance(row, dict) else None
                if isinstance(evidence, dict) and pa.push_payload(evidence) is None and pa.range_key(evidence) == dict(rng):
                    found.append(evidence)
                else:
                    unrecorded.append(dict(rng))
            current_base = {"registry_generation": generation, "ledger_head": ledger_head}
            run = evaluate(predecessor, successor, admission, found, current_base, hb_epoch)
            wi = _check.p1_readers()
            observed = {"current_base": current_base, "push_receipts_read_from_ledger": [r["result_sha256"] for r in found],
                        "unrecorded_push_ranges": unrecorded, "predecessor_request_digest": predecessor.get("request_digest"),
                        "predecessor_sha256": sha(predecessor), "admission": dict(admission), "chain": run["chain"],
                        "not_supplied_by_this_operation": ["required-check ledger receipts", "sign-off receipts",
                                                           "resolved SV_ISSUE facts", "base-state readback receipt"]}
            pair: dict[str, Any] = {}

            def append(transition_id_: str, cls: str, pred: str, succ: str, *, evidence: Mapping[str, Any],
                       authority_effect: str, hb_epoch: int) -> dict[str, Any]:  # noqa: ARG001 - authority_effect: the ledger's own NONE
                full = {**evidence, "observed": observed}
                repository_receipt = rl.append(transition_id_, cls, pred, succ, full, "NONE", hb_epoch=hb_epoch, idempotent_on=())
                boundary = {"operation": OPERATION_ID, "profile_id": PROFILE_ID, "change_id": change_id,
                            "target_repository": successor["target_repository"], "transition_id": transition_id_,
                            "admit_disposition": evidence["disposition"], "admit_failure_code": evidence.get("failure_code"),
                            "evidence_sha256": sha(full)}
                organization_receipt = org.aggregate_transition(
                    receipt=repository_receipt, org_transition_class="REPO_STATE_PROPAGATION",
                    predecessor_org_state_sha256=pred, successor_org_state_sha256=succ, boundary_evidence=boundary,
                    authority_effect="NONE", hb_epoch=repository_receipt["hb_reference"]["epoch"])
                pair.update(repository_receipt=repository_receipt, organization_receipt=organization_receipt)
                return pair

            wi.record(run["result"], successor, hb_epoch=hb_epoch, append=append)
    except ValueError as exc:
        return refusal("ORGANIZATION_LEDGER_APPEND_REFUSED", "SV_CHANGE_ADMIT_APPEND_COMPLETES_AT_BOTH_LEVELS",
                       "repair the refusal the ledger reported; the writer publishes only when both receipts exist",
                       "after the ledger refusal is repaired", detail=f"{type(exc).__name__}: {exc}")
    repository, organization = pair["repository_receipt"], pair["organization_receipt"]
    for row in (repository, organization):
        stored = _stored_epoch_refusal(row, hb_epoch)
        if stored is not None:
            stored["consequence_committed"] = "LOCAL_ONLY_NOT_PUBLISHED"  # the writer workflow pushes nothing after a refusal
            return stored
    store_mod = rl.ledger_store
    outcome = run["result"]
    return {
        "schema": RESULT_SCHEMA, "operation": OPERATION_ID, "disposition": "ALLOW", "transition_class": TRANSITION_CLASS,
        "appended": True, "change_id": change_id, "transition_id": tid, "target_repository": successor["target_repository"],
        "admit_disposition": outcome["disposition"], "admit_failure_code": outcome.get("failure_code"),
        "chain": [{"transition_class": s["transition_class"], "disposition": s["disposition"], "failure_code": s.get("failure_code")}
                  for s in run["chain"]],
        "repository_receipt_sha256": repository["receipt_sha256"], "organization_receipt_sha256": organization["receipt_sha256"],
        "organization_receipt_key": store_mod.receipt_key(organization["receipt_sha256"]),
        "repository_receipt_source_key": store_mod.source_key(repository["receipt_sha256"]),
        "evidence_sha256": organization["boundary_evidence"]["evidence_sha256"],
        "hb_epoch": repository["hb_reference"]["epoch"], "observed_current_base": observed["current_base"],
        "unrecorded_push_ranges": unrecorded, "consequence_committed": True, "authority_effect": "NONE",
    }


def bind_change_admit(location: str, result: Mapping[str, Any]) -> dict[str, Any]:
    """Read the appended pair back from `location` (a fresh fetch of the ref): sealed, in place, linked, carrying the lifecycle
    outcome, and the only SV_CHANGE_ADMIT receipt on the repository chain for its change."""
    store_mod = ingress.repository_ledger.ledger_store
    store = store_mod.open_store(store_mod.parse_locator(location))
    org_sha, repo_sha = result.get("organization_receipt_sha256"), result.get("repository_receipt_sha256")
    org = store.get(store_mod.receipt_key(org_sha)) if isinstance(org_sha, str) else None
    repo = store.get(store_mod.source_key(repo_sha)) if isinstance(repo_sha, str) else None
    evidence = repo.get("evidence") if isinstance(repo, dict) else None
    change_id = (evidence.get("record") or {}).get("change_id") if isinstance(evidence, dict) else None
    try:
        repo_store = store_mod.open_store(location + ":repository-ledger/" + repo["repository"])
        same = [r for r in ingress.repository_ledger.chain(repo_store, repo_store.get(store_mod.HEAD_KEY))
                if r.get("transition_class") == TRANSITION_CLASS and r.get("transition_id") == transition_id(str(change_id))]
    except Exception:  # noqa: BLE001 - an unreadable chain is a failed check below
        same = []
    checks = {
        "organization_receipt_sealed": pa._self_verifies(org) and org.get("receipt_sha256") == org_sha,
        "repository_receipt_sealed_beside_it": pa._self_verifies(repo) and repo.get("receipt_sha256") == repo_sha,
        "organization_receipt_names_repository_receipt": isinstance(org, dict) and org.get("repo_receipt_sha256") == repo_sha,
        "operation_is_sv_change_admit": isinstance(org, dict) and (org.get("boundary_evidence") or {}).get("operation") == OPERATION_ID,
        "transition_class_is_sv_change_admit": isinstance(repo, dict) and repo.get("transition_class") == TRANSITION_CLASS,
        "evidence_carries_the_lifecycle_outcome": isinstance(evidence, dict) and evidence.get("disposition") == result.get("admit_disposition")
        and evidence.get("failure_code") == result.get("admit_failure_code"),
        "evidence_is_the_appended_evidence": isinstance(evidence, dict) and sha(evidence) == result.get("evidence_sha256"),
        "exactly_one_admit_for_the_change": len(same) == 1,
        "epoch_supplied_not_clock": all(isinstance(r, dict) and (r.get("hb_reference") or {}).get("derived_from_clock") is False
                                        for r in (org, repo)),
    }
    if not all(checks.values()):
        failed = sorted(k for k, v in checks.items() if not v)
        return {"schema": READBACK_SCHEMA, "disposition": "FAIL_CLOSED", "failure_code": "SV_CHANGE_ADMIT_READBACK_FAILED",
                "failed_predicate": failed[0].upper(), "required_evidence_or_repair": "the fresh fetch must hold the sealed pair: "
                + ", ".join(failed), "retry_entrypoint": "resident-runtime/sv_change_admit_append.py::bind_change_admit",
                "owning_existing_goal": OWNING_GOAL, "next_attempt": "after a fresh fetch of the published ref",
                "checks": checks, "readback_writes": False, "authority_effect": "NONE_READBACK_ONLY"}
    return {"schema": READBACK_SCHEMA, "disposition": "ALLOW", "location": location, "checks": checks, "change_id": change_id,
            "admit_disposition": evidence["disposition"], "admit_failure_code": evidence.get("failure_code"),
            "organization_receipt_sha256": org_sha, "repository_receipt_sha256": repo_sha,
            "readback_writes": False, "authority_effect": "NONE_READBACK_ONLY"}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("append")
    a.add_argument("--predecessor", type=Path, required=True)
    a.add_argument("--successor", type=Path, required=True)
    a.add_argument("--admission", type=Path, required=True)
    a.add_argument("--hb-epoch", required=True, help="supplied epoch, ASCII digits >= 32; never from a clock")
    a.add_argument("--out", type=Path, default=None)
    r = sub.add_parser("readback")
    r.add_argument("--location", required=True)
    r.add_argument("--result", type=Path, required=True)
    r.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    if args.cmd == "append":
        epoch = int(args.hb_epoch) if re.fullmatch(r"[0-9]+", args.hb_epoch or "") else args.hb_epoch
        try:
            parts = [_read_json(p) for p in (args.predecessor, args.successor, args.admission)]
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            out = refusal("SV_CHANGE_ADMIT_REQUEST_MALFORMED", "REQUEST_CARRIES_PREDECESSOR_SUCCESSOR_AND_ADMISSION",
                          "supply the three request parts as JSON objects", "after readable parts are supplied; nothing was written",
                          detail=f"{type(exc).__name__}: {exc}")
        else:
            out = append_change_admit(*parts, hb_epoch=epoch)
    else:
        out = bind_change_admit(args.location, _read_json(args.result))
    text = json.dumps(out, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(json.dumps(out, sort_keys=True))
    return 0 if out.get("disposition") == "ALLOW" else 1


if __name__ == "__main__":
    sys.exit(main())
