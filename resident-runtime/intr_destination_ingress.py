#!/usr/bin/env python3
"""``ORGANIZATION_INTR_DESTINATION_INGRESS`` -- acknowledge a purpose-neutral diagnostic.

``intr-destination`` is the capability every organization can advertise so a
peer can address it without a purpose-specific route. Governance stays a
purpose route, bound to the organization that owns the decider. This operation
is the mesh primitive underneath those: a diagnostic crossing arrives, and both
ledger levels record the disposition. The disposition is transition evidence.

The payload is an ``ecosystem.communication``. That is a request class the
transport profile answers, and it carries the ``communication_id`` a closure
correlates on, so an outbound diagnostic can be emitted and closed. The body
schema is ``stegverse.org-intr-destination-diagnostic/v1``. A body that is not
that schema is a refusal, recorded, not an acknowledgement.

``self_close`` records a diagnostic this organization addresses to itself. It
does not read the federation directory and it does not name a peer. Authority
(``authority_effect``) and Time (``hb_reference``) are constraint variables on
the receipts.

The profile name ``InTr:Destination`` is local to this binding. The pinned SDK
baseline does not declare the profile, and the canonical StegOS connector
registry was not readable from the change that added it, so this repository
does not claim StegOS already named it.

The address did not select a processor, standing was already required at
ingress, and this operation does not re-decide either.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]

OPERATION_ID = "ORGANIZATION_INTR_DESTINATION_INGRESS"
REFUSED_CLASS = "ORGANIZATION_INTR_DESTINATION_INGRESS_REFUSED"
OWNER_REPOSITORY = "StegVerse-Labs/.github"
PROFILE_ID = "intr-destination"
PROFILE_NAME = "InTr:Destination"
OPERATION = "DIAGNOSTIC_CROSSING"
PAYLOAD_SCHEMA = "stegverse.org-intr-destination-diagnostic/v1"
RESULT_SCHEMA = "stegverse.org-intr-destination-result/v1"
COMMUNICATION_CLASS = "ecosystem.communication"
ALLOW = "ALLOW"
DENY = "DENY"
FAIL_CLOSED = "FAIL_CLOSED"
ACK_EFFECT = "NONE_DIAGNOSTIC_ACK_ONLY"
REFUSAL_EFFECT = "NONE_REFUSAL_ONLY"
CLOSURE_CLASS = "ORGANIZATION_INTR_DESTINATION_SELF_CLOSURE"
CLOSURE_REFUSED_CLASS = "ORGANIZATION_INTR_DESTINATION_SELF_CLOSURE_REFUSED"
CLOSURE_EFFECT = "NONE_DIAGNOSTIC_SELF_CLOSURE_ONLY"
SELF_CLOSURE_SCHEMA = "stegverse.org-intr-destination-self-closure/v1"


def _module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


repository_ledger = _module("repo_transition_emit", ".stegverse/transition-ledger/emit.py")
organization_ledger = _module("aggregate_repo_transition",
                              "resident-runtime/aggregate_repo_transition.py")


def canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def sha(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canon(value)).hexdigest()


def payload_sha(payload: Any) -> str:
    if isinstance(payload, Mapping):
        return sha(dict(payload))
    return sha(payload)


def shape_refusal(payload: Any) -> tuple[str, str] | None:
    """Why this payload is not a diagnostic this operation acknowledges."""
    if not isinstance(payload, Mapping):
        return ("SUBMISSION_IS_AN_ECOSYSTEM_COMMUNICATION", "payload is not an object")
    if payload.get("message_class") != COMMUNICATION_CLASS:
        return ("SUBMISSION_DECLARES_A_RESPONDED_REQUEST_CLASS",
                str(payload.get("message_class")))
    identifier = payload.get("communication_id")
    if not isinstance(identifier, str) or not identifier.strip():
        return ("SUBMISSION_CARRIES_THE_COMMUNICATION_ID_CLOSURE_CORRELATES_ON",
                repr(identifier))
    body = payload.get("body")
    observed = body.get("schema") if isinstance(body, Mapping) else body
    if not isinstance(body, Mapping) or observed != PAYLOAD_SCHEMA:
        return ("SUBMISSION_BODY_DECLARES_THE_BOUND_PAYLOAD_SCHEMA", str(observed))
    return None


def _evidence(payload: Any, packet_id: str, disposition: str, *,
              failed_predicate: str | None = None, detail: str | None = None,
              closure: str | None = None) -> dict[str, Any]:
    communication_id = payload.get("communication_id") if isinstance(payload, Mapping) else None
    if closure is not None and disposition == ALLOW:
        effect = CLOSURE_EFFECT
    else:
        effect = ACK_EFFECT if disposition == ALLOW else REFUSAL_EFFECT
    record: dict[str, Any] = {
        "profile_id": PROFILE_ID,
        "profile_name": PROFILE_NAME,
        "operation": OPERATION if closure is None else "DIAGNOSTIC_SELF_CLOSURE",
        "receiving_operation": OPERATION_ID,
        "owner_repository": OWNER_REPOSITORY,
        "packet_id": packet_id,
        "communication_id": communication_id if isinstance(communication_id, str) else None,
        "payload_sha256": payload_sha(payload),
        "payload_schema": PAYLOAD_SCHEMA,
        "disposition": disposition,
        "authority_effect": effect,
        "selects_processing": False,
        "purpose_specific_route": False,
        "standing_rechecked_here": False,
    }
    if closure is not None:
        record["closure"] = closure
        record["federation_directory_consulted"] = False
        record["peer_enumerated"] = False
    if failed_predicate is not None:
        record["failed_predicate"] = failed_predicate
        record["detail"] = detail
    return record


def _result(evidence: Mapping[str, Any], appended: Mapping[str, Any] | None, *,
            replayed: bool, received: bool) -> dict[str, Any]:
    disposition = evidence["disposition"]
    acknowledged = disposition == ALLOW and received and evidence.get("closure") is None
    closed = disposition == ALLOW and received and evidence.get("closure") == "SELF"
    result = {
        "schema": SELF_CLOSURE_SCHEMA if evidence.get("closure") == "SELF" else RESULT_SCHEMA,
        "organization": organization_ledger.C["organization"],
        "receiving_operation": OPERATION_ID,
        "owner_repository": OWNER_REPOSITORY,
        "profile_id": PROFILE_ID,
        "profile_name": PROFILE_NAME,
        "operation": evidence["operation"],
        "disposition": disposition,
        "received": received and evidence.get("closure") is None,
        "communication_acknowledged": acknowledged,
        "communication_id": evidence.get("communication_id"),
        "payload_schema": PAYLOAD_SCHEMA,
        "payload_sha256": evidence["payload_sha256"],
        "transition_replayed": replayed,
        "standing_rechecked_here": False,
        "selects_processing": False,
        "purpose_specific_route": False,
        "authority_effect": evidence["authority_effect"],
    }
    if evidence.get("closure") is not None:
        result["closure"] = evidence["closure"]
        result["closed"] = closed
        result["federation_directory_consulted"] = False
        result["peer_enumerated"] = False
    if evidence.get("failed_predicate") is not None:
        result["failed_predicate"] = evidence["failed_predicate"]
        result["detail"] = evidence.get("detail")
    if appended is None:
        result["repository_receipt_observed"] = False
        result["organization_receipt_observed"] = False
        result["refusal_recorded"] = False
        return result
    repository_receipt = appended["repository_receipt"]
    organization_receipt = appended["organization_receipt"]
    result.update({
        "repository_receipt_observed": True,
        "organization_receipt_observed": True,
        "repository_receipt_sha256": repository_receipt["receipt_sha256"],
        "organization_receipt_sha256": organization_receipt["receipt_sha256"],
        "organization_receipt_preserves_repository_receipt":
            organization_receipt["repo_receipt_sha256"] == repository_receipt["receipt_sha256"],
        "refusal_recorded": disposition != ALLOW,
    })
    return result


def _append(transition_class: str, packet_id: str, evidence: Mapping[str, Any],
            hb_epoch: int | None, *, predecessor: str | None = None, successor: str | None = None,
            boundary_evidence: Mapping[str, Any] | None = None,
            idempotent_on: tuple[str, ...] = ("communication_id", "payload_sha256", "disposition"),
            ) -> tuple[dict[str, Any], bool]:
    """Append at both levels. A replay of the same packet returns the recorded pair.

    The organization append owner is ``aggregate_transition``. It takes the
    repository receipt's epoch, so a replay rebuilds the same organization
    receipt rather than one stamped later.

    The keyword arguments let another writer operation on this same ref (for
    example ``sv_check_receipt_append``) reuse this one append path: it names
    its own state digests, boundary evidence and idempotency keys. Defaults
    are this operation's own, so the self-closure is unchanged.
    """
    if predecessor is None:
        predecessor = evidence["payload_sha256"]
    if successor is None:
        successor = sha({"disposition": evidence["disposition"], "packet_id": packet_id,
                         "communication_id": evidence.get("communication_id"),
                         "payload_sha256": evidence["payload_sha256"]})
    if boundary_evidence is None:
        boundary_evidence = {"operation": OPERATION_ID, "profile_id": PROFILE_ID,
                             "disposition": evidence["disposition"],
                             "communication_id": evidence.get("communication_id")}
    transition_id = transition_class + ":" + packet_id
    store = repository_ledger.repository_store()
    head = store.get(repository_ledger.ledger_store.HEAD_KEY)
    prior = repository_ledger.recorded(store, head, transition_id, transition_class)
    repository_receipt = repository_ledger.append(
        transition_id, transition_class, predecessor, successor, dict(evidence),
        "NONE", hb_epoch=hb_epoch,
        idempotent_on=idempotent_on)
    epoch = repository_receipt["hb_reference"]["epoch"]
    organization_receipt = organization_ledger.aggregate_transition(
        receipt=repository_receipt,
        org_transition_class="REPO_STATE_PROPAGATION",
        predecessor_org_state_sha256=predecessor,
        successor_org_state_sha256=successor,
        boundary_evidence=dict(boundary_evidence),
        authority_effect="NONE",
        hb_epoch=epoch)
    return ({"repository_receipt": repository_receipt,
             "organization_receipt": organization_receipt}, prior is not None)


def _recorded(disposition: str, payload: Any, packet_id: str, hb_epoch: int | None, *,
              failed_predicate: str | None = None, detail: str | None = None,
              closure: str | None = None) -> dict[str, Any]:
    evidence = _evidence(payload, packet_id, disposition,
                         failed_predicate=failed_predicate, detail=detail, closure=closure)
    if closure is None:
        transition_class = OPERATION_ID if disposition == ALLOW else REFUSED_CLASS
    else:
        transition_class = CLOSURE_CLASS if disposition == ALLOW else CLOSURE_REFUSED_CLASS
    try:
        appended, replayed = _append(transition_class, packet_id, evidence, hb_epoch)
    except ValueError as exc:
        if str(exc) != "ledger_receipt_collision":
            raise
        # The packet id already bound a different diagnostic. The recorded
        # transition stands; this attempt is not a second one.
        collided = _evidence(payload, packet_id, FAIL_CLOSED,
                             failed_predicate="ONE_PACKET_ID_BINDS_ONE_DIAGNOSTIC",
                             detail=str(exc), closure=closure)
        return _result(collided, None, replayed=False, received=False)
    return _result(evidence, appended, replayed=replayed, received=disposition == ALLOW)


def receive(payload: Any, *, registry: Mapping[str, Any], standing: Mapping[str, Any] | None = None,
            packet_id: str = "organization-intr-destination",
            hb_epoch: int | None = None, mesh_root: Path | None = None) -> dict[str, Any]:
    """Acknowledge one diagnostic, or record the refusal.

    ``standing`` and ``mesh_root`` are accepted because the capability resolver
    passes them to every receiving operation. Standing was required at ingress.
    A diagnostic does not leave, so the mesh is not used.
    """
    del standing, mesh_root
    if not isinstance(registry, Mapping):
        return _recorded(DENY, payload, packet_id, hb_epoch,
                         failed_predicate="CAPABILITY_MAP_IS_A_MAPPING",
                         detail="registry is not an object")
    refusal = shape_refusal(payload)
    if refusal is not None:
        return _recorded(DENY, payload, packet_id, hb_epoch,
                         failed_predicate=refusal[0], detail=refusal[1])
    return _recorded(ALLOW, payload, packet_id, hb_epoch)


def diagnostic_payload(communication_id: str) -> dict[str, Any]:
    """A purpose-neutral diagnostic this organization can close against itself."""
    return {
        "message_class": COMMUNICATION_CLASS,
        "communication_id": communication_id,
        "subject": "intr-destination diagnostic self-closure",
        "body": {"schema": PAYLOAD_SCHEMA, "probe": "diagnostic-self-closure"},
    }


def self_close(payload: Any, *, registry: Mapping[str, Any],
               packet_id: str = "intr-destination-self-closure",
               hb_epoch: int | None = None) -> dict[str, Any]:
    """Record an intr-destination diagnostic self-closure on both ledgers.

    The diagnostic is addressed to this organization. No peer is resolved and
    the federation directory is not read. Authority and Time stay constraint
    variables on the appended receipts; the disposition is the transition's
    evidence. ``communication_id`` is carried on the repository receipt and on
    the organization receipt's boundary evidence.
    """
    if not isinstance(registry, Mapping):
        return _recorded(DENY, payload, packet_id, hb_epoch, closure="SELF",
                         failed_predicate="CAPABILITY_MAP_IS_A_MAPPING",
                         detail="registry is not an object")
    if not isinstance(payload, Mapping):
        return _recorded(DENY, payload, packet_id, hb_epoch, closure="SELF",
                         failed_predicate="SUBMISSION_IS_AN_ECOSYSTEM_COMMUNICATION",
                         detail="payload is not an object")
    identifier = payload.get("communication_id")
    if not isinstance(identifier, str) or not identifier.strip() or any(
            ord(character) < 33 or ord(character) > 126 for character in identifier):
        return _recorded(DENY, payload, packet_id, hb_epoch, closure="SELF",
                         failed_predicate="SUBMISSION_CARRIES_THE_COMMUNICATION_ID_CLOSURE_CORRELATES_ON",
                         detail=repr(identifier))
    refusal = shape_refusal(payload)
    if refusal is not None:
        return _recorded(DENY, payload, packet_id, hb_epoch, closure="SELF",
                         failed_predicate=refusal[0], detail=refusal[1])
    return _recorded(ALLOW, payload, packet_id, hb_epoch, closure="SELF")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--payload", type=Path)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--packet-id", default="organization-intr-destination")
    parser.add_argument("--hb-epoch", type=int, default=None)
    parser.add_argument("--self-close", action="store_true",
                        help="record a diagnostic self-closure; no peer is named")
    parser.add_argument("--communication-id",
                        help="communication_id the self-closure correlates on")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    if args.self_close:
        if args.communication_id:
            payload = diagnostic_payload(args.communication_id)
        elif args.payload is not None:
            payload = json.loads(args.payload.read_text(encoding="utf-8"))
        else:
            raise SystemExit("self-close requires --communication-id or --payload")
        result = self_close(payload, registry=registry, packet_id=args.packet_id,
                            hb_epoch=args.hb_epoch)
    else:
        if args.payload is None:
            raise SystemExit("--payload is required unless --self-close is set")
        result = receive(
            json.loads(args.payload.read_text(encoding="utf-8")),
            registry=registry, packet_id=args.packet_id, hb_epoch=args.hb_epoch)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("disposition") == ALLOW else 1


if __name__ == "__main__":
    sys.exit(main())
