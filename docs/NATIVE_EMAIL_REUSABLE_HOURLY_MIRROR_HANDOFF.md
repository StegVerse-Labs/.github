# Native Email Reusable Hourly Mirror Handoff

Updated: 2026-09-10
Repository: `StegVerse-Labs/.github`
Task: `STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001`
COSV task vector: `10100000100000`
Reusable identity: `RT-NATIVE-EMAIL-ACTION-MONITOR-001`
Parent handoff: `docs/NATIVE_EMAIL_ACTION_MONITOR_MIRROR_HANDOFF.md`
Scheduler owner: `StegVerse-Labs/StegVerse-Healer` / `SHWP-HEALER-SOVEREIGN-SCHEDULER-001`
State: `SOURCE_INTEGRATION_MERGED / HOURLY_REUSABLE_BINDING_MERGED / KV_BEFORE_ARCHIVE_MERGED / RESIDENT_REFRESH_PROPAGATION_MERGED / BOUNDED_RETRY_MERGED / GOVERNED_ARCHIVE_MERGED / VERIFIED_SDK_SOURCE_REUSE_MERGED / SOURCE_PREP_LOCATOR_FORWARDING_REPAIR_IN_VALIDATION / AUTHENTIC_SCHEDULED_GMAIL_KV_GOVERNANCE_RECEIPT_PENDING`

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
-> exact-byte KV write + readback
-> bind exact reviewed Gmail IDs + verified KV receipts
-> StegOps generic stegverse.ingress-manifest.v1 governance route
-> canonical StegCore StegGate + commit coherence
-> only on ALLOW: TVC ARCHIVE_IDS bounded consequence
-> Gmail provider result + route/transaction/Master Records evidence
-> StegHealth / Canonical Work reconciliation
-> completed scheduler-cycle receipt
-> fresh later WorkerCoordinator cycle
```

## Merged implementation and validation

Core schedule / KV chain:

- `.github` #1252 / `700f959dca0160f0d71d92fc391c9f262f27feea` — reusable invocation.
- Healer #57 / `ef5d90a8c215056e055385a04534e16c49d9a3d5` — hourly UTC-slot schedule.
- `.github` #1255 / `2eb089842ea8960845dcd021f5241126432f3b74` — canonical task registration.
- `.github` #1259 / `569b6dde49cc9f568c0a24daf9fc723eee807b6f` — standing recurrence.
- Healer #58 / `a0f6daeaf33198f26e358c7b124fc9f80aad8b6b` — source/runtime separation.
- `.github` #1273 / `438aeb9a4b187419ea3a91984ed0436c89b26819` — WorkerCoordinator rearm.
- Healer #59 / `93b637ddcc48777900e3804f994b22036d507571` — KV-root forwarding; Test Readiness `34363810591` SUCCESS.
- `.github` #1342 / `1d4093e6266154a0552d942f3fc1b5fdafb71b70` — KV-before-archive implementation; Heartbeat `34544669388`, org-control `34544669233`, deterministic `34544669416` SUCCESS.
- `.github` #1356 / `2c8978eb89c0f99f2c221fc523710d2347a7cea1` — resident refresh carries KV wrapper/guard/writer; applicable validations SUCCESS.
- Healer #60 / `cd74e971ee54344c2f772fe2fd35827174914e66` and `.github` #1357 / `05c1250c91b6b09d54def657c37de5c77bd89c15` — failed/boundary attempts no longer satisfy a UTC-hour slot.
- Healer #61 / `9c1661476ff1eadbe8c6ba300519a0c3f925d2e9` — retry no sooner than 15 minutes, max four failed attempts per UTC-hour slot; Test Readiness `34551986643` SUCCESS.

Governed provider mutation:

- StegOps #18 / `0d3768a7f8575af18c67b01a40f6745f35b93c0f` — `ARCHIVE_IDS` executes only as the SDK/StegCore bounded consequence; exact head `624c4edcb8f46a4f526f31e1aa2117c6f6fc6834`; Guardrails `34555040293`, Test Readiness `34555040405`, BCAT `34555040586` SUCCESS.
- `.github` #1375 / `53175dadad4de762299a9c3be1ac67cbed71998e` — exact reviewed IDs + verified KV receipts bound into `stegverse.native-email-archive-governance-context/v1`; org-control `34555087030`, Heartbeat `34555087160`, deterministic `34555087161` SUCCESS.
- Healer #62 / `d4f038999a63a4e05bb0e818cb38dd176ae75299` — reuses the existing verified SV-DN1 production-source-preparation v2 receipt to augment local SDK/StegCore/Core-Lite/Master Records roots; exact head `b0c9cf69d4044e499a6170e8edb43947e1a4946f`, Test Readiness `34555673051` SUCCESS.

The stale `.github` #1280 branch remains CLOSED UNMERGED and superseded by #1342.

## Hourly and retry semantics

A slot is satisfied only by a retained reusable-task trigger receipt whose state is `AUTOMATABLE_STEPS_EXHAUSTED`. Failed/boundary attempts remain retryable, subject to:

```text
retry_interval_minutes: 15
max_attempts_per_slot: 4
```

A new UTC hour creates a new deterministic slot identity. Backoff checks themselves perform no Gmail or KV provider operation.

## KV-before-archive invariant

Failure observations are written under `05_Projects/StegVerse/Operations/GitHubFailureEmail/` using deterministic append-only records, fsync, and exact-byte readback. Failure-email archive is forbidden unless represented incidents have `KV_STORED_VERIFIED` receipts. Missing/invalid KV state fails closed.

The KV guard also binds the exact reviewed Gmail ID set and verified write receipts into the archive governance context. The context is evidence input only; it grants no mutation authority.

## Governed provider mutation boundary

`ARCHIVE_IDS` is a Gmail state transition. TV/TVC credential availability is not permission to execute it.

The merged StegOps path reuses the generic SDK governance architecture:

```text
stegverse.ingress-manifest.v1
-> governance processor / canonical route
-> canonical StegCore transaction lifecycle
-> StegGate ALLOW
-> commit coherence ALLOW
-> bounded TVC ARCHIVE_IDS consequence
```

The existing SDK authority model explicitly permits a trusted runtime-installed bounded consequence while keeping `caller request external_consequence_enabled=false`. Therefore no new SDK route or email-specific evaluator was created. The caller cannot self-enable Gmail mutation.

`TRASH_IDS` is intentionally not exposed by the native-email monitor broker because it is an unused provider-state mutation outside this task contract.

Scoped StegOps handoff: `StegVerse-Labs/StegOps-Orchestrator:docs/NATIVE_EMAIL_ARCHIVE_GOVERNED_CONSEQUENCE_MIRROR_HANDOFF.md`.

## SDK governance source dependency

The governed consequence requires already-local SDK, StegCore, Core-Lite, and Master Records source. Healer does not install or fetch those components. It may augment its repo map only from the existing SV-DN1 production-source-preparation v2 receipt when that receipt proves:

- `COMPLETE / SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE`;
- exactly four canonical components;
- SHA-256 source identities for all four;
- migration anchors verified;
- no network/GitHub/credential source acquisition or repository writeback;
- every declared root still materialized with its required runtime marker.

Absent or invalid source-prep evidence contributes zero roots. The current SV-DN1 handoff still states that an authentic production-source-preparation v2 receipt has **not yet been observed**, so this remains a real runtime dependency unless the four components are already present through the local repository map.

### Source-prep locator forwarding repair — 2026-09-10

GitHub reconciliation found a concrete adapter mismatch in `SV-DN1-PRODUCTION-SOURCE-PREP-001`: the canonical source-prep handoff and worker permit already-local source through `STEGVERSE_SDK_SOURCE_ROOT`, `STEGVERSE_STEGCORE_SOURCE_ROOT`, `STEGVERSE_CORE_LITE_SOURCE_ROOT`, and `STEGVERSE_MASTER_RECORDS_SOURCE_ROOT`, but the registered process adapter did not forward those four variables in its `env_allowlist`.

The repair branch `fix/native-email-source-prep-locators` adds only those four non-secret local-root locators to the existing adapter and adds deterministic regression coverage. It does not add network acquisition, credentials, GitHub runtime dependence, a new scheduler, a new WorkerCoordinator, or a new resident request. Until that repair is exact-head validated and merged, an authentic source-prep receipt remains pending.

## Remaining authentic predicates

Source construction identified in this lane is merged and validated except for the locator-forwarding repair described above. Runtime completion still requires authentic evidence of:

- an eligible resident hourly reusable-task invocation;
- already-materialized KnowledgeVault resolution;
- `KV_STORED_VERIFIED` for every observed failure incident;
- current local SDK/StegCore/Core-Lite/Master Records source availability;
- canonical SDK/StegCore ALLOW + commit-coherence evidence for the exact archive transition;
- corresponding TV/TVC Gmail mutation evidence;
- route/transaction/Master Records custody evidence;
- bounded mailbox progression;
- durable StegHealth/Canonical Work reconciliation.

No repository artifact substitutes for those resident/provider receipts. Source validation and merge do not prove live execution.

## README determination

`NO_README_CHANGE_REQUIRED` for `.github`: root documentation already covers resident source refresh, reusable tasks, Canonical Work ingress, resident execution, KnowledgeVault custody, and local source-root execution. This repair changes adapter forwarding to match that existing documented contract rather than changing repository responsibilities. StegOps and Healer READMEs were updated where their responsibilities materially changed.
