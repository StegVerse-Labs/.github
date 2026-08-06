# StegVerse-Labs Organization Mirror Handoff

## Authority

This file is the primary entry point and sole organizational exit point for organization-scoped work in `StegVerse-Labs`.

Repository-local `*_MIRROR_HANDOFF.md` files remain authoritative for repository-specific implementation evidence. Machine-readable state under `control/`, `tasks/`, `events/`, `heartbeats/`, `warrants/`, and `schemas/` is authoritative for scheduling and transition validation.

## Governing objective

```text
Activate parallel, collision-aware, purpose-bound ecosystem construction with
scoped claims, deterministic queueing, check-in closure, heartbeat reconciliation,
and repository-local enforcement adapters.
```

## Installed on main

- PR #1 merged at `fd020c055ade5ec33a670b2c4b4ede59e394e629`;
- PR #2 merged at `ff72d911f0587115e3bb621e6258a595da70eab2`;
- non-claimable organization control repository;
- task, claim, check-in, heartbeat, scan-warrant, and deficiency schemas;
- active-claim, queue, fencing-counter, heartbeat-state, and append-only event records;
- deterministic allocator with bounded fast-forward CAS retries;
- dependency-cycle, fencing, control-plane, and check-in validators;
- generated machine-state projection and drift workflow;
- `TASK-2026-0001` completed with accepted merged check-in.

## Current task

```yaml
task_id: TASK-2026-0002
issue: 3
status: checkin_pending
branch: feat/org-heartbeat-transport-v0.2
result: partial
```

## Current branch implementation

- deterministic center heartbeat assertion issuer;
- canonical payload digest and nonce generation;
- return validator with typed epoch, claim, fencing, scope, policy, evidence, and nonce deltas;
- separately scheduled expected-return watchdog;
- watchdog evidence records;
- scan-warrant opening for missing returns;
- no authority effect from heartbeat observations.

## Current non-claims

- heartbeat workflows are not merged or running on `main`;
- no repository claimant adapter has returned a nonce-bound beat;
- branch protection and required status checks are not confirmed;
- authoritative automated check-in mutation and atomic release are not active;
- repository-local fencing checks are not required across the ecosystem;
- statistical heartbeat baselines are not active.

## Next authorized actions

1. Review and merge the heartbeat transport branch.
2. Register the first scoped repository claimant without overlapping its active claim surfaces.
3. Install a repository-local return producer and fencing check.
4. Observe one complete nonce-bound heartbeat round trip.
5. Activate deficiency intake and warrant coalescing.
6. Add authoritative check-in mutation and claim release.
7. Propagate adapters to additional repositories through their local handoffs.

## Collision boundary

Do not modify StegCore's active external-evidence claim surfaces:

```text
src/stegcore/external_evidence.py
tests/test_external_evidence.py
scripts/verify_governance_external_evidence_contract.py
contracts/governance_external_evidence_snapshot/
.github/workflows/external-evidence-interop.yml
```

## Closure rule

No task is organizationally closed until its merged result is represented in machine state, its check-in is accepted, applicable claims are released, and this handoff reflects the resulting organization state.

## Archive readiness

```text
thread_archive_ready: false
reason: heartbeat transport and the first repository claimant round trip are not yet merged and evidenced.
```

## Progress snapshot

```text
StegVerse-Labs - 97% complete
StegVerse-Labs/.github - 98% complete
StegVerse-Labs/.github - 95% complete TO CONTROL-PLANE ACTIVATION
Fully developed files vs scaffolding and stubs: scheduler, allocator, fencing foundation,
check-in validation, machine projection, and heartbeat center/watchdog implementation are developed;
repository claimant adapters, live round-trip evidence, required checks, and authoritative release mutation remain.
Delta: organization control is merged; purposeful communications are implemented on the active branch but not yet operating end to end.
```
