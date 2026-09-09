# Native Email Reusable Hourly Mirror Handoff

Updated: 2026-09-09
Repository: `StegVerse-Labs/.github`
Task: `STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001`
COSV task vector: `10100000100000`
Reusable identity: `RT-NATIVE-EMAIL-ACTION-MONITOR-001`
Parent handoff: `docs/NATIVE_EMAIL_ACTION_MONITOR_MIRROR_HANDOFF.md`
Scheduler owner: `StegVerse-Labs/StegVerse-Healer` / existing `SHWP-HEALER-SOVEREIGN-SCHEDULER-001`

## Scoped objective

Make the existing native email action monitor both directly reusable through the canonical reusable-task trigger and recurring on an hourly timer without creating another mailbox monitor, heartbeat, polling loop, WorkerCoordinator, scheduler, or credential route.

## Source change

`feat/native-email-reusable-hourly-20260909` updates `scripts/trigger_reusable_task.py` so the already-registered `RT-NATIVE-EMAIL-ACTION-MONITOR-001` primary runner receives its required `--source-root` and `--runtime-root` arguments from the manifest-bound invocation parameters. Other reusable runners retain their prior command shape.

The hourly timer binding is owned downstream by `StegVerse-Labs/StegVerse-Healer:data/reusable_task_schedule.json` and executes through the already-existing sovereign Healer scheduler. Each UTC-hour slot uses a deterministic invocation id and retained local receipt so repeated resident visits within the same hour do not duplicate the reusable invocation.

## Cadence

```text
cadence: HOURLY
eligible_utc_hours: 00..23
at_most_once_per_slot: true
slot_identity: RT-NATIVE-EMAIL-ACTION-MONITOR-001 + UTC YYYYMMDDTHH
mailbox_batch_limit: existing native monitor limit (100)
```

A scheduled invocation may still stop at an existing provider/runtime boundary. Timer eligibility does not prove provider authorization, mailbox access, corrective-task completion, runtime activation, or Master Records custody.

## README determination

The root `.github/README.md` already documents the reusable-task architecture and the generic continuation/authority boundaries. This scoped change does not add a new repository responsibility or public interface; detailed cadence belongs in this task handoff and the Healer scheduler README. `NO_README_CHANGE_REQUIRED` for `.github` is therefore recorded for this change set.

## Validation requirements

- `tests/test_reusable_native_email_trigger.py` passes.
- Existing reusable-task and native-email tests remain green.
- StegVerse-Healer scheduled-task tests prove hourly configuration and same-slot idempotency.
- Both repository PRs merge before source integration is called complete.
- Authentic scheduled runtime receipt remains separately required before claiming live hourly execution observed.

## Current state

Source implementation is in progress on coordinated `.github` and `StegVerse-Healer` branches. No live hourly runtime receipt is claimed by this handoff.
