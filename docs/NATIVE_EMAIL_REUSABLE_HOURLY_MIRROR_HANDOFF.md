# Native Email Reusable Hourly Mirror Handoff

Updated: 2026-09-10
Repository: `StegVerse-Labs/.github`
Task: `STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001`
COSV task vector: `10100000100000`
Reusable identity: `RT-NATIVE-EMAIL-ACTION-MONITOR-001`
Parent handoff: `docs/NATIVE_EMAIL_ACTION_MONITOR_MIRROR_HANDOFF.md`
Scheduler owner: `StegVerse-Labs/StegVerse-Healer` / `SHWP-HEALER-SOVEREIGN-SCHEDULER-001`
Current implementation branch: `fix/native-email-kv-persistence-current-main-20260910`
State: `HOURLY_REUSABLE_RUNTIME_SOURCE_MERGED / KV_ROOT_FORWARDING_MERGED / CURRENT_MAIN_KV_BEFORE_ARCHIVE_SOURCE_IN_VALIDATION / AUTHENTIC_SCHEDULED_GMAIL_KV_RECEIPT_PENDING`

## Objective

Use the existing sovereign Healer scheduler and existing TV/TVC Gmail provider path to process the bounded GitHub/[Task Update] operational mailbox slice hourly. Normalized failure observations must be durably stored in the already-materialized Personal KnowledgeVault with exact-byte readback before the corresponding live Gmail IDs may be archived. No second monitor, scheduler, heartbeat, polling loop, WorkerCoordinator, provider mount, credential route, or second user-operated machine is introduced.

## Canonical execution path

```text
resident WorkerCoordinator cycle
-> standing SHWP-HEALER-SOVEREIGN-SCHEDULER-001 request
-> fresh claim/fence
-> existing Healer scheduler
-> hourly RT-NATIVE-EMAIL-ACTION-MONITOR-001 slot
-> scripts/trigger_reusable_task.py
-> scripts/consume_native_email_action_monitor_request_kv.py
-> resolve already-materialized KnowledgeVault root
-> scripts/run_native_email_action_monitor_kv_guard.py
-> TV/TVC-backed Gmail broker SEARCH_MESSAGES / SEARCH_IDS
-> normalize failure incidents
-> scripts/persist_native_email_incidents_to_kv.py
-> exact-byte KnowledgeVault write + fsync + readback
-> only then ARCHIVE_IDS for the exact reviewed live IDs
-> StegHealth failure reconciliation
-> Canonical Work / Interlock/InTr continuation when applicable
-> completed scheduler-cycle receipt
-> WorkerCoordinator HANDOFF_READY rearm for a fresh later cycle
```

## Hourly and recurring source already merged

- `.github` PR #1252 / `700f959dca0160f0d71d92fc391c9f262f27feea` made `RT-NATIVE-EMAIL-ACTION-MONITOR-001` executable through the canonical reusable-task trigger.
- `StegVerse-Healer` PR #57 / `ef5d90a8c215056e055385a04534e16c49d9a3d5` installed the hourly schedule with deterministic UTC-hour slot IDs and at-most-once-per-slot receipts.
- `.github` PR #1255 / `2eb089842ea8960845dcd021f5241126432f3b74` registered the canonical task.
- `.github` PR #1259 / `569b6dde49cc9f568c0a24daf9fc723eee807b6f` changed the Healer resident request from one-shot terminal consumption to a standing recurring request.
- `StegVerse-Healer` PR #58 / `a0f6daeaf33198f26e358c7b124fc9f80aad8b6b` separated local source from resident runtime and moved reusable-task slot receipts into the resident runtime.
- `.github` PR #1273 / `438aeb9a4b187419ea3a91984ed0436c89b26819` preserved completed-cycle evidence while returning `HANDOFF_READY` to WorkerCoordinator so each later scheduler cycle receives a fresh claim/fence; it also repaired automatic resident-dispatch source/runtime separation.
- `StegVerse-Healer` PR #59 / `93b637ddcc48777900e3804f994b22036d507571` forwards already-present non-secret KV path bindings through the existing reusable-task scheduler. Exact-head Test Readiness run `34363810591` passed.

## Current-main KV-before-archive repair

The original KV implementation branch behind PR #1280 diverged from current `.github/main` by 273 commits. It is not safe to merge directly. The functional deltas are being ported onto current main `77d0ae25b8abd4fac0ff4df04398c6cd6a59f7ce` on `fix/native-email-kv-persistence-current-main-20260910`.

The current-main port adds:

- `scripts/persist_native_email_incidents_to_kv.py` — deterministic append-only incident records under `05_Projects/StegVerse/Operations/GitHubFailureEmail/`, `O_EXCL` write-once semantics, fsync, and exact-byte readback;
- `scripts/run_native_email_action_monitor_kv_guard.py` — intercepts only the canonical monitor broker flow and refuses to forward `ARCHIVE_IDS` until normalized live failure incidents are persisted and read back;
- `scripts/consume_native_email_action_monitor_request_kv.py` — thin canonical wrapper around the existing consumer, preserving current-main consumer logic while requiring KnowledgeVault availability and substituting the KV guard only for the monitor subprocess;
- `tests/test_native_email_kv_persistence.py` and `tests/test_native_email_kv_entrypoint.py` — regression coverage for append-only/idempotent exact-byte persistence, persist-before-archive ordering, missing-KV fail-closed behavior, runtime materialization-receipt discovery, standing-request routing, and reusable-trigger routing.

The standing resident request now names `scripts/consume_native_email_action_monitor_request_kv.py`. The reusable-task trigger retains the registered historical primary runner reference but records and invokes the KV wrapper as the effective runner for this reusable identity, preventing either canonical entry route from bypassing persistence.

## KnowledgeVault resolution

The KV wrapper never mounts a provider and never acquires credentials. It accepts only an already-materialized local KnowledgeVault root. Resolution order is:

1. existing non-secret `STEGVERSE_KV_ROOT` or `STEGVERSE_KV_PROVIDER_MATERIALIZED_ROOT` when present and recognizable as a KnowledgeVault;
2. otherwise, resident `control/kv-provider-materialization/latest.json` with schema `stegverse.kv.provider-materialization-receipt/v2`, `exact_readback_verified=true`, TV/TVC credential authority, no persisted/consumer-visible provider credential, and a currently materialized `materialized_root`.

The second route is important because WorkerCoordinator process adapters intentionally sanitize child environments. The local materialization receipt is already resident state and contains the non-secret `materialized_root`; using it avoids broadening the shared process-adapter environment allowlist.

Missing, stale, invalid, or non-materialized KV state yields a retryable `KV_ROOT_NOT_MATERIALIZED` attempt with `archive_permitted=false`. The monitor/provider archive call is not attempted.

## Persistence contract

Each normalized incident record contains the canonical task/COSV identity, normalized repository/workflow/error signature, exact Gmail observation refs, provider/source class, and explicit non-authorizing evidence semantics. Its filename is deterministic from the incident ID plus observation-ref digest. Replaying the identical incident set is a no-op only when the exact stored bytes match; any collision with different bytes fails closed.

For live mailbox batches the enforced ordering is:

```text
SEARCH_MESSAGES
-> SEARCH_IDS exact bounded IDs
-> normalize / cluster incidents
-> append-only KV write
-> fsync
-> exact-byte readback
-> KV_STORED_VERIFIED receipt
-> ARCHIVE_IDS exact reviewed IDs
-> actionable failure search / inbox counts
-> StegHealth reconciliation
```

Archived historical replay is not restored or re-archived. Its normalized incidents are persisted into the same KV evidence class before subsequent StegHealth acknowledgement/progression.

## Validation evidence already retained

- #1252: Heartbeat `34332023132`, org-control `34332023277`, deterministic suite `34332023168` SUCCESS.
- Healer #57: Test Readiness `34332190725` SUCCESS.
- #1255: Heartbeat `34332579197`, org-control `34332579252`, deterministic suite `34332579274` SUCCESS.
- #1259 exact head: Heartbeat `34352789541`, org-control `34352789580`, deterministic suite `34352789603` SUCCESS.
- Healer #58 exact head: Test Readiness `34356342498` SUCCESS.
- #1273: org-control `34358206486`, Heartbeat `34358206495`, deterministic suite `34358206492` SUCCESS.
- Healer #59 exact head: Test Readiness `34363810591` SUCCESS; merge `93b637ddcc48777900e3804f994b22036d507571`.

The stale PR #1280 validation failures are not evidence against the current-main port because its head is 273 commits behind current main and includes stale shared-control files. The new branch must receive its own exact-head validation before merge.

## Remaining completion predicates

Source completion for the current-main KV port requires all retained `.github` validation suites to pass and the branch to merge without reverting unrelated current-main runtime evolution. Runtime completion additionally requires authentic evidence of:

- an eligible resident hourly reusable-task invocation;
- KnowledgeVault resolution from already-materialized local state;
- `KV_STORED_VERIFIED` for each observed failure incident before live archive;
- the corresponding TV/TVC Gmail provider operations;
- bounded mailbox progression;
- durable StegHealth/Canonical Work reconciliation for actionable incidents.

Source validation or merge does not substitute for those authentic runtime receipts.

## README determination

The root README already defines reusable-task constructs, Canonical Work ingress, resident execution semantics, Personal KnowledgeVault custody distinctions, and the functional-change invariant. This scoped change does not create a new repository responsibility or public interface; it hardens one existing resident task's ordering and evidence requirements. The task-specific behavioral contract is maintained here and in the canonical task record. If repository validation identifies a required root README delta, it must be added before merge.
