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
Recurring carrier merge: PR `#1259` / merge `569b6dde49cc9f568c0a24daf9fc723eee807b6f`
Resident runtime-root merge: `StegVerse-Labs/StegVerse-Healer#58` / merge `a0f6daeaf33198f26e358c7b124fc9f80aad8b6b`
State: `SOURCE_INTEGRATION_MERGED / HOURLY_REUSABLE_BINDING_MERGED / CANONICAL_TASK_REGISTERED / STANDING_RECURRING_CARRIER_MERGED / SOURCE_RUNTIME_SEPARATION_MERGED / WORKERCOORDINATOR_CYCLE_REARM_AND_DISPATCH_SOURCE_SEPARATION_IN_VALIDATION / AUTHENTIC_SCHEDULED_RUNTIME_RECEIPT_PENDING`

## Scoped objective

Make the existing native email action monitor directly reusable and recurring hourly through the existing sovereign Healer scheduler without creating another mailbox monitor, heartbeat, polling loop, WorkerCoordinator, scheduler, or credential route.

## Implemented hourly path

PR #1252 made `RT-NATIVE-EMAIL-ACTION-MONITOR-001` executable through the canonical reusable-task trigger. Healer PR #57 added an hourly schedule entry for all UTC hours with deterministic UTC-hour invocation IDs and retained receipts, enforcing at-most-once execution per hour slot. PR #1255 registered the exact goal in the canonical sharded Task Registry.

## Standing recurring carrier

PR #1259 repaired `RESIDENT-EXEC-HEALER-SOVEREIGN-SCHEDULER-001` from one-shot terminal consumption to a standing recurring scheduler request:

- `standing_request=true`;
- recurrence `EACH_ELIGIBLE_RESIDENT_SCHEDULER_CYCLE`;
- a successful `HEALER_SOVEREIGN_SCHEDULER_COMPLETED` result records one `CYCLE_COMPLETED` pass instead of retiring the request;
- `retry_allowed=true` and `request_consumed=false` remain true after each completed cycle.

The reusable-task layer retains the narrower per-UTC-hour idempotency boundary, so multiple resident scheduler cycles within one hour do not duplicate the email invocation.

## Source/runtime separation

Healer PR #58 repaired the scheduled invocation topology. The first hourly source implementation passed the local `.github` source checkout as both `source_root` and `runtime_root`, which could place reusable-task receipts under source and collapse source with execution state.

The merged repair now:

- treats the already-materialized local `.github` checkout only as `source_root`;
- resolves an actual resident heartbeat runtime from explicit `STEGVERSE_HEARTBEAT_ROOT` or exactly one canonical local heartbeat-runtime location;
- requires the materialized native-email standing request to validate that runtime candidate;
- passes the resident heartbeat tree only as `runtime_root`;
- stores `receipts/reusable-task/<UTC-hour-slot>.latest.json` under the resident runtime;
- fails closed with `RESIDENT_RUNTIME_ROOT_NOT_MATERIALIZED` rather than using source as runtime;
- preserves same-slot idempotency against the resident receipt.

## WorkerCoordinator cycle rearm

A post-merge lifecycle review found that the standing resident request alone was insufficient. WorkerCoordinator accepts a `COMPLETED` worker response as terminal task completion, releases the worker, and leaves the scheduler task in `COMPLETED`. Independent task control can acquire only a `HANDOFF_READY` unclaimed task, so the scheduler would still stop after its first successful WorkerCoordinator cycle.

The current repair keeps the completed-cycle evidence unchanged while changing only the WorkerCoordinator-facing lifecycle response:

```text
Healer child scheduler result: COMPLETE
-> durable scheduler worker receipt: state=COMPLETED / transition=HEALER_SOVEREIGN_SCHEDULER_COMPLETED
-> WorkerCoordinator-facing response: state=HANDOFF_READY / same completed-cycle transition
-> current claim + worker binding released by existing WorkerCoordinator HANDOFF_READY semantics
-> scheduler task remains eligible for a fresh independently admitted claim/fence on a later resident cycle
```

Blocked and failure responses are not rewritten. The task therefore receives a fresh fencing generation for each new scheduler cycle instead of retaining or reviving the prior claim.

## Automatic resident-dispatch source separation

The continuous WorkerCoordinator resident dispatcher invokes the generic request dispatcher from the resident tree and historically supplied that runtime root as both dispatcher `source_root` and `runtime_root`. The Healer request consumer delegates to `refresh_and_execute_resident_task.py`, whose refresh contract correctly requires source and runtime to remain distinct.

The sovereign service/bootstrap already provides the non-secret local canonical checkout as `STEGVERSE_HEARTBEAT_SOURCE_ROOT`. The current consumer repair therefore resolves source as follows:

1. If the dispatcher already supplies a distinct existing source root, use it.
2. If dispatcher source equals runtime, resolve `STEGVERSE_HEARTBEAT_SOURCE_ROOT`.
3. Require that candidate to be a distinct existing local directory containing `scripts/refresh_and_execute_resident_task.py`.
4. If no valid distinct source exists, record `DISTINCT_LOCAL_CANONICAL_SOURCE_REQUIRED`, keep the standing request retryable, and perform no runtime execution or network source fetch.

This repairs autonomous continuous-dispatch compatibility without changing the generic dispatcher contract for unrelated resident consumers.

## Cadence

```text
resident_scheduler_request: STANDING_RECURRING
resident_cycle_recurrence: EACH_ELIGIBLE_RESIDENT_SCHEDULER_CYCLE
workercoordinator_post_success_state: HANDOFF_READY
fresh_claim_and_fence_each_scheduler_cycle: true
dispatch_source_when_runtime_is_presented_as_source: STEGVERSE_HEARTBEAT_SOURCE_ROOT
source_runtime_separation_required: true
native_email_cadence: HOURLY
eligible_utc_hours: 00..23
at_most_once_per_hour_slot: true
slot_identity: RT-NATIVE-EMAIL-ACTION-MONITOR-001 + UTC YYYYMMDDTHH
receipt_location: resident heartbeat runtime / receipts/reusable-task/
mailbox_batch_limit: existing native monitor limit (100)
```

## Validation evidence

- PR #1252 exact head: Heartbeat `34332023132`, org-control `34332023277`, deterministic suite `34332023168` SUCCESS.
- Healer PR #57 exact head: Test Readiness `34332190725` SUCCESS.
- PR #1255 exact head: Heartbeat `34332579197`, org-control `34332579252`, deterministic suite `34332579274` SUCCESS.
- PR #1259 exact head `1b5bcd87b752ae643f88cbf1dc788f4a1c2dec45`: Heartbeat `34352789541`, org-control `34352789580`, deterministic suite `34352789603` SUCCESS.
- Healer PR #58 exact head `8fae4401381d7479373add148d21de6c514d2e7b`: Test Readiness `34356342498` SUCCESS.
- WorkerCoordinator cycle-rearm and automatic-dispatch source-separation validation are pending on PR #1273.

## README determination

The `.github` root README already documents resident requests, WorkerCoordinator lifecycle, source/runtime separation, and reusable-task architecture; no additional root README change is required for these task-specific lifecycle/consumer repairs. `StegVerse-Healer/README.md` was updated in PR #58 to document resident runtime separation and receipt placement.

## Remaining authentic boundary

After PR #1273 validates and merges, source-side reusable invocation, hourly scheduling, standing request recurrence, fresh scheduler claim/fence recurrence, automatic dispatcher source/runtime separation, canonical task registration, resident receipt placement, fail-closed runtime discovery, validation, and repository documentation are complete.

The remaining boundary is authentic resident execution: the already-local canonical source must be refreshed/materialized into the resident heartbeat runtime and the standing Healer scheduler must traverse one eligible cycle. Completion evidence for the timer requires a real resident `receipts/reusable-task/rt-native-email-action-monitor-001-<UTC-hour>Z.latest.json`. A mailbox-processing claim additionally requires the corresponding native-email monitor receipt and TV/TVC Gmail provider-operation evidence. No user-operated second machine is required.
