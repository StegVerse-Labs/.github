#!/usr/bin/env python3
"""Read-only request/scope-input validation; no registration derivation or authority.

This deliberately does not call transition run/plan/apply/verify, inspect the
live Registry, emit a COSV, write a seal, or claim that registration occurred.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import canonical_task_registration_transition as transition
import goal_scope_seal as scope_seal

AUTHORITY = "NONE_INPUT_PREFLIGHT_ONLY"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair",
       "retry_entrypoint", "owning_existing_goal", "next_attempt")


def check_request(request: Any, source: str = "<request>") -> dict[str, Any]:
    """Use the unchanged request validator and canonical scope-seal validator."""
    result = {"source": source, "input_status": "VALID", "failure": None,
              "authority_effect": AUTHORITY, "registration_proven": False,
              "native_transition_attempted": False, "derived_files": []}
    try:
        transition.validate_request(request)
        mode = request.get("registration_mode", transition.NEW_IDENTITY)
        sealed = request.get("sealed_scope")
        if mode == transition.NEW_IDENTITY or sealed is not None:
            scope_seal.validate_sealed_scope(sealed, request["task_id"], request["record"],
                                             new_identity=mode == transition.NEW_IDENTITY)
    except (transition.Refusal, scope_seal.ScopeRefusal) as exc:
        result["input_status"] = "INVALID"
        result["failure"] = {
            "failure_code": exc.code,
            "failed_predicate": getattr(exc, "predicate", scope_seal.PREDICATE),
            "required_evidence_or_repair": exc.repair,
            "retry_entrypoint": f"python scripts/registration_input_preflight.py {source}",
            "owning_existing_goal": transition.OWNING_GOAL,
            "next_attempt": "repair the declared input under its existing owner and rerun this preflight",
            "detail": exc.detail,
        }
    return result


def check_file(path: Path) -> dict[str, Any]:
    try:
        request = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {"source": str(path), "input_status": "INVALID",
                "authority_effect": AUTHORITY, "registration_proven": False,
                "native_transition_attempted": False, "derived_files": [],
                "failure": {"failure_code": "REQUEST_INPUT_UNREADABLE",
                            "failed_predicate": "READABLE_JSON_REQUEST_INPUT",
                            "required_evidence_or_repair": "provide a readable UTF-8 JSON request",
                            "retry_entrypoint": f"python scripts/registration_input_preflight.py {path}",
                            "owning_existing_goal": transition.OWNING_GOAL,
                            "next_attempt": "repair the existing request file and rerun preflight",
                            "detail": type(exc).__name__}}
    return check_request(request, str(path))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("requests", nargs="+", type=Path)
    args = parser.parse_args(argv)
    results = [check_file(path) for path in args.requests]
    valid = sum(item["input_status"] == "VALID" for item in results)
    print(json.dumps({"schema": "stegverse.registration-input-preflight/v1",
                      "authority_effect": AUTHORITY, "registration_proven": False,
                      "valid": valid, "invalid": len(results) - valid,
                      "results": results}, indent=2, ensure_ascii=False))
    return 0 if valid == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
