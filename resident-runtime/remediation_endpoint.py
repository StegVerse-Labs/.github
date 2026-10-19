#!/usr/bin/env python3
"""`stegverse-labs.remediation` -- StegHealer classifies a remediation lane that crossed into this organization.

A non-ALLOW carries its remediation fork (NODE_INGRESS_SETTLED_SPECIFICATION §8).
The fork's route is calculated from where the need for remediation was
recognized, the manifested path and the direct route to StegHealer, and every
organization crossing on it is an Interlock/InTr egress followed by an
Interlock/InTr ingress. The lane arrives here through this organization's InTr
ingress, addressed to this service, which is the route's last hop.

StegHealer (StegVerse-Labs/StegVerse-Healer) is a StegVerse-Labs repository, so
the classification is made here, by its classifier, loaded only from the
anonymous checkout of the commit `org-runtime/remediation-classifier.json`
pins. The classification is non-authorizing: it names RESUBMIT, RE_MANIFEST or
governance review and grants nothing. It returns to the origin on the
acknowledgement, and the governed decision on it is separate. StegHealer never
alters, changes or creates a manifest.

The classification is the transition that occurred here, so it is recorded here
at both ledger levels with the transition class `REMEDIATION_CLASSIFIED`, into
the chain it judged. A lane this endpoint cannot classify is still recorded:
FAIL_CLOSED, naming why. Nothing is guessed and nothing waits.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
ORGANIZATION = "StegVerse-Labs"
SERVICE_ID = "stegverse-labs.remediation"
REQUEST_SCHEMA = "stegverse.org-remediation-classification-request/v1"
RESULT_SCHEMA = "stegverse.org-remediation-classification/v1"
TRANSITION_CLASS = "REMEDIATION_CLASSIFIED"
PIN = ROOT / "org-runtime/remediation-classifier.json"


def canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canon(value)).hexdigest()


def _module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def classifier_pin() -> dict[str, Any]:
    return json.loads(PIN.read_text(encoding="utf-8"))


def load_classifier(pin: Mapping[str, Any] | None = None, root: Path | None = None):
    """StegHealer's classifier from the verified pinned checkout, or None with the reason."""
    pin = pin or classifier_pin()
    checkout = Path(root or ROOT) / pin["materialized_path"]
    module_path, _, function = str(pin["classifier"]).partition("::")
    if not (checkout / module_path).is_file():
        return None, "REMEDIATION_CLASSIFIER_NOT_MATERIALIZED"
    head = subprocess.run(["git", "-C", str(checkout), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=False).stdout.strip()
    if head != pin["commit"]:
        return None, "REMEDIATION_CLASSIFIER_NOT_AT_PINNED_COMMIT"
    classify = getattr(_module("steghealer_remediation_intake", checkout / module_path), function, None)
    if not callable(classify):
        return None, "REMEDIATION_CLASSIFIER_ENTRY_ABSENT"
    return classify, None


def route_arrives_here(route: Any, origin: Any) -> str | None:
    """None when the calculated route ends at this service and its crossing from `origin` was InTr."""
    if not isinstance(route, Mapping):
        return "REMEDIATION_ROUTE_ABSENT"
    hops = route.get("direct_route_to_steghealer")
    if not isinstance(hops, list) or not hops:
        return "REMEDIATION_ROUTE_HAS_NO_HOPS"
    last = hops[-1]
    if (last.get("from"), last.get("to"), last.get("crossing")) != (ORGANIZATION, SERVICE_ID, "INTERNAL_ENDPOINT"):
        return "REMEDIATION_ROUTE_DOES_NOT_END_AT_THIS_SERVICE"
    if origin != ORGANIZATION:
        crossing = {(h.get("from"), h.get("to"), h.get("crossing")) for h in hops if isinstance(h, Mapping)}
        if ((origin, ORGANIZATION, "INTERLOCK_INTR_EGRESS") not in crossing
                or (origin, ORGANIZATION, "INTERLOCK_INTR_INGRESS") not in crossing):
            return "REMEDIATION_ROUTE_CROSSING_FROM_ORIGIN_IS_NOT_INTERLOCK_INTR"
    return None


def classify(packet: Mapping[str, Any], *, loader=load_classifier) -> dict[str, Any]:
    """Classify the remediation lane a packet carries; never authorize anything."""
    if (packet.get("destination") or {}).get("service") != SERVICE_ID:
        raise SystemExit("wrong-remediation-destination")
    body = (packet.get("payload") or {}).get("body") or {}
    request = body.get("remediation_request")
    origin = (packet.get("origin") or {}).get("org")
    result: dict[str, Any] = {
        "schema": RESULT_SCHEMA,
        "service_id": SERVICE_ID,
        "classifying_organization": ORGANIZATION,
        "classifier": classifier_pin()["classifier"],
        "classifier_repository": classifier_pin()["repository"],
        "classifier_commit": classifier_pin()["commit"],
        "request_packet_id": packet.get("packet_id"),
        "origin_organization": origin,
        "sdk_request_sha256": body.get("sdk_request_sha256"),
        "remediation_request_sha256": body.get("remediation_request_sha256"),
        "remediation_route_sha256": body.get("remediation_route_sha256"),
        "classification_grants_authority": False,
        "governance_disposition": "NOT_EVALUATED",
        "external_side_effect": False,
        "authority_effect": "NONE_CLASSIFICATION_ONLY",
    }
    refusal = None
    if body.get("schema") != REQUEST_SCHEMA:
        refusal = "REMEDIATION_REQUEST_SCHEMA_NOT_RECEIVED:" + str(body.get("schema"))
    elif not isinstance(request, dict):
        refusal = "REMEDIATION_REQUEST_ABSENT"
    elif hashlib.sha256(canon(request)).hexdigest() != body.get("remediation_request_sha256"):
        refusal = "REMEDIATION_REQUEST_DIGEST_MISMATCH"
    elif (request.get("remediation_route") or {}).get("route_sha256") != body.get("remediation_route_sha256"):
        refusal = "REMEDIATION_ROUTE_DIGEST_MISMATCH"
    else:
        refusal = route_arrives_here(request.get("remediation_route"), origin)
    if refusal is None:
        classifier, refusal = loader()
        if classifier is not None:
            try:
                classification = classifier(request["non_allow"], request["original_request"])
            except (ValueError, KeyError, TypeError) as exc:
                refusal = "REMEDIATION_NOT_CLASSIFIABLE:" + str(exc)[:200]
            else:
                if classification.get("execution_authority_granted") is not False:
                    refusal = "REMEDIATION_CLASSIFICATION_AUTHORITY_ESCALATION"
                else:
                    return {**result, "disposition": "ALLOW", "state": TRANSITION_CLASS,
                            "classification": classification,
                            "suggested_action": classification.get("suggested_action")}
    return {**result, "disposition": "FAIL_CLOSED", "state": "REMEDIATION_NOT_CLASSIFIED",
            "classification": None, "reason": refusal}


def record(packet: Mapping[str, Any], outcome: Mapping[str, Any], *,
           hb_epoch: int | None = None) -> dict[str, str]:
    """Append the classification at both ledger levels: repository first, organization consuming it.

    `hb_epoch` is the carrier's heartbeat epoch, supplied by the caller; both
    receipts carry that exact reference. It is checked by the shared rule as
    given: absent or invalid is the six-field refusal, raised before either
    ledger is touched, as governance_endpoint.record does; no clock is read.
    """
    kernel = _module("org_kernel_record_epoch", ROOT / "org-kernel/kernel.py")
    refused = kernel.writer_epoch_refusal(
        hb_epoch, retry_entrypoint="resident-runtime/remediation_endpoint.py::record (hb_epoch=)")
    if refused is not None:
        raise SystemExit(json.dumps(refused, sort_keys=True))
    transition_id = TRANSITION_CLASS + ":" + hashlib.sha256(str(packet.get("packet_id")).encode()).hexdigest()[:24]
    predecessor = "sha256:" + str(outcome.get("remediation_request_sha256"))
    successor = sha(dict(outcome))
    evidence = {"request_packet_id": packet.get("packet_id"),
                "origin_organization": outcome.get("origin_organization"),
                "classification": dict(outcome)}
    completed = subprocess.run(
        [sys.executable, str(ROOT / ".stegverse/transition-ledger/emit.py"),
         "--transition-id", transition_id, "--transition-class", TRANSITION_CLASS,
         "--predecessor-state-sha256", predecessor, "--successor-state-sha256", successor,
         "--evidence-json", json.dumps(evidence, sort_keys=True), "--authority-effect", "NONE",
         "--hb-epoch", str(hb_epoch)],
        cwd=ROOT, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise SystemExit("remediation-classification-repository-receipt-failed:"
                         + (completed.stderr or completed.stdout).strip()[-300:])
    repository_receipt = json.loads(completed.stdout.strip().splitlines()[-1])
    organization_ledger = _module("aggregate_repo_transition", ROOT / "resident-runtime/aggregate_repo_transition.py")
    organization_receipt = organization_ledger.aggregate_transition(
        repository_receipt, org_transition_class="REPO_STATE_PROPAGATION",
        predecessor_org_state_sha256=predecessor, successor_org_state_sha256=successor,
        boundary_evidence={"service_id": SERVICE_ID, "transition_class": TRANSITION_CLASS,
                           "disposition": outcome.get("disposition"),
                           "request_packet_id": packet.get("packet_id")},
        authority_effect="NONE", hb_epoch=hb_epoch)
    return {"repository_receipt_sha256": repository_receipt["receipt_sha256"],
            "organization_receipt_sha256": organization_receipt["receipt_sha256"]}


def cli_hb_epoch(text: str | None) -> tuple[int | None, dict[str, Any] | None]:
    """--hb-epoch as typed, checked by the kernel's shared rule: (epoch, None) or (None, refusal).

    Absent is HB_EPOCH_NOT_SUPPLIED and anything coerced is HB_EPOCH_INVALID,
    as writer_epoch_refusal states them; no clock is read.
    """
    kernel = _module("org_kernel_cli_epoch", ROOT / "org-kernel/kernel.py")
    refused = kernel.writer_epoch_refusal(text, retry_entrypoint="resident-runtime/remediation_endpoint.py (--hb-epoch)")
    if refused is not None:
        return None, refused
    return int(text), None  # admitted as ASCII digits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--hb-epoch", type=str, default=None,
                        help="carrier heartbeat epoch, supplied by the caller as ASCII digits; "
                             "required, never sampled here")
    args = parser.parse_args()
    hb_epoch, epoch_refused = cli_hb_epoch(args.hb_epoch)
    if epoch_refused is not None:
        # Nothing is classified, appended or written (no --out); the exit is 1.
        print(json.dumps(epoch_refused, sort_keys=True))
        return 1
    # Read before, and outside, the own-state fault handling: an unreadable packet
    # is the terminal six-field CLI_INPUT_INVALID (F-INPUT-TRACE), nothing written.
    kernel = _module("org_kernel_cli_input", ROOT / "org-kernel/kernel.py")
    packet = kernel.cli_input_json(args.packet, "--packet", retry_entrypoint="resident-runtime/remediation_endpoint.py")
    outcome = classify(packet)
    receipts = record(packet, outcome, hb_epoch=hb_epoch)
    result = {**outcome, **receipts, "records_authority": "ORGANIZATION_RECORDS_ONLY"}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    # Every failure is six fields on stdout, never a traceback (F-WRITER-TRACE).
    sys.exit(_module("org_kernel_writer_cli", ROOT / "org-kernel/kernel.py").run_writer_cli(
        main, retry_entrypoint="resident-runtime/remediation_endpoint.py"))
