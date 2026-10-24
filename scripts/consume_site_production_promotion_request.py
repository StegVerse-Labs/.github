#!/usr/bin/env python3
"""Consume a committed SPPA request manifest against the real organization ledger.

The manifest-dispatched run of the Site production-promotion authorization
transition (scripts/authorize_site_production_promotion.py). It follows the
org claim allocator request path: a request committed at one of the fixed
REQUEST_RELS under control/resident-execution-request.d/ is materialized into
the resident runtime and visited by scripts/dispatch_resident_execution_requests.py
(selector `site_production_promotion`), which hands this consumer the ledger
roots it was supplied (STEGVERSE_REPO_LEDGER_ROOT / STEGVERSE_ORG_LEDGER_ROOT).
Without them nothing is evaluated against a ledger: FAIL_CLOSED, six fields.

The request is never authority: it names the evidence, SPPA decides, the
receipt it appends is the record, and only a receipt that reads back is a
disposition. This consumer contacts no provider, changes no provider setting,
deploys nothing and reads no clock. A hosted environment is refused, as for
the org claim allocator (clean_env).

Expected first real run: FAIL_CLOSED. Until Labs#3241 and Labs#3243 merge
and a carrier frame reaches the request (JDQ Q-D-6, default refuse), no
carrier heartbeat epoch is supplied, so a promotion whose other predicates
all pass is FAIL_CLOSED HB_EPOCH_NOT_SUPPLIED, and a retro-classification is
FAIL_CLOSED on its first failed predicate.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "stegverse.resident-execution-request/v1"
TASK_ID = "STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001"
MODE = "SITE_PRODUCTION_PROMOTION_AUTHORIZATION"
ENTRYPOINT = "scripts/consume_site_production_promotion_request.py"
TRANSITION = "scripts/authorize_site_production_promotion.py"
# The fixed list. A path here is read only if a committed request was materialized there.
REQUEST_RELS = (
    Path("control/resident-execution-request.d/site-production-promotion-001.json"),
)
CONSUMPTION_DIR = Path("receipts/sovereign-host/site-production-promotion-consumptions")
RECEIPT_REL = Path("receipts/sovereign-host/site-production-promotion-request-consumption.latest.json")
RETRY_ENTRYPOINT = ENTRYPOINT + "::consume"
LEDGER_REQUIRED = "LEDGER_LOCATION_REQUIRED_FROM_MATERIALIZER"
REQUEST_INVALID = "SITE_PRODUCTION_PROMOTION_REQUEST_INVALID"
HOSTED_REFUSED = "HOSTED_ENVIRONMENT_NOT_ADMITTED"
REQUIRED = {
    "schema": SCHEMA,
    "state": "REQUESTED",
    "task_id": TASK_ID,
    "mode": MODE,
    "entrypoint": ENTRYPOINT,
    "transition": TRANSITION,
    "credential_authority": "TV/TVC",
    "github_token_runtime_authority": "NONE",
    "authority_effect": "NONE_REQUEST_ONLY",
}
REQUIRED_FALSE = ("github_token_required", "network_source_fetch_allowed", "second_machine_required",
                  "heartbeat_grants_execution_authority", "request_grants_promotion_authority",
                  "provider_settings_change_allowed", "deployment_performed_by_consumer")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def validate_request(request: Any) -> None:
    if not isinstance(request, Mapping):
        raise ValueError("request is not an object")
    for key, expected in REQUIRED.items():
        if request.get(key) != expected:
            raise ValueError(f"request {key} must be {expected!r}")
    for key in REQUIRED_FALSE:
        if request.get(key) is not False:
            raise ValueError(f"request {key} must be false")
    if request.get("sppa_remains_promotion_authority_record") is not True:
        raise ValueError("request must leave the SPPA receipt as the only promotion record")
    promotion = request.get("promotion_request")
    if not isinstance(promotion, Mapping):
        raise ValueError("request carries no promotion_request")
    if request.get("promotion_request_sha256") != stable_hash(promotion):
        raise ValueError("promotion_request_sha256 does not recompute")


def refusal(request: Mapping[str, Any] | None, rel: Path | None, code: str, detail: str, repair: str) -> dict[str, Any]:
    return {
        "schema": "stegverse.resident-execution-request-consumption/v1",
        "state": "FAIL_CLOSED", "task_id": TASK_ID, "mode": MODE,
        "request_id": (request or {}).get("request_id") if isinstance(request, Mapping) else None,
        "request_ref": rel.as_posix() if rel else None,
        "disposition": "FAIL_CLOSED", "failure_code": code, "failed_predicate": code, "detail": detail,
        "required_evidence_or_repair": repair, "retry_entrypoint": RETRY_ENTRYPOINT,
        "owning_existing_goal": TASK_ID,
        "next_attempt": "on the next resident dispatch after the repair is recorded",
        "transition_attempted": False, "receipt_appended": False, "promotion_may_proceed": False,
        "consequence_committed": False, "authority_effect": "NONE_REFUSAL_ONLY",
    }


def write_once(path: Path, value: Mapping[str, Any]) -> dict[str, Any]:
    """The first record of this disposition is kept; a replay returns it unchanged."""
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(value, indent=2, sort_keys=True) + "\n"
    fd, name = tempfile.mkstemp(prefix=".once-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(rendered)
        try:
            os.link(name, path)
        except FileExistsError:
            return json.loads(path.read_text(encoding="utf-8"))
    finally:
        os.unlink(name)
    return dict(value)


def consume_one(source: Path, runtime: Path, rel: Path, *, repo_ledger_root: Path | None,
                org_ledger_root: Path | None, hb_epoch: str | None, sppa) -> dict[str, Any]:
    try:
        request = json.loads((runtime / rel).read_text(encoding="utf-8"))
        validate_request(request)
    except (ValueError, json.JSONDecodeError) as exc:
        return refusal(None, rel, REQUEST_INVALID, str(exc),
                       "commit a request matching " + SCHEMA + " with mode " + MODE)
    if repo_ledger_root is None:
        # Supplied, never derived: the real ledger is never located from the host.
        return refusal(request, rel, LEDGER_REQUIRED, "ledger roots not supplied",
                       "dispatch with STEGVERSE_REPO_LEDGER_ROOT (and the declared organization store or root)")
    try:
        result = sppa.authorize(request["promotion_request"], source=source, repo_ledger_root=repo_ledger_root,
                                org_ledger_root=org_ledger_root, hb_epoch=hb_epoch)
    except ValueError as exc:
        return refusal(request, rel, REQUEST_INVALID, "promotion_request: " + str(exc),
                       "commit a promotion_request matching " + sppa.REQUEST_SCHEMA)
    body = {
        "schema": "stegverse.resident-execution-request-consumption/v1",
        "state": "ATTEMPT_RECORDED" if result.get("receipt_appended") or result.get("transition_class") is None
        else "FAIL_CLOSED",
        "task_id": TASK_ID, "mode": MODE, "request_id": request.get("request_id"),
        "request_ref": rel.as_posix(), "request_sha256": stable_hash(request),
        "promotion_request_sha256": request["promotion_request_sha256"],
        "transition_class": result.get("transition_class"), "transition_id": result.get("transition_id"),
        "disposition": result.get("disposition"), "classification": result.get("classification"),
        "failed_predicates": result["evidence"]["failed_predicates"],
        "repository_receipt_sha256": result.get("repository_receipt_sha256"),
        "organization_receipt_sha256": result.get("organization_receipt_sha256"),
        "receipt_appended": result.get("receipt_appended"),
        "organization_readback": result.get("organization_readback"),
        "promotion_may_proceed": result.get("promotion_may_proceed") is True,
        "carrier_hb_epoch_supplied": hb_epoch is not None,
        "request_granted_promotion_authority": False, "deployment_performed": False,
        "provider_settings_changed": False, "authority_effect": "NONE",
    }
    for field in sppa.SIX_FIELDS:
        if field in result:
            body[field] = result[field]
    key = result.get("transition_id") or ("UNRECORDED-" + stable_hash(
        {"request": body["request_sha256"], "failure_code": result.get("failure_code")})[:24])
    retained = write_once(runtime / CONSUMPTION_DIR / f"{key}.json", body)
    (runtime / RECEIPT_REL).parent.mkdir(parents=True, exist_ok=True)
    (runtime / RECEIPT_REL).write_text(json.dumps({**retained, "evidence_ref": (CONSUMPTION_DIR / f"{key}.json").as_posix()},
                                                  indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return retained


def consume(source_root: Path, runtime_root: Path, *, repo_ledger_root: Path | None = None,
            org_ledger_root: Path | None = None, hb_epoch: str | None = None,
            env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source, runtime = source_root.expanduser().resolve(), runtime_root.expanduser().resolve()
    present = [rel for rel in REQUEST_RELS if (runtime / rel).is_file()]
    if not present:
        return {"schema": "stegverse.resident-execution-request-consumption/v1", "state": "NO_REQUEST",
                "task_id": TASK_ID, "mode": MODE, "transition_attempted": False, "authority_effect": "NONE"}
    allocator = _load("sppa_consumer_org_claim", source / "scripts/consume_org_claim_allocator_request.py")
    try:
        allocator.clean_env(dict(os.environ if env is None else env))
    except RuntimeError as exc:
        return refusal(None, present[0], HOSTED_REFUSED, str(exc),
                       "run on the resident dispatch path; a hosted runner is not an admitted execution locus")
    sppa = _load("sppa_consumer_transition", source / TRANSITION)
    attempts = [consume_one(source, runtime, rel, repo_ledger_root=repo_ledger_root, org_ledger_root=org_ledger_root,
                            hb_epoch=hb_epoch, sppa=sppa) for rel in present]
    if len(attempts) == 1:
        return attempts[0]
    return {"schema": "stegverse.resident-execution-request-consumption/v1",
            "state": "FAIL_CLOSED" if any(a["state"] == "FAIL_CLOSED" for a in attempts) else "ATTEMPT_RECORDED",
            "task_id": TASK_ID, "mode": MODE, "attempts": attempts, "authority_effect": "NONE"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--repo-ledger-root", type=Path, default=None)
    parser.add_argument("--org-ledger-root", type=Path, default=None)
    parser.add_argument("--hb-epoch", type=str, default=None, help="carrier-supplied heartbeat epoch; never sampled")
    args = parser.parse_args()
    result = consume(args.source_root, args.runtime_root, repo_ledger_root=args.repo_ledger_root,
                     org_ledger_root=args.org_ledger_root, hb_epoch=args.hb_epoch)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] in ("NO_REQUEST", "ATTEMPT_RECORDED") else 1


if __name__ == "__main__":
    raise SystemExit(main())
