"""Stdlib JSON Schema subset validator for the NWI-S0 schemas (no new dependency).

Implements exactly the keywords those schemas use and refuses any other keyword, so a schema
cannot silently rely on something unchecked. Yields (json_pointer, keyword) per violation.
"""
from __future__ import annotations

import re
from typing import Any, Iterator

ANNOTATIONS = {"$id", "$schema", "title", "description", "$comment", "x-derivation", "x-migrated-unknown-allowed", "x-carrier",
               "x-canonical-serialization"}
KEYWORDS = {"type", "properties", "required", "additionalProperties", "items", "enum", "const", "pattern", "minLength",
            "minItems", "minimum", "uniqueItems", "anyOf", "allOf", "not", "if", "then", "propertyNames"}
_TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}


def _type_ok(v: Any, t: str) -> bool:
    if t == "integer":
        return isinstance(v, int) and not isinstance(v, bool)
    if t == "number":
        return isinstance(v, (int, float)) and not isinstance(v, bool)
    return isinstance(v, _TYPES[t])


def errors(inst: Any, schema: dict, path: str = "") -> Iterator[tuple[str, str]]:
    unknown = set(schema) - KEYWORDS - ANNOTATIONS
    if unknown:
        raise ValueError("unsupported schema keywords at %s: %s" % (path or "/", sorted(unknown)))
    here = path or "/"
    if "type" in schema:
        ts = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_type_ok(inst, t) for t in ts):
            yield here, "type"
            return
    if "const" in schema and inst != schema["const"]:
        yield here, "const"
    if "enum" in schema and inst not in schema["enum"]:
        yield here, "enum"
    if isinstance(inst, str):
        if "minLength" in schema and len(inst) < schema["minLength"]:
            yield here, "minLength"
        if "pattern" in schema and re.search(schema["pattern"], inst) is None:
            yield here, "pattern"
    if isinstance(inst, (int, float)) and not isinstance(inst, bool) and "minimum" in schema and inst < schema["minimum"]:
        yield here, "minimum"
    if isinstance(inst, list):
        if "minItems" in schema and len(inst) < schema["minItems"]:
            yield here, "minItems"
        if schema.get("uniqueItems") and len({repr(x) for x in inst}) != len(inst):
            yield here, "uniqueItems"
        if "items" in schema:
            for i, x in enumerate(inst):
                yield from errors(x, schema["items"], "%s/%d" % (path, i))
    if isinstance(inst, dict):
        for r in schema.get("required", []):
            if r not in inst:
                yield "%s/%s" % (path, r), "required"
        props = schema.get("properties", {})
        for k, v in inst.items():
            if "propertyNames" in schema and list(errors(k, schema["propertyNames"])):
                yield "%s/%s" % (path, k), "propertyNames"
            if k in props:
                yield from errors(v, props[k], "%s/%s" % (path, k))
            elif schema.get("additionalProperties") is False:
                yield "%s/%s" % (path, k), "additionalProperties"
            elif isinstance(schema.get("additionalProperties"), dict):
                yield from errors(v, schema["additionalProperties"], "%s/%s" % (path, k))
    for sub in schema.get("allOf", []):
        yield from errors(inst, sub, path)
    if "anyOf" in schema and not any(not list(errors(inst, s, path)) for s in schema["anyOf"]):
        yield here, "anyOf"
    if "not" in schema and not list(errors(inst, schema["not"], path)):
        yield here, "not"
    if "if" in schema and not list(errors(inst, schema["if"], path)) and "then" in schema:
        yield from errors(inst, schema["then"], path)


def validate(inst: Any, schema: dict) -> list[tuple[str, str]]:
    return sorted(set(errors(inst, schema)))
