from __future__ import annotations

import hashlib
import json
import secrets
from pathlib import Path
from typing import Any


def _canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def issue_claim_assertions(root: Path, epoch: int, issued_at: str, write: bool) -> list[str]:
    """Issue organization claim assertions for an already-owned heartbeat epoch.

    This function never increments heartbeat state. Epoch ownership belongs only
    to the single HeartbeatRuntime cycle. It therefore cannot become a second
    heartbeat or scheduler.
    """
    claims_path = root / "control" / "claims-active.json"
    org_path = root / "control" / "org-state.json"
    if not claims_path.exists() or not org_path.exists():
        return []

    claims = json.loads(claims_path.read_text(encoding="utf-8")).get("claims", [])
    org = json.loads(org_path.read_text(encoding="utf-8"))
    out = root / "heartbeats" / "outbound"
    issued: list[str] = []

    for claim in claims:
        lease = claim.get("lease") or {}
        fencing_token = lease.get("fencing_token")
        if not isinstance(fencing_token, int) or isinstance(fencing_token, bool) or fencing_token < 1:
            continue
        assertion = {
            "schema": "stegverse.org-heartbeat/v1",
            "epoch": epoch,
            "nonce": secrets.token_hex(16),
            "issued_at": issued_at,
            "claimant_id": claim["task_id"],
            "repository": claim["repository"]["full_name"],
            "claims": [claim],
            "fencing_token": fencing_token,
            "scope": claim.get("scope", {}),
            "policy_version": org["schema"],
            "evidence_pointer": claim.get("last_evidence_pointer"),
            "authority_effect": "none",
        }
        assertion["payload_sha256"] = hashlib.sha256(_canon(assertion)).hexdigest()
        relative = Path("heartbeats") / "outbound" / f"{claim['task_id']}-{epoch}.json"
        issued.append(str(relative))
        if write:
            out.mkdir(parents=True, exist_ok=True)
            (root / relative).write_text(json.dumps(assertion, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return issued
