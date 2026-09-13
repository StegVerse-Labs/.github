#!/usr/bin/env python3
"""WorkerCoordinator wrapper for the existing Shared Docs provider-integrity consumer.

This worker creates no provider, credential, user-verification, transition, or runtime
authority. WorkerCoordinator owns claim/fence; TV/TVC remains provider/credential
authority. The wrapped consumer performs only the already-defined read-only evidence
observation and writes its secret-free receipt inside the fenced adapter sandbox.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

TASK_ID = "SHARED-DOCS-PROVIDER-FREEZE-INTEGRATION-001"
CONSUMER = Path("control/resident-execution-request.d/consume-shared-docs-provider-content-integrity.py")
RECEIPT = "receipts/sovereign-host/shared-docs-provider-content-integrity.latest.json"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def load_invocation() -> dict[str, Any]:
    value = json.load(sys.stdin)
    require(isinstance(value, dict), "worker invocation object required")
    require(value.get("schema") == "stegverse.worker-invocation/v0.1", "worker invocation schema mismatch")
    task = value.get("task") or {}
    handoff = value.get("handoff") or {}
    require(task.get("task_id") == TASK_ID, "task id mismatch")
    require(task.get("state") == "ACTIVE", "worker requires ACTIVE claimed task")
    require(isinstance(task.get("claim_id"), str) and bool(task.get("claim_id")), "claim required")
    require(isinstance((task.get("heartbeat_timing") or {}).get("fencing_token"), int), "fence required")
    authority = handoff.get("authority") or {}
    require(authority.get("credential_authority") == "TV/TVC", "credential authority drift")
    require(authority.get("execution_authority_created") is False, "handoff may not mint execution authority")
    return value


def run_consumer(root: Path) -> dict[str, Any]:
    target = root / CONSUMER
    require(target.is_file(), "shared docs provider consumer not materialized")
    spec = importlib.util.spec_from_file_location("shared_docs_provider_content_integrity_consumer", target)
    require(spec is not None and spec.loader is not None, "consumer import unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.consume(root, root, environ=os.environ)
    require(isinstance(result, dict), "consumer result object required")
    return result


def main() -> int:
    invocation = load_invocation()
    epoch = int(invocation.get("heartbeat_epoch") or 0)
    result = run_consumer(Path.cwd())
    observed = result.get("state") == "COMPLETED"
    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": "COMPLETED" if observed else "ACTIVE",
        "transition_id": "SHARED_DOCS_PROVIDER_CONTENT_INTEGRITY_OBSERVED" if observed else "SHARED_DOCS_PROVIDER_CONTENT_INTEGRITY_RETRY",
        "transition_sequence": 1 if observed else 0,
        "expected_next_transition": None if observed else "RETRY_AUTHENTIC_PROVIDER_OBSERVATION",
        "expected_next_earliest_epoch": None if observed else epoch + 1,
        "expected_next_latest_epoch": None if observed else epoch + 64,
        "checkpoint_ref": RECEIPT,
        "evidence_refs": [RECEIPT],
        "cost_observation": {
            "external_cost_usd": 0,
            "provider_mutation_performed": False,
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE"
        }
    }
    print(json.dumps(response, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
