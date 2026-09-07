from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

TASK_ID = "AUTHORITY-TIME-GOVERNANCE-COORDINATE-001"
WORKER_ID = "authority-time-governance-coordinate-worker"
SCHEMA = "stegverse.authority-time-governance-conformance-receipt/v1"

NON_AUTHORIZING_SIGNALS = {
    "wall_clock": "TIME_REFERENCE_ONLY",
    "heartbeat": "OBSERVATION_REFERENCE_ONLY",
    "observer_freshness": "OBSERVATION_ONLY",
    "workflow_success": "VALIDATION_EVIDENCE_ONLY",
    "carrier_correctness": "TRANSPORT_CONSISTENCY_ONLY",
}

AUTHORIZED_AUTHORITY_SOURCES = {
    "StegCore/StegGate",
    "InTr/Interlock",
    "TV/TVC",
}

FORBIDDEN_AUTHORITY_KEYS = {
    "wall_clock_grants_authority",
    "heartbeat_grants_authority",
    "observer_freshness_grants_authority",
    "workflow_success_grants_authority",
    "carrier_correctness_grants_authority",
}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _walk(value: Any, prefix: str = "") -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for key in sorted(value):
            path = f"{prefix}.{key}" if prefix else key
            child = value[key]
            yield path, child
            yield from _walk(child, path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            path = f"{prefix}[{index}]"
            yield path, child
            yield from _walk(child, path)


def evaluate_declaration(declaration: dict[str, Any]) -> dict[str, Any]:
    violations: list[dict[str, Any]] = []

    for path, value in _walk(declaration):
        key = path.rsplit(".", 1)[-1]
        if key in FORBIDDEN_AUTHORITY_KEYS and value is True:
            violations.append(
                {
                    "path": path,
                    "code": "NON_AUTHORIZING_SIGNAL_PROMOTED_TO_AUTHORITY",
                    "value": value,
                }
            )

    asserted_source = declaration.get("authority_source")
    protected_boundary = bool(declaration.get("protected_boundary", False))
    requested_transition = bool(declaration.get("requests_transition", False))
    disposition = declaration.get("disposition")

    if protected_boundary and requested_transition:
        if asserted_source not in AUTHORIZED_AUTHORITY_SOURCES:
            violations.append(
                {
                    "path": "authority_source",
                    "code": "PROTECTED_BOUNDARY_AUTHORITY_MISSING_OR_UNKNOWN",
                    "value": asserted_source,
                }
            )
        if disposition == "ALLOW" and asserted_source is None:
            violations.append(
                {
                    "path": "disposition",
                    "code": "ALLOW_WITHOUT_SEPARATE_AUTHORITY",
                    "value": disposition,
                }
            )

    if declaration.get("human_review_timeout_result") == "ALLOW":
        violations.append(
            {
                "path": "human_review_timeout_result",
                "code": "HUMAN_TIMEOUT_MUST_NOT_SILENTLY_ALLOW",
                "value": "ALLOW",
            }
        )

    state = "PASS" if not violations else "FAIL_CLOSED"
    normalized = {
        "task_id": TASK_ID,
        "state": state,
        "violations": violations,
        "authority_effect": "NONE_VALIDATION_ONLY",
        "credential_authority": "TV/TVC",
        "runtime_admissibility_authority": "StegCore/StegGate",
        "packet_transition_governance": "InTr/Interlock",
        "non_authorizing_signals": NON_AUTHORIZING_SIGNALS,
    }
    normalized["input_sha256"] = _sha256(_canonical_json(declaration))
    normalized["receipt_sha256"] = _sha256(_canonical_json(normalized))
    return normalized


def evaluate_file(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        receipt = {
            "schema": SCHEMA,
            "task_id": TASK_ID,
            "worker_id": WORKER_ID,
            "state": "FAIL_CLOSED",
            "reason": "INVALID_OR_UNREADABLE_INPUT",
            "detail": str(exc),
            "authority_effect": "NONE_VALIDATION_ONLY",
        }
        receipt["receipt_sha256"] = _sha256(_canonical_json(receipt))
        return receipt

    if not isinstance(payload, dict):
        receipt = {
            "schema": SCHEMA,
            "task_id": TASK_ID,
            "worker_id": WORKER_ID,
            "state": "FAIL_CLOSED",
            "reason": "DECLARATION_MUST_BE_OBJECT",
            "authority_effect": "NONE_VALIDATION_ONLY",
        }
        receipt["receipt_sha256"] = _sha256(_canonical_json(receipt))
        return receipt

    result = evaluate_declaration(payload)
    return {
        "schema": SCHEMA,
        "worker_id": WORKER_ID,
        **result,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fail closed when time/reference/observation evidence is promoted into StegVerse governance authority."
    )
    parser.add_argument("declaration", type=Path)
    parser.add_argument("--output", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    receipt = evaluate_file(args.declaration)
    rendered = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if receipt.get("state") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
