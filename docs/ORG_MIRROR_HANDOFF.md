# StegVerse-Labs Organization Mirror Handoff

## Authority

This file is the primary organizational continuation and exit record for `StegVerse-Labs` organization-scoped work. Repository-local `*_MIRROR_HANDOFF.md` files remain authoritative for repository-specific implementation. Machine-readable state under `control/`, `tasks/`, `events/`, `heartbeats/`, `handoffs/`, `warrants/`, `receipts/`, and `schemas/` is authoritative for worker scheduling and transition validation.

## Active goal

```text
goal_id: STEGVERSE-HEARTBEAT-WORKER-PROTOCOL-001
repository: StegVerse-Labs/.github
branch: main
parent_owner: issue #12
executor_lifecycle_owner: issue #13
custody_owner: issue #14
status_owner: issue #15
StegGate_admission_owner: issue #24
scoped_handoff: docs/HEARTBEAT_CONTINUITY_WORKER_MIRROR_HANDOFF.md
```

## Canonical architecture

StegVerse has **one heartbeat**.

The heartbeat function itself is the worker scheduling and continuity coordination frame. On each heartbeat epoch it evaluates HANDOFF / worker-registry state. No eligible work means no worker is initiated. Eligible work may be atomically checked out under the existing bounded authority / collision / fencing rules. Active workers return relative transition information on that same heartbeat. The heartbeat epoch is therefore the common timing frame for worker progress, expected/observed transitions, system signals, and delta-HB continuity evidence.

There is no normative second worker heartbeat and no normative third-party scheduler layer.

A missing, late, unchanged, or non-following transition is an observation. It is **not by itself evidence that continuity is lost**. Continuity interpretation depends on the broader expected/observed transition and signal evidence and the ability to reconcile or reconstruct the path.

## Current worker truth

The former ChatGPT `StegVerse Worker Cycle` bootstrap automation is disabled and is not current execution authority or the SHWP scheduler.

Canonical registry state is now:

```text
task_id: STEGGATE-AUDITKIT-001
repository: StegVerse-Labs/ara-admissibility-interop
state: HANDOFF_READY
executor_binding: UNBOUND
worker_id: null
claim_id: null
heartbeat_timing: null
archive_eligible: false
```

The existing Master Records checkpoint remains valid historical/custody evidence, but it does not imply an active worker.

Canonical files:

```text
control/heartbeat-state.json
control/worker-registry.json
control/worker-status.json
control/heartbeat-continuity.json
handoffs/STEGGATE-AUDITKIT-001.json
schemas/heartbeat.schema.json
schemas/heartbeat-transition-observation.schema.json
schemas/worker-registry.schema.json
schemas/worker-runtime-cost-basis.schema.json
scripts/issue_heartbeats.py
scripts/project_heartbeat_workers.py
scripts/reconcile_heartbeat_continuity.py
scripts/watch_heartbeat_returns.py
docs/HEARTBEAT_CONTINUITY_WORKER_MIRROR_HANDOFF.md
```

## Installed single-HB continuity / worker slice

Implemented on 2026-08-08:

```text
4fef7cf  heartbeat transition observation schema
1419f4f  worker runtime cost-basis schema
129d407  heartbeat continuity reconciler
770084f  worker registry HB-relative timing + cost/external-job refs
160918e  worker status projector uses organization HB epoch as canonical timing frame
b6a4761  disabled bootstrap worker reconciled to HANDOFF_READY / UNBOUND
1eeb9db  GitHub workflow changed to validation-only; scheduled cron removed
4317e98  heartbeat continuity projection seeded
2ea6a40  scoped heartbeat continuity worker handoff
```

Hosted validation:

```text
Heartbeat Worker Project run 31234619218: SUCCESS
Heartbeat Worker Project run 31234633127: SUCCESS
```

The GitHub workflow is a validator/projector only. It is not a scheduler or production activation dependency.

## Master Records reconciliation rule

Known HB-relative worker expiry does not equal completion.

If the heartbeat reaches a worker's known expiry and the required final worker report is absent from Master Records, the continuity reconciler must surface a lifecycle inconsistency and produce recovery/reconciliation work for normal registry admission. The expired worker does not silently regain authority.

Investigation may require sandbox testing. Candidate solutions remain non-executable until an appropriate remediation is validated and admitted through the normal registry/authority path.

## Ecosystem transaction cost basis

Worker expiry and deployment estimates must increasingly use evidence rather than guessed fixed intervals.

The ecosystem transaction cost basis applies to internal and external-entity jobs and may accumulate evidenced:

- heartbeat transitions to completion and idle-transition behavior;
- compute and token consumption;
- storage and network consumption;
- latency;
- operator burden;
- external provider / external entity cost;
- failure, retry, investigation, sandbox, recovery, custody, and reconstruction costs;
- worker class / capability;
- task / external-entity job class;
- authority, admissibility, evidence, and reconstruction constraints.

As evidence grows, it should improve expected completion envelopes, worker expiry estimates, worker/capability selection, handoff/recovery decisions, capacity planning, external-job costing, pricing strategy, and provider-independence decisions.

Cost never overrides admissibility, authority, evidence fidelity, or reconstructability.

## Historical executor proof retained

The disabled bootstrap executor previously performed real ara implementation and hosted validation:

```text
StegVerse-Labs/ara-admissibility-interop
branch: feat/steggate-v46-schema-foundation
implemented: fixtures/verifier/cases.json
implemented: tools/verify_audit_kit.py
integrated: .github/workflows/steggate-schema-foundation.yml
validated head: ba68c6e93f2d97c9355832d9bfb226900f27c7a1
StegGate Schema Foundation run: 31231723418
job: 93036736627
result: SUCCESS
```

Master Records checkpoint evidence retained:

```text
repository: master-records/orchestration
commit: 484696c2d6d7b69fa324e5b1f169c51d740ad925
custody_record: custody/worker-lifecycle/SHWP-CUSTODY-STEGGATE-AUDITKIT-001-G1-001.json
custody_sha256: ac2cbba5b3f3c2e91893eabc63c9ba2221c226cbe1c7e3c70459d9ce75dc0cb2
validation run: 31231978969
job: 93037458942
result: SUCCESS
```

These are historical implementation/custody proofs, not evidence that a worker is currently active.

## Collision / coordination invariant

All SHWP child issues are implementation details of issue #12, not independent architecture workstreams. Parent #12 controls if a child description conflicts with the single-heartbeat model.

No session or worker may introduce a separate scheduler, worker heartbeat, conversational activation dependency, or third-party wake dependency as the normative SHWP architecture.

Status reads are observational and must not trigger duplicate work.

## Current build boundary

Built:

- heartbeat issuance/return primitives;
- deterministic return comparison and fault/warrant primitive;
- HANDOFF and worker registry contracts;
- claim/fencing identities;
- Master Records checkpoint custody first slice;
- HB-relative worker timing contract;
- expected/observed transition + signal / delta-HB contract;
- continuity reconciler with `continuity_lost=false` for observation-only discrepancies;
- known-expiry + missing-Master-Records-finalization recovery-task candidate;
- worker runtime / external-job cost-basis contract;
- validation-only hosted checks.

Not yet proven:

- one native high-frequency heartbeat function that composes HANDOFF discovery, atomic worker checkout, worker initiation, and worker transition returns;
- exactly-one worker activation under competing heartbeat cycles;
- worker transition responses on every heartbeat in a live runtime;
- cost-basis-derived expiry estimation from a growing empirical transaction dataset;
- automatic admission/execution of validated recovery/remediation tasks;
- full lifecycle custody through expiry, recovery, completion, and claim release.

## Next implementation seam

Under issue #12, compose the existing organization heartbeat path with HANDOFF / worker-registry evaluation in one internal heartbeat cycle and prove:

```text
no eligible work -> no worker initiated
eligible HANDOFF -> exactly one fenced worker initiated
active worker -> relative transition state returned every HB
expected/observed transitions + signals -> delta-HB evidence
known expiry + missing required MR final report -> recovery task
investigation -> sandbox candidate -> validated remediation -> registry
transaction cost observations -> improved worker expiry/deployment estimate
no third-party scheduler required
```

## Session posture

This conversation is an implementation session only. It has no scheduled monitoring task and no automation has been created or enabled for it.

```text
thread_archive_ready: false
reason: active implementation goal remains incomplete and native single-HB worker initiation is not yet proven
```
