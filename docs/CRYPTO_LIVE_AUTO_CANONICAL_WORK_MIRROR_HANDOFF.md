# Crypto Live Auto Canonical Work Mirror Handoff

Updated: 2026-09-09
Repository: `StegVerse-Labs/.github`
Task Registry ID: `CRYPTO-LIVE-AUTO-001`
COSV task vector: `50000000106000`
Source task owner: `StegVerse-Labs/crypto-bot`
Related goals: `CRYPTO-MONEY-MANAGER-001`, `CRYPTO-LIVE-AUTO-001`
Adjacent governed owners: `StegVerse-Labs/TVC#119`, `StegVerse-Labs/stegfin-governance#84`
Status: `RESIDENT_INGRESS_SELF_MATERIALIZATION_REPAIR_STAGED / AUTHENTIC_INGRESS_PENDING`
Authority effect: `NONE_COORDINATION_AND_REQUEST_STAGING_ONLY`

## Purpose

Bring the already-existing machine-owned CryptoBot live-trading task into the canonical StegVerse Task Registry and the already-generalized Canonical Work resident ingress path. This work does not create a new trading task, runtime, heartbeat, oscillator, scheduler, WorkerCoordinator, credential path, Coinbase provider path, governance gate, or execution authority.

## Canonical sources reused

- `StegVerse-Labs/crypto-bot/claims/CRYPTO-LIVE-AUTO-001.claim.json`
- `StegVerse-Labs/crypto-bot/docs/LIVE_TRADING_AUTOMATION_MIRROR_HANDOFF.md`
- `StegVerse-Labs/crypto-bot/docs/HB_INTR_RUNTIME_CONSUMPTION_MIRROR_HANDOFF.md`
- `StegVerse-Labs/crypto-bot/config/runtime-profile.json`
- `StegVerse-Labs/TVC#119`
- `StegVerse-Labs/stegfin-governance#84`
- `docs/CANONICAL_WORK_COORDINATION_RUNTIME_MIRROR_HANDOFF.md`
- `docs/CROSS_TASK_COORDINATION_MIRROR_HANDOFF.md`
- `master-records/orchestration/CANONICAL_WORK_COORDINATION_CUSTODY_MIRROR_HANDOFF.md`

## Machine preflight

Result: `ADMIT_COORDINATION`.

Resolved before mutation:

- repository-local CryptoBot machine-owned claim exists and is unreleased;
- `CRYPTO-LIVE-AUTO-001` is registered in `data/canonical-task-registry.json`;
- no `CRYPTO-LIVE-AUTO-001` WorkerCoordinator claim/fence exists in the canonical worker registry, so none is projected or fabricated here;
- Master Records already provides the canonical work event/custody/reconciliation path;
- the canonical registered-task ingress and resident dispatcher already exist and are reused;
- TV/TVC remains Coinbase credential/provider boundary;
- StegFin #84 remains the bounded live-runtime governance decision owner.

## README impact completeness

The repository README already documents the generalized Canonical Work task-ingress path, resident request dispatch, task identity separation, and that source request staging does not itself prove runtime execution. This repair changes failure recovery inside the existing consumer rather than adding a new public interface, runtime, scheduler, credential path, or capability class. README wording was reviewed and remains sufficient; no duplicate CryptoBot-specific README section is required.

## Registered task boundary

The canonical task record remains `PROPOSED` source state. It carries no WorkerCoordinator claim/fence and permits only the existing next transition `INGRESS_ADMITTED` through Interlock/InTr.

Runtime requirements deliberately describe the already-owned chain:

`canonical task ingress -> Master Records reconciliation -> WorkerCoordinator admission/claim/fence if independently admitted -> TVC current-iPhone/SKAP/provider evidence -> StegFin #84 bounded decision -> first max-$10 ETH-USD LIMIT/GTC post_only proof -> reconciliation -> next snapshot -> second bounded cycle -> repeat-loop proof`.

## Staged request

Request: `control/resident-execution-request.d/canonical-work-crypto-live-auto-001.json`

Identity:

- request id: `RESIDENT-EXEC-CANONICAL-WORK-CRYPTO-LIVE-AUTO-001`
- task id: `CRYPTO-LIVE-AUTO-001`
- COSV profile: `task.v1`
- COSV vector: `50000000106000`
- mode: `CANONICAL_WORK_EVENT_BOOTSTRAP`
- authority effect: `NONE_REQUEST_ONLY`
- credential authority: `TV/TVC`
- GitHub token runtime authority: `NONE`
- second machine required: `false`

Expected authentic consumption evidence:

`receipts/sovereign-host/canonical-work-crypto-live-auto-request-consumption.latest.json`

No source merge, CI run, heartbeat reference, task registration, staged request, or COSV pointer may be substituted for this authentic consumption receipt.

## Resident-ingress repair — 2026-09-09

Investigation found two stale-resident failure modes in the generalized Canonical Work request consumer that could indefinitely prevent a newly registered task from reaching the existing bootstrap path even though source registration was correct:

1. the consumer checked only for the request file already present in the resident runtime and returned `NO_REQUEST` before performing source materialization;
2. the consumer deliberately preserves an existing resident monolithic task registry, so an older resident registry can legitimately predate `CRYPTO-LIVE-AUTO-001` and then fail exact task resolution even after the request arrives.

The repair on `fix/crypto-live-auto-resident-ingress-20260909` changes only the already-existing resident consumer:

- each explicitly enumerated request is exact-byte materialized from the already-local canonical source before request validation;
- the existing resident monolithic registry remains preserved;
- when that preserved registry does not contain the requested task, the consumer extracts exactly one matching source task and writes a task-specific fallback shard under `data/canonical-task-records/<task_id>.json`;
- if the resident monolithic registry already contains the task, no fallback shard is created;
- duplicate task identity remains fail-closed;
- source/network fetch, credential use, claim/fence minting, heartbeat/oscillator execution authority, and second-machine requirements remain false;
- consumption receipts now expose both request self-materialization and task-identity materialization evidence.

Focused regression coverage was added in `tests/test_crypto_live_auto_resident_ingress_repair.py` for:

- missing resident request exact-copy recovery;
- stale resident monolithic registry + task-specific fallback shard recovery without overwriting the resident registry;
- preservation of an already-current resident task identity without creating a duplicate shard.

This is a source repair only until merged, propagated into the sovereign resident source projection, and authentically executed. It does not fabricate or satisfy the missing runtime receipt.

## Cross-task predicate boundary

`control/cross-task-coordination.d/crypto-live-auto-001-canonical-work-ingress.json` records two exact subject-bound predicates:

1. `canonical_work_request_staged` — source-staging evidence only;
2. `resident_request_consumed` — remains `UNKNOWN` until the exact request is authentically consumed.

The subject is the pair:

`task_id=CRYPTO-LIVE-AUTO-001 + request_id=RESIDENT-EXEC-CANONICAL-WORK-CRYPTO-LIVE-AUTO-001`.

No other resident request may satisfy it.

## COSV pointer

```text
task_id: CRYPTO-LIVE-AUTO-001
profile: task.v1
vector: 50000000106000
lifecycle: MACHINE_OWNED
canonical_owner_installed: true
thread_required: false
blocker_count: 6
evidence_complete: false
activated: false
propagated: false
```

Preflight receipt: `receipts/preflight/CRYPTO-LIVE-AUTO-COSV-POINTER-001.json`.

The structural preflight PASS proves the task/COSV pointer and coordination contract are admissible. It does not prove authentic resident consumption, WorkerCoordinator admission, current P-256 liveness, iPhone ingress, SKAP custody, current grant state, Coinbase provider state, StegFin approval, order execution, settlement, or repeat-loop activation.

### Exact next evidence action

After the repair is merged and resident source refresh has materialized the updated consumer, dispatch the existing `canonical_work_coordination` resident consumer and require production of exactly:

`receipts/sovereign-host/canonical-work-crypto-live-auto-request-consumption.latest.json`

Only after that receipt exists may downstream Master Records reconciliation and WorkerCoordinator admission review advance. Provider interaction remains downstream under TVC #119 and StegFin #84.

## Current completion boundary

Source registration, COSV pointer binding, request staging, and structural preflight validation are complete. The resident-ingress stale-projection repair is staged for validation. Live trading activation is not complete. Authentic resident request consumption, Master Records reconciliation, WorkerCoordinator admission, TVC current-iPhone/SKAP provider evidence, StegFin bounded approval, the first bounded live order, reconciliation, and second-cycle proof remain outstanding.
