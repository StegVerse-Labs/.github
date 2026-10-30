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
import re
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

INTR_PROTOCOL_GOAL = "INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001"


#: P1 interface (#163): where the ledger writers load from and where their
#: contracts resolve. Both default to this checkout, which is today's
#: behaviour. A consumer that carries this operation without carrying the
#: writers names them with `--ledger-component <path>` (a root holding
#: `.stegverse/transition-ledger/emit.py` and
#: `resident-runtime/aggregate_repo_transition.py`) and the root its contracts
#: live in with `--consumer-root <path>` (a root holding
#: `.stegverse/transition-ledger/contract.json` and `org-contract.json`). The
#: ledger *locations* stay STEGVERSE_REPO_LEDGER_ROOT / STEGVERSE_ORG_LEDGER_ROOT.
#: A path that is given and does not hold those files fails closed.
LEDGER_COMPONENT_PATH_INVALID = "LEDGER_COMPONENT_PATH_INVALID"
CONSUMER_ROOT_PATH_INVALID = "CONSUMER_ROOT_PATH_INVALID"
LEDGER_COMPONENT_FILES = (".stegverse/transition-ledger/emit.py",
                          "resident-runtime/aggregate_repo_transition.py")
#: The flat layout of the shared ledger component (as in
#: org-kernel/organization-ledger/): the same two writers as siblings. Either
#: layout is accepted for --ledger-component.
LEDGER_COMPONENT_FLAT_FILES = ("emit.py", "aggregate_repo_transition.py")
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")
LEDGER_COMPONENT_LAYOUTS = (" and ".join(LEDGER_COMPONENT_FILES)
                            + ", or as siblings " + " and ".join(LEDGER_COMPONENT_FLAT_FILES),)
CONSUMER_ROOT_FILES = (".stegverse/transition-ledger/contract.json",
                       ".stegverse/transition-ledger/org-contract.json")


class LedgerPathRefused(SystemExit):
    """A FAIL_CLOSED refusal of a given ledger path; `.refusal` carries the six fields."""

    def __init__(self, refusal: Mapping[str, Any]):
        super().__init__(refusal["failure_code"] + ":" + refusal["detail"])
        self.refusal = dict(refusal)


def _ledger_path_refusal(code: str, predicate: str, option: str, path: Any,
                         required: tuple[str, ...], entrypoint: str, goal: str) -> LedgerPathRefused:
    return LedgerPathRefused({
        "disposition": "FAIL_CLOSED",
        "failure_code": code,
        "failed_predicate": predicate,
        "detail": option + " " + str(path) + " does not hold " + ", ".join(required),
        "required_evidence_or_repair": (
            "give " + option + " a directory holding " + ", ".join(required)
            + ", or omit it to use this checkout"),
        "retry_entrypoint": entrypoint,
        "owning_existing_goal": goal,
        "next_attempt": "run again with a valid " + option + "; nothing was loaded or appended",
    })


def ledger_writer_refusal(exc: SystemExit, entrypoint: str,
                          goal: str) -> tuple[dict[str, Any], bool] | None:
    """A ledger writer's refusal and whether it carried its own record, or None.

    The ledger component's LedgerRefusal (ledger_common.py, flat next to
    emit.py) subclasses SystemExit and carries its refusal as `.refusal`, a
    dict: that is returned as given, (refusal, True), and printed unchanged.
    An old-layout writer raises a plain SystemExit(message): only when it
    came out of a ledger writer call itself (`_ledger_write`, which marks it
    LedgerWriterExit) is the message given the six fields here, FAIL_CLOSED,
    (fields, False). Any other SystemExit -- an int or None code, or a message
    from anything but a writer call (e.g. repository-receipt-failed) -- is not
    a ledger refusal (None) and is re-raised by the caller.
    """
    refusal = getattr(exc, "refusal", None)
    if isinstance(refusal, dict):
        return refusal, True
    if not isinstance(exc, LedgerWriterExit) or not isinstance(exc.code, str):
        return None
    message = exc.code
    head = message.split(":", 1)[0].strip()
    code = head if re.fullmatch(r"[A-Z][A-Z0-9_]*", head) else "LEDGER_WRITER_REFUSED"
    return {
        "disposition": "FAIL_CLOSED",
        "failure_code": code,
        "failed_predicate": "LEDGER_WRITER_ADMITS_THE_APPEND",
        "detail": message,
        "required_evidence_or_repair": "repair what the ledger writer refused (" + message + ") and run again",
        "retry_entrypoint": entrypoint,
        "owning_existing_goal": goal,
        "next_attempt": "run again once the ledger writer's refusal is repaired; nothing was written",
    }, False


class LedgerWriterExit(SystemExit):
    """A plain SystemExit(message) that a ledger writer call itself raised (old layout)."""


def _ledger_write(call: Any, *args: Any, **kwargs: Any) -> Any:
    """Run one ledger writer call; a plain SystemExit(message) from it is marked as the writer's.

    Only a plain SystemExit is marked. A LedgerRefusal (it carries
    `.refusal`), the writer's other SystemExit subclasses (e.g.
    OrgLedgerAppendRefused) and an exit with no message pass through unchanged.
    """
    try:
        return call(*args, **kwargs)
    except SystemExit as exc:
        if type(exc) is not SystemExit or not isinstance(exc.code, str):
            raise
        raise LedgerWriterExit(exc.code) from exc


def cli_hb_epoch(text: str | None, entrypoint: str,
                 goal: str) -> tuple[int | None, dict[str, Any] | None]:
    """--hb-epoch as typed, checked by the shared rule: (epoch, None) or (None, refusal).

    argparse hands over the raw text (type=str), so the shared validator
    (supplied_epoch_failure, the egress boundary's copy) sees it uncoerced:
    '+33', ' 33' and '3_3' are HB_EPOCH_INVALID, and '0033' is 33. An absent
    --hb-epoch stays None, as before.
    """
    if text is None:
        return None, None
    rule = _module("organization_egress_boundary_cli_epoch",
                   "resident-runtime/organization_egress_boundary.py").supplied_epoch_failure
    failure = rule(text)
    if failure is None:
        return int(text), None  # admitted as ASCII digits
    code, detail = failure
    return None, {
        "disposition": "FAIL_CLOSED",
        "failure_code": code,
        "failed_predicate": "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH",
        "detail": detail,
        "required_evidence_or_repair": ("pass --hb-epoch as the carrier supplied it: ASCII digits "
                                        "with value >= 32"),
        "retry_entrypoint": entrypoint,
        "owning_existing_goal": goal,
        "next_attempt": "run again with the supplied epoch; nothing was received or appended",
    }


def bind_ledger_writers(ledger_component: Path | str | None = None,
                        consumer_root: Path | str | None = None) -> dict[str, Any]:
    """Load the ledger writers from `ledger_component`, their contracts from `consumer_root`.

    Either left None keeps this checkout. Both are checked before anything is
    loaded, so a refused path leaves the writers already bound in place.
    """
    global repository_ledger, organization_ledger
    entrypoint = "resident-runtime/intr_destination_ingress.py (--ledger-component, --consumer-root)"
    component = Path(ledger_component).expanduser().resolve() if ledger_component is not None else None
    consumer = Path(consumer_root).expanduser().resolve() if consumer_root is not None else None
    layout = (None if component is None
              else LEDGER_COMPONENT_FILES if all((component / name).is_file() for name in LEDGER_COMPONENT_FILES)
              else LEDGER_COMPONENT_FLAT_FILES
              if all((component / name).is_file() for name in LEDGER_COMPONENT_FLAT_FILES)
              else ())
    if component is not None and not layout:
        raise _ledger_path_refusal(LEDGER_COMPONENT_PATH_INVALID, "LEDGER_COMPONENT_PATH_HOLDS_THE_LEDGER_WRITERS",
                                   "--ledger-component", ledger_component, LEDGER_COMPONENT_LAYOUTS,
                                   entrypoint, INTR_PROTOCOL_GOAL)
    if consumer is not None and not all((consumer / name).is_file() for name in CONSUMER_ROOT_FILES):
        raise _ledger_path_refusal(CONSUMER_ROOT_PATH_INVALID, "CONSUMER_ROOT_PATH_HOLDS_THE_LEDGER_CONTRACTS",
                                   "--consumer-root", consumer_root, CONSUMER_ROOT_FILES,
                                   entrypoint, INTR_PROTOCOL_GOAL)
    try:
        contracts = ({name: json.loads((consumer / name).read_text(encoding="utf-8"))
                      for name in CONSUMER_ROOT_FILES} if consumer is not None else None)
    except ValueError as exc:
        raise _ledger_path_refusal(CONSUMER_ROOT_PATH_INVALID, "CONSUMER_ROOT_PATH_HOLDS_THE_LEDGER_CONTRACTS",
                                   "--consumer-root", str(consumer_root) + " (" + str(exc) + ")",
                                   CONSUMER_ROOT_FILES, entrypoint, INTR_PROTOCOL_GOAL) from None
    base = component if component is not None else ROOT
    files = layout or LEDGER_COMPONENT_FILES
    repository = _module_at("repo_transition_emit_bound", base / files[0])
    organization = _module_at("aggregate_repo_transition_bound", base / files[1])
    if contracts is not None:
        repository.ROOT, repository.C = consumer, contracts[CONSUMER_ROOT_FILES[0]]
        organization.ROOT, organization.C = consumer, contracts[CONSUMER_ROOT_FILES[1]]
    repository_ledger, organization_ledger = repository, organization
    return {"ledger_component": str(base), "consumer_root": str(consumer if consumer is not None else ROOT),
            "ledger_component_is_this_checkout": component is None,
            "ledger_component_layout": "FLAT" if files == LEDGER_COMPONENT_FLAT_FILES else "NESTED",
            "consumer_root_is_this_checkout": consumer is None}


def _module_at(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


_LEDGER_GITSTORE: Any = None


def _two_level_atomic():
    """resident-runtime/ledger_gitstore.py two_level_atomic: both halves' locations are resolved and
    checked before either is written, and a failure after the repository half rolls its ref back."""
    global _LEDGER_GITSTORE
    if _LEDGER_GITSTORE is None:
        _LEDGER_GITSTORE = _module("ledger_gitstore_for_intr_destination_ingress", "resident-runtime/ledger_gitstore.py")
    return _LEDGER_GITSTORE.two_level_atomic(ROOT, surface=_LEDGER_GITSTORE.BoundSurface(emit=repository_ledger, aggregate=organization_ledger))


def _append(transition_class: str, packet_id: str, evidence: Mapping[str, Any],
            hb_epoch: int | None, *, operation: str = OPERATION_ID, profile_id: str = PROFILE_ID,
            boundary_extra: Mapping[str, Any] | None = None) -> tuple[dict[str, Any], bool]:
    """Append at both levels, all or nothing (see _two_level_atomic); a refusal of either
    location raises ledger_gitstore.TwoLevelAppendRefused (a ValueError) before any write."""
    with _two_level_atomic():
        return _append_halves(transition_class, packet_id, evidence, hb_epoch, operation=operation,
                              profile_id=profile_id, boundary_extra=boundary_extra)


def _append_halves(transition_class: str, packet_id: str, evidence: Mapping[str, Any],
                   hb_epoch: int | None, *, operation: str = OPERATION_ID, profile_id: str = PROFILE_ID,
                   boundary_extra: Mapping[str, Any] | None = None) -> tuple[dict[str, Any], bool]:
    """Append at both levels. A replay of the same packet returns the recorded pair.

    ``operation``, ``profile_id`` and ``boundary_extra`` name another operation on
    the same two-level append (resident-runtime/ledger_gitstore.py, the InTr path
    transfer); their defaults are this ingress, so its receipts are unchanged. The
    organization receipt goes through aggregate_transition on the declared
    {store: git} locus, never through ledger_root().

    The organization append owner is ``aggregate_transition``. It takes the
    repository receipt's epoch, so a replay rebuilds the same organization
    receipt rather than one stamped later.
    """
    predecessor = evidence["payload_sha256"]
    successor = sha({"disposition": evidence["disposition"], "packet_id": packet_id,
                     "communication_id": evidence.get("communication_id"),
                     "payload_sha256": evidence["payload_sha256"]})
    transition_id = transition_class + ":" + packet_id
    store = repository_ledger.repository_store()
    head = store.get(repository_ledger.ledger_store.HEAD_KEY)
    prior = _ledger_write(repository_ledger.recorded, store, head, transition_id, transition_class)
    repository_receipt = _ledger_write(repository_ledger.append,
        transition_id, transition_class, predecessor, successor, dict(evidence),
        "NONE", hb_epoch=hb_epoch,
        idempotent_on=("communication_id", "payload_sha256", "disposition"))
    epoch = repository_receipt["hb_reference"]["epoch"]
    organization_receipt = _ledger_write(organization_ledger.aggregate_transition,
        receipt=repository_receipt,
        org_transition_class="REPO_STATE_PROPAGATION",
        predecessor_org_state_sha256=predecessor,
        successor_org_state_sha256=successor,
        boundary_evidence={"operation": operation, "profile_id": profile_id,
                           "disposition": evidence["disposition"],
                           "communication_id": evidence.get("communication_id"),
                           **dict(boundary_extra or {})},
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
    parser.add_argument("--hb-epoch", type=str, default=None)
    parser.add_argument("--self-close", action="store_true",
                        help="record a diagnostic self-closure; no peer is named")
    parser.add_argument("--communication-id",
                        help="communication_id the self-closure correlates on")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--ledger-component", type=Path, default=None,
                        help="root the ledger writers load from (.stegverse/transition-ledger/emit.py, "
                             "resident-runtime/aggregate_repo_transition.py); default: this checkout")
    parser.add_argument("--consumer-root", type=Path, default=None,
                        help="root the ledger contracts resolve from (.stegverse/transition-ledger/"
                             "contract.json, org-contract.json); default: this checkout")
    args = parser.parse_args()
    hb_epoch, epoch_refused = cli_hb_epoch(args.hb_epoch, "resident-runtime/intr_destination_ingress.py (--hb-epoch)", INTR_PROTOCOL_GOAL)
    if epoch_refused is not None:
        # Nothing is received, appended or written (no --out); the exit is 1.
        print(json.dumps({**epoch_refused, "appended": False,
                          "authority_effect": "NONE_REFUSAL_ONLY"}, sort_keys=True))
        return 1
    if args.ledger_component is not None or args.consumer_root is not None:
        try:
            bind_ledger_writers(args.ledger_component, args.consumer_root)
        except LedgerPathRefused as refused:
            result = {**refused.refusal, "appended": False, "authority_effect": "NONE_REFUSAL_ONLY"}
            if args.out:
                args.out.parent.mkdir(parents=True, exist_ok=True)
                args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(json.dumps(result, sort_keys=True))
            return 1
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    # Usage errors exit before the ledger is touched, so the SystemExit caught
    # below is only ever the ledger writer's.
    if args.self_close:
        if args.communication_id:
            payload = diagnostic_payload(args.communication_id)
        elif args.payload is not None:
            payload = json.loads(args.payload.read_text(encoding="utf-8"))
        else:
            raise SystemExit("self-close requires --communication-id or --payload")
    elif args.payload is None:
        raise SystemExit("--payload is required unless --self-close is set")
    else:
        payload = json.loads(args.payload.read_text(encoding="utf-8"))
    try:
        if args.self_close:
            result = self_close(payload, registry=registry, packet_id=args.packet_id,
                                hb_epoch=hb_epoch)
        else:
            result = receive(payload, registry=registry, packet_id=args.packet_id, hb_epoch=hb_epoch)
    except SystemExit as exc:
        refused = ledger_writer_refusal(
            exc, "resident-runtime/intr_destination_ingress.py (--self-close, --hb-epoch)", INTR_PROTOCOL_GOAL)
        if refused is None:
            raise
        refusal, carried = refused
        # The ledger writer refused (e.g. HB_EPOCH_NOT_SUPPLIED). A carried
        # refusal is printed exactly as given; an old-layout message gets the
        # six fields. Nothing is written (no --out), and the exit is 1.
        print(json.dumps(refusal) if carried else json.dumps(
            {**refusal, "appended": False, "refusal_source": "LEDGER_WRITER",
             "authority_effect": "NONE_REFUSAL_ONLY"}, sort_keys=True))
        return 1
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("disposition") == ALLOW else 1


if __name__ == "__main__":
    sys.exit(main())
