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
Canonical Task Registry merge: PR `#1255` / merge `2eb089842ea8960845dcd021f5241126432f3b74`
State: `SOURCE_INTEGRATION_MERGED / HOURLY_REUSABLE_BINDING_MERGED / CANONICAL_TASK_REGISTERED / RESIDENT_RECURRING_CARRIER_REPAIR_IN_VALIDATION / AUTHENTIC_SCHEDULED_RUNTIME_RECEIPT_PENDING`

## Scoped objective

Make the existing native email action monitor directly reusable and recurring hourly through the existing sovereign Healer scheduler without creating another mailbox monitor, heartbeat, polling loop, WorkerCoordinator, scheduler, or credential route.

## Implemented hourly path

PR #1252 made `RT-NATIVE-EMAIL-ACTION-MONITOR-001` executable through the canonical reusable-task trigger. Healer PR #57 added an hourly schedule entry for all UTC hours with deterministic UTC-hour invocation IDs and retained receipts, enforcing at-most-once execution per hour slot. PR #1255 registered the exact goal in the canonical sharded Task Registry.

## Resident recurring-carrier defect and repair

Post-merge runtime investigation found a deeper carrier defect in `scripts/consume_healer_sovereign_scheduler_request.py`: `RESIDENT-EXEC-HEALER-SOVEREIGN-SCHEDULER-001` was treated as a one-shot terminal request. Once any scheduler pass emitted `HEALER_SOVEREIGN_SCHEDULER_COMPLETED`, later resident visits returned `ALREADY_CONSUMED`. That lifecycle is incompatible with an hourly scheduler even though the hourly target configuration itself was correct.

Branch `fix/healer-recurring-resident-scheduler-20260909` repairs the carrier by:

- marking `control/resident-execution-request.d/healer-sovereign-scheduler-001.json` as `standing_request=true` with recurrence `EACH_ELIGIBLE_RESIDENT_SCHEDULER_CYCLE`;
- treating `HEALER_SOVEREIGN_SCHEDULER_COMPLETED` as one completed scheduler cycle rather than retirement of the standing request;
- keeping `retry_allowed=true` and `request_consumed=false` after a completed cycle;
- replacing the prior exactly-once terminal test with a deterministic test proving two eligible resident visits execute two scheduler cycles.

The hourly reusable-task layer still provides the narrower per-hour idempotency boundary, so repeated resident scheduler cycles during the same UTC hour do not duplicate the native-email invocation.

## Cadence

```text
resident_scheduler_request: STANDING_RECURRING
resident_cycle_recurrence: EACH_ELIGIBLE_RESIDENT_SCHEDULER_CYCLE
native_email_cadence: HOURLY
eligible_utc_hours: 00..23
at_most_once_per_hour_slot: true
slot_identity: RT-NATIVE-EMAIL-ACTION-MONITOR-001 + UTC YYYYMMDDTHH
mailbox_batch_limit: existing native monitor limit (100)
```

## Validation evidence already merged

- PR #1252 exact head: Heartbeat `34332023132`, org-control `34332023277`, deterministic suite `34332023168` SUCCESS.
- Healer PR #57 exact head: Test Readiness `34332190725` SUCCESS.
- PR #1255 exact head: Heartbeat `34332579197`, org-control `34332579252`, deterministic suite `34332579274` SUCCESS.

## README determination

No additional `.github/README.md` change is required: the root README already documents resident request/reusable-task architecture. StegVerse-Healer README already documents reusable-task scheduling responsibility from PR #57. This repair changes lifecycle semantics of the existing scheduler request, documented here and in deterministic tests.

## Remaining authentic boundary

After the recurring-carrier repair validates and merges, source-side recurring execution semantics are complete. Authentic operation still requires the resident runtime to materialize the updated standing request/consumer and produce a real scheduler-cycle receipt. The first hourly mailbox-processing claim additionally requires the corresponding reusable-task and TV/TVC Gmail/provider monitor receipts.
