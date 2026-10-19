#!/usr/bin/env python3
"""Answer one invariant question against caller-supplied invariant sources.

Reusable task RT-INVARIANT-EVALUATION-001. Two question shapes are accepted,
each under its own schema string and both defined in
source-bundles/reusable-task-registry.d/RT-INVARIANT-EVALUATION-001.json:

- stegverse.invariant-question/v1 names an invariant_id ("invariant:<key>" or
  "prohibition:<NAME>") of the canonical invariants document and a subject
  document; it asks whether the subject's assertions conform.
- stegverse.invariant-pointer-assertion/v1 asserts a value for one JSON
  pointer of the supplied canonical sources.

The answer (stegverse.invariant-evaluation/v1) is:

- ALLOW        every assertion conforms to the declared value
- DENY         an assertion contradicts the declared value
- FAIL_CLOSED  the question or a source cannot be trusted or parsed, a bound
               is exceeded, a canonical source claims an authority effect, or
               the supplied sources disagree
- UNDECIDABLE  the invariant is not declared in the supplied sources, or the
               subject is silent on it; exactly one idempotent relay-queue
               entry names it for its owner

Only the bytes the caller supplies are read: each source carries repo, rev,
path and sha256, and the digest is verified before the bytes are parsed. Nothing
is fetched, no subprocess is started and nothing is written except the optional
write-once relay-queue file the CLI is pointed at. Every citation is
repo@rev:path:line, including on UNDECIDABLE and on a parse refusal (the
refusal line; question bytes are cited as question@<question_sha256>:question:
<line>). Every non-ALLOW carries the six fields of
scripts/validate_transition_disposition.py NON_ALLOW_REQUIRED (plus
evidence_refs). The answer is evidence only: authority_effect is
NONE_ANSWER_ONLY, it admits nothing and commits nothing.

Malformed input never raises: truncated JSON, a digest mismatch, an over-size
or over-depth input and an unhashable or mistyped value all produce a six-field
FAIL_CLOSED answer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from json.decoder import scanstring
from pathlib import Path
from typing import Any, Mapping, Sequence

REUSABLE_TASK_ID = "RT-INVARIANT-EVALUATION-001"
QUESTION_SCHEMA = "stegverse.invariant-question/v1"
ANSWER_SCHEMA = "stegverse.invariant-evaluation/v1"
RELAY_ENTRY_SCHEMA = "stegverse.invariant-relay-queue-entry/v1"
AUTHORITY_EFFECT = "NONE_ANSWER_ONLY"
EVIDENCE_CLASS = "SOURCE_VALIDATION"
POINTER_QUESTION_SCHEMA = "stegverse.invariant-pointer-assertion/v1"
CANONICAL_SCHEMA = "stegverse.task-registry-global-invariants/v1"
CANONICAL_PATH = "data/task-registry-global-invariants.json"
# A canonical source may only describe itself as non-authorizing.
ALLOWED_SOURCE_AUTHORITY_EFFECTS = frozenset({"NONE", "NONE_REGISTRY_INVARIANT_ONLY", "NONE_TEST_FIXTURE", "NONE_ANSWER_ONLY"})
# Keys under which a subject names prohibitions it honours or has violated.
PROHIBITION_HONOURED_KEYS = frozenset({"prohibitions", "honoured_prohibitions", "prohibitions_applied"})
PROHIBITION_VIOLATED_KEYS = frozenset({"violated_prohibitions", "violations", "prohibition_violations"})
# Owner of refusals that precede a well-formed question, and of every
# pointer-assertion answer: the first existing_owner_refs entry of the shard.
OWNING_EXISTING_GOAL = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"
_OWNER_ID = re.compile(r"[A-Z0-9][A-Z0-9-]{2,127}")
RETRY_ENTRYPOINT = "scripts/invariant_evaluation.py --question <question.json> --source <repo> <rev> <path> <sha256> <file>"
# The existing Labs convention for a receiver that cannot answer now: a durable
# write-once queue entry, materialized on the next event, never a poll.
RELAY_CONVENTION = "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION"
RELAY_CONVENTION_REF = "management/UNIVERSAL_DATA_TRANSPORT_INVARIANT.json#receiver_unavailable_disposition"

DISPOSITIONS = ("ALLOW", "DENY", "FAIL_CLOSED", "UNDECIDABLE")

# Every MAX_* bound is declared, with the same value, in the spec's bounds
# (tests/test_invariant_evaluation.py asserts the two agree).
MAX_QUESTION_BYTES = 64 * 1024
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SOURCES = 16
# At most MAX_DEPTH containers ({ or [) may be open at once; the next opening
# bracket fails closed. The value is the spec's bounds.max_json_nesting.
MAX_DEPTH = 64
MAX_CONTAINER_ITEMS = 100_000
MAX_POINTER_TOKENS = 32
MAX_FIELD_CHARS = 512

_WS = re.compile(r"[ \t\n\r]*")
_NUMBER = re.compile(r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][-+]?\d+)?")
_HEX64 = re.compile(r"[0-9a-f]{64}")
_BAD_POINTER_ESCAPE = re.compile(r"~(?![01])")
_LITERALS = (("true", True), ("false", False), ("null", None))


class Refusal(Exception):
    """A bounded, typed reason to answer FAIL_CLOSED."""

    def __init__(self, failure_code: str, failed_predicate: str, repair: str, refs: Sequence[str] = ()):
        super().__init__(failure_code)
        self.failure_code = failure_code
        self.failed_predicate = failed_predicate
        self.repair = repair
        self.refs = list(refs)


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --- bounded, position-aware JSON parser -------------------------------------
#
# The stdlib parser reports no positions and recurses without a caller-set
# bound. This one is recursive descent with an explicit depth limit and an
# explicit item limit per container, and it records the 1-based line of every
# value by JSON pointer so a citation names the line that declares it.


class _Parser:
    def __init__(self, text: str, label: str, cite_prefix: str | None):
        self.text = text
        self.label = label
        self.cite_prefix = cite_prefix
        self.lines: dict[str, int] = {}

    def refuse(self, code: str, predicate: str, idx: int) -> Refusal:
        line = self.text.count("\n", 0, min(idx, len(self.text))) + 1
        # The refusal cites the line it stopped on, as repo@rev:path:line.
        refs = [f"{self.cite_prefix}:{line}"] if self.cite_prefix else []
        return Refusal(code, f"{predicate} at {self.label} line {line}",
                       "supply complete, well-formed JSON within the declared bounds", refs)

    def line_at(self, idx: int) -> int:
        return self.text.count("\n", 0, idx) + 1

    def ws(self, idx: int) -> int:
        return _WS.match(self.text, idx).end()

    def parse(self) -> Any:
        idx = self.ws(0)
        value, idx = self.value(idx, "", 0)
        idx = self.ws(idx)
        if idx != len(self.text):
            raise self.refuse("JSON_TRAILING_DATA", "JSON_SINGLE_VALUE", idx)
        return value

    def value(self, idx: int, pointer: str, depth: int) -> tuple[Any, int]:
        # depth is the number of containers already open around this value.
        if idx >= len(self.text):
            raise self.refuse("JSON_TRUNCATED", "JSON_COMPLETE", idx)
        self.lines.setdefault(pointer, self.line_at(idx))
        ch = self.text[idx]
        if ch in "{[" and depth >= MAX_DEPTH:
            raise self.refuse("INPUT_DEPTH_EXCEEDED", f"JSON_NESTING<={MAX_DEPTH}", idx)
        if ch == "{":
            return self.obj(idx + 1, pointer, depth + 1)
        if ch == "[":
            return self.arr(idx + 1, pointer, depth + 1)
        if ch == '"':
            return self.string(idx + 1)
        for word, literal in _LITERALS:
            if self.text.startswith(word, idx):
                return literal, idx + len(word)
        match = _NUMBER.match(self.text, idx)
        if match:
            raw = match.group()
            try:
                number = float(raw) if any(c in raw for c in ".eE") else int(raw)
            except ValueError:
                # int() refuses more digits than the interpreter's conversion limit.
                raise self.refuse("JSON_NUMBER_OUT_OF_RANGE", "JSON_FINITE_NUMBER", idx) from None
            if number != number or number in (float("inf"), float("-inf")):
                raise self.refuse("JSON_NUMBER_OUT_OF_RANGE", "JSON_FINITE_NUMBER", idx)
            return number, match.end()
        raise self.refuse("JSON_MALFORMED", "JSON_VALUE", idx)

    def string(self, idx: int) -> tuple[str, int]:
        try:
            value, end = scanstring(self.text, idx, True)
        except (ValueError, IndexError):
            raise self.refuse("JSON_TRUNCATED" if '"' not in self.text[idx:] else "JSON_MALFORMED",
                              "JSON_STRING", idx) from None
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            # A \ud800-style escape decodes to a lone surrogate, which no UTF-8 text can carry.
            raise self.refuse("JSON_MALFORMED", "JSON_STRING_UNICODE_SCALAR_VALUES", idx) from None
        return value, end

    def obj(self, idx: int, pointer: str, depth: int) -> tuple[dict[str, Any], int]:
        out: dict[str, Any] = {}
        idx = self.ws(idx)
        if self.text.startswith("}", idx):
            return out, idx + 1
        for _ in range(MAX_CONTAINER_ITEMS):
            if not self.text.startswith('"', idx):
                raise self.refuse("JSON_TRUNCATED" if idx >= len(self.text) else "JSON_MALFORMED",
                                  "JSON_OBJECT_KEY", idx)
            key_idx = idx
            key, idx = self.string(idx + 1)
            if key in out:
                raise self.refuse("JSON_DUPLICATE_KEY", "JSON_UNIQUE_KEYS", key_idx)
            idx = self.ws(idx)
            if not self.text.startswith(":", idx):
                raise self.refuse("JSON_TRUNCATED" if idx >= len(self.text) else "JSON_MALFORMED",
                                  "JSON_OBJECT_COLON", idx)
            child = pointer + "/" + key.replace("~", "~0").replace("/", "~1")
            # A member is cited at the line that names its key.
            self.lines[child] = self.line_at(key_idx)
            out[key], idx = self.value(self.ws(idx + 1), child, depth)
            idx = self.ws(idx)
            if self.text.startswith(",", idx):
                idx = self.ws(idx + 1)
                continue
            if self.text.startswith("}", idx):
                return out, idx + 1
            raise self.refuse("JSON_TRUNCATED" if idx >= len(self.text) else "JSON_MALFORMED",
                              "JSON_OBJECT_DELIMITER", idx)
        raise self.refuse("INPUT_SIZE_EXCEEDED", f"JSON_CONTAINER_ITEMS<={MAX_CONTAINER_ITEMS}", idx)

    def arr(self, idx: int, pointer: str, depth: int) -> tuple[list[Any], int]:
        out: list[Any] = []
        idx = self.ws(idx)
        if self.text.startswith("]", idx):
            return out, idx + 1
        for position in range(MAX_CONTAINER_ITEMS):
            item, idx = self.value(idx, f"{pointer}/{position}", depth)
            out.append(item)
            idx = self.ws(idx)
            if self.text.startswith(",", idx):
                idx = self.ws(idx + 1)
                continue
            if self.text.startswith("]", idx):
                return out, idx + 1
            raise self.refuse("JSON_TRUNCATED" if idx >= len(self.text) else "JSON_MALFORMED",
                              "JSON_ARRAY_DELIMITER", idx)
        raise self.refuse("INPUT_SIZE_EXCEEDED", f"JSON_CONTAINER_ITEMS<={MAX_CONTAINER_ITEMS}", idx)


def parse_json(data: bytes, label: str, limit: int, cite_prefix: str | None = None) -> tuple[Any, dict[str, int]]:
    if not isinstance(data, (bytes, bytearray)):
        raise Refusal("INPUT_BYTES_REQUIRED", f"{label} supplied as bytes",
                      "supply the exact bytes, not a decoded or parsed value")
    # Refused before any line is read, so the refusal cites line 1.
    refs = [f"{cite_prefix}:1"] if cite_prefix else []
    if len(data) > limit:
        raise Refusal("INPUT_SIZE_EXCEEDED", f"{label} bytes<={limit}",
                      "supply a smaller input or split the question", refs)
    try:
        text = bytes(data).decode("utf-8")
    except UnicodeDecodeError:
        raise Refusal("INPUT_NOT_UTF8", f"{label} is UTF-8", "supply UTF-8 JSON bytes", refs) from None
    parser = _Parser(text, label, cite_prefix)
    return parser.parse(), parser.lines


# --- question and sources ------------------------------------------------------


def _field(mapping: Mapping[str, Any], key: str, label: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip() or len(value) > MAX_FIELD_CHARS:
        raise Refusal("INPUT_FIELD_INVALID", f"{label}.{key} is a non-empty string of <= {MAX_FIELD_CHARS} chars",
                      f"supply {label}.{key} as a string")
    return value


def pointer_tokens(pointer: str) -> list[str]:
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise Refusal("QUESTION_POINTER_INVALID", "invariant_pointer is an RFC 6901 JSON pointer",
                      "supply a pointer such as /invariants/<key>")
    if _BAD_POINTER_ESCAPE.search(pointer):
        raise Refusal("QUESTION_POINTER_INVALID", "invariant_pointer escapes ~ only as ~0 or ~1 (RFC 6901)",
                      "escape ~ as ~0 and / as ~1")
    tokens = pointer[1:].split("/")
    if len(tokens) > MAX_POINTER_TOKENS:
        raise Refusal("INPUT_DEPTH_EXCEEDED", f"invariant_pointer tokens<={MAX_POINTER_TOKENS}",
                      "supply a shorter pointer")
    return [t.replace("~1", "/").replace("~0", "~") for t in tokens]


def pointer_of(tokens: Sequence[str]) -> str:
    return "".join("/" + t.replace("~", "~0").replace("/", "~1") for t in tokens)


def _source_ref(question: Mapping[str, Any], key: str) -> dict[str, str]:
    ref = question.get(key)
    label = f"question.{key}"
    if not isinstance(ref, Mapping):
        raise Refusal("QUESTION_WELL_FORMED", f"{label} is an object with repository, path, revision, digest",
                      f"supply {label}")
    out = {k: _field(ref, k, label) for k in ("repository", "path", "revision", "digest")}
    if not (out["digest"].startswith("sha256:") and _HEX64.fullmatch(out["digest"][7:])):
        raise Refusal("QUESTION_WELL_FORMED", f"{label}.digest is sha256:<64 lowercase hex>",
                      f"supply {label}.digest as the sha256 of the bytes it names")
    return out


def parse_question(question_bytes: bytes, question_sha256: str | None = None,
                   context: dict[str, str] | None = None) -> dict[str, Any]:
    prefix = f"question@{question_sha256}:question" if question_sha256 else None
    question, lines = parse_json(question_bytes, "question", MAX_QUESTION_BYTES, prefix)
    if prefix and context is not None:
        context["question_root"] = f"{prefix}:{lines.get('', 1)}"
    try:
        return _check_question(question)
    except Refusal as refusal:
        # A shape refusal of parsed question bytes cites the question root line.
        if prefix and not refusal.refs:
            refusal.refs = [f"{prefix}:{lines.get('', 1)}"]
        raise


def _check_question(question: Any) -> dict[str, Any]:
    if not isinstance(question, dict):
        raise Refusal("QUESTION_OBJECT_REQUIRED", "question is a JSON object", "supply a question object")
    schema = question.get("schema")
    if schema not in (QUESTION_SCHEMA, POINTER_QUESTION_SCHEMA):
        raise Refusal("QUESTION_SCHEMA_UNSUPPORTED", f"question.schema in ({QUESTION_SCHEMA}, {POINTER_QUESTION_SCHEMA})",
                      f"set schema to {QUESTION_SCHEMA} or {POINTER_QUESTION_SCHEMA}")
    _field(question, "question_id", "question")
    if schema == QUESTION_SCHEMA:
        kind, _, name = _field(question, "invariant_id", "question").partition(":")
        if kind not in ("invariant", "prohibition") or not name:
            raise Refusal("QUESTION_WELL_FORMED", "question.invariant_id is invariant:<key> or prohibition:<NAME>",
                          "supply an invariant_id of the canonical invariants document")
        if not _OWNER_ID.fullmatch(_field(question, "owning_existing_goal", "question")):
            raise Refusal("QUESTION_WELL_FORMED", "question.owning_existing_goal is a canonical task id",
                          "name the existing goal that owns the repair, such as STEGVERSE-CANONICAL-WORK-COORDINATION-001")
        _source_ref(question, "invariants_source")
        _source_ref(question, "subject")
        return question
    pointer = question.get("invariant_pointer")
    if not isinstance(pointer, str) or len(pointer) > MAX_FIELD_CHARS:
        raise Refusal("INPUT_FIELD_INVALID", "question.invariant_pointer is a string",
                      "supply question.invariant_pointer as a string")
    pointer_tokens(pointer)
    if "asserted_value" not in question:
        raise Refusal("QUESTION_ASSERTION_REQUIRED", "question.asserted_value present",
                      "supply the value the question asserts")
    return question


def source_binding(source: Any, position: int) -> dict[str, str]:
    label = f"sources[{position}]"
    if not isinstance(source, Mapping):
        raise Refusal("SOURCE_OBJECT_REQUIRED", f"{label} is an object with repo, rev, path, sha256, data",
                      "supply each source as a mapping")
    binding = {key: _field(source, key, label) for key in ("repo", "rev", "path", "sha256")}
    if not _HEX64.fullmatch(binding["sha256"]):
        raise Refusal("SOURCE_DIGEST_INVALID", f"{label}.sha256 is 64 lowercase hex",
                      "supply the sha256 of the source bytes")
    return binding


def cite(binding: Mapping[str, str], line: int) -> str:
    return f"{binding['repo']}@{binding['rev']}:{binding['path']}:{line}"


def resolve(document: Any, tokens: Sequence[str]) -> tuple[bool, Any, int]:
    """(present, value, number of leading tokens that resolve)."""
    node = document
    for depth, token in enumerate(tokens):
        if isinstance(node, dict) and token in node:
            node = node[token]
        elif isinstance(node, list) and token.isdigit() and int(token) < len(node) and (token == "0" or not token.startswith("0")):
            node = node[int(token)]
        else:
            return False, None, depth
    return True, node, len(tokens)


class _Doc:
    """One supplied source: digest verified, then parsed with line positions."""

    def __init__(self, source: Mapping[str, Any], binding: dict[str, str], position: int):
        data = source.get("data")
        label = f"sources[{position}]"
        if not isinstance(data, (bytes, bytearray)):
            raise Refusal("INPUT_BYTES_REQUIRED", f"{label}.data supplied as bytes",
                          "supply the exact source bytes", [cite(binding, 1)])
        # The digest is checked before a single byte is parsed.
        if sha256_hex(bytes(data)) != binding["sha256"]:
            raise Refusal("SOURCE_DIGEST_MISMATCH", f"sha256({label}.data) == {label}.sha256",
                          "supply the bytes the declared digest names, or the digest of the bytes supplied",
                          [cite(binding, 1)])
        prefix = f"{binding['repo']}@{binding['rev']}:{binding['path']}"
        self.binding = binding
        self.doc, self.lines = parse_json(data, prefix, MAX_SOURCE_BYTES, prefix)

    def cite(self, pointer: str = "") -> str:
        return cite(self.binding, self.lines.get(pointer, 1))

    def require_non_authorizing(self) -> None:
        """A canonical source must describe itself with an allowed authority_effect."""
        effect = self.doc.get("authority_effect") if isinstance(self.doc, dict) else None
        if not isinstance(effect, str) or effect not in ALLOWED_SOURCE_AUTHORITY_EFFECTS:
            raise Refusal("SOURCE_AUTHORITY_EFFECT_NOT_ALLOWED",
                          f"canonical source authority_effect is a string in {sorted(ALLOWED_SOURCE_AUTHORITY_EFFECTS)}",
                          "supply a canonical source that claims no authority, or correct it through its owner",
                          [self.cite("/authority_effect" if isinstance(self.doc, dict) and "authority_effect" in self.doc else "")])


def _walk(value: Any, pointer: str = ""):
    """Every object member below value as (pointer, key, member value)."""
    if isinstance(value, dict):
        for key, child in value.items():
            path = pointer + "/" + key.replace("~", "~0").replace("/", "~1")
            yield path, key, child
            yield from _walk(child, path)
    elif isinstance(value, list):
        for position, child in enumerate(value):
            yield from _walk(child, f"{pointer}/{position}")


# --- answer --------------------------------------------------------------------


def evaluation_key(question_sha256: str, bindings: Sequence[Mapping[str, str]]) -> str:
    ordered = sorted((dict(b) for b in bindings), key=lambda b: (b["repo"], b["path"], b["rev"], b["sha256"]))
    return sha256_hex(canonical({"question_sha256": question_sha256, "sources": ordered}))


def _non_allow(answer: dict[str, Any], *, failure_code: str, failed_predicate: str, repair: str,
               evidence_refs: Sequence[str], next_attempt: str, owner: str = OWNING_EXISTING_GOAL) -> dict[str, Any]:
    answer.update({
        "failure_code": failure_code,
        "failed_predicate": failed_predicate,
        "required_evidence_or_repair": repair,
        "retry_entrypoint": RETRY_ENTRYPOINT,
        "owning_existing_goal": owner,
        "next_attempt": next_attempt,
        "evidence_refs": list(evidence_refs) or [f"SOURCE_RECORD_ONLY:{REUSABLE_TASK_ID}"],
    })
    return answer


def _base(question_sha256: str | None, key: str | None) -> dict[str, Any]:
    return {
        "schema": ANSWER_SCHEMA,
        "reusable_task_id": REUSABLE_TASK_ID,
        "question_sha256": question_sha256,
        "evaluation_key": key,
        "evidence_class": EVIDENCE_CLASS,
        "authority_effect": AUTHORITY_EFFECT,
        "consequence_committed": False,
        "citations": [],
    }


def relay_queue_entry(answer: Mapping[str, Any], question: Mapping[str, Any],
                      bindings: Sequence[Mapping[str, str]]) -> dict[str, Any]:
    """The single relay entry an UNDECIDABLE answer names, keyed by evaluation_key."""
    entry = {
        "schema": RELAY_ENTRY_SCHEMA,
        "entry_id": answer["evaluation_key"],
        "queue_disposition": RELAY_CONVENTION,
        "convention_ref": RELAY_CONVENTION_REF,
        "state": "QUEUED_FOR_OWNER_DETERMINATION",
        "relay_to": answer["owning_existing_goal"],
        "question_id": question["question_id"],
        "question_schema": question["schema"],
        "question_sha256": answer["question_sha256"],
        "citations": list(answer["citations"]),
        "sources": sorted((dict(b) for b in bindings), key=lambda b: (b["repo"], b["path"], b["rev"], b["sha256"])),
        "authority_effect": "NONE_RELAY_ONLY",
    }
    for key in ("invariant_pointer", "invariant_id", "subject"):
        if key in question:
            entry[key] = question[key]
    return entry


def _undecidable(answer: dict[str, Any], question: Mapping[str, Any], bindings: Sequence[Mapping[str, str]], *,
                 failure_code: str, failed_predicate: str, repair: str, owner: str) -> dict[str, Any]:
    answer["disposition"] = "UNDECIDABLE"
    _non_allow(answer, failure_code=failure_code, failed_predicate=failed_predicate, repair=repair,
               evidence_refs=list(answer["citations"]) + [f"{b['repo']}@{b['rev']}:{b['path']}#sha256={b['sha256']}" for b in bindings],
               next_attempt="ON_RELAY_QUEUE_ENTRY_ANSWERED_OR_NEW_SOURCE_REVISION", owner=owner)
    answer["relay_queue_entry"] = relay_queue_entry(answer, question, bindings)
    return answer


def _bindings(sources: Any, question_root: str | None = None) -> list[dict[str, str]]:
    try:
        return _check_bindings(sources, question_root)
    except Refusal as refusal:
        # No source binding to cite yet: the refusal cites the question root line.
        if question_root and not refusal.refs:
            refusal.refs = [question_root]
        raise


def _check_bindings(sources: Any, question_root: str | None) -> list[dict[str, str]]:
    if not isinstance(sources, (list, tuple)):
        raise Refusal("SOURCES_LIST_REQUIRED", "sources is a list", "supply the sources as a list")
    if not sources:
        # No source to cite: the refusal cites the question root line.
        raise Refusal("SOURCES_REQUIRED", "at least one source supplied", "supply the invariant source bytes",
                      [question_root] if question_root else [])
    if len(sources) > MAX_SOURCES:
        raise Refusal("INPUT_SIZE_EXCEEDED", f"sources<={MAX_SOURCES}", "supply fewer sources")
    bindings = [source_binding(source, n) for n, source in enumerate(sources)]
    seen: set[tuple[str, str, str]] = set()
    for binding in bindings:
        identity = (binding["repo"], binding["rev"], binding["path"])
        if identity in seen:
            raise Refusal("SOURCE_DUPLICATE", "each repo@rev:path is supplied once", "drop the duplicate source")
        seen.add(identity)
    return bindings


def _evaluate_pointer(question: dict[str, Any], question_sha256: str, sources: Sequence[Any],
                      bindings: list[dict[str, str]]) -> dict[str, Any]:
    key = evaluation_key(question_sha256, bindings)
    tokens = pointer_tokens(question["invariant_pointer"])
    expected = canonical(question["asserted_value"])

    found: list[tuple[Any, str]] = []
    nearest: list[str] = []
    for position, (source, binding) in enumerate(zip(sources, bindings)):
        doc = _Doc(source, binding, position)
        # Every source of a pointer assertion is canonical for it.
        doc.require_non_authorizing()
        present, value, depth = resolve(doc.doc, tokens)
        if present:
            found.append((value, doc.cite(question["invariant_pointer"])))
        else:
            # The deepest container that exists is where the pointer would be declared.
            nearest.append(doc.cite(pointer_of(tokens[:depth])))

    answer = _base(question_sha256, key)
    answer.update({
        "question_id": question["question_id"],
        "invariant_pointer": question["invariant_pointer"],
        "asserted_value": question["asserted_value"],
        "sources": [dict(b) for b in bindings],
        "citations": [c for _, c in found],
        "declared_values": [{"citation": c, "value": v} for v, c in found],
    })
    if not found:
        answer["citations"] = nearest
        return _undecidable(answer, question, bindings, failure_code="INVARIANT_NOT_DECLARED_IN_SUPPLIED_SOURCES",
                            failed_predicate=f"some supplied source declares {question['invariant_pointer']}",
                            repair="the invariant owner declares the pointer in a canonical source, or the caller supplies the source that does",
                            owner=OWNING_EXISTING_GOAL)
    declared = {canonical(v) for v, _ in found}
    if len(declared) > 1:
        raise Refusal("SOURCES_CONFLICT", f"every supplied source declaring {question['invariant_pointer']} agrees",
                      "the invariant owner reconciles the conflicting declarations", answer["citations"])
    if expected in declared:
        answer["disposition"] = "ALLOW"
        return answer
    answer["disposition"] = "DENY"
    return _non_allow(answer, failure_code="INVARIANT_ASSERTION_CONTRADICTED",
                      failed_predicate=f"asserted_value == declared value of {question['invariant_pointer']}",
                      repair="correct the asserted value to the declared one, or change the invariant through its owner",
                      evidence_refs=answer["citations"],
                      next_attempt="ON_CORRECTED_QUESTION_OR_NEW_SOURCE_REVISION")


def _load_ref(question: Mapping[str, Any], role: str, sources: Sequence[Any], bindings: list[dict[str, str]]) -> _Doc:
    ref = _source_ref(question, role)
    for position, binding in enumerate(bindings):
        if (binding["repo"], binding["rev"], binding["path"]) == (ref["repository"], ref["revision"], ref["path"]):
            if ref["digest"] != "sha256:" + binding["sha256"]:
                raise Refusal("SOURCE_DIGEST_MISMATCH", f"question.{role}.digest == sha256 of the supplied source",
                              "cite the digest of the bytes supplied, or supply the bytes the question cites",
                              [cite(binding, 1)])
            return _Doc(sources[position], binding, position)
    raise Refusal("SOURCE_NOT_SUPPLIED", f"question.{role} {ref['repository']}@{ref['revision']}:{ref['path']} is supplied",
                  f"supply the bytes question.{role} cites",
                  [f"{ref['repository']}@{ref['revision']}:{ref['path']}:1"])


def _evaluate_question(question: dict[str, Any], question_sha256: str, sources: Sequence[Any],
                       bindings: list[dict[str, str]], owner: str) -> dict[str, Any]:
    key = evaluation_key(question_sha256, bindings)
    canon = _load_ref(question, "invariants_source", sources, bindings)
    if canon.binding["path"] != CANONICAL_PATH or not isinstance(canon.doc, dict) or canon.doc.get("schema") != CANONICAL_SCHEMA:
        raise Refusal("CANONICAL_SOURCE_INVALID", f"invariants_source is {CANONICAL_PATH} with schema {CANONICAL_SCHEMA}",
                      f"supply {CANONICAL_PATH} at an exact revision", [canon.cite()])
    canon.require_non_authorizing()

    answer = _base(question_sha256, key)
    answer.update({
        "question_id": question["question_id"],
        "invariant_id": question["invariant_id"],
        "sources": [dict(b) for b in bindings],
    })
    kind, _, name = question["invariant_id"].partition(":")
    invariants = canon.doc.get("invariants") if isinstance(canon.doc.get("invariants"), dict) else {}
    prohibitions = canon.doc.get("prohibitions") if isinstance(canon.doc.get("prohibitions"), list) else []
    container = "/invariants" if kind == "invariant" else "/prohibitions"
    if kind == "invariant" and name in invariants:
        declared = invariants[name]
        declaring = canon.cite(pointer_of(["invariants", name]))
    elif kind == "prohibition" and name in prohibitions:
        declared = True
        declaring = canon.cite(f"/prohibitions/{prohibitions.index(name)}")
    else:
        answer["citations"] = [canon.cite(container if container in canon.lines else "")]
        return _undecidable(answer, question, bindings, failure_code="INVARIANT_NOT_DECLARED_IN_SUPPLIED_SOURCES",
                            failed_predicate=f"{container} of the supplied canonical source declares {question['invariant_id']}",
                            repair="the invariant owner declares it in the canonical source, or the caller supplies the revision that does",
                            owner=owner)

    subject = _load_ref(question, "subject", sources, bindings)
    conforming: list[str] = []
    contradicting: list[str] = []
    for path, member, value in _walk(subject.doc):
        if kind == "invariant" and member == name:
            (conforming if canonical(value) == canonical(declared) else contradicting).append(subject.cite(path))
        elif kind == "prohibition" and isinstance(value, list) and name in value:
            at = subject.cite(f"{path}/{value.index(name)}")
            if member in PROHIBITION_HONOURED_KEYS:
                conforming.append(at)
            elif member in PROHIBITION_VIOLATED_KEYS:
                contradicting.append(at)
    answer["citations"] = [declaring] + conforming + contradicting
    if contradicting:
        answer["disposition"] = "DENY"
        return _non_allow(answer, failure_code="INVARIANT_ASSERTION_CONTRADICTED",
                          failed_predicate=f"every subject assertion of {name} equals the declared value",
                          repair=f"repair the subject so every assertion of {name} equals the declared value, or change the invariant through its owner",
                          evidence_refs=[declaring] + contradicting,
                          next_attempt="ON_CORRECTED_SUBJECT_OR_NEW_SOURCE_REVISION", owner=owner)
    if conforming:
        answer["disposition"] = "ALLOW"
        return answer
    # Silence is not conformance.
    answer["citations"] = [declaring, subject.cite()]
    return _undecidable(answer, question, bindings, failure_code="SUBJECT_SILENT_ON_INVARIANT",
                        failed_predicate=f"the subject asserts {name}",
                        repair=f"supply a subject that asserts {name}, or a reader with more evidence answers the relay entry",
                        owner=owner)


def _evaluate(question_bytes: bytes, sources: Sequence[Any], context: dict[str, str]) -> dict[str, Any]:
    question_sha256 = sha256_hex(bytes(question_bytes)) if isinstance(question_bytes, (bytes, bytearray)) else None
    question = parse_question(question_bytes, question_sha256, context)
    if question["schema"] == QUESTION_SCHEMA:
        # The question names the existing goal that owns the repair; from here on
        # every non-ALLOW, refusals included, routes to it.
        context["owner"] = question["owning_existing_goal"]
    bindings = _bindings(sources, context.get("question_root"))
    if question["schema"] == QUESTION_SCHEMA:
        return _evaluate_question(question, question_sha256, sources, bindings, context["owner"])
    return _evaluate_pointer(question, question_sha256, sources, bindings)


def evaluate(question_bytes: bytes, sources: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Answer the question. Never raises for any supplied input."""
    question_sha256 = None
    context = {"owner": OWNING_EXISTING_GOAL}
    try:
        if isinstance(question_bytes, (bytes, bytearray)):
            question_sha256 = sha256_hex(bytes(question_bytes))
        return _evaluate(question_bytes, sources, context)
    except Refusal as refusal:
        answer = _base(question_sha256, None)
        answer["disposition"] = "FAIL_CLOSED"
        answer["citations"] = [r for r in refusal.refs if "@" in r]
        return _non_allow(answer, failure_code=refusal.failure_code, failed_predicate=refusal.failed_predicate,
                          repair=refusal.repair, evidence_refs=refusal.refs,
                          next_attempt="ON_CORRECTED_INPUT_SUPPLIED", owner=context["owner"])
    except (TypeError, ValueError, AttributeError, KeyError, IndexError, RecursionError, OverflowError) as error:
        answer = _base(question_sha256, None)
        answer["disposition"] = "FAIL_CLOSED"
        # Once the question parsed, the rejected value is cited at the question root line.
        answer["citations"] = [context["question_root"]] if "question_root" in context else []
        return _non_allow(answer, failure_code="INPUT_VALUE_REJECTED",
                          failed_predicate=f"input values are of the declared types ({type(error).__name__})",
                          repair="supply hashable, typed values matching the question and source shapes",
                          evidence_refs=answer["citations"], next_attempt="ON_CORRECTED_INPUT_SUPPLIED", owner=context["owner"])


def enqueue(queue_dir: Path, entry: Mapping[str, Any]) -> tuple[Path, bool]:
    """Write the relay entry once. A repeat of the same key writes nothing."""
    path = Path(queue_dir) / f"{entry['entry_id']}.json"
    payload = canonical(entry) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(payload)
    except FileExistsError:
        return path, False
    return path, True


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--question", required=True, type=Path)
    parser.add_argument("--source", nargs=5, action="append", default=[],
                        metavar=("REPO", "REV", "PATH", "SHA256", "FILE"))
    parser.add_argument("--relay-queue-dir", type=Path,
                        help="write the UNDECIDABLE relay entry here, write-once")
    args = parser.parse_args(argv)

    def read(path: Path, limit: int) -> bytes | None:
        # Bounded read: one byte past the limit is enough to refuse.
        try:
            with path.open("rb") as handle:
                return handle.read(limit + 1)
        except OSError:
            return None

    question = read(args.question, MAX_QUESTION_BYTES)
    sources = [{"repo": r, "rev": v, "path": p, "sha256": s, "data": read(Path(f), MAX_SOURCE_BYTES)}
               for r, v, p, s, f in args.source]
    answer = evaluate(question, sources)
    if answer["disposition"] == "UNDECIDABLE" and args.relay_queue_dir is not None:
        path, created = enqueue(args.relay_queue_dir, answer["relay_queue_entry"])
        answer["relay_queue_ref"] = {"path": str(path), "created": created}
    print(json.dumps(answer, indent=2, sort_keys=True))
    return 0 if answer["disposition"] == "ALLOW" else 2


if __name__ == "__main__":
    sys.exit(main())
