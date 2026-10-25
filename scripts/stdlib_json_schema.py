"""Standard-library JSON Schema validator for exactly the keywords StegVerse's schemas use (StegVerse-org/.github#166).

The decision (Rigel, relayed by Coordination, Oct 23): no new dependency; reduce the ones there are. The schemas the
schema-only consumer tests exercise (schemas/hil-explanation-trial-record.v1.schema.json,
schemas/user-facing-explanation.v1.schema.json here, and orchestration/schemas/task-registry.schema.json in
StegVerse-org/.github) were enumerated keyword by keyword; this module implements those keywords with Draft 2020-12
semantics and nothing else:

  assertions   type enum const properties required additionalProperties items minItems uniqueItems contains
               minLength pattern minimum maximum minProperties maxProperties allOf anyOf not if then
  annotations  $schema $id $comment title description format

Fail closed, never silently accept:
  * any other keyword anywhere in the schema (else, $ref, prefixItems, oneOf, ...) raises SchemaUnsupported when
    the validator is built, so no instance is ever judged valid against a schema it does not fully understand;
  * a supported keyword in a form not implemented here (items as a list, a non-integer minLength, an unknown type
    name, a pattern that does not compile, ...) raises SchemaUnsupported the same way;
  * $schema, where present at the root, must be Draft 2020-12.

`format` is an annotation, as in Draft 2020-12's default format-annotation vocabulary and as
jsonschema.Draft202012Validator applies it without a format checker: it never decides validity, and the agreement
fixtures show both validators accepting a malformed date-time. `pattern` uses Python's re.search, as jsonschema does.
Equality (enum, const, uniqueItems) treats true/false as distinct from 1/0 and 1 as equal to 1.0, as jsonschema
does. Lowest supported mode E0: no clock, no network, no I/O beyond the CLI's own file reads.

  python3 scripts/stdlib_json_schema.py validate --schema S.json --instance I.json   (exit 0 valid, 1 invalid, 2 refused)
  python3 scripts/stdlib_json_schema.py keywords --schema S.json                     (the keywords a schema uses)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any, Iterator

DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"
ANNOTATIONS = frozenset({"$schema", "$id", "$comment", "title", "description", "format"})
ASSERTIONS = frozenset({"type", "enum", "const", "properties", "required", "additionalProperties", "items",
                        "minItems", "uniqueItems", "contains", "minLength", "pattern", "minimum", "maximum",
                        "minProperties", "maxProperties", "allOf", "anyOf", "not", "if", "then"})
SUPPORTED = ANNOTATIONS | ASSERTIONS
TYPES = frozenset({"null", "boolean", "object", "array", "number", "string", "integer"})
REFUSAL = {"failure_code": "SCHEMA_KEYWORD_UNSUPPORTED", "failed_predicate": "EVERY_SCHEMA_KEYWORD_IS_IMPLEMENTED",
           "retry_entrypoint": "scripts/stdlib_json_schema.py validate",
           "owning_existing_goal": "StegVerse-org/.github#166 ENTERPRISE-HOST-PROVIDER-ERADICATION-001",
           "next_attempt": "the next validation after the keyword is implemented with its own known-good and "
                           "known-bad fixtures and agreement against jsonschema in StegVerse-org/.github CI"}


class SchemaUnsupported(ValueError):
    """The schema uses a keyword, or a keyword form, this validator does not implement. Six fields in .item."""

    def __init__(self, path: str, detail: str):
        super().__init__(f"{path}: {detail}")
        self.item = {"disposition": "FAIL_CLOSED", **REFUSAL, "schema_path": path,
                     "required_evidence_or_repair": f"{path}: {detail}; implement it in scripts/stdlib_json_schema.py "
                                                    "with fixtures, or keep the schema to the supported keywords"}


def _is_int(v: Any) -> bool:
    return (isinstance(v, int) and not isinstance(v, bool)) or (isinstance(v, float) and v.is_integer())


def _is_num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _nonneg_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


def equal(a: Any, b: Any) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if _is_num(a) and _is_num(b):
        return a == b
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    return type(a) is type(b) and a == b


def is_type(v: Any, name: str) -> bool:
    return {"null": v is None, "boolean": isinstance(v, bool), "object": isinstance(v, dict),
            "array": isinstance(v, list), "number": _is_num(v), "string": isinstance(v, str),
            "integer": _is_int(v)}[name]


def _check(schema: Any, path: str, root: bool = False) -> None:
    """Refuse, before any instance is judged, a schema with anything this module does not implement."""
    if isinstance(schema, bool):
        return
    if not isinstance(schema, dict):
        raise SchemaUnsupported(path, f"a schema must be an object or a boolean, not {type(schema).__name__}")
    for k in schema:
        if k not in SUPPORTED:
            raise SchemaUnsupported(f"{path}/{k}", f"keyword {k!r} is not implemented")
    if "$schema" in schema and not root:
        raise SchemaUnsupported(f"{path}/$schema", "$schema below the root (an embedded resource) is not implemented")
    if "$schema" in schema and schema["$schema"] != DRAFT_2020_12:
        raise SchemaUnsupported(f"{path}/$schema", f"dialect {schema['$schema']!r} is not Draft 2020-12")
    for k in ("$id", "$comment", "title", "description", "format"):
        if k in schema and not isinstance(schema[k], str):
            raise SchemaUnsupported(f"{path}/{k}", f"{k} must be a string")
    if "type" in schema:
        t = schema["type"]
        names = t if isinstance(t, list) else [t]
        if not names or not all(isinstance(n, str) and n in TYPES for n in names) or len(set(names)) != len(names):
            raise SchemaUnsupported(f"{path}/type", f"type {t!r} is not a type name or a list of distinct names")
    if "enum" in schema and not isinstance(schema["enum"], list):
        raise SchemaUnsupported(f"{path}/enum", "enum must be an array")
    if "required" in schema and not (isinstance(schema["required"], list) and
                                     all(isinstance(x, str) for x in schema["required"])):
        raise SchemaUnsupported(f"{path}/required", "required must be an array of strings")
    for k in ("minItems", "minLength", "minProperties", "maxProperties"):
        if k in schema and not _nonneg_int(schema[k]):
            raise SchemaUnsupported(f"{path}/{k}", f"{k} must be a non-negative integer")
    for k in ("minimum", "maximum"):
        if k in schema and not _is_num(schema[k]):
            raise SchemaUnsupported(f"{path}/{k}", f"{k} must be a number")
    if "uniqueItems" in schema and not isinstance(schema["uniqueItems"], bool):
        raise SchemaUnsupported(f"{path}/uniqueItems", "uniqueItems must be a boolean")
    if "pattern" in schema:
        if not isinstance(schema["pattern"], str):
            raise SchemaUnsupported(f"{path}/pattern", "pattern must be a string")
        try:
            re.compile(schema["pattern"])
        except re.error as exc:
            raise SchemaUnsupported(f"{path}/pattern", f"pattern does not compile: {exc}") from None
    if "properties" in schema:
        if not isinstance(schema["properties"], dict):
            raise SchemaUnsupported(f"{path}/properties", "properties must be an object")
        for name, sub in schema["properties"].items():
            _check(sub, f"{path}/properties/{name}")
    for k in ("additionalProperties", "items", "contains", "not", "if", "then"):
        if k in schema:
            if isinstance(schema[k], list):
                raise SchemaUnsupported(f"{path}/{k}", f"{k} as an array is not the Draft 2020-12 form")
            _check(schema[k], f"{path}/{k}")
    for k in ("allOf", "anyOf"):
        if k in schema:
            if not isinstance(schema[k], list) or not schema[k]:
                raise SchemaUnsupported(f"{path}/{k}", f"{k} must be a non-empty array")
            for i, sub in enumerate(schema[k]):
                _check(sub, f"{path}/{k}/{i}")


def _errors(v: Any, s: Any, path: str) -> Iterator[str]:
    if s is True:
        return
    if s is False:
        yield f"{path}: false schema"
        return
    if "type" in s:
        names = s["type"] if isinstance(s["type"], list) else [s["type"]]
        if not any(is_type(v, n) for n in names):
            yield f"{path}: type"
    if "const" in s and not equal(v, s["const"]):
        yield f"{path}: const"
    if "enum" in s and not any(equal(v, e) for e in s["enum"]):
        yield f"{path}: enum"
    if isinstance(v, dict):
        props = s.get("properties", {})
        for name in s.get("required", []):
            if name not in v:
                yield f"{path}: required {name}"
        for name, sub in props.items():
            if name in v:
                yield from _errors(v[name], sub, f"{path}/{name}")
        if "additionalProperties" in s:
            for name in v:
                if name not in props:
                    yield from _errors(v[name], s["additionalProperties"], f"{path}/{name}")
        if "minProperties" in s and len(v) < s["minProperties"]:
            yield f"{path}: minProperties"
        if "maxProperties" in s and len(v) > s["maxProperties"]:
            yield f"{path}: maxProperties"
    if isinstance(v, list):
        if "items" in s:
            for i, x in enumerate(v):
                yield from _errors(x, s["items"], f"{path}/{i}")
        if "minItems" in s and len(v) < s["minItems"]:
            yield f"{path}: minItems"
        if s.get("uniqueItems") and any(equal(v[i], v[j]) for i in range(len(v)) for j in range(i + 1, len(v))):
            yield f"{path}: uniqueItems"
        if "contains" in s and not any(next(_errors(x, s["contains"], path), None) is None for x in v):
            yield f"{path}: contains"
    if isinstance(v, str):
        if "minLength" in s and len(v) < s["minLength"]:
            yield f"{path}: minLength"
        if "pattern" in s and not re.search(s["pattern"], v):
            yield f"{path}: pattern"
    if _is_num(v):
        if "minimum" in s and v < s["minimum"]:
            yield f"{path}: minimum"
        if "maximum" in s and v > s["maximum"]:
            yield f"{path}: maximum"
    for i, sub in enumerate(s.get("allOf", [])):
        yield from _errors(v, sub, f"{path}[allOf/{i}]")
    if "anyOf" in s and not any(next(_errors(v, sub, path), None) is None for sub in s["anyOf"]):
        yield f"{path}: anyOf"
    if "not" in s and next(_errors(v, s["not"], path), None) is None:
        yield f"{path}: not"
    if "if" in s and "then" in s and next(_errors(v, s["if"], path), None) is None:
        yield from _errors(v, s["then"], f"{path}[then]")


class Validator:
    """Built once per schema; building refuses (SchemaUnsupported) a schema this module does not fully implement."""

    def __init__(self, schema: Any):
        _check(schema, "#", root=True)
        self.schema = schema

    def errors(self, instance: Any) -> list[str]:
        return list(_errors(instance, self.schema, "$"))

    def is_valid(self, instance: Any) -> bool:
        return next(_errors(instance, self.schema, "$"), None) is None

    def validate(self, instance: Any) -> None:
        errs = self.errors(instance)
        if errs:
            raise ValueError("instance does not validate: " + "; ".join(errs[:5]))


def keywords(schema: Any) -> set[str]:
    """Every keyword a schema uses, read at keyword positions only (property names are not keywords)."""
    found: set[str] = set()

    def walk(s: Any) -> None:
        if not isinstance(s, dict):
            return
        for k, v in s.items():
            found.add(k)
            if k == "properties" and isinstance(v, dict):
                for sub in v.values():
                    walk(sub)
            elif k in ("additionalProperties", "items", "contains", "not", "if", "then", "else", "propertyNames",
                       "unevaluatedProperties", "unevaluatedItems"):
                walk(v)
            elif k in ("allOf", "anyOf", "oneOf", "prefixItems") and isinstance(v, list):
                for sub in v:
                    walk(sub)
            elif k in ("$defs", "definitions", "patternProperties", "dependentSchemas") and isinstance(v, dict):
                for sub in v.values():
                    walk(sub)
    walk(schema)
    return found


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="command", required=True)
    v = sub.add_parser("validate")
    v.add_argument("--schema", required=True)
    v.add_argument("--instance", required=True)
    k = sub.add_parser("keywords")
    k.add_argument("--schema", required=True)
    a = p.parse_args(argv)
    schema = json.loads(open(a.schema, encoding="utf-8").read())
    if a.command == "keywords":
        used = keywords(schema)
        print(json.dumps({"used": sorted(used), "unsupported": sorted(used - SUPPORTED)}, indent=1))
        return 0 if used <= SUPPORTED else 2
    try:
        validator = Validator(schema)
    except SchemaUnsupported as exc:
        print(json.dumps(exc.item, sort_keys=True))
        return 2
    errs = validator.errors(json.loads(open(a.instance, encoding="utf-8").read()))
    print(json.dumps({"valid": not errs, "errors": errs[:20]}, sort_keys=True))
    return 0 if not errs else 1


if __name__ == "__main__":
    raise SystemExit(main())
