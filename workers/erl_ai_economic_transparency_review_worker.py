#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path.cwd().resolve()
TASK = "SHWP-ERL-AI-ECON-TRANSPARENCY-REVIEW-001"
RECEIPT = ROOT / "receipts" / "erl-ai-economic-transparency-review" / f"{TASK}.json"
BUNDLED_REVIEW_ROOT = ROOT / "review-packages" / "erl-ai-economic-transparency-001"
BUNDLE_MANIFEST = BUNDLED_REVIEW_ROOT / "manifest.json"

REQUIRED_RELATIVE_PATHS = [
    "assessments/reviews/ai-economic-transparency-consumer-surface-independent-review-package.2026-09-03.json",
    "research-data/ai-economic-transparency/candidate-results.consumer-surfaces.2026-09-03.json",
    "research-data/ai-economic-transparency/openai-consumer-surface-observation.2026-09-03.json",
    "research-data/ai-economic-transparency/anthropic-consumer-surface-observation.2026-09-03.json",
    "research-data/ai-economic-transparency/deepseek-consumer-surface-observation.2026-09-03.json",
    "assessments/reviews/ai-economic-transparency-consumer-surface-contradiction-review.2026-09-03.json",
    "schemas/ai-economic-transparency-observation.schema.json",
    "standards/ai-economic-transparency.v1.md",
]

def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        name = handle.name
    os.replace(name, path)

def source_roots() -> list[Path]:
    roots: list[Path] = [BUNDLED_REVIEW_ROOT]
    explicit = os.environ.get("STEGVERSE_ERL_SOURCE_ROOT")
    if explicit:
        roots.append(Path(explicit))
    roots.extend([
        ROOT / "workloads" / "Executive_Rhetoric_Ledger",
        Path.home() / ".stegverse" / "workloads" / "Executive_Rhetoric_Ledger",
        Path.home() / ".stegverse" / "source" / "Executive_Rhetoric_Ledger",
        Path("/var/lib/stegverse/workloads/Executive_Rhetoric_Ledger"),
        Path("/var/lib/stegverse/source/Executive_Rhetoric_Ledger"),
    ])
    return roots

def verify_bundle_manifest(root: Path) -> tuple[bool, list[str]]:
    if root != BUNDLED_REVIEW_ROOT.resolve():
        return True, []
    if not BUNDLE_MANIFEST.is_file():
        return False, ["bundle manifest missing"]
    try:
        manifest = json.loads(BUNDLE_MANIFEST.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, [f"bundle manifest unreadable: {exc}"]
    if manifest.get("schema") != "stegverse.erl.ai-economic-transparency-review-input-bundle/v1":
        return False, ["bundle manifest schema mismatch"]
    indexed = {row.get("relative_path"): row for row in manifest.get("files") or [] if isinstance(row, dict)}
    errors: list[str] = []
    for rel in REQUIRED_RELATIVE_PATHS:
        row = indexed.get(rel)
        if row is None:
            errors.append(f"manifest missing {rel}")
            continue
        path = root / rel
        if not path.is_file():
            errors.append(f"bundle missing {rel}")
            continue
        expected = row.get("sha256")
        actual = f"sha256:{sha256_file(path)}"
        if expected != actual:
            errors.append(f"hash mismatch {rel}: expected {expected} actual {actual}")
    return not errors, errors

def find_source_root() -> Path | None:
    for candidate in source_roots():
        try:
            root = candidate.expanduser().resolve()
        except Exception:
            continue
        if all((root / p).is_file() for p in REQUIRED_RELATIVE_PATHS):
            ok, _ = verify_bundle_manifest(root)
            if ok:
                return root
    return None

def load_json(root: Path, rel: str) -> dict[str, Any]:
    return json.loads((root / rel).read_text(encoding="utf-8"))

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def evaluate(root: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    providers = ["openai", "anthropic", "deepseek"]
    obs: dict[str, dict[str, Any]] = {}
    for provider in providers:
        rel = f"research-data/ai-economic-transparency/{provider}-consumer-surface-observation.2026-09-03.json"
        obs[provider] = load_json(root, rel)

    results = load_json(root, "research-data/ai-economic-transparency/candidate-results.consumer-surfaces.2026-09-03.json")
    contradiction = load_json(root, "assessments/reviews/ai-economic-transparency-consumer-surface-contradiction-review.2026-09-03.json")
    package = load_json(root, "assessments/reviews/ai-economic-transparency-consumer-surface-independent-review-package.2026-09-03.json")

    def record(name: str, passed: bool, detail: str) -> None:
        checks.append({"check": name, "passed": bool(passed), "detail": detail})

    record("package_scope", package.get("review_scope") == "FINALIZED_CONSUMER_NON_ACCOUNT_ATTRIBUTED_SURFACES_ONLY", str(package.get("review_scope")))
    record("package_providers", package.get("providers") == providers, json.dumps(package.get("providers")))
    record("provider_wide_forbidden", "provider-wide transparency ranking" in (package.get("forbidden_promotions") or []), "package forbidden promotions")

    for provider in providers:
        o = obs[provider]
        record(f"{provider}_surface", o.get("surface_class") == "CONSUMER_NON_ACCOUNT_ATTRIBUTED", str(o.get("surface_class")))
        record(f"{provider}_scope", o.get("rating_scope") == "SURFACE_SPECIFIC", str(o.get("rating_scope")))
        record(f"{provider}_protocol_complete", o.get("protocol_complete") is True, str(o.get("protocol_complete")))
        record(f"{provider}_rating", o.get("disclosure_burden_rating") == 5, str(o.get("disclosure_burden_rating")))
        record(f"{provider}_nonreconstructable", o.get("reconstructable_actual_cost") is False and o.get("literal_request_cost_usd") is None, "literal cost remains unresolved")
        scenarios = o.get("scale_scenarios") or []
        counts = [s.get("equivalent_requests") for s in scenarios]
        unknown_ok = counts == [1000, 100000, 1000000] and all(
            s.get("state") == "UNBOUNDED_UNKNOWN"
            and s.get("known_total_cost_usd") is None
            and s.get("lower_bound_usd") is None
            and s.get("upper_bound_usd") is None
            for s in scenarios
        )
        record(f"{provider}_scale_unknown", unknown_ok, json.dumps(scenarios, sort_keys=True))
        record(f"{provider}_no_activation", o.get("activation_authorized") is False, str(o.get("activation_authorized")))

    finding_map = {f.get("provider"): f for f in (results.get("findings") or [])}
    record("candidate_results_state", results.get("state") == "CANDIDATE_RESULTS_PENDING_INDEPENDENT_REVIEW", str(results.get("state")))
    record("candidate_provider_wide_forbidden", results.get("provider_wide_ranking_authorized") is False, str(results.get("provider_wide_ranking_authorized")))
    for provider in providers:
        f = finding_map.get(provider) or {}
        record(f"{provider}_candidate_matches", f.get("surface_class") == "CONSUMER_NON_ACCOUNT_ATTRIBUTED" and f.get("disclosure_burden_rating") == 5 and f.get("scale_sensitivity_state") == "UNBOUNDED_UNKNOWN", json.dumps(f, sort_keys=True))

    c_map = {r.get("provider"): r for r in (contradiction.get("provider_reviews") or [])}
    record("contradiction_complete", contradiction.get("state") == "COMPLETE", str(contradiction.get("state")))
    for provider in providers:
        r = c_map.get(provider) or {}
        record(f"{provider}_contradiction", r.get("result") == "NO_MATERIAL_CONTRADICTION", str(r.get("result")))

    passed = all(c["passed"] for c in checks)
    recommendation = "APPROVE" if passed else "REVISE"
    evidence_hashes = {
        rel: f"sha256:{sha256_file(root / rel)}"
        for rel in REQUIRED_RELATIVE_PATHS
        if (root / rel).is_file()
    }
    return {
        "schema": "stegverse.erl.ai-economic-transparency-independent-review-runtime/v1",
        "task_id": "ERL-AI-ECON-TRANSPARENCY-001",
        "review_worker_task_id": TASK,
        "review_scope": "FINALIZED_CONSUMER_NON_ACCOUNT_ATTRIBUTED_SURFACES_ONLY",
        "state": "COMPLETE",
        "reviewer_independence": "SEPARATE_RESIDENT_WORKER_IDENTITY_NO_RESEARCH_PROMOTION_OR_REPOSITORY_WRITEBACK_AUTHORITY",
        "checks": checks,
        "recommendation": recommendation,
        "activation_recommendation": "PENDING",
        "publication_recommendation": "PENDING",
        "evidence_hashes": evidence_hashes,
        "authority_effect": "NONE_REVIEW_RECOMMENDATION_ONLY",
    }

def response(state: str, transition: str, seq: int, next_transition: str | None, blocker: dict[str, Any] | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": seq,
        "expected_next_transition": next_transition,
        "expected_next_earliest_epoch": None,
        "expected_next_latest_epoch": None,
        "checkpoint_ref": str(RECEIPT.relative_to(ROOT)),
        "evidence_refs": [str(RECEIPT.relative_to(ROOT)), "StegVerse-Labs/Executive_Rhetoric_Ledger#104"],
    }
    if blocker:
        out["blocker"] = blocker
    return out

def main() -> int:
    invocation = json.load(sys.stdin)
    task = invocation.get("task") or {}
    epoch = invocation.get("heartbeat_epoch")
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1" or task.get("task_id") != TASK or not isinstance(epoch, int):
        return 2
    timing = task.get("heartbeat_timing") or {}
    claim = task.get("claim_id")
    fence = timing.get("fencing_token")
    if not isinstance(claim, str) or not claim or not isinstance(fence, int):
        return 3

    root = find_source_root()
    if root is None:
        blocker = {
            "dependency_class": "INTERNAL_CAPABILITY",
            "problem_statement": "No hash-valid local ERL independent-review package is available.",
            "solution_required": True,
            "may_remain_blocked": False,
            "workaround_candidates": ["Use the bundled hash-bound review package shipped with the worker, or resolve the released Executive_Rhetoric_Ledger source from canonical local StegVerse source/workload locations without network checkout."],
            "next_solution_action": "Repair the local hash-bound review package or materialize canonical ERL source locally, then retry the same fenced task.",
            "machine_observable_release_condition": "a complete hash-valid local review package resolves",
            "github_token_required": False,
            "non_tv_tvc_secret_or_token_required": False,
            "third_party_blocker": False,
            "human_action_required": False,
        }
        durable = {
            "schema": "stegverse.erl-ai-economic-transparency-review-worker-receipt/v0.1",
            "task_id": TASK,
            "heartbeat_epoch": epoch,
            "claim_id": claim,
            "fencing_token": fence,
            "state": "BLOCKED",
            "transition_id": "ERL_AI_ECON_REVIEW_SOURCE_NOT_MATERIALIZED",
            "github_token_used": False,
            "non_tv_tvc_secret_or_token_used": False,
            "research_promotion_authority": False,
            "publication_authority": False,
            "repository_writeback_authority": False,
            "blocker": blocker,
        }
        atomic_write(RECEIPT, durable)
        json.dump(response("BLOCKED", durable["transition_id"], 1, "ERL_AI_ECON_INDEPENDENT_REVIEW_COMPLETE", blocker), sys.stdout)
        print()
        return 0

    review = evaluate(root)
    durable = {
        "schema": "stegverse.erl-ai-economic-transparency-review-worker-receipt/v0.1",
        "task_id": TASK,
        "heartbeat_epoch": epoch,
        "claim_id": claim,
        "fencing_token": fence,
        "state": "COMPLETED",
        "transition_id": "ERL_AI_ECON_INDEPENDENT_REVIEW_COMPLETE",
        "review": review,
        "source_root": str(root),
        "source_package_class": "BUNDLED_HASH_BOUND" if root == BUNDLED_REVIEW_ROOT.resolve() else "LOCAL_CANONICAL_ERL_SOURCE",
        "github_token_used": False,
        "non_tv_tvc_secret_or_token_used": False,
        "research_promotion_authority": False,
        "publication_authority": False,
        "repository_writeback_authority": False,
    }
    atomic_write(RECEIPT, durable)
    json.dump(response("COMPLETED", durable["transition_id"], 2, None), sys.stdout)
    print()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
