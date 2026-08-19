# Healer Failure-Mailbox Live-Shadow Source Validation Receipt

Date: 2026-08-18
Repository: `StegVerse-Labs/.github`
Task: `HEALER-FAILURE-MAILBOX-LIVE-SHADOW-001`
Authority effect: **NONE**
Runtime activation effect: **NONE**
Heartbeat effect: **NONE**
Credential authority: **TV/TVC**

## Installed execution surfaces

- `workers/healer_failure_mailbox_shadow_worker.py`
- `handoffs/HEALER-FAILURE-MAILBOX-LIVE-SHADOW-001.json`
- `control/worker-registry.d/healer-failure-mailbox-shadow-001.json`
- `control/process-worker-adapters.d/healer-failure-mailbox-shadow-001.json`
- `tests/test_healer_failure_mailbox_shadow_worker.py`

The worker accepts only already-materialized local Healer source, a bounded mailbox-observation JSONL batch, and a non-secret manifest. Gmail/OAuth/GitHub credential-bearing environment variables are rejected before execution. Mailbox credentials are not available to the worker.

## Validation attempt 1 — PR #231

Both canonical validation workflows failed before reaching the new shadow-worker tests because of pre-existing central control-plane drift:

- four executable handoffs had schema/metadata drift;
- `.github/workflows/test-lanes-autolaunch-validation.yml` was absent from the workflow-surface registry.

Those defects were repaired on `main` without granting runtime, credential, spend, or heartbeat authority.

## Validation attempt 2 — PR #232

Workflow: `Heartbeat Worker Project - Validation Only / No GitHub Token Authority`
Run: `32215254150`
Job: `95955450006`

Positive evidence before the unrelated suite failures:

- canonical JSON parse: **PASS**, 301 JSON surfaces;
- executable handoff validation: **PASS**, `count=36 live_lanes=32 skipped_non_executable=5`;
- all four Healer shadow-worker focused tests: **PASS**:
  - forbidden Gmail/GitHub credential environment blocks before execution;
  - invocation requires a canonical scheduler claim and TV/TVC authority boundary;
  - manifest must attest `mailbox_mutated=false` and `credential_authority=TV/TVC`;
  - registry/adapter/handoff contract exposes no mailbox, OAuth, GitHub, or provider credential variables.

The complete deterministic repository suite remained red (`431` tests, `11` failures and `17` errors) because of independent central migration debt. Examples include stale pre-independent-oscillator HB30/HB31 expectations, removed state-transition helper APIs, engine-v12 assertions while the current carrier import resolves to engine-v13, missing retrospective denominator entries, and older mirror-handoff ownership metadata. These failures do **not** constitute a live-shadow worker failure and must not be repaired by restoring worker/task causality to heartbeat progression.

Workflow: `Validate organization control plane - No GitHub Token Authority`
Run: `32215254108`
Job: `95955449816`

Positive evidence:

- workflow-surface hygiene: **PASS**, 18/18 actual/registered surfaces;
- organization control-plane invariants: **PASS**;
- active-worker state invariant: **PASS**, 28 fragment active tasks.

Remaining failure:

- 14 older `*_MIRROR_HANDOFF.md` files lack the required `## Execution ownership and collision partition` section under `control/handoff-execution-ownership-policy.json`.
- Policy default for an absent section is `RECONCILIATION_REQUIRED` with `manual_execution_allowed=false`; absence therefore cannot authorize manual/session duplicate execution.

## Current classification

```text
shadow_worker_source: INSTALLED
shadow_worker_focused_contract_validation: PASS
central_executable_handoff_validation: PASS
central_workflow_hygiene: PASS
central_active_worker_invariant: PASS
complete_central_test_suite: FAIL_INDEPENDENT_MIGRATION_DEBT
sovereign_shadow_execution: NOT_OBSERVED
mailbox_transport_materialization: NOT_OBSERVED
canonical_scheduler_claim: NOT_OBSERVED
package_release: PROHIBITED
```

## Next governed path

1. Preserve the current independent oscillator semantics; do not resurrect pre-oscillator state-transition causality to satisfy stale tests.
2. Reconcile central migration debt under the owning heartbeat/COSV/handoff workstreams.
3. TVC owns credential-bearing mailbox observation/materialization. It must emit only a sanitized bounded JSONL batch plus a non-secret manifest.
4. WorkerCoordinator may bind `HEALER-FAILURE-MAILBOX-LIVE-SHADOW-001` only after that materialized input is available and a fresh collision-safe claim exists.
5. A coverage gap blocks the batch. Unable/impossible-to-repair follows the sandbox-resolution protocol.

Source validation is not runtime activation, live mailbox processing, or release evidence.
