#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


class MatrixError(ValueError):
    pass


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def load(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise MatrixError(f"JSON object required: {path}")
    return value


def get_path(value: Mapping[str, Any], dotted: str) -> Any:
    current: Any = value
    for part in dotted.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return None
        current = current[part]
    return current


def compare(actual: Any, op: str, expected: Any) -> bool:
    if op == "eq":
        return actual == expected
    if op == "gte":
        return isinstance(actual, (int, float)) and not isinstance(actual, bool) and actual >= expected
    if op == "in":
        return isinstance(expected, list) and actual in expected
    raise MatrixError(f"unsupported matrix operator: {op}")


def evaluate(matrix: Mapping[str, Any], snapshot: Mapping[str, Any]) -> dict[str, Any]:
    if matrix.get("schema") != "stegverse.test-lanes-autolaunch-matrix/v1":
        raise MatrixError("matrix schema mismatch")
    if snapshot.get("schema") != "stegverse.test-lanes-autolaunch-snapshot/v1":
        raise MatrixError("snapshot schema mismatch")
    if snapshot.get("matrix_id") != matrix.get("matrix_id"):
        raise MatrixError("snapshot matrix identity mismatch")

    authority = matrix.get("authority")
    if not isinstance(authority, Mapping):
        raise MatrixError("matrix authority section required")
    if authority.get("heartbeat_grants_execution_authority") is not False:
        raise MatrixError("heartbeat may not grant execution authority")
    if authority.get("primary_provider") != "stegverse_local":
        raise MatrixError("StegVerse local must remain primary")
    if authority.get("credential_authority") != "TV/TVC":
        raise MatrixError("credential authority drift")
    if authority.get("non_tv_tvc_secret_or_token_allowed") is not False:
        raise MatrixError("NON-TV/TVC secret authority prohibited")

    predicates = matrix.get("predicates")
    if not isinstance(predicates, list) or not predicates:
        raise MatrixError("matrix predicates required")

    rows: list[dict[str, Any]] = []
    blocking: list[str] = []
    prohibitive_failures: list[str] = []
    seen: set[str] = set()
    for raw in predicates:
        if not isinstance(raw, Mapping):
            raise MatrixError("predicate row must be object")
        predicate_id = raw.get("id")
        if not isinstance(predicate_id, str) or not predicate_id:
            raise MatrixError("predicate id required")
        if predicate_id in seen:
            raise MatrixError(f"duplicate predicate: {predicate_id}")
        seen.add(predicate_id)
        klass = raw.get("class")
        if klass not in {"REQUIRED", "OPTIONAL", "PROHIBITIVE", "MACHINE_OWNED", "HUMAN_AUTHORITY"}:
            raise MatrixError(f"invalid predicate class: {predicate_id}")
        path = raw.get("path")
        if not isinstance(path, str) or not path:
            raise MatrixError(f"predicate path required: {predicate_id}")
        actual = get_path(snapshot, path)
        passed = compare(actual, str(raw.get("op")), raw.get("value"))
        required = raw.get("required") is True
        row = {
            "id": predicate_id,
            "class": klass,
            "path": path,
            "required": required,
            "passed": passed,
            "actual": actual,
            "expected": raw.get("value"),
        }
        rows.append(row)
        if required and not passed:
            if klass == "PROHIBITIVE":
                prohibitive_failures.append(predicate_id)
            else:
                blocking.append(predicate_id)

    if prohibitive_failures:
        state = "FAIL_CLOSED"
        transition = matrix.get("fail_closed_transition")
    elif blocking:
        state = "BLOCKED"
        transition = matrix.get("blocked_transition")
    else:
        state = "ALLOW_EXECUTION_CLAIM"
        transition = matrix.get("allow_transition")

    result = {
        "schema": "stegverse.test-lanes-autolaunch-evaluation/v1",
        "matrix_id": matrix.get("matrix_id"),
        "test_id": matrix.get("test_id"),
        "mode": matrix.get("mode"),
        "state": state,
        "next_transition": transition,
        "heartbeat_grants_execution_authority": False,
        "execution_authority_granted": False,
        "fresh_execution_claim_required": state == "ALLOW_EXECUTION_CLAIM",
        "primary_provider": "stegverse_local",
        "third_party_role": "CONTROL_OR_FALLBACK_ONLY",
        "credential_authority": "TV/TVC",
        "non_tv_tvc_secret_or_token_allowed": False,
        "blocking_predicates": blocking,
        "prohibitive_failures": prohibitive_failures,
        "predicate_count": len(rows),
        "passed_predicate_count": sum(1 for row in rows if row["passed"]),
        "rows": rows,
        "matrix_sha256": digest(matrix),
        "snapshot_sha256": digest(snapshot),
    }
    unsigned = dict(result)
    result["evaluation_sha256"] = digest(unsigned)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate the canonical StegVerse nine-lane autolaunch condition matrix. Heartbeat events wake evaluation but never grant execution authority.")
    parser.add_argument("--matrix", type=Path, default=Path("control/test-lanes-autolaunch-matrix.v1.json"))
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        result = evaluate(load(args.matrix), load(args.snapshot))
    except Exception as exc:
        print(json.dumps({"state": "FAIL_CLOSED", "reason": str(exc), "execution_authority_granted": False}, sort_keys=True))
        return 2
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["state"] in {"BLOCKED", "ALLOW_EXECUTION_CLAIM"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
