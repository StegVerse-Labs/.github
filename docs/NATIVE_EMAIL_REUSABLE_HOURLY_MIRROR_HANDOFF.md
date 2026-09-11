# Native Email Reusable Hourly Mirror Handoff

Updated: 2026-09-10
Repository: `StegVerse-Labs/.github`
Task: `STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001`
COSV task vector: `10100000100000`
Reusable identity: `RT-NATIVE-EMAIL-ACTION-MONITOR-001`
Parent handoff: `docs/NATIVE_EMAIL_ACTION_MONITOR_MIRROR_HANDOFF.md`
Scheduler owner: `StegVerse-Labs/StegVerse-Healer` / `SHWP-HEALER-SOVEREIGN-SCHEDULER-001`
State: `SOURCE_INTEGRATION_MERGED / HOURLY_REUSABLE_BINDING_MERGED / KV_BEFORE_ARCHIVE_MERGED / RESIDENT_REFRESH_PROPAGATION_MERGED / RETRY_SEMANTICS_AND_BOUNDED_BACKOFF_MERGED / ARCHIVE_GOVERNANCE_CONTEXT_IN_VALIDATION / AUTHENTIC_SCHEDULED_GMAIL_KV_GOVERNANCE_RECEIPT_PENDING`

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
-> TV/TVC-backed Gmail SEARCH_MESSAGES / SEARCH_IDS
-> normalize failure incidents
-> scripts/persist_native_email_incidents_to_kv.py
-> append-only write + fsync + exact-byte readback
-> bind exact reviewed message IDs + verified KV receipts into archive governance context
-> StegOps generic stegverse.ingress-manifest.v1 governance route
-> canonical StegCore StegGate + commit coherence
-> only on ALLOW: TVC ARCHIVE_IDS bounded consequence
-> Gmail provider result + route/transaction/Master Records evidence
-> StegHealth failure reconciliation
-> Canonical Work / Interlock/InTr continuation when applicable
-> completed scheduler-cycle receipt
-> WorkerCoordinator HANDOFF_READY rearm
```

## Merged implementation and validation

- `.github` #1252 / `700f959dca0160f0d71d92fc391c9f262f27feea`: reusable invocation.
- Healer #57 / `ef5d90a8c215056e055385a04534e16c49d9a3d5`: hourly deterministic UTC-slot schedule.
- `.github` #1255 / `2eb089842ea8960845dcd021f5241126432f3b74`: canonical task registration.
- `.github` #1259 / `569b6dde49cc9f568c0a24daf9fc723eee807b6f`: standing recurring scheduler request.
- Healer #58 / `a0f6daeaf33198f26e358c7b124fc9f80aad8b6b`: source/runtime separation and resident slot-receipt placement.
- `.github` #1273 / `438aeb9a4b187419ea3a91984ed0436c89b26819`: fresh WorkerCoordinator claim/fence rearm and automatic-dispatch source separation.
- Healer #59 / `93b637ddcc48777900e3804f994b22036d507571`: non-secret KV-root forwarding; Test Readiness `34363810591` SUCCESS.
- `.github` #1342 / `1d4093e6266154a0552d942f3fc1b5fdafb71b70`: KV-before-archive implementation; exact head `78d628a342be58a863db3978de5969ff892d8894`, Heartbeat `34544669388`, org-control `34544669233`, deterministic suite `34544669416` SUCCESS.
- `.github` #1356 / `2c8978eb89c0f99f2c221fc523710d2347a7cea1`: resident refresh now carries KV wrapper, guard, and writer; exact head `229c217904770b3ab44a6aa346984cbc147692f8`, Workspace DEVICE_KV `34551259728`, org-control `34551259752`, Heartbeat `34551259798`, deterministic suite `34551259733` SUCCESS.
- Healer #60 / `cd74e971ee54344c2f772fe2fd35827174914e66`: failed/boundary reusable receipts no longer satisfy an hourly slot; exact head `d64c83454f0e86fa732ac3d1ab8ae748cc682c11`, Test Readiness `34551667188` SUCCESS.
- `.github` #1357 / `05c1250c91b6b09d54def657c37de5c77bd89c15`: pre-execution/KV-proof pending states return nonzero to the reusable trigger; exact head `3bc48019106386dc066d0dc1cd7148530d20e762`, org-control `34551629855`, deterministic suite `34551629876`, Heartbeat `34551629899` SUCCESS.
- Healer #61 / `9c1661476ff1eadbe8c6ba300519a0c3f925d2e9`: failed-slot recovery is bounded to no sooner than every 15 minutes and at most four failed attempts per UTC-hour slot; exact head `6c17cec579c19e67053578030cf7efd2e1c9edaf`, Test Readiness `34551986643` SUCCESS.

The stale `.github` #1280 branch remains CLOSED UNMERGED and is superseded by #1342.

## Hourly and retry semantics

A slot is satisfied only by a retained reusable-task trigger receipt whose state is `AUTOMATABLE_STEPS_EXHAUSTED`. A failed or `BOUNDARY_RECORDED` attempt is not promoted to successful hourly execution.

Failed attempts retain non-secret attempt metadata beside the resident slot receipt. Before another provider-capable attempt, Healer enforces:

```text
retry_interval_minutes: 15
max_attempts_per_slot: 4
```

A new UTC hour creates a new deterministic slot ID and fresh attempt state. Backoff checks themselves perform no Gmail/KV provider operation. This permits recovery without a tight retry loop.

## KV-before-archive invariant

Normalized GitHub failure observations are stored under `05_Projects/StegVerse/Operations/GitHubFailureEmail/` with deterministic append-only semantics, fsync, and exact-byte readback. Live `ARCHIVE_IDS` cannot reach the Gmail provider until those incident records have `KV_STORED_VERIFIED` evidence. Missing/invalid KnowledgeVault state fails closed and leaves the mailbox batch unarchived.

The KV root is accepted only from an already-materialized non-secret local binding or validated resident `control/kv-provider-materialization/latest.json`; this task does not mount a provider or acquire credentials.

The KV guard now additionally binds the exact reviewed Gmail ID set and the verified write receipts into `stegverse.native-email-archive-governance-context/v1`. That context is evidence input only. It does not itself authorize Gmail mutation.

## Governed provider mutation boundary

`ARCHIVE_IDS` changes external provider state. The StegOps broker therefore may not call TVC archive merely because the Gmail credential session exists. The in-validation integration reuses the installed generic SDK path:

```text
stegverse.ingress-manifest.v1
-> governance processor / canonical route
-> canonical StegCore transaction lifecycle
-> StegGate evaluation
-> commit coherence
-> bounded consequence callback
```

The callback is the exact TVC `ARCHIVE_IDS` operation. A non-ALLOW governance disposition or commit-coherence refusal leaves the callback unreachable. Successful source execution must retain the transaction identity, manifest receipt, route receipt chain, result binding, and Master Records custody status. The provider credential remains TV/TVC-owned and never enters the manifest.

`TRASH_IDS` is not part of the canonical native-email monitor contract and is being removed from the StegOps monitor broker rather than left as an ungoverned mutation surface.

Scoped StegOps handoff: `StegVerse-Labs/StegOps-Orchestrator:docs/NATIVE_EMAIL_ARCHIVE_GOVERNED_CONSEQUENCE_MIRROR_HANDOFF.md`.

## Resident source propagation

The existing local source refresh copies the KV wrapper, guard, and writer into resident runtime before local request dispatch on a fresh continuous-runtime cycle. Bootstrap supplies the distinct `STEGVERSE_HEARTBEAT_SOURCE_ROOT`; no second source transport or user-operated machine is required.

The archive governance change modifies the already-propagated KV guard rather than adding a new resident script, so the existing refresh set remains sufficient for the `.github` side. StegOps and SDK are resolved from the already-materialized local repository map.

## Remaining authentic predicates

Source validation for the archive-governance binding is still pending. Runtime completion additionally requires authentic evidence of:

- an eligible resident hourly reusable-task invocation;
- already-materialized KnowledgeVault resolution;
- `KV_STORED_VERIFIED` for every observed failure incident before live archive;
- canonical SDK/StegCore ALLOW + commit-coherence evidence for the exact archive transition;
- corresponding TV/TVC Gmail provider mutation evidence;
- route/transaction/Master Records custody evidence;
- bounded mailbox progression;
- durable StegHealth/Canonical Work reconciliation for actionable incidents.

No repository artifact currently substitutes for those resident/provider receipts. Source validation and merge do not prove live execution.

## README determination

`NO_README_CHANGE_REQUIRED` for `.github`: root documentation already covers local resident source refresh, reusable-task constructs, Canonical Work ingress, resident execution, and Personal KnowledgeVault custody. StegOps README is being updated because its provider-boundary behavior materially changes; Healer README already documents the retry/backoff behavior.
