# Native Email Reusable Hourly Mirror Handoff

Updated: 2026-09-09
Repository: `StegVerse-Labs/.github`
Task: `STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001`
COSV task vector: `10100000100000`
Reusable identity: `RT-NATIVE-EMAIL-ACTION-MONITOR-001`
Parent handoff: `docs/NATIVE_EMAIL_ACTION_MONITOR_MIRROR_HANDOFF.md`
Scheduler owner: `StegVerse-Labs/StegVerse-Healer` / existing `SHWP-HEALER-SOVEREIGN-SCHEDULER-001`
Source merge: PR `#1252` / merge `700f959dca0160f0d71d92fc391c9f262f27feea`
Scheduler merge: `StegVerse-Labs/StegVerse-Healer#57` / merge `ef5d90a8c215056e055385a04534e16c49d9a3d5`
State: `SOURCE_INTEGRATION_MERGED / HOURLY_REUSABLE_BINDING_MERGED / CANONICAL_TASK_SHARD_RECONCILIATION_IN_PROGRESS / AUTHENTIC_SCHEDULED_RUNTIME_RECEIPT_PENDING`

## Scoped objective

Make the existing native email action monitor both directly reusable through the canonical reusable-task trigger and recurring on an hourly timer without creating another mailbox monitor, heartbeat, polling loop, WorkerCoordinator, scheduler, or credential route.

## Merged source

PR #1252 updates `scripts/trigger_reusable_task.py` so the already-registered `RT-NATIVE-EMAIL-ACTION-MONITOR-001` primary runner receives its required `--source-root` and `--runtime-root` arguments from the manifest-bound invocation parameters. Other reusable runners retain their prior command shape.

The hourly timer binding is merged in `StegVerse-Labs/StegVerse-Healer#57` through `data/reusable_task_schedule.json` and the existing sovereign Healer scheduler. Each UTC-hour slot uses a deterministic invocation id and retained local receipt so repeated resident visits within the same hour do not duplicate the reusable invocation.

## Cadence

```text
cadence: HOURLY
eligible_utc_hours: 00..23
at_most_once_per_slot: true
slot_identity: RT-NATIVE-EMAIL-ACTION-MONITOR-001 + UTC YYYYMMDDTHH
mailbox_batch_limit: existing native monitor limit (100)
```

A scheduled invocation may still stop at an existing provider/runtime boundary. Timer eligibility does not prove provider authorization, mailbox access, corrective-task completion, runtime activation, or Master Records custody.

## Canonical Task Registry reconciliation

The post-merge registry check found that the reusable-task registry and COSV task-vector index already contained this identity, but the canonical sharded Task Registry did not contain the exact task record. The reconciliation branch `fix/native-email-canonical-task-registry-20260909` adds:

- `data/canonical-task-records/STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001.json` with `coordination_state=PROPOSED`, `checkout_state=UNCLAIMED`, COSV `10100000100000`, source/dependency/evidence bindings, and `allowed_next_transitions=[INGRESS_ADMITTED]`;
- `tests/test_native_email_canonical_task_registry.py` proving generic sharded Task Registry resolution and canonical-work ingress eligibility.

This registry repair records coordination intent only; it does not claim a WorkerCoordinator claim/fence, mailbox execution, provider authorization, or activation.

## README determination

The root `.github/README.md` already documents the reusable-task architecture, sharded canonical Task Registry model, and generic continuation/authority boundaries. This scoped change does not add a new repository responsibility or public interface; detailed cadence and task-specific registry state belong in this handoff and the Healer scheduler README. `NO_README_CHANGE_REQUIRED` for `.github` is therefore recorded for this change set.

## Validation evidence

The exact PR #1252 head `d13f210e7a75e9a3a6515d157d9bc4fed148f51b` passed all retained pull-request validation families before merge:

- Heartbeat Worker Project - Validation Only / No GitHub Token Authority: run `34332023132` SUCCESS.
- Validate organization control plane - No GitHub Token Authority: run `34332023277` SUCCESS.
- Deterministic Repository Suite - Diagnostic Evidence Only: run `34332023168` SUCCESS.

The coordinated Healer exact head `99e63e6e01962232125f70becec5e21eac11ae30` passed Test Readiness run `34332190725` after correcting a test-fixture aliasing defect; the scheduler implementation itself was not weakened.

## Remaining authentic boundary

Source integration, reusable invocation binding, hourly cadence configuration, same-slot idempotency, tests, README maintenance, and both repository merges are complete. Canonical Task Registry shard reconciliation is being validated. After that, the remaining evidence boundary is an authentic resident Healer scheduled invocation producing a retained reusable-task receipt for an hourly slot. Until that is observed, this handoff does not claim live hourly mailbox execution.
