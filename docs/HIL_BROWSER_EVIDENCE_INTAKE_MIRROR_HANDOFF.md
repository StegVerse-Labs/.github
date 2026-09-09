# HIL Browser Evidence Intake Mirror Handoff

Updated: 2026-09-08
Repository: `StegVerse-Labs/.github`
Issue: `#1211`
Goal task: `SHWP-HIL-SOVEREIGN-RECEIVER-001`
COSV: `50000000105000`
Canonical request: `RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002`
Predicate: `PRED-RESIDENT-REQUEST-CONSUMED-HIL-SOVEREIGN-RECEIVER-002`

## Triggering physical evidence

A current-iPhone standalone browser context produced component result `BROWSER_HIL_LOCAL_READY_OBSERVED` with HIL claim/fence G25. The ChatGPT in-app browser simultaneously showed an independent fail-closed state because it is a separate WebKit storage/service-worker context. Browser contexts must therefore be treated as independent resident storage partitions unless an explicit governed transfer exists.

The screenshot establishes that a physical result was displayed, but screenshots are not accepted by this intake as the canonical component artifact. The exact exported JSON is required.

## Canonical request binding

Exact stable request SHA256:

`6bf940fb920f672111ba1040fd0bf9bf7016d6bf032bbcfd164a1a2347ee7038`

The Site successor binds this request id/hash into the browser receiver execution result. The intake rejects any mismatch.

## Intake implementation

`scripts/intake_hil_browser_execution_evidence.py`

Inputs:
- canonical `control/resident-execution-request.d/hil-sovereign-receiver-001.json`
- exact JSON exported by the physical current-iPhone HIL browser surface

Required component evidence includes:
- `BROWSER_HIL_LOCAL_READY_OBSERVED`
- exact request id/hash
- exact HIL task id
- `ctx_<32hex>` browser context id
- claim/fence consistency above G24
- canonical local-ready transition
- journal replay `PASS`
- no second claim
- browser execution observed
- same-device true
- TV/TVC credentials
- GitHub runtime authority NONE
- heartbeat authority false
- InTr transition authority not claimed by the component
- component `request_consumption_claimed=false`

If and only if all checks pass, the deterministic intake can emit the existing canonical HIL resident-consumption schema with:

```text
state = COMPLETED
runtime_execution_attempted = true
runtime_execution_surface = CURRENT_USER_IPHONE_BROWSER
terminal_hil_transition_observed = true
terminal_hil_transition = HIL_RECEIVER_LOCAL_READY_PUBLIC_RENDEZVOUS_REQUIRED
broader_hil_lifecycle_complete = false
retry_allowed = false
```

This does not pretend a Python subprocess ran. The consumption receipt records the portable browser successor as the runtime execution surface and embeds the exact component evidence plus its stable hash.

## Evidence boundary

No physical evidence JSON is committed by this source change. CI fixtures are synthetic negative/positive validator tests only and do not satisfy the runtime predicate.

The predicate remains unsatisfied until the exact physical browser artifact is supplied to the canonical intake and the resulting receipt is persisted at the canonical resident runtime evidence location.

## Authority invariants

```text
WorkerCoordinator claim/fence authority = unchanged
Interlock/InTr transition authority = unchanged
TV/TVC credential authority = unchanged
GitHub token runtime authority = NONE
HB execution authority = NONE
second machine required = false
screenshot substitution = prohibited
source/CI/merge authority effect = NONE
```
