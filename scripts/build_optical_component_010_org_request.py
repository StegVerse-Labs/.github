#!/usr/bin/env python3
"""Emit the organization transition request for the optical goal's COMPONENT_010 append.

Blocker 1 of OPTICAL-PHYSICAL-STATE-REPLAY-RESEARCH-001 is satisfied by "the
owning lane's manifest-directed append of
COMPONENT_010_SESSION_EVENT_FOR_GOVERNED_EXECUTION to the Organization ledger
root under ORGANIZATION_LEDGER_LOCK". This writes the committed request that
append is received from, a `stegverse.organization-transition-request/v1` file
under .stegverse/transition-requests/, the same shape StegVerse-SDK
scripts/build_capability_boundary_experiment_org_request.py (SDK#553, 5dd0f25)
writes for StegVerse-org/.github.

The manifest is not composed here. It is taken from a declaration in the
canonical records only, with no input empty or a placeholder. The declaration
must conform to schemas/component-010-session-event-input.schema.json, which
fixes each input's type and the values it may take: the published SDK routes,
the standing modes, the supplied hb_epoch (which created_at must equal, and
which the request carries for the committed-request intake) and the permitted
acting parties, none of them an AI session. It is then checked by the ingress's own
stegverse.manifest_contract.validate_ingress_manifest. Both run before any
digest is taken, and the canonical digest is the one this organization's
ingress recomputes: resident-runtime/organization_manifest_ingress.py
`derive_execution_request(manifest, boundary())`, not the wire digest. When the
records declare no manifest for the transition, nothing is written and the
refusal is returned with its six fields, naming each undeclared input.

The canonical records and the ingress are both read from --organization-root,
the checkout the request is then written into.

It grants nothing. The ingress decides the disposition and the ledger records
it; a request file is not an Organization receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import functools
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
# The repository's stdlib schema checker, the one hil_explanation_experiment.py
# also validates with; no third-party validator.
from user_facing_explanation import ExplanationError, schema_check  # noqa: E402

GOAL = "OPTICAL-PHYSICAL-STATE-REPLAY-RESEARCH-001"
TRANSITION = "COMPONENT_010_SESSION_EVENT_FOR_GOVERNED_EXECUTION"
COMPONENT = "RTC-TASK-REGISTRY-SESSION-ACTOR-GATE-010"
SCHEMA = "stegverse.organization-transition-request/v1"
REQUEST_ID = "OPTICAL-COMPONENT-010-SESSION-EVENT-001"
REQUEST_PATH = f".stegverse/transition-requests/{REQUEST_ID}.json"

TASK_RECORD = f"data/canonical-task-records/{GOAL}.json"
COMPONENT_PROFILE = "data/goal-task-component-profiles/ECOSYSTEM-INGRESS-AI-BOUNDARIES-001.json"
INGRESS = "resident-runtime/organization_manifest_ingress.py"
DECLARATION_SCHEMA = "schemas/component-010-session-event-input.schema.json"

# Pinned when a declared manifest exists and its request has been built once and
# reviewed. Unpinned, the builder refuses to write: a digest it has never been
# held to is not an assertion.
MANIFEST_FILE_SHA256: str | None = None
CANONICAL_MANIFEST_SHA256: str | None = None
REQUEST_FILE_SHA256: str | None = None

# Required by the SDK ingress envelope (stegverse.manifest_contract
# validate_ingress_manifest), each of which the declaration must supply.
SDK_MANIFEST_INPUTS = (
    "manifest.source_framework",
    "manifest.source_output_id",
    "manifest.created_at",
    "manifest.declared_intent",
    "manifest.requested_consequence",
    "manifest.payload_or_payload_commitment",
    "manifest.extensions.stegverse_route",
)
STANDING_INPUTS = ("standing.mode", "standing.node_ref", "standing.predecessor")
# The supplied HB epoch the committed-request intake requires on the request.
EPOCH_INPUTS = ("hb_epoch",)
NULLABLE_INPUTS = ("standing.predecessor",)
# A value that only stands in for one is not a declaration of it. Matched
# against the upper-cased string, anywhere in the declared manifest or standing.
PLACEHOLDER_PREFIXES = ("OWNER_PLACEHOLDER", "PLACEHOLDER", "TODO", "TBD", "<")

INPUTS_UNDECLARED = "COMPONENT_010_MANIFEST_INPUTS_UNDECLARED"
DIGEST_NOT_PINNED = "COMPONENT_010_REQUEST_DIGEST_NOT_PINNED"
DIGEST_MISMATCH = "COMPONENT_010_REQUEST_DIGEST_MISMATCH"
CONTRACT_INVALID = "COMPONENT_010_MANIFEST_CONTRACT_INVALID"
SCHEMA_INVALID = "COMPONENT_010_DECLARATION_SCHEMA_INVALID"
HB_EPOCH_INVALID = "COMPONENT_010_HB_EPOCH_INVALID"
SDK_UNAVAILABLE = "COMPONENT_010_INGRESS_SDK_UNAVAILABLE"
CANONICAL_REFUSED = "COMPONENT_010_MANIFEST_INGRESS_CANONICAL_REFUSED"
RECORDS_UNREADABLE = "COMPONENT_010_CANONICAL_RECORDS_UNREADABLE"
RETRY_ENTRYPOINT = "scripts/build_optical_component_010_org_request.py --organization-root ."


class Refusal(Exception):
    def __init__(self, record: dict[str, Any]):
        super().__init__(record["failure_code"])
        self.record = record


def _read(root: Path, relative: str) -> Any:
    try:
        return json.loads((root / relative).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise refusal(RECORDS_UNREADABLE, f"{relative} is readable JSON under the organization root",
                      "run against a StegVerse-Labs/.github checkout carrying the canonical records",
                      detail=f"{root / relative}: {exc}") from exc


def refusal(failure_code: str, failed_predicate: str, repair: str, **detail: Any) -> Refusal:
    return Refusal({
        "disposition": "FAIL_CLOSED",
        "failure_code": failure_code,
        "failed_predicate": failed_predicate,
        "required_evidence_or_repair": repair,
        "retry_entrypoint": RETRY_ENTRYPOINT,
        "owning_existing_goal": GOAL,
        "next_attempt": f"after the canonical records declare the {TRANSITION} manifest",
        "consequence_committed": False,
        **detail,
    })


def blocker(record: dict[str, Any]) -> dict[str, Any]:
    """blockers[0], which must be the COMPONENT_010 append this request serves."""
    first = (record.get("blockers") or [None])[0]
    if not isinstance(first, dict) or first.get("failed_predicate") != \
            f"ORGANIZATION_RECEIPT_APPENDED_UNDER_LOCK:{TRANSITION}":
        raise refusal("COMPONENT_010_BLOCKER_NOT_FOUND",
                      f"{TASK_RECORD} blockers[0] is the {TRANSITION} append",
                      "restore blockers[0] of the canonical task record")
    return first


def declarations(value: Any) -> list[dict[str, Any]]:
    """Every object in the records that names the transition and carries a manifest form."""
    found: list[dict[str, Any]] = []
    if isinstance(value, dict):
        if TRANSITION in value.values() and ("manifest" in value or "build_manifest" in value):
            found.append(value)
        for child in value.values():
            found.extend(declarations(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(declarations(child))
    return found


def component_inputs(profile: dict[str, Any]) -> list[str]:
    rows = [c for c in profile.get("selected_components") or [] if c.get("component_id") == COMPONENT]
    if len(rows) != 1:
        raise refusal("COMPONENT_010_CONTRACT_NOT_FOUND",
                      f"{COMPONENT_PROFILE} declares {COMPONENT} exactly once",
                      f"restore the {COMPONENT} component contract")
    return list(rows[0].get("inputs") or [])


def _placeholder(value: Any, *, nested: bool = False) -> bool:
    """An empty value, or a sentinel standing in for one anywhere within it.

    Emptiness counts only for the declared value itself: a real manifest may
    carry an empty list or string inside it, but never a sentinel.
    """
    if isinstance(value, str):
        text = value.strip()
        return text.upper().startswith(PLACEHOLDER_PREFIXES) or (not nested and not text)
    if isinstance(value, (dict, list)):
        children = value.values() if isinstance(value, dict) else value
        return (not nested and not value) or any(_placeholder(v, nested=True) for v in children)
    return False


def _present(declaration: dict[str, Any] | None, dotted: str) -> bool:
    """The input is declared with a real value: not absent, empty or a placeholder."""
    if declaration is None:
        return False
    head, _, rest = dotted.partition(".")
    node: Any = declaration.get(head)
    if rest == "payload_or_payload_commitment":
        if not isinstance(node, dict):
            return False
        value = node.get("payload", node.get("payload_commitment"))
        return value is not None and not _placeholder(value)
    for key in rest.split(".") if rest else ():
        if not isinstance(node, dict) or key not in node:
            return False
        node = node[key]
    if node is None:
        # A null predecessor is the declared genesis standing, not an absent one.
        return dotted in NULLABLE_INPUTS
    return not _placeholder(node)


def placeholder_paths(value: Any, path: str) -> list[str]:
    """Every string within the value that stands in for one, by dotted path."""
    if isinstance(value, str):
        return [path] if value.strip().upper().startswith(PLACEHOLDER_PREFIXES) else []
    if isinstance(value, dict):
        return [p for k, v in value.items() for p in placeholder_paths(v, f"{path}.{k}")]
    if isinstance(value, list):
        return [p for i, v in enumerate(value) for p in placeholder_paths(v, f"{path}[{i}]")]
    return []


def missing_inputs(record: dict[str, Any], profile: dict[str, Any],
                   declaration: dict[str, Any] | None) -> list[str]:
    """The inputs a valid request needs that no canonical record declares."""
    missing = []
    manifest = (declaration or {}).get("manifest")
    payload = manifest.get("payload") if isinstance(manifest, dict) else None
    for name in component_inputs(profile):
        # task_id is the canonical goal itself; every other component-010 input
        # is a fact of a session event, which only a declaration can supply.
        if name == "task_id" and record.get("task_id") == GOAL:
            continue
        if not (isinstance(payload, dict) and payload.get(name) is not None
                and not _placeholder(payload[name])):
            missing.append(f"{COMPONENT}.{name}")
    missing += [n for n in SDK_MANIFEST_INPUTS + STANDING_INPUTS + EPOCH_INPUTS
                if not _present(declaration, n)]
    # A placeholder anywhere else, source_instance or context_refs included, is
    # missing too: only the listed inputs are required, but none may be faked.
    covered = [c for m in missing for c in (
        ("manifest.payload", "manifest.payload_commitment") if m == "manifest.payload_or_payload_commitment"
        else (m,))]
    for head in ("manifest", "standing"):
        missing += [p for p in placeholder_paths((declaration or {}).get(head), head)
                    if not any(p == c or p.startswith((c + ".", c + "[")) for c in covered)]
    return missing


def schema_violation(declaration: dict[str, Any], schema: dict[str, Any]) -> str | None:
    """None when the declaration conforms to the schema; else the checker's code, e.g. schema:enum:$.x."""
    try:
        schema_check(declaration, schema)
    except ExplanationError as exc:
        return str(exc)
    return None


def validate_declaration(declaration: dict[str, Any], root: Path = ROOT) -> None:
    """Refuse, with six fields, a declaration that does not conform to the input schema."""
    violation = schema_violation(declaration, _read(root, DECLARATION_SCHEMA))
    if violation is None:
        return
    raise refusal(
        SCHEMA_INVALID, f"the declared {TRANSITION} manifest conforms to {DECLARATION_SCHEMA}",
        f"correct the declaration in {TASK_RECORD} so it conforms to {DECLARATION_SCHEMA}; "
        "a value the schema does not list (an acting party, a route, a standing mode) "
        "is added by the owner's merge of the schema, never by the declaration",
        detail=violation, schema_path=re.sub(r"^schema:[A-Za-z]+:", "", violation),
        inputs_read=[TASK_RECORD, COMPONENT_PROFILE, DECLARATION_SCHEMA])


@functools.lru_cache(maxsize=None)
def _kernel() -> Any:
    spec = importlib.util.spec_from_file_location("org_kernel_component_010", ROOT / "org-kernel" / "kernel.py")
    kernel = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(kernel)
    return kernel


def validate_epoch(declaration: dict[str, Any]) -> None:
    """The supplied hb_epoch passes the kernel's shared rule, and created_at is its text.

    The rule is org-kernel/kernel.py supplied_epoch_failure, the one the
    committed-request intake applies on receipt; no clock is read.
    """
    hb_epoch = declaration.get("hb_epoch")
    failure = _kernel().supplied_epoch_failure(hb_epoch)
    if failure is None and declaration["manifest"].get("created_at") != str(hb_epoch):
        failure = (HB_EPOCH_INVALID, f"created_at {declaration['manifest'].get('created_at')!r} "
                                     f"is not the supplied hb_epoch {hb_epoch!r}")
    if failure is None:
        return
    raise refusal(HB_EPOCH_INVALID, "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH",
                  f"declare hb_epoch in {TASK_RECORD} as ASCII digits with value >= 32, and created_at "
                  "as its decimal text; no clock is read for either",
                  detail=f"{failure[0]}: {failure[1]}")


@functools.lru_cache(maxsize=None)
def ingress_module(root: Path = ROOT) -> Any:
    """The organization root's ingress, which imports the SDK it validates and derives with."""
    spec = importlib.util.spec_from_file_location("organization_manifest_ingress", root / INGRESS)
    ingress = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ingress)
    return ingress


def ingress_validate(manifest: dict[str, Any], root: Path = ROOT) -> None:
    """The ingress's own envelope check, stegverse.manifest_contract.validate_ingress_manifest."""
    ingress_module(root).validate_ingress_manifest(manifest)


def ingress_canonical(manifest: dict[str, Any], root: Path = ROOT) -> str:
    """The canonical projection exactly as this organization's ingress derives it."""
    ingress = ingress_module(root)
    return ingress.derive_execution_request(manifest, ingress.boundary())["canonical_manifest_sha256"]


def manifest_file_bytes(manifest: dict[str, Any]) -> bytes:
    return (json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def request_file_bytes(request: dict[str, Any]) -> bytes:
    return (json.dumps(request, indent=2) + "\n").encode("utf-8")


def _held_to(name: str, pinned: str | None, actual: str) -> None:
    if pinned is None:
        raise refusal(DIGEST_NOT_PINNED, f"{name} is pinned in this builder",
                      f"build once, review, and pin {name} = {actual}", observed_sha256=actual)
    if pinned != actual:
        raise refusal(DIGEST_MISMATCH, f"{name} equals its pinned value",
                      "rebuild from the canonical records, or re-review and re-pin",
                      expected_sha256=pinned, observed_sha256=actual)


def build_request(root: Path = ROOT, *, canonical_of: Callable[[dict[str, Any]], str] | None = None,
                  validate_of: Callable[[dict[str, Any]], None] | None = None,
                  pins: dict[str, str | None] | None = None) -> tuple[dict[str, Any], bytes]:
    """Return the request and its file bytes, or raise Refusal with six fields.

    The records are read from `root`, and the ingress that validates and derives
    is the one `root` carries.
    """
    root = Path(root).resolve()
    canonical_of = canonical_of or (lambda m: ingress_canonical(m, root))
    validate_of = validate_of or (lambda m: ingress_validate(m, root))
    pins = pins if pins is not None else {
        "MANIFEST_FILE_SHA256": MANIFEST_FILE_SHA256,
        "CANONICAL_MANIFEST_SHA256": CANONICAL_MANIFEST_SHA256,
        "REQUEST_FILE_SHA256": REQUEST_FILE_SHA256,
    }
    record = _read(root, TASK_RECORD)
    profile = _read(root, COMPONENT_PROFILE)
    edge = blocker(record)
    found = declarations(record) + declarations(profile)
    declaration = found[0] if len(found) == 1 else None
    missing = missing_inputs(record, profile, declaration)
    if len(found) > 1 or missing or "build_manifest" in (declaration or {}):
        raise refusal(
            INPUTS_UNDECLARED,
            f"the canonical records declare exactly one complete {TRANSITION} manifest",
            f"the owning lane declares the {TRANSITION} manifest in {TASK_RECORD}, "
            f"supplying every missing input from an authentic session event; "
            "a build_manifest form is received by the ingress, not built here",
            missing_inputs=missing, declarations_found=len(found),
            satisfying_edge=edge.get("satisfying_edge"),
            inputs_read=[TASK_RECORD, COMPONENT_PROFILE])
    # The declared inputs are held to their schema first: an acting party, route,
    # standing mode or created_at the schema does not admit is refused here.
    validate_declaration(declaration, root)
    validate_epoch(declaration)
    manifest = json.loads(manifest_file_bytes(declaration["manifest"]))
    # The check the ingress applies on receipt runs here next, so no digest is
    # computed, or pinned, for a manifest the ingress would refuse.
    try:
        validate_of(manifest)
    except ImportError as exc:
        raise refusal(SDK_UNAVAILABLE,
                      f"the SDK {INGRESS} imports is installed where the request is built",
                      "install the StegVerse-SDK commit the organization workflows pin, then rebuild",
                      detail=str(exc)) from exc
    except ValueError as exc:
        raise refusal(CONTRACT_INVALID,
                      "the declared manifest passes stegverse.manifest_contract.validate_ingress_manifest",
                      f"correct the declared {TRANSITION} manifest in {TASK_RECORD}",
                      detail=str(exc)) from exc
    # derive_execution_request refuses some manifests the envelope check admits
    # (a processing capability its route does not select, for one). Every digest
    # is taken before any pin is consulted, so that refusal is reached, and
    # returned with its six fields, while the pins are still unset.
    try:
        canonical = canonical_of(manifest)
    except ValueError as exc:
        raise refusal(CANONICAL_REFUSED,
                      f"{INGRESS} derive_execution_request(manifest, boundary()) admits the declared manifest",
                      f"correct the declared {TRANSITION} manifest in {TASK_RECORD} so the ingress derives it",
                      detail=str(exc)) from exc
    request = {
        "schema": SCHEMA,
        "request_id": REQUEST_ID,
        "owning_existing_goal": GOAL,
        "purpose": (f"Append {TRANSITION} to the Organization ledger root under "
                    f"ORGANIZATION_LEDGER_LOCK, satisfying blockers[0] of {GOAL}: "
                    f"{edge['satisfying_edge']}."),
        "manifest": manifest,
        "expected_canonical_manifest_sha256": canonical,
        "standing": declaration["standing"],
        "hb_epoch": declaration["hb_epoch"],
    }
    data = request_file_bytes(request)
    _held_to("MANIFEST_FILE_SHA256", pins["MANIFEST_FILE_SHA256"],
             hashlib.sha256(manifest_file_bytes(manifest)).hexdigest())
    _held_to("CANONICAL_MANIFEST_SHA256", pins["CANONICAL_MANIFEST_SHA256"], canonical)
    _held_to("REQUEST_FILE_SHA256", pins["REQUEST_FILE_SHA256"], hashlib.sha256(data).hexdigest())
    return request, data


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--organization-root", type=Path, required=True,
                   help="StegVerse-Labs/.github checkout whose canonical records and ingress "
                        "the request is built from, and which it is written into")
    a = p.parse_args(argv)
    try:
        _, data = build_request(a.organization_root)
    except Refusal as exc:
        print(json.dumps(exc.record, indent=2, sort_keys=True))
        return 2
    out = a.organization_root / REQUEST_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    print(f"{REQUEST_PATH} {hashlib.sha256(data).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
