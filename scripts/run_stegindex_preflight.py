#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

INDEX_HANDOFF = Path("STEGINDEX_MIRROR_HANDOFF.md")
CANONICAL_RESOLVER = Path("scripts/preflight.py")


class PreflightError(RuntimeError):
    pass


def _index_root(explicit: Path | None = None) -> Path:
    raw = str(explicit) if explicit is not None else str(os.environ.get("STEGVERSE_STEGINDEX_SOURCE_ROOT") or "").strip()
    if not raw:
        roots_raw = str(os.environ.get("STEGVERSE_REPO_ROOTS_JSON") or "").strip()
        if roots_raw:
            try:
                roots = json.loads(roots_raw)
            except json.JSONDecodeError as exc:
                raise PreflightError("STEGVERSE_REPO_ROOTS_JSON is invalid JSON") from exc
            if not isinstance(roots, dict):
                raise PreflightError("STEGVERSE_REPO_ROOTS_JSON must be an object")
            raw = str(
                roots.get("StegVerse-Labs/StegIndex")
                or roots.get("StegIndex")
                or ""
            ).strip()
    if not raw:
        raise PreflightError("canonical StegIndex source is not present in local source bindings")
    root = Path(raw).expanduser().resolve()
    required = (root / INDEX_HANDOFF, root / CANONICAL_RESOLVER)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise PreflightError("StegIndex source incomplete: " + ",".join(missing))
    return root


def run_canonical(
    *,
    index_root: Path,
    query: str,
    predicate: str | None = None,
    capability_id: str | None = None,
    intent: str = "DISCOVER",
) -> dict[str, Any]:
    command = [
        sys.executable,
        str(index_root / CANONICAL_RESOLVER),
        "--query", query,
    ]
    completed = subprocess.run(
        command,
        cwd=index_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
        env={"PATH": os.environ.get("PATH", "")},
    )
    if completed.returncode != 0:
        raise PreflightError(f"canonical StegIndex resolver exited {completed.returncode}: {completed.stderr.strip()[-1000:]}")
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise PreflightError("canonical StegIndex resolver emitted invalid JSON") from exc

    first = result.get("first_actionable_predicate")
    if predicate and isinstance(first, dict) and first.get("predicate_id") != predicate:
        raise PreflightError(
            f"canonical StegIndex resolved {first.get('predicate_id')} instead of requested {predicate}"
        )
    if capability_id and not any(
        isinstance(cap, dict) and cap.get("capability_id") == capability_id
        for cap in result.get("capabilities", [])
    ):
        raise PreflightError(f"canonical StegIndex did not resolve requested capability {capability_id}")

    result["consumer"] = "StegVerse-Labs/.github"
    result["consumer_intent"] = intent
    result["index_root"] = str(index_root)
    result["canonical_resolver_invoked"] = True
    result["network_fetch_performed"] = False
    result["credential_read_or_acquired"] = False
    result["github_token_required"] = False
    result["credential_authority"] = "TV/TVC"
    result["authority_effect"] = "NONE_READ_RESOLVE_ONLY"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Invoke canonical StegIndex preflight from an already-local source.")
    parser.add_argument("--index-root", type=Path)
    parser.add_argument("--query", required=True)
    parser.add_argument("--predicate")
    parser.add_argument("--capability-id")
    parser.add_argument(
        "--intent",
        choices=["DISCOVER","CREATE_WORK","DECLARE_BLOCKER","RUNTIME_EVIDENCE","AUTHORITY_CHANGE"],
        default="DISCOVER",
    )
    args = parser.parse_args()

    try:
        root = _index_root(args.index_root)
        result = run_canonical(
            index_root=root,
            query=args.query,
            predicate=args.predicate,
            capability_id=args.capability_id,
            intent=args.intent,
        )
    except PreflightError as exc:
        result = {
            "schema": "stegverse.stegindex-preflight-result/v1",
            "query": args.query,
            "capabilities": [],
            "predicates": [],
            "capability_risk": {
                "matches": [],
                "transition_surfaces": [],
                "required_governance": [],
                "trusted_or_available_implies_authority": False,
                "runtime_dependency": False,
                "copy_payloads": False,
                "authority_effect": "NONE_INDEX_ONLY",
            },
            "first_actionable_predicate": None,
            "machine_continuation_required": False,
            "generic_blocker_permitted": False,
            "state": "PREFLIGHT_UNAVAILABLE",
            "problem_statement": str(exc),
            "source_unavailable_is_implementation_missing": False,
            "network_fetch_performed": False,
            "credential_read_or_acquired": False,
            "github_token_required": False,
            "credential_authority": "TV/TVC",
            "authority_effect": "NONE_READ_RESOLVE_ONLY",
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("state") != "PREFLIGHT_UNAVAILABLE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
