#!/usr/bin/env python3
"""Heartbeat-owned deployment worker for the stable StegGate rendezvous.

The worker is deliberately narrow:
- it consumes only CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID;
- it fetches and verifies the canonical Site rendezvous Worker source;
- it deploys only stegverse-steggate-rendezvous to stegverse.org/api/steggate/*;
- it verifies readiness, health, and exact four-disposition self-test;
- it persists no credential values.

Missing provider credentials are a BLOCKED worker state, not task completion.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path.cwd().resolve()
RECEIPT_ROOT = (ROOT / "receipts" / "steggate-rendezvous-worker").resolve()
TASK_ID = "STEGGATE-STABLE-RENDEZVOUS-WORKER-001"
SITE_WORKER_URL = "https://raw.githubusercontent.com/StegVerse-Labs/Site/main/src/steggate-rendezvous-worker.js"
SITE_WORKER_GIT_BLOB_SHA = "4acf5dc498297f1b2972195df74af8b60796f608"
STABLE_ORIGIN = "https://stegverse.org/api/steggate"


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def request_json(url: str, *, token: str | None = None, timeout: int = 20) -> tuple[int, dict]:
    headers = {"accept": "application/json", "user-agent": "StegVerse-Heartbeat-Rendezvous-Worker/1"}
    if token:
        headers["authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            body = json.loads(exc.read().decode("utf-8"))
        except Exception:
            body = {"error": "http_error"}
        return exc.code, body


def write_receipt(path: Path, body: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def response(state: str, transition: str, epoch: int, receipt_ref: str, *, next_transition: str | None, retry_latest: int | None) -> dict:
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": 1,
        "expected_next_transition": next_transition,
        "expected_next_earliest_epoch": None if next_transition is None else epoch + 1,
        "expected_next_latest_epoch": retry_latest,
        "checkpoint_ref": receipt_ref,
        "evidence_refs": [receipt_ref],
        "cost_observation": {
            "hb_transition_count": 1,
            "compute_units": 1,
            "external_cost_usd": 0,
            "task_class": "steggate_stable_rendezvous"
        }
    }


def main() -> int:
    invocation = json.load(sys.stdin)
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return 2
    epoch = invocation.get("heartbeat_epoch")
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    if not isinstance(epoch, int) or task.get("task_id") != TASK_ID:
        return 3

    execution = handoff.get("execution") or {}
    required = set(execution.get("required_capabilities") or [])
    if not {"deployment_update", "runtime_observation"}.issubset(required):
        return 4
    if "receipts/steggate-rendezvous-worker/**" not in set(execution.get("allowed_paths") or []):
        return 5

    claim_id = task.get("claim_id")
    timing = task.get("heartbeat_timing") or {}
    fence = timing.get("fencing_token")
    if not claim_id or not isinstance(fence, int):
        return 6

    token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
    receipt_ref = f"receipts/steggate-rendezvous-worker/{TASK_ID}.json"
    receipt_path = (ROOT / receipt_ref).resolve()
    if RECEIPT_ROOT not in receipt_path.parents:
        return 7

    base_receipt = {
        "schema": "stegverse.steggate-rendezvous-worker-receipt/v0.1",
        "task_id": TASK_ID,
        "goal_id": "STEGGATE-STABLE-RENDEZVOUS-HARDENING",
        "claim_id": claim_id,
        "worker_id": task.get("worker_id"),
        "worker_instance_id": task.get("worker_instance_id"),
        "fencing_token": fence,
        "heartbeat_epoch": epoch,
        "stable_origin": STABLE_ORIGIN,
        "credentials_recorded": False,
        "authority_effect": "bounded_rendezvous_deployment_only"
    }

    if not token or not account_id:
        receipt = dict(base_receipt)
        receipt.update({
            "state": "BLOCKED",
            "transition": "CREDENTIAL_VALUES_ABSENT",
            "release_condition": "CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID are both present in the authorized heartbeat execution environment.",
            "next_action": "Re-evaluate credential presence on the next admitted heartbeat."
        })
        write_receipt(receipt_path, receipt)
        json.dump(response("BLOCKED", "CREDENTIAL_VALUES_ABSENT", epoch, receipt_ref, next_transition="CREDENTIAL_RECHECK", retry_latest=epoch + 32), sys.stdout)
        sys.stdout.write("\n")
        return 0

    status, capability = request_json(f"https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/scripts", token=token)
    if status != 200 or capability.get("success") is not True:
        receipt = dict(base_receipt)
        receipt.update({
            "state": "BLOCKED",
            "transition": "CREDENTIAL_CAPABILITY_REJECTED",
            "cloudflare_http_status": status,
            "release_condition": "The supplied account/token pair must be authorized for Workers script deployment in the declared Cloudflare account.",
            "next_action": "Re-evaluate the credential capability on the next admitted heartbeat."
        })
        write_receipt(receipt_path, receipt)
        json.dump(response("BLOCKED", "CREDENTIAL_CAPABILITY_REJECTED", epoch, receipt_ref, next_transition="CREDENTIAL_RECHECK", retry_latest=epoch + 32), sys.stdout)
        sys.stdout.write("\n")
        return 0

    with urllib.request.urlopen(SITE_WORKER_URL, timeout=20) as resp:
        worker_source = resp.read()
    observed_blob = git_blob_sha(worker_source)
    if observed_blob != SITE_WORKER_GIT_BLOB_SHA:
        receipt = dict(base_receipt)
        receipt.update({
            "state": "BLOCKED",
            "transition": "SOURCE_DRIFT_REVIEW_REQUIRED",
            "expected_site_worker_blob": SITE_WORKER_GIT_BLOB_SHA,
            "observed_site_worker_blob": observed_blob,
            "release_condition": "Heartbeat worker authorization is reconciled to the current canonical Site rendezvous source blob.",
            "next_action": "Fail closed; do not deploy mutable unreviewed source."
        })
        write_receipt(receipt_path, receipt)
        json.dump(response("BLOCKED", "SOURCE_DRIFT_REVIEW_REQUIRED", epoch, receipt_ref, next_transition="SOURCE_RECONCILIATION", retry_latest=epoch + 32), sys.stdout)
        sys.stdout.write("\n")
        return 0

    with tempfile.TemporaryDirectory(prefix="steggate-rendezvous-") as td:
        root = Path(td)
        src = root / "src"
        src.mkdir()
        (src / "steggate-rendezvous-worker.js").write_bytes(worker_source)
        cfg = {
            "name": "stegverse-steggate-rendezvous",
            "main": "src/steggate-rendezvous-worker.js",
            "compatibility_date": "2026-08-08",
            "workers_dev": True,
            "preview_urls": False,
            "observability": {"enabled": True},
            "account_id": account_id,
            "routes": [{"pattern": "stegverse.org/api/steggate/*", "zone_name": "stegverse.org"}]
        }
        (root / "wrangler.json").write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
        env = os.environ.copy()
        proc = subprocess.run(
            ["npx", "--yes", "wrangler@latest", "deploy", "--config", "wrangler.json"],
            cwd=root,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=180,
            check=False,
        )
        if proc.returncode != 0:
            receipt = dict(base_receipt)
            receipt.update({
                "state": "ACTIVE",
                "transition": "DEPLOYMENT_RETRY_REQUIRED",
                "provider_exit_code": proc.returncode,
                "next_action": "Retry bounded deployment on the next admitted heartbeat."
            })
            write_receipt(receipt_path, receipt)
            json.dump(response("ACTIVE", "DEPLOYMENT_RETRY_REQUIRED", epoch, receipt_ref, next_transition="DEPLOYMENT_RETRY", retry_latest=epoch + 8), sys.stdout)
            sys.stdout.write("\n")
            return 0

    readiness_status, readiness = request_json(STABLE_ORIGIN + "/readiness")
    health_status, health = request_json(STABLE_ORIGIN + "/health")
    self_status, self_test = request_json(STABLE_ORIGIN + "/v1/self-test")
    dispositions = set()
    for item in self_test.get("results", []):
        if isinstance(item, dict) and item.get("disposition"):
            dispositions.add(item["disposition"])
    if not dispositions and isinstance(self_test.get("observed"), dict):
        dispositions.update(self_test["observed"].values())

    accepted = (
        readiness_status == 200 and readiness.get("state") == "READY"
        and health_status == 200 and health.get("healthy") is True and health.get("canonical_three_layer_bound") is True
        and self_status == 200 and self_test.get("status", self_test.get("state")) == "PASS"
        and {"ALLOW", "DENY", "REVIEW", "FAIL_CLOSED"}.issubset(dispositions)
    )
    if not accepted:
        receipt = dict(base_receipt)
        receipt.update({
            "state": "ACTIVE",
            "transition": "LIVE_ACCEPTANCE_RETRY_REQUIRED",
            "readiness_http_status": readiness_status,
            "health_http_status": health_status,
            "self_test_http_status": self_status,
            "observed_dispositions": sorted(dispositions),
            "next_action": "Retry live acceptance on the next admitted heartbeat; deployment does not imply acceptance."
        })
        write_receipt(receipt_path, receipt)
        json.dump(response("ACTIVE", "LIVE_ACCEPTANCE_RETRY_REQUIRED", epoch, receipt_ref, next_transition="LIVE_ACCEPTANCE_RETRY", retry_latest=epoch + 8), sys.stdout)
        sys.stdout.write("\n")
        return 0

    receipt = dict(base_receipt)
    receipt.update({
        "state": "COMPLETED",
        "transition": "LIVE_ACCEPTANCE_PASS",
        "source_site_worker_blob": observed_blob,
        "readiness": "PASS",
        "health": "PASS",
        "self_test": "PASS",
        "observed_dispositions": sorted(dispositions),
        "next_action": "Propagate stable-rendezvous completion evidence to Site#24 and release the worker task."
    })
    write_receipt(receipt_path, receipt)
    json.dump(response("COMPLETED", "LIVE_ACCEPTANCE_PASS", epoch, receipt_ref, next_transition=None, retry_latest=None), sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
