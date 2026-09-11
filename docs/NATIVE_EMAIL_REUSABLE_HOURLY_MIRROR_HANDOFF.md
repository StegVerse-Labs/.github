# Native Email Reusable Hourly Mirror Handoff

Updated: 2026-09-10
Repository: `StegVerse-Labs/.github`
Task: `STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001`
COSV task vector: `10100000100000`
Reusable identity: `RT-NATIVE-EMAIL-ACTION-MONITOR-001`
Parent handoff: `docs/NATIVE_EMAIL_ACTION_MONITOR_MIRROR_HANDOFF.md`
Scheduler owner: `StegVerse-Labs/StegVerse-Healer` / `SHWP-HEALER-SOVEREIGN-SCHEDULER-001`
State: `SOURCE_INTEGRATION_MERGED / HOURLY_REUSABLE_BINDING_MERGED / KV_BEFORE_ARCHIVE_MERGED / RESIDENT_REFRESH_PROPAGATION_IN_VALIDATION / AUTHENTIC_SCHEDULED_GMAIL_KV_RECEIPT_PENDING`

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

## Merged source chain

- `.github` #1252 / `700f959dca0160f0d71d92fc391c9f262f27feea`: reusable trigger execution.
- `StegVerse-Healer` #57 / `ef5d90a8c215056e055385a04534e16c49d9a3d5`: hourly deterministic UTC-slot scheduling.
- `.github` #1255 / `2eb089842ea8960845dcd021f5241126432f3b74`: canonical task registration.
- `.github` #1259 / `569b6dde49cc9f568c0a24daf9fc723eee807b6f`: standing recurring resident scheduler request.
- `StegVerse-Healer` #58 / `a0f6daeaf33198f26e358c7b124fc9f80aad8b6b`: source/runtime separation and resident receipt placement.
- `.github` #1273 / `438aeb9a4b187419ea3a91984ed0436c89b26819`: fresh WorkerCoordinator claim/fence recurrence and automatic dispatcher source/runtime separation.
- `StegVerse-Healer` #59 / `93b637ddcc48777900e3804f994b22036d507571`: non-secret KV-root forwarding through the existing scheduler path; Test Readiness `34363810591` SUCCESS.
- `.github` #1342 / `1d4093e6266154a0552d942f3fc1b5fdafb71b70`: current-main KV-before-archive implementation. Exact head `78d628a342be58a863db3978de5969ff892d8894` passed Heartbeat `34544669388`, organization-control `34544669233`, and Deterministic Repository Suite `34544669416`.

## KV-before-archive contract

The merged current-main implementation adds:

- `scripts/persist_native_email_incidents_to_kv.py`: deterministic append-only failure-observation records under `05_Projects/StegVerse/Operations/GitHubFailureEmail/`, with write-once behavior, fsync, and exact-byte readback;
- `scripts/run_native_email_action_monitor_kv_guard.py`: prevents live `ARCHIVE_IDS` from reaching the provider until normalized live failure incidents have been persisted and verified;
- `scripts/consume_native_email_action_monitor_request_kv.py`: thin wrapper around the evolved current-main consumer, preserving existing resident logic while enforcing KV availability and guarded monitor execution;
- focused regression tests for idempotent exact-byte storage, KV-before-archive ordering, fail-closed missing KV, materialization-receipt discovery, stale monitor-receipt rejection, and both canonical entry routes.

Both the standing resident request and reusable hourly trigger route through the KV wrapper. Neither canonical entry route may bypass persistence.

## KnowledgeVault resolution

The wrapper mounts no provider and acquires no credential. It accepts only an already-materialized local KnowledgeVault root, resolved from either:

1. existing non-secret `STEGVERSE_KV_ROOT` / `STEGVERSE_KV_PROVIDER_MATERIALIZED_ROOT`; or
2. resident `control/kv-provider-materialization/latest.json` carrying schema `stegverse.kv.provider-materialization-receipt/v2`, `exact_readback_verified=true`, TV/TVC credential authority, no persisted/consumer-visible provider credential, and a currently materialized `materialized_root`.

The resident receipt route avoids widening the shared WorkerCoordinator process-adapter environment allowlist. Missing or invalid KV state remains retryable and forbids live archive.

## Resident source-refresh propagation repair

Post-merge inspection of `scripts/refresh_sovereign_worker_runtime_source.py` found that the existing resident refresh copied the historical native-email consumer and base monitor but did not copy the three KV enforcement scripts introduced by #1342. Because `control/resident-execution-request.d/native-email-action-monitor-001.json` now names `scripts/consume_native_email_action_monitor_request_kv.py`, a refreshed resident could receive the new request while missing its executable entrypoint.

The current repair adds all three required scripts to the existing `STATIC_FILES` refresh set:

```text
scripts/consume_native_email_action_monitor_request_kv.py
scripts/run_native_email_action_monitor_kv_guard.py
scripts/persist_native_email_incidents_to_kv.py
```

`tests/test_native_email_kv_resident_refresh.py` asserts that all three remain part of the static resident source set and are not classified as mutable runtime state. This uses the existing local source-refresh mechanism; no network source transport, second scheduler, or alternate dispatcher is added.

## Stale implementation retired from coordination

PR #1280 used the earlier `fix/native-email-kv-persistence-20260909` branch and was found 273 commits behind current main. Its functional intent was ported onto current main in #1342 without overwriting evolved runtime/control-plane logic. PR #1280 is CLOSED UNMERGED and must not be progressed or used as the canonical implementation source.

## Remaining authentic predicates

After the resident refresh propagation repair validates and merges, source integration required for both hourly source execution and direct resident request dispatch is complete. Runtime completion still requires authentic resident evidence of:

- an eligible hourly reusable-task invocation;
- KnowledgeVault resolution from already-materialized resident/local state;
- `KV_STORED_VERIFIED` for every observed failure incident before live archive;
- corresponding TV/TVC Gmail provider operations;
- bounded mailbox progression;
- durable StegHealth/Canonical Work reconciliation for actionable incidents.

Repository search after #1342 merge did not identify an authentic retained `receipts/reusable-task/rt-native-email-action-monitor-001-<UTC-hour>Z.latest.json`; documentation references are not runtime evidence. The task therefore remains nonterminal pending resident execution evidence.

## README determination

`NO_README_CHANGE_REQUIRED` for `.github`: the root README already defines local resident source refresh, reusable-task constructs, Canonical Work ingress, resident execution semantics, Personal KnowledgeVault custody distinctions, and the functional-change invariant. This repair only restores dependency parity for an already-documented resident task path.
