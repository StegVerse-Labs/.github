# HIL Universal InTr Materialization Ingress Mirror Handoff

Updated: 2026-08-29
Repository: `StegVerse-Labs/.github`
Issue: #415
Parent HIL activation owner: #246

```text
goal_id: SHWP-HIL-INTR-MATERIALIZATION-INGRESS-415
state: IMPLEMENTED_ON_BRANCH_VALIDATION_PENDING
credential_authority: TV/TVC
github_token_runtime_authority: NONE
authority_effect: NONE_INGRESS_ONLY
runtime_ingress_observed: false
hil_execution_observed: false
```

## Purpose

Close the far-side transport-to-runtime-queue source seam for the existing HIL Universal InTr path without turning transport into execution authority.

Canonical sequence:

```text
registered StegOS Node local outbox
-> TVC admitted route
-> TVC bounded single-use EGRESS authorization
-> StegOS sovereign relay EGRESS executor
-> scripts/serve_hil_intr_materialization_ingress.py
-> runtime/intr-materialization/<materialization_id>.json
-> existing rootless source-refresh watcher
-> existing consume_hil_intr_materialization_request.py
-> existing refresh_and_execute_resident_task.py
-> WorkerCoordinator HIL claim/fence
```

## Ingress contract

The ingress accepts only `POST /intr/materialization` with the transport headers emitted by the merged StegOS executor:

```text
Content-Type: application/octet-stream | application/json
X-StegVerse-Transport: InTr
X-StegVerse-Authorization-Id: non-empty
X-StegVerse-Payload-SHA256: exact raw-body SHA-256
```

The body must independently pass the existing `validate_request()` contract for `stegverse.universal-intr-materialization-request/v1`.

Before returning HTTP 202, the ingress:

1. verifies body size and exact transport payload SHA-256;
2. parses the exact JSON request;
3. reuses the canonical HIL materialization validator;
4. persists a canonicalized request write-once under `intr-materialization/`;
5. persists a write-once ingress receipt under `receipts/sovereign-network/hil-intr-ingress/`;
6. updates only the non-authorizing latest-ingress projection.

Same exact request/authorization is idempotent. A different authorization attempting to overwrite the same materialization receipt fails closed.

## Runtime materialization

`refresh_sovereign_worker_runtime_source.py` now carries `scripts/serve_hil_intr_materialization_ingress.py` into the deployment-local resident runtime during the existing local source refresh. No network fetch or credential acquisition is added.

The server defaults to one request (`--max-requests 1`) and loopback binding. A non-loopback listener requires an explicit TLS certificate and key. Those files are runtime transport identity material; this source lane does not create, store, or authorize them.

## Non-claims

An `INGRESS_ADMITTED` receipt proves only exact queue admission. It does **not** prove:

```text
HIL WorkerCoordinator execution
HIL receiver readiness
HIL exact-byte custody
TVC lifecycle admission
grant consumption
private review
publication
Master Records ingestion
G18 completion
```

The ingress mints no claim/fence, requires no G18 claim, creates no HeartBeat authority, and accepts no GitHub token or bearer credential path.

## Validation boundary

Required before merge:

```text
tests/test_hil_intr_materialization_ingress.py: PASS
existing HIL materialization consumer tests: PASS
sovereign worker source-refresh tests: PASS
organization control-plane validation: PASS
heartbeat validation-only workflow: PASS
```

Source/CI success remains non-runtime evidence. `runtime_ingress_observed` stays false until a real sovereign runtime produces the ingress receipt.
