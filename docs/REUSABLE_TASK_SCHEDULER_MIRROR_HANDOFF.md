# Reusable Task Scheduler Mirror Handoff

Updated: 2026-09-13
Repository: `StegVerse-Labs/.github`
Reusable Task ID: `RT-REUSABLE-TASK-SCHEDULER-001`
Status: `SOURCE MERGED / RUNTIME EVIDENCE PENDING`

## Purpose

Provide one neutral reusable scheduling capability for all registered reusable tasks. Healer is a consumer/example of reusable scheduling, not the semantic or implementation owner of the generic scheduler.

## Canonical source

- `source-bundles/reusable-task-registry.d/RT-REUSABLE-TASK-SCHEDULER-001.json`
- `data/reusable-task-scheduler-contract.json`
- `scripts/run_reusable_task_scheduler.py`
- `scripts/trigger_reusable_task.py`
- `tests/test_neutral_reusable_task_scheduler.py`

## Merged source evidence

PR #1748 exact head `c5763b714c26004636026e1dd32bdbe8cfa40665` passed Organization Control `34778911267`, Deterministic Repository Suite `34778911254`, and Heartbeat `34778911249`, then squash-merged at `035f2694e142d07a763c217311c6a558f034f3de`.

Stale-base PR #1745 was closed unmerged after its own exact head passed the same three validation classes. No runtime evidence is inferred from either validation set.

## Semantics

One invocation evaluates one schedule document, selects due reusable identities, and invokes each through the canonical reusable-task trigger. Child completion and boundary receipts are preserved exactly. A child boundary does not become scheduler authority and does not create a synthetic child success.

The scheduler may not schedule itself. It creates no scheduler-specific WorkerCoordinator, Interlock/InTr, credential, user-verification, provider, publication, runtime, HeartBeat, or Master Records authority.

## Authority owners

- Task Registry: coordination only.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: governed transition/admission authority.
- TV/TVC: credential/provider/release authority.
- KV/SKAP Vault: sole user-verification authority.
- Master Records: observed-reality custody/reconstruction.
- HeartBeat or another resident carrier: may trigger the scheduler, but grants no scheduler authority.
- GitHub: source/evidence coordination only; runtime authority `NONE`.

## Healer relationship

The existing Healer reusable-task scheduling code is evidence that the scheduling pattern works and may consume this neutral reusable task. It is not the canonical generic owner. Migration should delegate Healer's generic reusable-task pass to `RT-REUSABLE-TASK-SCHEDULER-001` and preserve Healer-specific schedule/configuration separately.

## Runtime evidence

Source implementation, merge state, and CI validation do not prove resident scheduling execution. Authentic runtime evidence requires a manifest-bound invocation of `RT-REUSABLE-TASK-SCHEDULER-001`, its standardized runner result, retained child trigger/boundary receipts, and the ordinary reusable-task lifecycle custody/reconstruction chain where applicable.

## Next admissible work

Migrate consumers such as Healer to invoke this reusable identity rather than owning duplicate generic scheduling logic. Separately, retain authentic runtime evidence when the neutral scheduler is invoked on a sovereign resident surface. No dependent Goal Task runtime predicate may be promoted from source migration alone.
