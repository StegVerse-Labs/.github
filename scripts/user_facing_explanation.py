#!/usr/bin/env python3
"""Universal user-facing explanation contract (stegverse.user-facing-explanation/v1).

Builds the one versioned explanation artifact every public-facing StegVerse surface
shows for a governed outcome: human-readable prose by default, plus a complete,
self-contained JSON artifact a person can copy into any independent LLM.

This is a scaled-up Human-in-the-Loop (HIL) experiment in actual ecosystem use.
Owner-reported research origin: the conversation between Rigel Randolph and Sara
Katpar (docs/USER_FACING_EXPLANATION_CONTRACT_MIRROR_HANDOFF.md).

Non-authoritative by construction: the artifact is a projection of a canonical
disposition record. It never authorizes, executes, records, verifies, or mutates
anything; it never carries secrets; it never invents evidence; a remediation
draft inside it is unsubmitted and non-authorizing. The canonical receipt,
predicate and evidence it describes remain the only authority.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

SCHEMA = "stegverse.user-facing-explanation/v1"
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "user-facing-explanation.v1.schema.json"
ECOSYSTEM_IDENTIFIER = "STEGVERSE"
EXPLANATION_VERSION = "1.0.0"
RECOGNITION_PROBE_LITERAL = "STEGVERSE_ECOSYSTEM_KNOWLEDGE_PROBE_V1"
RECOGNITION_PROBE_STATUS = "CANDIDATE_NOT_CANONICAL"

DISPOSITIONS = ("ALLOW", "DENY", "FAIL_CLOSED", "UNKNOWN")
OBSERVATIONS = ("OBSERVED", "NOT_AUTHENTICALLY_OBSERVED", "UNKNOWN")
AUTHORITY_SOURCES = ("TASK_REGISTRY", "WORKERCOORDINATOR", "INTERLOCK_INTR", "MANIFEST", "TV_TVC", "KV_SKAP_VAULT", "NONE")
EVIDENCE_KINDS = ("RECEIPT_REF", "PROVENANCE_REF", "SOURCE_REF", "PUBLIC_URL", "DIGEST", "NONE")
PREDICATE_RE = re.compile(r"^[A-Za-z0-9_:.-]{1,160}$")  # canonical predicates are copied verbatim; some producers emit lower-case names
SECRET_KEY_RE = re.compile(r"(token|secret|credential|password|passwd|private[_-]?key|api[_-]?key|bearer|cookie|client[_-]?secret)", re.I)
# Boolean flags that *describe* sanitization are not secret material.
FLAG_KEYS = frozenset({"secrets_present", "credential_material_present"})
# Matched anywhere in a value: the artifact is meant to be copied into third-party
# LLMs, so a credential embedded in prose or a locator must be refused too.
SECRET_VALUE_RE = re.compile(
    r"(^Bearer\s+\S+"
    r"|\bBearer\s+[A-Za-z0-9._~+/-]{16,}=*"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----"
    r"|\bgh[pousr]_[A-Za-z0-9]{20,}"
    r"|\bgithub_pat_[A-Za-z0-9_]{20,}"
    r"|\bsk-[A-Za-z0-9_-]{16,}"
    r"|\bAKIA[0-9A-Z]{16}\b"
    r"|\bxox[abposr]-[A-Za-z0-9-]{10,})"
)

OUTCOME_CLASSES = {
    ("ALLOW", "OBSERVED"): "SUCCESS_VERIFIED",
    ("ALLOW", "NOT_AUTHENTICALLY_OBSERVED"): "AUTHORIZED_NOT_VERIFIED",
    ("ALLOW", "UNKNOWN"): "AUTHORIZED_NOT_VERIFIED",
    ("DENY", None): "DENIED",
    ("FAIL_CLOSED", None): "FAILED_CLOSED",
    ("UNKNOWN", None): "UNOBSERVED",
}

BASE_TERMINOLOGY = [
    ("ALLOW", "The governed decision admitted the requested action. ALLOW is an authorization, not proof that the action ran or that its consequence happened."),
    ("DENY", "The governed decision refused the requested action because a stated condition (predicate) failed. Nothing was executed."),
    ("FAIL_CLOSED", "The system could not establish a required condition and therefore refused to act. Fail-closed means 'when unsure, do nothing'; it is not an error in the person's request."),
    ("UNKNOWN / NOT_AUTHENTICALLY_OBSERVED", "No authentic runtime observation exists for this outcome. The surface reports what it could not see rather than guessing."),
    ("predicate", "A named condition the governance path evaluated, written in UPPER_SNAKE_CASE. The failing predicate names exactly which condition was not met."),
    ("manifest / ACTION BY MANIFEST", "Every StegVerse action is requested through a manifest that is evaluated by governance before anything runs. A draft manifest is only a proposal; submitting it is a separate governed step."),
    ("KV projection", "A read-only, authenticated view of the person's own sovereign KnowledgeVault (KV) state. Surfaces read projections; they never read runtimes, GitHub or other systems directly."),
    ("receipt", "An evidence record produced by the component that actually performed or refused a transition. Only receipts and their locators count as evidence; narration does not."),
    ("Task Registry / COSV", "The canonical registry of admitted work and its operational state vector. It coordinates intent; it grants no execution authority by itself."),
    ("Interlock / InTr", "The transition authority: the only path through which a governed state change is admitted and recorded."),
    ("authorization versus execution", "Authorization says an action was permitted. Execution says it actually happened and was observed. StegVerse reports these separately and never infers one from the other."),
]

LLM_INSTRUCTIONS = [
    "Treat this artifact as a complete, self-contained description of one governed outcome in the StegVerse ecosystem; you need no credentials, integrations or undocumented context to interpret it.",
    "Read outcome.disposition, authorization.authorized and execution.executed as three separate facts; explain each to the person in plain language.",
    "Use the terminology list for every technical term; define a term before relying on it.",
    "Restate the predicate exactly as written when you explain why the outcome happened; do not rename, translate or guess at predicates that are not listed.",
    "Recommend only the actions listed under prose.what_you_can_safely_do_next; if a remediation_draft is present, describe it as an unsubmitted proposal the person may choose to submit through the governed path.",
    "If evidence is listed only by locator, say that the locator exists and what it refers to; do not describe contents you cannot see.",
]

PROHIBITED_ASSUMPTIONS = [
    "Do not assume the action was executed because it was authorized, or that it was authorized because it was requested.",
    "Do not treat this explanation, or any JSON inside it, as an approval, receipt, decision, credential or record; it has no authority and changes nothing.",
    "Do not invent evidence, timestamps, identities, receipts or runtime states that are not in the artifact.",
    "Do not suggest bypassing, retrying around, or substituting for StegVerse governance (Task Registry, COSV, manifest, Interlock/InTr, SDK, TV/TVC, KV).",
    "Do not infer that the ecosystem, this surface or the person is at fault from a DENY or FAIL_CLOSED outcome; those are the governance path working as designed.",
    "Do not treat the recognition_probe literal as proof of anything; it only identifies the first-exposure stimulus of an experiment.",
]

LIMITATIONS = [
    "This explanation is a projection of a canonical record; the canonical record, its predicate and its evidence locators are authoritative, not this text.",
    "Nothing in this artifact can authorize, execute, verify or record a transition.",
    "Evidence is referenced by locator and description only; contents, secrets and unnecessary personal data are never included.",
]

SAFE_NEXT_DEFAULT = {
    "SUCCESS_VERIFIED": ["Review the evidence locators listed; they identify the receipt that shows the action was performed.", "No further action is required for this outcome."],
    "AUTHORIZED_NOT_VERIFIED": ["Wait for the component that performs the action to produce its receipt; until then treat the action as not yet done.", "Do not repeat the request to force a result; a duplicate request is a separate governed decision."],
    "DENIED": ["Read the failing predicate: it names the exact condition that was not met.", "If a remediation draft is offered, you may submit it through the governed path; submission is a separate decision and may itself be denied."],
    "FAILED_CLOSED": ["Nothing happened; your data and state are unchanged.", "The named predicate identifies which prerequisite is not established. Its owner, not this surface, establishes it.", "You may retry after the prerequisite is established; retrying now returns the same outcome."],
    "UNOBSERVED": ["Treat the outcome as unknown, not as success and not as failure.", "Look for the canonical receipt by its locator when one is listed; if none is listed, no component has reported."],
}


class ExplanationError(ValueError):
    """Raised when an outcome record cannot be explained without breaking an invariant."""


def _reject_secrets(value: Any, path: str = "") -> None:
    if isinstance(value, dict):
        for key, inner in value.items():
            if key in FLAG_KEYS and isinstance(inner, bool):
                continue
            if SECRET_KEY_RE.search(str(key)):
                raise ExplanationError("secret_material_present:" + (path + "." if path else "") + str(key))
            _reject_secrets(inner, (path + "." if path else "") + str(key))
    elif isinstance(value, list):
        for index, inner in enumerate(value):
            _reject_secrets(inner, path + "[" + str(index) + "]")
    elif isinstance(value, str) and SECRET_VALUE_RE.search(value):
        raise ExplanationError("secret_material_present:" + (path or "<root>"))


# Characters that make text display as something other than what it is: format characters (bidi
# overrides and isolates, zero-width), lone surrogates, line/paragraph separators and control characters
# other than tab, newline and carriage return. The prose and the portable JSON are read by people and
# pasted into third-party LLMs, so such text is refused rather than passed through.
_HIDDEN_CATEGORIES = {"Cf", "Cs", "Zl", "Zp"}
_ALLOWED_CONTROLS = {"\t", "\n", "\r"}


def _reject_hidden_text(value: Any, path: str = "") -> None:
    if isinstance(value, dict):
        for key, inner in value.items():
            _reject_hidden_text(str(key), (path + "." if path else "") + "<key>")
            _reject_hidden_text(inner, (path + "." if path else "") + str(key))
    elif isinstance(value, list):
        for index, inner in enumerate(value):
            _reject_hidden_text(inner, path + "[" + str(index) + "]")
    elif isinstance(value, str):
        for ch in value:
            category = unicodedata.category(ch)
            if category in _HIDDEN_CATEGORIES or (category == "Cc" and ch not in _ALLOWED_CONTROLS):
                raise ExplanationError("text_not_displayable:" + (path or "<root>"))


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise ExplanationError(code)


def _str(value: Any, code: str) -> str:
    _require(isinstance(value, str) and value.strip() != "", code)
    return value


def _predicate(value: Any, code: str) -> str:
    _require(isinstance(value, str) and PREDICATE_RE.match(value) is not None, code)
    return value


def _evidence(items: Any) -> list[dict[str, Any]]:
    _require(items is None or isinstance(items, list), "evidence_invalid")
    out: list[dict[str, Any]] = []
    for item in items or []:
        _require(isinstance(item, dict), "evidence_item_invalid")
        kind = item.get("kind")
        _require(kind in EVIDENCE_KINDS, "evidence_kind_invalid")
        ref = item.get("ref")
        _require(ref is None or (isinstance(ref, str) and ref.strip() != ""), "evidence_ref_invalid")
        _require(not (kind != "NONE" and ref is None), "evidence_ref_required_for_kind:" + str(kind))
        out.append({"kind": kind, "ref": ref, "description": _str(item.get("description"), "evidence_description_required"), "sanitized": True})
    return out


def _remediation(draft: Any) -> dict[str, Any] | None:
    if draft is None:
        return None
    _require(isinstance(draft, dict), "remediation_draft_invalid")
    _require(draft.get("submitted") is False, "remediation_draft_must_be_unsubmitted")
    _require(draft.get("manifest_admitted") is False, "remediation_draft_must_not_be_admitted")
    _require(draft.get("authority_effect") in ("NONE_REQUEST_ONLY", "NONE"), "remediation_draft_must_be_non_authorizing")
    _require(draft.get("disposition") not in ("ALLOW",), "remediation_draft_must_not_carry_allow")
    return {"submitted": False, "manifest_admitted": False, "authority_effect": "NONE_REQUEST_ONLY", "non_authorizing": True, "draft": dict(draft)}


def _prose(outcome_class: str, action: str, predicate: str, authority_source: str, why: str | None, evidence: list[dict[str, Any]], next_steps: list[str] | None, draft_present: bool) -> dict[str, Any]:
    ev = ("Evidence is referenced by locator: " + "; ".join(e["description"] + (" (" + e["ref"] + ")" if e["ref"] else "") for e in evidence) + ".") if evidence else "No evidence record is referenced for this outcome; nothing has been produced by a component that performs or refuses this action."
    default_reason = {
        "SUCCESS_VERIFIED": "the condition " + predicate + " was satisfied and the performing component reported its receipt",
        "AUTHORIZED_NOT_VERIFIED": "the condition " + predicate + " was satisfied, but no receipt from the performing component has been observed",
        "DENIED": "the condition " + predicate + " failed",
        "FAILED_CLOSED": "the prerequisite named by " + predicate + " is not established, and the system never acts on an unestablished prerequisite",
        "UNOBSERVED": "no authentic observation reached this surface; the reported condition is " + predicate,
    }[outcome_class]
    reason = why or default_reason
    if outcome_class == "SUCCESS_VERIFIED":
        what = "The request '" + action + "' was authorized and its execution was observed."
        summary = "Succeeded and verified."
        authorized = "The action '" + action + "' was authorized by " + authority_source + " under the condition " + predicate + "."
        executed = "The action was executed and its consequence was observed by the component that performed it."
    elif outcome_class == "AUTHORIZED_NOT_VERIFIED":
        what = "The request '" + action + "' was authorized, but no authentic observation of its execution exists yet."
        summary = "Authorized; execution not verified."
        authorized = "The action '" + action + "' was authorized by " + authority_source + " under the condition " + predicate + "."
        executed = "Nothing is known to have been executed: no receipt from the performing component has been observed. Authorization is not execution."
    elif outcome_class == "DENIED":
        what = "The request '" + action + "' was refused."
        summary = "Denied; nothing was executed."
        authorized = "Nothing was authorized. The governed decision returned DENY because " + predicate + " failed."
        executed = "Nothing was executed and no state changed."
    elif outcome_class == "FAILED_CLOSED":
        what = "The request '" + action + "' could not be evaluated because a required prerequisite is not established, so the system refused to act."
        summary = "Failed closed; nothing was executed."
        authorized = "Nothing was authorized. The governance path returned FAIL_CLOSED on " + predicate + ", which names the missing prerequisite."
        executed = "Nothing was executed and no state changed. Failing closed is the designed behaviour when a prerequisite is missing, not a fault in the request."
    else:
        what = "The outcome of the request '" + action + "' is unknown: no authentic observation of a decision or an execution exists."
        summary = "Unknown; not success, not failure."
        authorized = "No authorization is known. The reported condition is " + predicate + "."
        executed = "No execution is known. Treat the action as not done until a receipt is observed."
    steps = list(next_steps) if next_steps else list(SAFE_NEXT_DEFAULT[outcome_class])
    if draft_present:
        steps.append("An unsubmitted remediation draft is attached; it proposes nothing until you submit it through the governed path, where it receives its own decision.")
    return {
        "what_happened": what,
        "why": "Because " + reason + ".",
        "outcome_summary": summary,
        "what_was_authorized": authorized,
        "what_was_executed": executed,
        "what_evidence_exists": ev,
        "what_you_can_safely_do_next": steps,
        "limitations": list(LIMITATIONS),
    }


def build_explanation(record: dict[str, Any], *, surface: dict[str, Any], terminology: list[tuple[str, str]] | None = None) -> dict[str, Any]:
    """Project a canonical outcome record into the explanation artifact.

    ``record`` is producer-supplied and already canonical; only whitelisted fields are
    read, so unnecessary personal data never reaches the artifact. Secrets anywhere in
    the record or surface descriptor abort the build.
    """
    _require(isinstance(record, dict), "record_invalid")
    _require(isinstance(surface, dict), "surface_invalid")
    _reject_secrets(record)
    _reject_secrets(surface)
    _reject_hidden_text(record)
    _reject_hidden_text(surface)
    disposition = record.get("disposition")
    _require(disposition in DISPOSITIONS, "disposition_invalid")
    predicate = _predicate(record.get("predicate"), "predicate_invalid")
    predicates = record.get("predicates") or [predicate]
    _require(isinstance(predicates, list) and all(isinstance(p, str) and PREDICATE_RE.match(p) for p in predicates), "predicates_invalid")
    if predicate not in predicates:
        predicates = [predicate] + list(predicates)
    predicates = list(dict.fromkeys(predicates))
    action = _str(record.get("requested_action"), "requested_action_required")
    authority_source = record.get("authority_source", "NONE")
    _require(authority_source in AUTHORITY_SOURCES, "authority_source_invalid")
    observation = record.get("consequence_observation", "UNKNOWN")
    _require(observation in OBSERVATIONS, "consequence_observation_invalid")
    if disposition != "ALLOW":
        _require(observation != "OBSERVED", "non_allow_cannot_observe_consequence")
    evidence = _evidence(record.get("evidence"))
    if disposition == "ALLOW" and observation == "OBSERVED":
        _require(any(e["kind"] in ("RECEIPT_REF", "PROVENANCE_REF", "DIGEST") for e in evidence), "observed_execution_requires_receipt_evidence")
    outcome_class = OUTCOME_CLASSES[(disposition, observation if disposition == "ALLOW" else None)]
    authorized = disposition == "ALLOW"
    executed = disposition == "ALLOW" and observation == "OBSERVED"
    execution_state = "VERIFIED" if executed else ("NOT_VERIFIED" if authorized else "NOT_EXECUTED")
    why = record.get("why")
    _require(why is None or (isinstance(why, str) and why.strip() != ""), "why_invalid")
    next_steps = record.get("safe_next_steps")
    _require(next_steps is None or (isinstance(next_steps, list) and all(isinstance(s, str) and s.strip() for s in next_steps)), "safe_next_steps_invalid")
    draft = _remediation(record.get("remediation_draft"))
    canonical_ref = record.get("canonical_record_ref")
    _require(canonical_ref is None or (isinstance(canonical_ref, str) and canonical_ref.strip() != ""), "canonical_record_ref_invalid")
    terms = list(BASE_TERMINOLOGY) + [(t, d) for t, d in (terminology or [])]
    artifact: dict[str, Any] = {
        "schema": SCHEMA,
        "ecosystem_identifier": ECOSYSTEM_IDENTIFIER,
        "explanation_type": "OUTCOME_EXPLANATION",
        "explanation_version": EXPLANATION_VERSION,
        "surface": {k: surface[k] for k in ("repository", "surface_id", "surface_version") if k in surface},
        "outcome": {"disposition": disposition, "observation_state": observation if disposition == "ALLOW" else ("UNKNOWN" if disposition == "UNKNOWN" else "NOT_AUTHENTICALLY_OBSERVED"), "outcome_class": outcome_class, "predicate": predicate, "predicates": predicates, "canonical_record_ref": canonical_ref},
        "authorization": {"authorized": authorized, "requested_action": action, "authority_source": authority_source},
        "execution": {"executed": executed, "execution_state": execution_state, "consequence_observation": observation if disposition == "ALLOW" else ("UNKNOWN" if disposition == "UNKNOWN" else "NOT_AUTHENTICALLY_OBSERVED")},
        "prose": _prose(outcome_class, action, predicate, authority_source, why, evidence, next_steps, draft is not None),
        "terminology": [{"term": t, "definition": d} for t, d in terms],
        "evidence": evidence,
        "remediation_draft": draft,
        "llm_interpretation": {"instructions": list(LLM_INSTRUCTIONS), "prohibited_assumptions": list(PROHIBITED_ASSUMPTIONS), "self_contained": True},
        "authority": {"authority_effect": "NONE", "explanation_is_non_authoritative": True, "canonical_record_mutation": False, "alternate_governance_path": False},
        "sanitization": {"secrets_present": False, "personal_data_minimized": True, "invented_evidence": False},
        "recognition_probe": {"literal": RECOGNITION_PROBE_LITERAL, "status": RECOGNITION_PROBE_STATUS, "note": "Identifies the first-exposure stimulus of the scaled-up HIL experiment; echoing it proves nothing."},
    }
    if isinstance(record.get("produced_at"), str) and record["produced_at"]:
        artifact["produced_at"] = record["produced_at"]
    _require(len(json.dumps(artifact)) > 0, "artifact_unserializable")
    return artifact


def render_prose(artifact: dict[str, Any]) -> str:
    """Default presentation: prose only, no predicates or JSON as the primary experience."""
    p = artifact["prose"]
    lines = [
        "What happened: " + p["what_happened"],
        "Why: " + p["why"],
        "Outcome: " + p["outcome_summary"],
        "What was authorized: " + p["what_was_authorized"],
        "What was executed: " + p["what_was_executed"],
        "What evidence exists: " + p["what_evidence_exists"],
        "What you can safely do next:",
    ]
    lines += ["  - " + s for s in p["what_you_can_safely_do_next"]]
    lines.append("Limitations:")
    lines += ["  - " + s for s in p["limitations"]]
    return "\n".join(lines) + "\n"


# --- minimal JSON-schema checker (the subset the contract schema uses; no third-party dependency) ---

def _type_ok(value: Any, type_name: str) -> bool:
    return {"object": isinstance(value, dict), "array": isinstance(value, list), "string": isinstance(value, str), "boolean": isinstance(value, bool), "null": value is None, "number": isinstance(value, (int, float)) and not isinstance(value, bool), "integer": isinstance(value, int) and not isinstance(value, bool)}[type_name]


def _matches(value: Any, schema: dict[str, Any]) -> bool:
    try:
        schema_check(value, schema, "")
        return True
    except ExplanationError:
        return False


def schema_check(value: Any, schema: dict[str, Any], path: str = "$") -> None:
    if "const" in schema:
        _require(value == schema["const"], "schema:const:" + path)
    if "enum" in schema:
        _require(value in schema["enum"], "schema:enum:" + path)
    if "type" in schema:
        types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        _require(any(_type_ok(value, t) for t in types), "schema:type:" + path)
    if isinstance(value, str):
        if "minLength" in schema:
            _require(len(value) >= schema["minLength"], "schema:minLength:" + path)
        if "pattern" in schema:
            _require(re.search(schema["pattern"], value) is not None, "schema:pattern:" + path)
    if isinstance(value, list):
        if "minItems" in schema:
            _require(len(value) >= schema["minItems"], "schema:minItems:" + path)
        if schema.get("uniqueItems"):
            _require(len({json.dumps(v, sort_keys=True) for v in value}) == len(value), "schema:uniqueItems:" + path)
        if "items" in schema:
            for index, item in enumerate(value):
                schema_check(item, schema["items"], path + "[" + str(index) + "]")
        if "contains" in schema:
            _require(any(_matches(item, schema["contains"]) for item in value), "schema:contains:" + path)
    if isinstance(value, dict):
        for key in schema.get("required", []):
            _require(key in value, "schema:required:" + path + "." + key)
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in value:
                _require(key in props, "schema:additionalProperties:" + path + "." + key)
        for key, sub in props.items():
            if key in value:
                schema_check(value[key], sub, path + "." + key)
    if isinstance(value, dict) and "maxProperties" in schema:
        _require(len(value) <= schema["maxProperties"], "schema:maxProperties:" + path)
    if isinstance(value, (int, float)) and not isinstance(value, bool) and "minimum" in schema:
        _require(value >= schema["minimum"], "schema:minimum:" + path)
    if "not" in schema:
        _require(not _matches(value, schema["not"]), "schema:not:" + path)
    if "anyOf" in schema:
        _require(any(_matches(value, sub) for sub in schema["anyOf"]), "schema:anyOf:" + path)
    for sub in schema.get("allOf", []):
        if "if" in sub:
            if _matches(value, sub["if"]):
                schema_check(value, sub["then"], path)
        else:
            schema_check(value, sub, path)


def validate_explanation(artifact: dict[str, Any], schema_path: Path = SCHEMA_PATH) -> dict[str, Any]:
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    schema_check(artifact, schema)
    _reject_secrets(artifact)
    _reject_hidden_text(artifact)
    # Invariants the schema cannot express structurally.
    _require(artifact["outcome"]["predicate"] in artifact["outcome"]["predicates"], "predicate_not_in_predicates")
    _require(artifact["remediation_draft"] is None or artifact["remediation_draft"]["draft"].get("submitted") is False, "remediation_draft_submitted")
    for e in artifact["evidence"]:
        _require(e["kind"] == "NONE" or (isinstance(e["ref"], str) and e["ref"].strip() != ""), "evidence_ref_missing")
    return artifact



# Reason catalogs (surface compatibility requirement 7): a producer that refuses or decides gives each
# predicate it can return a plain-language reason, so the "Why" a person reads is never only a restated
# predicate. A "PREFIX:detail" predicate uses its prefix's reason.
_PREDICATE_TOKEN_RE = re.compile(r"\b(?:[A-Z]{2,}(?:_[A-Z0-9]+)+|[a-z]+(?:_[a-z0-9]+)+)\b")


def reason_key(predicate: str) -> str:
    return predicate.split(":", 1)[0]


def check_reason_catalog(reasons: dict[str, str], predicates: set[str] | list[str]) -> list[str]:
    """Return the violations of a surface's reason catalog against the predicates its source can return
    (empty list = conforms). Checks: every predicate (by prefix) has a reason, every reason names a
    returnable predicate, and every reason is plain language: non-empty, starts lower-case so it reads
    after "Because", carries no trailing full stop, and restates no predicate-shaped token."""
    violations: list[str] = []
    keys = {reason_key(p) for p in predicates}
    if not isinstance(reasons, dict):
        return ["reasons_not_a_mapping"]
    for key in sorted(keys - set(reasons)):
        violations.append("predicate_without_reason:" + key)
    for key in sorted(set(reasons) - keys):
        violations.append("reason_without_returnable_predicate:" + key)
    for key, text in sorted(reasons.items()):
        if not isinstance(text, str) or len(text.strip()) < 20 or text != text.strip():
            violations.append("reason_too_short_or_untrimmed:" + str(key))
            continue
        if not text[0].islower():
            violations.append("reason_must_start_lower_case:" + key)
        if text.endswith("."):
            violations.append("reason_must_not_end_with_full_stop:" + key)
        if _PREDICATE_TOKEN_RE.search(text):
            violations.append("reason_restates_a_predicate:" + key)
    return violations

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--outcome", required=True, help="path to a canonical outcome record (JSON)")
    parser.add_argument("--surface-repository", required=True)
    parser.add_argument("--surface-id", required=True)
    parser.add_argument("--surface-version")
    parser.add_argument("--prose", action="store_true", help="print the default prose instead of the JSON artifact")
    args = parser.parse_args(argv)
    try:
        record = json.loads(Path(args.outcome).read_text(encoding="utf-8"))
        surface = {"repository": args.surface_repository, "surface_id": args.surface_id}
        if args.surface_version:
            surface["surface_version"] = args.surface_version
        artifact = validate_explanation(build_explanation(record, surface=surface))
    except (ExplanationError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"schema": SCHEMA, "disposition": "FAIL_CLOSED", "predicate": "EXPLANATION_NOT_BUILDABLE", "reason": str(exc)}))
        return 2
    sys.stdout.write(render_prose(artifact) if args.prose else json.dumps(artifact, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
