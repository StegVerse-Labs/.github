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
WorkerCoordinator rearm/source-separation merge: PR `#1273` / merge `438aeb9a4b187419ea3a91984ed0436c89b26819`
State: `SOURCE_INTEGRATION_MERGED / HOURLY_REUSABLE_BINDING_MERGED / CANONICAL_TASK_REGISTERED / STANDING_RECURRENCE_MERGED / SOURCE_RUNTIME_SEPARATION_MERGED / WORKERCOORDINATOR_REARM_MERGED / KV_FAILURE_PERSISTENCE_IN_VALIDATION / AUTHENTIC_SCHEDULED_KV_RECEIPT_PENDING`

## Scoped objective

Make the existing native email action monitor directly reusable and recurring hourly through the existing sovereign Healer scheduler, and persist normalized GitHub failure observations into the already-materialized KnowledgeVault before live failure mail is archived, without creating another mailbox monitor, heartbeat, polling loop, WorkerCoordinator, scheduler, credential route, or KV provider-mount path.

## Implemented hourly path

PR #1252 made `RT-NATIVE-EMAIL-ACTION-MONITOR-001` executable through the canonical reusable-task trigger. Healer PR #57 added an hourly schedule entry for all UTC hours with deterministic UTC-hour invocation IDs and retained receipts, enforcing at-most-once execution per hour slot. PR #1255 registered the exact goal in the canonical sharded Task Registry.

## Standing recurring carrier

PR #1259 repaired `RESIDENT-EXEC-HEALER-SOVEREIGN-SCHEDULER-001` from one-shot terminal consumption to a standing recurring scheduler request:

- `standing_request=true`;
- recurrence `EACH_ELIGIBLE_RESIDENT_SCHEDULER_CYCLE`;
- a successful `HEALER_SOVEREIGN_SCHEDULER_COMPLETED` result records one completed pass instead of retiring the request;
- `retry_allowed=true` and `request_consumed=false` remain true after each completed cycle.

The reusable-task layer retains the narrower per-UTC-hour idempotency boundary, so multiple resident scheduler cycles within one hour do not duplicate the email invocation.

## Source/runtime separation

Healer PR #58 repaired the scheduled invocation topology. The merged path treats the already-materialized local `.github` checkout only as `source_root`, resolves the actual resident heartbeat runtime separately, stores reusable-task receipts under resident runtime, and fails closed if no resident runtime is materialized.

PR #1273 additionally repaired automatic resident dispatch when the runtime tree is initially presented as both dispatcher source and runtime. The Healer request consumer resolves the existing `STEGVERSE_HEARTBEAT_SOURCE_ROOT`, requires it to be a distinct already-local canonical source tree, and performs no network source fetch.

## WorkerCoordinator cycle rearm

PR #1273 also repaired the scheduler task lifecycle. A successful scheduler pass preserves its durable completed-cycle receipt and transition, but the WorkerCoordinator-facing response is `HANDOFF_READY`. Existing WorkerCoordinator semantics therefore release the current claim/worker binding and permit a fresh fenced acquisition on a later scheduler cycle. Blocked and failed responses are unchanged.

## KnowledgeVault failure-observation persistence

The native email monitor previously normalized GitHub failure incidents but archived the exact Gmail message IDs before any KV persistence step existed. That meant a successful provider archive could discard inbox visibility even if later durable KV storage failed.

The current repair adds a narrow storage-evidence leg to the existing task rather than creating a second monitor or ingestion path:

- `scripts/persist_native_email_incidents_to_kv.py` writes normalized failure observations only;
- `scripts/run_native_email_action_monitor_kv_guard.py` wraps the existing monitor broker and gates `ARCHIVE_IDS` on successful KV persistence/readback;
- `scripts/consume_native_email_action_monitor_request.py` requires an already-materialized KnowledgeVault from `STEGVERSE_KV_ROOT` or `STEGVERSE_KV_PROVIDER_MATERIALIZED_ROOT` and remains retryable when neither resolves;
- `StegVerse-Healer` forwards those two non-secret path bindings through the existing scheduler/reusable-task hop;
- archived replay incidents are backfilled into the same KV record class before downstream failure reconciliation proceeds.

The canonical KV location for this task is:

```text
05_Projects/StegVerse/Operations/GitHubFailureEmail/
```

Each record contains bounded normalized operational evidence: task/COSV binding, incident ID, normalized repository/workflow/error signature, Gmail message-ID evidence references, and storage/evidence semantics. Full email bodies, credentials, provider tokens, and unrelated personal mailbox contents are not written.

The record writer is append-only and deterministic. It uses canonical JSON bytes, exclusive creation, fsync, exact-byte readback verification, and a filename derived from incident identity plus the exact observation-reference set. Repeated identical replay is a verified no-op; a conflicting write fails closed.

### Required ordering

For a live failure batch the enforced ordering is:

```text
SEARCH_MESSAGES
-> normalize GitHub failure incidents
-> exact-byte KnowledgeVault write
-> exact-byte KnowledgeVault readback verification
-> ARCHIVE_IDS for the exact bounded Gmail IDs
-> actionable recheck / inbox accounting
-> StegHealth failure reconciliation
-> Canonical Work / InTr continuation when applicable
```

If KV persistence fails or no already-materialized KV root resolves, `ARCHIVE_IDS` is not called for the failure batch. The standing task remains retryable.

KV is storage/evidence in this path. The writer does not mount providers, resolve credentials, create task identity, admit execution, mint a claim/fence, or perform a governed state transition.

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
kv_failure_record_root: 05_Projects/StegVerse/Operations/GitHubFailureEmail/
kv_exact_byte_readback_required: true
archive_after_required_kv_persistence_only: true
mailbox_batch_limit: existing native monitor limit (100)
```

## Validation evidence already merged

- PR #1252 exact head: Heartbeat `34332023132`, org-control `34332023277`, deterministic suite `34332023168` SUCCESS.
- Healer PR #57 exact head: Test Readiness `34332190725` SUCCESS.
- PR #1255 exact head: Heartbeat `34332579197`, org-control `34332579252`, deterministic suite `34332579274` SUCCESS.
- PR #1259 exact head `1b5bcd87b752ae643f88cbf1dc788f4a1c2dec45`: Heartbeat `34352789541`, org-control `34352789580`, deterministic suite `34352789603` SUCCESS.
- Healer PR #58 exact head `8fae4401381d7479373add148d21de6c514d2e7b`: Test Readiness `34356342498` SUCCESS.
- PR #1273 exact head: organization-control `34358206486`, Heartbeat `34358206495`, deterministic suite `34358206492` SUCCESS.
- KV persistence and Healer KV-path-forwarding validation are pending on the current coordinated branches.

## README determination

This KV persistence change materially changes runtime behavior and failure handling, so repository README maintenance is required in the current change set. The README must state that normalized GitHub failure observations are persisted to an already-materialized KnowledgeVault with exact-byte verification before live failure mail may be archived, and that missing KV persistence blocks archive rather than falling back. `StegVerse-Healer/README.md` is being updated in its coordinated branch to document non-secret KV path forwarding.

## Remaining authentic boundary

After the KV persistence and Healer path-forwarding changes validate and merge, source-side reusable invocation, hourly scheduling, standing recurrence, fresh scheduler claims/fences, automatic dispatcher source/runtime separation, KV-before-archive ordering, exact-byte KV persistence/readback, failure reconciliation ordering, and repository documentation will be source-complete.

Authentic operation still requires a resident scheduler traversal producing a retained reusable-task receipt plus a native-email monitor receipt whose `kv_persistence.write_receipts` prove real KnowledgeVault writes/readbacks for observed failures, together with corresponding TV/TVC Gmail provider-operation evidence. Source validation alone is not runtime proof. No user-operated second machine is required.
