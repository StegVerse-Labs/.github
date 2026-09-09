#!/usr/bin/env python3
"""WorkerCoordinator-selectable post-terminal SV001 evidence-chain continuation.

This worker never reruns terminal SV001. It reuses the existing continuation script
and remains fail-closed on missing downstream evidence. Selection/claim/fence state
is WorkerCoordinator-owned; any custody mutation remains subject to the current
Interlock/InTr and Master Records semantics required by the canonical handoff.

Resident evidence transport is sovereign-local first. A hosted rendezvous URL, when
configured, is fallback-only and is eligible only when no canonical local resident
rendezvous is reachable. A reachable local resident with no evidence or invalid
evidence never falls through to hosted transport.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

TASK_ID = "STEGVERSE001-EVIDENCE-CHAIN-CONTINUATION-001"
WORKER_ID = "stegverse001-evidence-chain-continuation-worker"
BOUND_STATE_ENV = "STEGVERSE_BOUND_STATE_ROOT"
CONTINUATION_REL = Path("scripts/continue_stegverse001_evidence_chain.py")
SITE_PROOF_REL = Path("observed/site-master-records-custody.latest.json")
SITE_PROOF_SCHEMA = "stegos.master-records.portable-sv001-custody-proof/v1"
RENDEZVOUS_DISCOVERY_SCHEMA = "stegverse.resident-rendezvous.discovery/v1"
RENDEZVOUS_FETCH_SCHEMA = "stegverse.resident-rendezvous.site-custody-evidence-fetch/v1"
RENDEZVOUS_ENVELOPE_SCHEMA = "stegverse.resident-rendezvous.site-custody-evidence/v1"
RENDEZVOUS_URL_ENV = "STEGVERSE_RESIDENT_RENDEZVOUS_URL"
RENDEZVOUS_NODE_ENV = "STEGVERSE_RESIDENT_RENDEZVOUS_NODE_REF"
LOCAL_RENDEZVOUS_BASES = ("http://127.0.0.1:8000", "http://localhost:8000")
CANONICAL_NODE_REF = re.compile(r"^SV-NODE-[0-9a-f]{24}$")
HOSTED_ENV = (
    "GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "VERCEL_ENV",
    "CF_PAGES", "CLOUDFLARE_WORKERS",
)
FORBIDDEN_CREDENTIAL_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GIT_ASKPASS",
    "GOOGLE_ACCESS_TOKEN", "GOOGLE_REFRESH_TOKEN", "OAUTH_TOKEN",
)
RETRYABLE_STATES = {
    "SV001_RECEIPT_NOT_OBSERVED",
    "SITE_GOVERNED_CUSTODY_PENDING",
    "SITE_GOVERNED_CUSTODY_PROOF_INVALID",
    "SV002_SOURCE_NOT_CURRENT",
}


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def validate_invocation(invocation: Mapping[str, Any]) -> None:
    task = invocation.get("task") or {}
    if task.get("task_id") != TASK_ID:
        raise RuntimeError("unexpected task_id")
    if task.get("worker_id") != WORKER_ID:
        raise RuntimeError("unexpected worker_id")
    if not task.get("claim_id"):
        raise RuntimeError("WorkerCoordinator claim required")
    handoff = invocation.get("handoff") or {}
    authority = handoff.get("authority") or {}
    if authority.get("credential_authority") != "TV/TVC":
        raise RuntimeError("credential authority drift")
    if authority.get("github_token_required") is not False:
        raise RuntimeError("GitHub token may not be required")
    if authority.get("non_tv_tvc_secret_or_token_allowed") is not False:
        raise RuntimeError("non-TV/TVC secret/token authority forbidden")
    if authority.get("heartbeat_grants_execution_authority") is not False:
        raise RuntimeError("HB32 may not grant execution authority")
    if authority.get("repository_writeback_authority") is not False:
        raise RuntimeError("continuation worker may not write repository state")


def require_bound_state_root() -> Path:
    raw = str(os.getenv(BOUND_STATE_ENV) or "").strip()
    if not raw:
        raise RuntimeError("bound state root unavailable")
    root = Path(raw).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _valid_rendezvous_base(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"}):
        raise RuntimeError("resident rendezvous evidence endpoint must use HTTPS or localhost")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise RuntimeError("resident rendezvous evidence endpoint must be a clean origin")
    return value.rstrip("/")


def _is_local_base(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and parsed.hostname in {"127.0.0.1", "localhost"}


def _canonical_sha256_uri(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _validate_relayed_proof(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping) or value.get("schema") != SITE_PROOF_SCHEMA:
        raise RuntimeError("relayed Site custody proof schema mismatch")
    if value.get("state") != "PASS" or value.get("execution_surface") != "CURRENT_USER_IPHONE":
        raise RuntimeError("relayed Site custody proof state mismatch")
    if value.get("intr_governance_admission_observed") is not True or value.get("reconstruction_state") != "PASS":
        raise RuntimeError("relayed Site custody proof lacks governed reconstruction PASS")
    if value.get("site_custody_authority") is not False or value.get("site_execution_authority") is not False:
        raise RuntimeError("relayed Site custody proof authority boundary mismatch")
    if value.get("heartbeat_granted_authority") is not False:
        raise RuntimeError("relayed Site custody proof heartbeat authority boundary mismatch")
    if value.get("prior_receipt_authorizes_transition") is not False or value.get("historical_state_retroactively_authorized") is not False:
        raise RuntimeError("relayed Site custody proof prior-state authority boundary mismatch")
    return dict(value)


def _request_json(url: str, *, node_ref: str | None = None, timeout: float = 5.0) -> tuple[str, Any | None]:
    headers = {"Accept": "application/json", "User-Agent": "StegVerse-SV001-Evidence-Continuation/2"}
    if node_ref:
        headers["X-StegVerse-Node-Ref"] = node_ref
    req = Request(url, method="GET", headers=headers)
    try:
        with urlopen(req, timeout=timeout) as response:
            return "REACHABLE", json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code >= 500 or exc.code == 404:
            return "UNAVAILABLE", None
        raise RuntimeError(f"resident rendezvous rejected request: HTTP {exc.code}") from exc
    except (URLError, TimeoutError, ConnectionError, OSError):
        return "UNAVAILABLE", None
    except json.JSONDecodeError as exc:
        raise RuntimeError("resident rendezvous returned malformed JSON") from exc


def _discover_local_node_ref(base: str) -> tuple[str, str | None]:
    state, value = _request_json(base + "/api/resident-rendezvous/v1/discovery", timeout=3.0)
    if state != "REACHABLE":
        return state, None
    if not isinstance(value, Mapping) or value.get("schema") != RENDEZVOUS_DISCOVERY_SCHEMA or value.get("state") != "AVAILABLE":
        raise RuntimeError("reachable sovereign resident discovery response invalid")
    if value.get("gateway_execution_authority") != "NONE" or value.get("discovery_grants_authority") is not False or value.get("authority_effect") != "NONE_DISCOVERY_ONLY":
        raise RuntimeError("reachable sovereign resident discovery authority boundary invalid")
    node_ref = str(value.get("target_node_ref") or "")
    if not CANONICAL_NODE_REF.fullmatch(node_ref):
        raise RuntimeError("reachable sovereign resident discovery node ref invalid")
    return "REACHABLE", node_ref


def _fetch_evidence_from_reachable_base(bound: Path, base: str, node_ref: str) -> Path | None:
    url = base + "/api/resident-rendezvous/v1/evidence/site-governed-custody?" + urlencode({"target_node_ref": node_ref})
    state, payload = _request_json(url, node_ref=node_ref, timeout=20.0)
    if state != "REACHABLE":
        raise RuntimeError("reachable resident discovery lost custody evidence endpoint")
    if not isinstance(payload, Mapping) or payload.get("schema") != RENDEZVOUS_FETCH_SCHEMA:
        raise RuntimeError("resident rendezvous evidence response invalid")
    if payload.get("gateway_execution_authority") != "NONE" or payload.get("evidence_grants_authority") is not False or payload.get("authority_effect") != "NONE_EVIDENCE_ONLY":
        raise RuntimeError("resident rendezvous evidence authority boundary invalid")
    if payload.get("state") == "NO_EVIDENCE":
        return None
    if payload.get("state") != "EVIDENCE_AVAILABLE":
        raise RuntimeError("resident rendezvous evidence state invalid")
    envelope = payload.get("evidence")
    if not isinstance(envelope, Mapping) or envelope.get("schema") != RENDEZVOUS_ENVELOPE_SCHEMA or envelope.get("target_node_ref") != node_ref:
        raise RuntimeError("resident rendezvous evidence envelope invalid")
    if envelope.get("gateway_execution_authority") != "NONE" or envelope.get("evidence_grants_authority") is not False or envelope.get("authority_effect") != "NONE_EVIDENCE_ONLY":
        raise RuntimeError("resident rendezvous evidence envelope authority boundary invalid")
    proof = _validate_relayed_proof(envelope.get("proof"))
    claimed_digest = str(envelope.get("proof_sha256") or "")
    if claimed_digest != _canonical_sha256_uri(proof):
        raise RuntimeError("resident rendezvous evidence proof digest mismatch")
    target = bound / SITE_PROOF_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def fetch_rendezvous_evidence(bound: Path) -> Path | None:
    """Read Site custody evidence from sovereign local resident first.

    Hosted configuration is fallback-only. It is consulted only when every local
    candidate is unavailable. A reachable local resident is authoritative for
    transport state: NO_EVIDENCE returns pending and malformed/invalid data fails
    closed without hosted fallthrough.
    """
    explicit_raw = str(os.getenv(RENDEZVOUS_URL_ENV) or "").strip()
    explicit_node = str(os.getenv(RENDEZVOUS_NODE_ENV) or "").strip()
    explicit = _valid_rendezvous_base(explicit_raw) if explicit_raw else ""
    if explicit_node and not CANONICAL_NODE_REF.fullmatch(explicit_node):
        raise RuntimeError("resident rendezvous node ref invalid")

    local_candidates: list[str] = []
    if explicit and _is_local_base(explicit):
        local_candidates.append(explicit)
    for base in LOCAL_RENDEZVOUS_BASES:
        if base not in local_candidates:
            local_candidates.append(base)

    for base in local_candidates:
        state, discovered_node = _discover_local_node_ref(base)
        if state != "REACHABLE":
            continue
        node_ref = discovered_node or explicit_node
        if explicit_node and discovered_node != explicit_node:
            raise RuntimeError("configured resident node ref disagrees with sovereign local discovery")
        return _fetch_evidence_from_reachable_base(bound, base, node_ref)

    if not explicit or _is_local_base(explicit):
        return None
    if not explicit_node:
        return None
    # Hosted transport is fallback only and is never eligible while a sovereign
    # local resident is reachable. Its availability grants no authority.
    return _fetch_evidence_from_reachable_base(bound, explicit, explicit_node)


def materialize_invocation_evidence(invocation: Mapping[str, Any], bound: Path) -> Path | None:
    """Persist non-authorizing Site custody proof in the admitted observed/** lane."""
    evidence = invocation.get("evidence") or {}
    if not isinstance(evidence, Mapping):
        raise RuntimeError("invocation evidence must be an object")
    proof = evidence.get("site_governed_custody_proof")
    existing = bound / SITE_PROOF_REL
    if proof is None:
        if existing.is_file():
            return existing
        return fetch_rendezvous_evidence(bound)
    if not isinstance(proof, Mapping):
        raise RuntimeError("site_governed_custody_proof must be an object")
    if proof.get("schema") != SITE_PROOF_SCHEMA:
        raise RuntimeError("site governed custody proof schema mismatch")
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text(json.dumps(dict(proof), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return existing


def execute(invocation: Mapping[str, Any]) -> dict[str, Any]:
    if any(truthy(os.getenv(name)) for name in HOSTED_ENV):
        raise RuntimeError("hosted environment cannot execute sovereign continuation")
    present = [name for name in FORBIDDEN_CREDENTIAL_ENV if truthy(os.getenv(name))]
    if present:
        raise RuntimeError("credential-bearing environment forbidden: " + ",".join(sorted(present)))

    validate_invocation(invocation)
    root = Path(__file__).resolve().parents[1]
    continuation = root / CONTINUATION_REL
    if not continuation.is_file():
        raise RuntimeError("canonical SV001 evidence-chain continuation source missing")
    bound = require_bound_state_root()
    site_proof = materialize_invocation_evidence(invocation, bound)

    child = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", str(Path.home())),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY": "TV/TVC",
    }
    command = [sys.executable, str(continuation), "--source-root", str(root)]
    if site_proof is not None:
        command.extend(["--site-custody-proof", str(site_proof)])

    proc = subprocess.run(
        command,
        cwd=root,
        env=child,
        capture_output=True,
        text=True,
        check=False,
        timeout=840,
    )
    result = parse_last_json(proc.stdout)
    if not isinstance(result, dict):
        raise RuntimeError("continuation returned no machine-readable result")

    state = str(result.get("state") or "UNKNOWN")
    receipt = {
        "schema": "stegverse.sv001-evidence-chain-worker-receipt/v1",
        "task_id": TASK_ID,
        "worker_id": WORKER_ID,
        "claim_id": (invocation.get("task") or {}).get("claim_id"),
        "continuation_state": state,
        "continuation_returncode": proc.returncode,
        "continuation_result": result,
        "site_governed_custody_proof_supplied": site_proof is not None,
        "site_governed_custody_proof_ref": SITE_PROOF_REL.as_posix() if site_proof is not None else None,
        "site_governed_custody_proof_authority_effect": "NONE_EVIDENCE_ONLY",
        "resident_rendezvous_primary_transport": "SOVEREIGN_LOCAL_RESIDENT",
        "hosted_rendezvous_role": "FALLBACK_ONLY",
        "sv001_reexecution_performed": False,
        "master_records_mutation_performed": bool(result.get("master_records_mutation_performed", False)),
        "heartbeat_grants_execution_authority": False,
        "prior_receipt_authorizes_next_transition": False,
        "credential_authority": "TV/TVC",
        "github_token_used": False,
        "repository_writeback_performed": False,
        "authority_effect": "NONE_CONTINUATION_ORCHESTRATION_ONLY",
    }
    target = bound / "receipts" / "latest.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt["local_receipt_ref"] = "receipts/latest.json"
    return receipt


def worker_response(receipt: Mapping[str, Any]) -> dict[str, Any]:
    state = str(receipt.get("continuation_state") or "UNKNOWN")
    evidence = [str(receipt.get("local_receipt_ref") or "receipts/latest.json")]
    if state == "PASS":
        return {
            "schema": "stegverse.worker-response/v0.1",
            "state": "COMPLETED",
            "transition_id": "STEGVERSE001_EVIDENCE_CHAIN_CONTINUATION_COMPLETE",
            "transition_sequence": 2,
            "expected_next_transition": None,
            "evidence_refs": evidence,
            "credential_authority": "TV/TVC",
            "github_token_used": False,
            "repository_writeback_performed": False,
        }
    if state in RETRYABLE_STATES or bool((receipt.get("continuation_result") or {}).get("retry_allowed")):
        return {
            "schema": "stegverse.worker-response/v0.1",
            "state": "HANDOFF_READY",
            "transition_id": "STEGVERSE001_EVIDENCE_CHAIN_CONTINUATION_PENDING",
            "transition_sequence": 1,
            "expected_next_transition": "STEGVERSE001_EVIDENCE_CHAIN_CONTINUATION_COMPLETE",
            "evidence_refs": evidence,
            "credential_authority": "TV/TVC",
            "github_token_used": False,
            "repository_writeback_performed": False,
        }
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "BLOCKED",
        "transition_id": "STEGVERSE001_EVIDENCE_CHAIN_CONTINUATION_BLOCKED",
        "transition_sequence": 1,
        "expected_next_transition": "STEGVERSE001_EVIDENCE_CHAIN_CONTINUATION_COMPLETE",
        "evidence_refs": evidence,
        "credential_authority": "TV/TVC",
        "github_token_used": False,
        "repository_writeback_performed": False,
        "blocker": {
            "trigger_type": "DOWNSTREAM_EVIDENCE_CHAIN_DEFECT",
            "dependency_class": "INTERNAL_CAPABILITY",
            "problem_statement": f"continuation state {state}",
            "solution_required": True,
            "workaround_candidates": [
                "re-evaluate the existing HB32/self-heal/source-refresh runtime solutions",
                "repair only the exact continuation defect without rerunning terminal SV001"
            ],
            "next_solution_action": "Diagnose existing runtime solution registry before any successor runtime implementation.",
            "resolvable_by_current_worker": False,
            "escalation_target": "SOVEREIGN_RUNTIME_SANDBOX_RESOLUTION",
            "required_capabilities": ["repository_resolution", "sandbox_validation"],
            "completion_evidence": ["continuation retry state returns PASS"],
            "same_level_retry_authorized": False
        },
    }


def blocked_response(exc: Exception) -> dict[str, Any]:
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "BLOCKED",
        "transition_id": "STEGVERSE001_EVIDENCE_CHAIN_CONTINUATION_WORKER_BLOCKED",
        "transition_sequence": 1,
        "expected_next_transition": "STEGVERSE001_EVIDENCE_CHAIN_CONTINUATION_COMPLETE",
        "error": str(exc),
        "evidence_refs": [],
        "credential_authority": "TV/TVC",
        "github_token_used": False,
        "repository_writeback_performed": False,
    }


def main() -> int:
    try:
        raw = sys.stdin.readline()
        invocation = json.loads(raw)
        if not isinstance(invocation, dict):
            raise RuntimeError("worker invocation must be a JSON object")
        receipt = execute(invocation)
        print(json.dumps(worker_response(receipt), sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps(blocked_response(exc), sort_keys=True))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
