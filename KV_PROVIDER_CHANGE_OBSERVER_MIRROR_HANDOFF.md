# KV Provider Change Observer Mirror Handoff

Status: SOURCE_MERGED_VALIDATED / RESIDENT_ACTIVATION_PENDING
Repository: `StegVerse-Labs/.github`
Issue: #362
Implementation PR: #363
Validated head: `ea2b1ee3c5be0ff76402af7fce90de23252c857c`
Merge commit: `f6e31f28b5b795e2a9e67128189a6de153c1f39a`
Task-vector integration PR: #402
Task-vector merge: `f258e3e7d6dca999b1a24095495b344e73401742`
Updated: 2026-08-29
Authority effect: NONE
Credential authority: TV/TVC
Production monitoring authority: SOVEREIGN_RESIDENT_ONLY

## Purpose

Provide the machine-execution surface that observes authoritative provider/source change feeds for Personal KV connection assemblies and emits bounded, non-secret source-change observations.

This lane operationalizes the source contract merged in `StegVerse-Labs/continuity-vault-kit`:

- `KV_CONNECTION_ASSEMBLY_SOURCE_MIRROR_HANDOFF.md`
- `KV_MONITOR_TARGETS_CANONICAL_STATE_MIRROR_HANDOFF.md`
- `schemas/kv-source-change-observation.schema.json`
- `schemas/kv-connection-health-receipt.schema.json`

## Execution model

```text
canonical private-KV Monitor_Targets.json
 -> admitted resident provider-change observer
 -> authoritative provider docs/changelog/status source
 -> TLS/source-policy verification
 -> content/version fingerprint
 -> classified source-change observation
 -> KV connection-health reconciler
 -> revalidation / repair state
```

## Hard boundaries

1. GitHub Actions may validate source only. It is never production monitoring authority.
2. The observer must run on an admitted sovereign/resident StegVerse surface.
3. Provider credentials, passwords, tokens, API keys, cookies, private keys, and reusable authentication material are prohibited inputs.
4. The observer performs public/documentation/status observation only; it does not authenticate to owner accounts.
5. It performs no provider mutation, payment, trade, transfer, send, delete, upload, or account-management action.
6. TV/TVC credential authority remains unchanged.
7. SKAP is not resolved by this observer.
8. The observer may emit only non-secret compatibility evidence.
9. Source authenticity/policy admission, TLS transport, and persistence must fail closed.
10. Observed changes do not automatically rewrite a connection route or mark it VERIFIED; they trigger the canonical KV connection-health/revalidation process.

## Implemented machine surfaces

- `KV_PROVIDER_CHANGE_OBSERVER_MIRROR_HANDOFF.md`
- `handoffs/KV-PROVIDER-CHANGE-OBSERVER-001.json`
- `control/worker-registry.d/kv-provider-change-observer-001.json`
- `control/process-worker-adapters.d/kv-provider-change-observer-001.json`
- `control/task-vectors/KV-PROVIDER-CHANGE-OBSERVER-001.json`
- `workers/kv_provider_change_observer_worker.py`
- `tests/test_kv_provider_change_observer_worker.py`
- `schemas/kv-provider-monitor-targets.v1.schema.json`
- `scripts/check_kv_provider_change_observer.py`

## Validation and integration evidence

PR #363 is merged. Its exact implementation head `ea2b1ee3c5be0ff76402af7fce90de23252c857c` produced successful hosted validation evidence:

- Validate organization control plane - No GitHub Token Authority: run `33191598718` SUCCESS
- Heartbeat Worker Project - Validation Only / No GitHub Token Authority: run `33191598517` SUCCESS

PR #402 later projected `KV-PROVIDER-CHANGE-OBSERVER-001` and the connection-health reconciler into canonical task-vector control. That PR merged as `f258e3e7d6dca999b1a24095495b344e73401742` and explicitly preserves independent task-control ownership, two-blocker registry/handoff parity, no credential/provider-operation authority, no third-party-runtime requirement, and no activation claim.

Hosted validation proves source/control-plane conformance only. It does not prove resident execution.

## Admission dependencies

- sovereign resident worker runtime is genuinely active;
- canonical machine-readable KV monitoring targets are available from the private KV;
- each target source is explicitly admitted as authoritative public provider documentation/changelog/status;
- no credential-bearing environment is present;
- output persistence target is resident/private and non-secret;
- connection-health reconciler is admitted to consume the observation without acquiring provider or verification authority.

## Output

The worker emits observations compatible with:

`stegverse.kv.source-change-observation/v1`

and never marks a connection as VERIFIED by itself.

## Remaining machine-execution work

1. Observe an admitted sovereign/resident worker claim for `KV-PROVIDER-CHANGE-OBSERVER-001`.
2. Bind the worker to canonical private-KV `Monitor_Targets.json` rather than an ad hoc external target list.
3. Execute an authentic baseline poll against admitted public provider documentation/status targets.
4. Persist the resulting non-secret fingerprints/observations on the resident/private evidence surface.
5. Prove handoff into the KV connection-health reconciler.
6. On an actual source change, prove stale VERIFIED state is invalidated and the separate revalidation-proof lane is invoked without granting credentials or provider-operation authority.

## Current boundary

Repository/source implementation, worker registration, exact-head hosted validation, merge, and canonical task-vector integration are COMPLETE.

Issue #362 is therefore complete for its repository-owned deliverable and may remain closed. The remaining deficit is authentic resident execution evidence, not additional implementation in this issue.

No provider source poll, resident claim, private-KV target binding, or production observation is claimed by this handoff absent inspectable runtime evidence.
