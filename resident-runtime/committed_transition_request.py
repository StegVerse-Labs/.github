#!/usr/bin/env python3
"""Committed transition requests: the push-to-main intake of the organization ledger writer.

Action is by manifest. A request committed under `.stegverse/transition-requests/`
(schema stegverse.organization-transition-request/v1) is the state transition
that starts a run of `.github/workflows/organization-ledger-transition.yml`; the
run takes every input from that request. Ported from StegVerse-org/.github's
writer (organization-ledger-transition.yml, manifest_directed_run_inputs.py) and
adapted to this organization's own ingress,
resident-runtime/organization_manifest_ingress.py.

- `validate`: every request of the push is checked before anything is appended.
  It names `owning_existing_goal` and `standing`, carries exactly one manifest
  form (`build_manifest` arguments, or the exact `manifest` with its
  `expected_canonical_manifest_sha256`), and supplies `hb_epoch` under the
  kernel's shared rule (org-kernel/kernel.py::supplied_epoch_failure); no
  clock is read for it. One invalid request refuses the whole push.
- A request that declares `mesh_root`, or whose process this boundary binds to
  egress (org-runtime/interlock-intr.json), is deferred and not received: this
  writer binds no mesh, and receiving it would only record its emission as
  refused and spend the request. A deferral is reported, not failed.
- `build`: the pinned SDK Manifest Builder builds the manifest, or the exact
  manifest is submitted unchanged only when it reproduces its digest.
- `ingress-result` and `confirm`: the ingress disposition, and the receipts it
  recorded, read back from a fresh fetch of the published ref.

Every non-ALLOW outcome is printed as one line of JSON carrying the six fields.
Non-authorizing: this resolves inputs and reports; the ingress decides and the
organization ledger records.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable, Mapping

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "stegverse.organization-transition-request/v1"
REQUEST_DIR = ".stegverse/transition-requests/"
RETRY_ENTRYPOINT = ".github/workflows/organization-ledger-transition.yml"
OWNING_EXISTING_GOAL = "StegVerse-Labs/.github#2897 / StegVerse-org/.github#162 P0-runtime-and-custody"
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _kernel():
    spec = importlib.util.spec_from_file_location("org_kernel_intake", ROOT / "org-kernel" / "kernel.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def refused(failure_code: str, failed_predicate: str, repair: str, next_attempt: str,
            *, disposition: str = "FAIL_CLOSED", **detail: Any) -> dict[str, Any]:
    return {"disposition": disposition, "failure_code": failure_code, "failed_predicate": failed_predicate,
            "required_evidence_or_repair": repair, "retry_entrypoint": RETRY_ENTRYPOINT,
            "owning_existing_goal": OWNING_EXISTING_GOAL, "next_attempt": next_attempt,
            "consequence_committed": False, "authority_effect": "NONE_INPUT_RESOLUTION_ONLY", **detail}


def emit(record: Mapping[str, Any]) -> None:
    print(json.dumps(record, sort_keys=True))


def load(path: Path) -> dict[str, Any]:
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError("request is not a JSON object")
    return document


def request_process(request: Mapping[str, Any]) -> Any:
    """The processing capability a committed request declares, or None."""
    if isinstance(request.get("build_manifest"), dict):
        return request["build_manifest"].get("process")
    manifest = request.get("manifest")
    processing = manifest.get("processing") if isinstance(manifest, dict) else None
    return processing.get("capability") if isinstance(processing, dict) else None


def egress_bound_processes(boundary: Mapping[str, Any]) -> set[Any]:
    egress = boundary.get("egress") or {}
    return {binding.get("profile_id") for binding in egress.get("capability_destination_bindings") or []
            if isinstance(binding, dict)}


def validate(path: str, request: Any, *, egress_bound: set[Any],
             epoch_failure: Callable[[Any], Any]) -> dict[str, Any] | None:
    """None when the request is receivable; otherwise its six-field record.

    A record with "deferred": true is not a failure of the run.
    """
    fix = "commit a corrected successor request under " + REQUEST_DIR
    if not (path.startswith(REQUEST_DIR) and path.endswith(".json") and ".." not in path):
        return refused("TRANSITION_REQUEST_PATH_INVALID", "REQUEST_IS_A_COMMITTED_TRANSITION_REQUEST",
                       "a JSON file directly under " + REQUEST_DIR, fix, request=path)
    if not isinstance(request, dict):
        return refused("TRANSITION_REQUEST_UNREADABLE", "COMMITTED_TRANSITION_REQUEST_IS_A_JSON_OBJECT",
                       "commit the request as a JSON object", fix, request=path)
    if request.get("schema") != SCHEMA:
        return refused("TRANSITION_REQUEST_SCHEMA_INVALID", "REQUEST_SCHEMA_IS_ORGANIZATION_TRANSITION_REQUEST_V1",
                       "declare schema " + SCHEMA, fix, request=path)
    request_id = request.get("request_id")
    if not (isinstance(request_id, str) and _TOKEN.match(request_id)):
        return refused("TRANSITION_REQUEST_ID_INVALID", "REQUEST_ID_IS_ONE_VISIBLE_TOKEN",
                       "declare request_id as one token of [A-Za-z0-9._-]", fix, request=path)
    goal = request.get("owning_existing_goal")
    if not (isinstance(goal, str) and goal.strip()):
        return refused("TRANSITION_REQUEST_GOAL_ABSENT", "REQUEST_NAMES_ITS_OWNING_EXISTING_GOAL",
                       "declare owning_existing_goal: the existing goal this transition belongs to", fix,
                       request=path, request_id=request_id)
    if not (isinstance(request.get("standing"), dict) and request["standing"]):
        return refused("TRANSITION_REQUEST_STANDING_ABSENT", "REQUEST_DECLARES_ITS_STANDING",
                       "declare standing (mode, node_ref and the predecessor key) as an object", fix,
                       request=path, request_id=request_id)
    if ("build_manifest" in request) == ("manifest" in request):
        return refused("TRANSITION_REQUEST_MANIFEST_FORM_INVALID", "REQUEST_CARRIES_EXACTLY_ONE_MANIFEST_FORM",
                       "declare either build_manifest arguments or an exact manifest, not both or neither", fix,
                       request=path, request_id=request_id)
    failure = epoch_failure(request.get("hb_epoch"))
    if failure is not None:
        code, detail = failure
        return refused(code, "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH",
                       "declare hb_epoch as ASCII digits with value >= 32 (" + detail + "); no clock is read for it",
                       fix, request=path, request_id=request_id)
    if "mesh_root" in request:
        return refused("TRANSITION_REQUEST_DEFERRED_MESH_NOT_BOUND", "WRITER_BINDS_THE_DECLARED_MESH",
                       "this writer binds no mesh; nothing was received, recorded or spent",
                       "receive it once this writer binds a declared mesh_root", deferred=True,
                       request=path, request_id=request_id, owning_existing_goal_of_request=goal)
    if request_process(request) in egress_bound:
        return refused("TRANSITION_REQUEST_DEFERRED_EGRESS_WITHOUT_MESH", "EGRESS_BOUND_REQUEST_HAS_A_MESH",
                       "its process leaves this organization and no mesh is bound; nothing was received, "
                       "recorded or spent", "receive it once this writer binds a declared mesh_root",
                       deferred=True, request=path, request_id=request_id, owning_existing_goal_of_request=goal)
    return None


def committed_manifest(request: Mapping[str, Any], *, build: Callable[..., Any],
                       canonical_of: Callable[[Any], str]) -> dict[str, Any]:
    """The manifest one committed request submits, built or exact."""
    fix = "commit a corrected successor request under " + REQUEST_DIR
    request_id = request.get("request_id")
    if "build_manifest" in request:
        try:
            manifest = build(**request["build_manifest"])
            canonical = canonical_of(manifest)
        except (TypeError, ValueError) as exc:
            return refused("TRANSITION_REQUEST_NOT_BUILDABLE", "BUILD_MANIFEST_ARGUMENTS_BUILD_A_MANIFEST",
                           "build_manifest arguments the pinned SDK Manifest Builder accepts", fix,
                           request_id=request_id, detail=str(exc)[:300])
        return {"disposition": "ALLOW", "manifest": manifest, "canonical_manifest_sha256": canonical,
                "source": "BUILT_BY_PINNED_SDK"}
    manifest, expected = request.get("manifest"), request.get("expected_canonical_manifest_sha256")
    if not isinstance(manifest, dict) or not (isinstance(expected, str) and _SHA256.match(expected)):
        return refused("EXACT_MANIFEST_UNBOUND", "EXACT_MANIFEST_NAMES_ITS_CANONICAL_DIGEST",
                       "an exact manifest object with expected_canonical_manifest_sha256 (64 lowercase hex)",
                       fix, request_id=request_id)
    try:
        canonical = canonical_of(manifest)
    except (TypeError, ValueError) as exc:
        return refused("EXACT_MANIFEST_NOT_ADMISSIBLE", "EXACT_MANIFEST_IS_A_VALID_INGRESS_MANIFEST",
                       "a manifest the pinned SDK admits at ingress", fix, request_id=request_id,
                       detail=str(exc)[:300])
    if canonical != expected:
        return refused("EXACT_MANIFEST_DIGEST_MISMATCH", "EXACT_MANIFEST_REPRODUCES_ITS_CANONICAL_DIGEST",
                       "the unchanged manifest whose canonical digest is " + expected,
                       "commit the exact frozen manifest unchanged", request_id=request_id, observed=canonical)
    return {"disposition": "ALLOW", "manifest": manifest, "canonical_manifest_sha256": canonical,
            "source": "EXACT_COMMITTED_MANIFEST"}


def ingress_outcome(name: str, result: Any) -> tuple[dict[str, Any], bool]:
    """The ingress result's summary line, and whether the run continues.

    A DENY or FAIL_CLOSED the ingress recorded on the ledger is a disposition
    and is published; only an ingress that recorded nothing fails the run.
    """
    if not isinstance(result, dict) or "disposition" not in result:
        return refused("INGRESS_RESULT_ABSENT", "INGRESS_WRITES_ITS_RESULT",
                       "organization_manifest_ingress.py wrote no result; nothing is known to be recorded",
                       "re-run the push once the ingress writes --out", request=name), False
    receipt = result.get("organization_receipt_sha256") or result.get("refusal_organization_receipt_sha256")
    if result["disposition"] == "ALLOW":
        return {"disposition": "ALLOW", "request": name, "organization_receipt_sha256": receipt,
                "transition_replayed": result.get("transition_replayed")}, True
    record = refused("INGRESS_" + str(result["disposition"]),
                     str(result.get("failed_predicate") or "INGRESS_DISPOSITION_IS_ALLOW"),
                     "a request that satisfies the failed predicate (" + str(result.get("detail")) + ")",
                     "commit a successor request once the failed predicate is repaired",
                     disposition=str(result["disposition"]), request=name, organization_receipt_sha256=receipt,
                     recorded=receipt is not None)
    return record, receipt is not None


def _digest(value: Any) -> str:
    return str(value or "").removeprefix("sha256:")


def confirm(readback: Mapping[str, Any], results: list[tuple[str, Any]]) -> list[dict[str, Any]]:
    """Six-field records for every recorded receipt the fresh read does not hold."""
    if readback.get("disposition") != "ALLOW":
        return [refused("INTAKE_READBACK_NOT_ALLOW", "ORGANIZATION_LEDGER_READS_BACK",
                        str(readback.get("required_evidence_or_repair") or "the published ref did not read back"),
                        "re-run the push; the ledger is the evidence, not this run")]
    chain = {_digest(row.get("receipt_sha256")) for row in readback.get("chain") or []}
    missing = []
    for name, result in results:
        if not isinstance(result, dict):
            continue
        receipt = result.get("organization_receipt_sha256") or result.get("refusal_organization_receipt_sha256")
        if receipt and _digest(receipt) not in chain:
            missing.append(refused("INTAKE_RECEIPT_NOT_ON_PUBLISHED_REF", "RECORDED_RECEIPT_READS_BACK",
                                   "receipt " + str(receipt) + " is not on the fresh fetch of the ref",
                                   "re-run the push; an exact replay completes it", request=name))
    return missing


def _sdk() -> tuple[Callable[..., Any], Callable[[Any], str]]:
    from stegverse.manifest_builder import build_manifest
    from stegverse.manifest_contract import validate_ingress_manifest
    spec = importlib.util.spec_from_file_location("ingress", ROOT / "resident-runtime" / "organization_manifest_ingress.py")
    ingress = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ingress)

    def canonical_of(manifest: Any) -> str:
        validate_ingress_manifest(manifest)
        return ingress.derive_execution_request(manifest, ingress.boundary())["canonical_manifest_sha256"]
    return build_manifest, canonical_of


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    v = sub.add_parser("validate")
    v.add_argument("--requests", type=Path, required=True)
    v.add_argument("--receivable-out", type=Path, required=True)
    b = sub.add_parser("build")
    b.add_argument("--request", type=Path, required=True)
    b.add_argument("--out", type=Path, required=True)
    r = sub.add_parser("ingress-result")
    r.add_argument("--result", type=Path, required=True)
    c = sub.add_parser("confirm")
    c.add_argument("--readback", type=Path, required=True)
    c.add_argument("--results", type=Path, required=True)
    args = parser.parse_args(argv)

    if args.command == "validate":
        boundary = json.loads((ROOT / "org-runtime" / "interlock-intr.json").read_text(encoding="utf-8"))
        bound, epoch_failure = egress_bound_processes(boundary), _kernel().supplied_epoch_failure
        receivable, invalid = [], False
        for path in [line.strip() for line in args.requests.read_text(encoding="utf-8").splitlines() if line.strip()]:
            try:
                request: Any = load(Path(path))
            except (OSError, ValueError):
                request = None
            record = validate(path, request, egress_bound=bound, epoch_failure=epoch_failure)
            if record is None:
                receivable.append(path)
            else:
                emit(record)
                invalid = invalid or not record.get("deferred")
        if invalid:
            # One invalid request refuses the push before anything is appended.
            args.receivable_out.write_text("", encoding="utf-8")
            return 1
        args.receivable_out.write_text("".join(p + "\n" for p in receivable), encoding="utf-8")
        print(json.dumps({"disposition": "ALLOW", "receivable": receivable}, sort_keys=True))
        return 0
    if args.command == "build":
        request = load(args.request)
        build, canonical_of = _sdk()
        resolved = committed_manifest(request, build=build, canonical_of=canonical_of)
        if resolved["disposition"] != "ALLOW":
            emit(resolved)
            return 1
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "manifest.json").write_text(json.dumps(resolved["manifest"], indent=2, sort_keys=True) + "\n")
        (args.out / "standing.json").write_text(json.dumps(request["standing"], indent=2, sort_keys=True) + "\n")
        (args.out / "hb_epoch").write_text(str(request["hb_epoch"]))
        (args.out / "canonical_manifest_sha256").write_text(resolved["canonical_manifest_sha256"])
        print(json.dumps({"disposition": "ALLOW", "request_id": request["request_id"], "source": resolved["source"],
                          "canonical_manifest_sha256": resolved["canonical_manifest_sha256"]}, sort_keys=True))
        return 0
    if args.command == "ingress-result":
        try:
            result: Any = json.loads(args.result.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            result = None
        record, proceed = ingress_outcome(args.result.parent.name, result)
        emit(record)
        return 0 if proceed else 1
    try:
        readback: Any = json.loads(args.readback.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        readback = {}
    results = []
    for path in sorted(args.results.glob("*/ingress.json")):
        try:
            results.append((path.parent.name, json.loads(path.read_text(encoding="utf-8"))))
        except (OSError, ValueError):
            results.append((path.parent.name, None))
    missing = confirm(readback, results)
    for record in missing:
        emit(record)
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
