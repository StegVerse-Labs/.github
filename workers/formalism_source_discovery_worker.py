#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any

ROOT = Path.cwd().resolve()
CONFIG_PATH = ROOT / "control" / "formalism-source-discovery.json"
RECEIPT_ROOT = (ROOT / "receipts" / "formalism-source-discovery").resolve()
TASK_ID = "SHWP-FORMALISM-SOURCE-DISCOVERY-001"
CAPABILITY = "formalism_source_discovery"
CURRENT_AUTHORITY = "TV/TVC"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be object")
    return value


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = handle.name
    os.replace(temporary, path)


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def handoffs(root: Path) -> list[Path]:
    found: list[Path] = []
    for base in (root, root / "docs"):
        if base.is_dir():
            found.extend(path for path in sorted(base.glob("*_MIRROR_HANDOFF.md")) if path.is_file())
    return found


def explicit_roots() -> dict[str, Path]:
    raw = os.environ.get("STEGVERSE_FORMALISM_ROOTS_JSON", "")
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    result: dict[str, Path] = {}
    for repository, path in parsed.items():
        if isinstance(repository, str) and isinstance(path, str) and path:
            result[repository] = Path(path).expanduser().resolve()
    return result


def candidate_paths(repository: str, templates: list[str]) -> list[Path]:
    owner, repo = repository.split("/", 1)
    out: list[Path] = []
    seen: set[str] = set()
    for template in templates:
        rendered = template.format(owner=owner, repo=repo)
        path = Path(rendered).expanduser()
        if not path.is_absolute():
            path = ROOT / path
        resolved = path.resolve()
        key = str(resolved)
        if key not in seen:
            seen.add(key)
            out.append(resolved)
    return out


def discover(config: dict[str, Any]) -> dict[str, Any]:
    explicit = explicit_roots()
    templates = [item for item in config.get("search_templates", []) if isinstance(item, str)]
    rows: list[dict[str, Any]] = []
    roots: dict[str, str] = {}
    missing: list[str] = []
    ambiguous: list[str] = []
    invalid: list[str] = []

    for repository in config.get("repositories", []):
        if not isinstance(repository, str) or "/" not in repository:
            continue
        candidates: list[tuple[Path, str]] = []
        if repository in explicit:
            candidates.append((explicit[repository], "EXPLICIT_NONSECRET_OVERRIDE"))
        candidates.extend((path, "CANONICAL_LOCAL_SEARCH") for path in candidate_paths(repository, templates))

        valid: list[tuple[Path, str, list[Path]]] = []
        observed: list[dict[str, Any]] = []
        seen: set[str] = set()
        for path, source in candidates:
            key = str(path)
            if key in seen:
                continue
            seen.add(key)
            is_dir = path.is_dir()
            mirrors = handoffs(path) if is_dir else []
            observed.append({
                "path": key,
                "source": source,
                "directory_present": is_dir,
                "mirror_handoff_present": bool(mirrors),
            })
            if is_dir and mirrors:
                valid.append((path, source, mirrors))

        # An explicit valid root is authoritative over search-path duplicates because
        # it is a non-secret runtime locator supplied by the already-authorized carrier.
        explicit_valid = [item for item in valid if item[1] == "EXPLICIT_NONSECRET_OVERRIDE"]
        selected: tuple[Path, str, list[Path]] | None = None
        state: str
        if len(explicit_valid) == 1:
            selected = explicit_valid[0]
            state = "DISCOVERED"
        elif len(valid) == 1:
            selected = valid[0]
            state = "DISCOVERED"
        elif len(valid) > 1:
            state = "AMBIGUOUS"
            ambiguous.append(repository)
        else:
            any_directory = any(item["directory_present"] for item in observed)
            state = "INVALID_HANDOFF" if any_directory else "MISSING"
            (invalid if any_directory else missing).append(repository)

        row: dict[str, Any] = {
            "repository": repository,
            "state": state,
            "observed_candidates": observed,
            "selected_root": None,
            "selected_source": None,
            "mirror_handoffs": [],
        }
        if selected is not None:
            root, source, mirrors = selected
            row["selected_root"] = str(root)
            row["selected_source"] = source
            row["mirror_handoffs"] = [str(path.relative_to(root)) for path in mirrors]
            roots[repository] = str(root)
        rows.append(row)

    complete = len(roots) == len(config.get("repositories", [])) and not missing and not ambiguous and not invalid
    return {
        "complete": complete,
        "repositories": rows,
        "roots": dict(sorted(roots.items())),
        "missing": sorted(missing),
        "ambiguous": sorted(ambiguous),
        "invalid_handoff": sorted(invalid),
        "network_checkout_performed": False,
        "credential_authority": CURRENT_AUTHORITY,
        "github_token_required": False,
        "authority_effect": "NONE_LOCAL_DISCOVERY_ONLY",
    }


def main() -> int:
    try:
        invocation = json.load(sys.stdin)
    except Exception:
        return 2
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return 3
    epoch = invocation.get("heartbeat_epoch")
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    if not isinstance(epoch, int) or task.get("task_id") != TASK_ID:
        return 4
    claim_id = task.get("claim_id")
    timing = task.get("heartbeat_timing") or {}
    fence = timing.get("fencing_token")
    if not isinstance(claim_id, str) or not claim_id or not isinstance(fence, int):
        return 5
    execution = handoff.get("execution") or {}
    if CAPABILITY not in set(execution.get("required_capabilities") or []):
        return 6
    if "receipts/formalism-source-discovery/**" not in set(execution.get("allowed_paths") or []):
        return 7

    config = load(CONFIG_PATH)
    if config.get("schema") != "stegverse.formalism-source-discovery/v0.1":
        return 8
    if config.get("credential_authority") != CURRENT_AUTHORITY or config.get("github_token_required") is not False or config.get("network_checkout_authority") is not False:
        return 9

    result = discover(config)
    state = "COMPLETED" if result["complete"] else "BLOCKED"
    transition = "FORMALISM_SOURCE_ROOTS_DISCOVERED" if result["complete"] else "FORMALISM_SOURCE_ROOTS_INCOMPLETE"
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    manifest = {
        "schema": "stegverse.formalism-roots-manifest/v0.1",
        "goal_id": config["goal_id"],
        "generated_at": now,
        "state": state,
        "roots": result["roots"],
        "source_discovery_sha256": canonical_hash(result),
        "credential_authority": CURRENT_AUTHORITY,
        "github_token_required": False,
        "network_checkout_performed": False,
        "authority_effect": "NONE_SOURCE_LOCATOR_ONLY"
    }
    receipt = {
        "schema": "stegverse.formalism-source-discovery-receipt/v0.1",
        "goal_id": config["goal_id"],
        "task_id": TASK_ID,
        "heartbeat_epoch": epoch,
        "claim_id": claim_id,
        "worker_id": task.get("worker_id"),
        "worker_instance_id": task.get("worker_instance_id"),
        "fencing_token": fence,
        "generated_at": now,
        "state": state,
        "transition_id": transition,
        "result": result,
        "roots_manifest_ref": "receipts/formalism-source-discovery/formalism-roots.json",
        "fail_closed": True,
        "credential_authority": CURRENT_AUTHORITY,
        "github_token_required": False,
        "network_checkout_performed": False,
        "heartbeat_grants_execution_authority": False,
        "authority_effect": "NONE_LOCAL_DISCOVERY_ONLY"
    }
    atomic_write(RECEIPT_ROOT / "formalism-roots.json", manifest)
    atomic_write(RECEIPT_ROOT / f"{TASK_ID}.json", receipt)

    blocker = None
    if not result["complete"]:
        blocker = {
            "dependency_class": "INTERNAL_CAPABILITY",
            "problem_statement": "One or more first-cohort formalism/runtime source roots are absent, ambiguous, or lack canonical mirror-handoff standing.",
            "solution_required": True,
            "may_remain_blocked": False,
            "next_solution_action": "DERIVE_SEPARATELY_AUTHORIZED_FORMALISM_SOURCE_MATERIALIZATION_TASK",
            "machine_observable_release_condition": "formalism-roots.json reaches COMPLETED with one unique handoff-bearing local root for every configured repository",
            "missing_repositories": result["missing"],
            "ambiguous_repositories": result["ambiguous"],
            "invalid_handoff_repositories": result["invalid_handoff"],
            "github_token_required": False
        }
    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": 1,
        "expected_next_transition": None if state == "COMPLETED" else "FORMALISM_SOURCE_DISCOVERY_RECHECK",
        "expected_next_earliest_epoch": None if state == "COMPLETED" else epoch + 1,
        "expected_next_latest_epoch": None if state == "COMPLETED" else epoch + 1,
        "checkpoint_ref": f"receipts/formalism-source-discovery/{TASK_ID}.json",
        "evidence_refs": [
            "control/formalism-source-discovery.json",
            "receipts/formalism-source-discovery/formalism-roots.json",
            f"receipts/formalism-source-discovery/{TASK_ID}.json"
        ],
        "blocker": blocker,
        "cost_observation": {"hb_transition_count": 1, "compute_units": 1, "external_cost_usd": 0, "task_class": "formalism_source_discovery"}
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
