# Crypto Live Auto Canonical Work Mirror Handoff

Updated: 2026-09-06
Repository: `StegVerse-Labs/.github`
Task Registry ID: `CRYPTO-LIVE-AUTO-001`
Source task owner: `StegVerse-Labs/crypto-bot`
Related goals: `CRYPTO-MONEY-MANAGER-001`, `CRYPTO-LIVE-AUTO-001`
Adjacent governed owners: `StegVerse-Labs/TVC#119`, `StegVerse-Labs/stegfin-governance#84`
Status: `CANONICAL_TASK_REGISTRATION_AND_RESIDENT_REQUEST_STAGED / AUTHENTIC_INGRESS_PENDING`
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
- `CRYPTO-LIVE-AUTO-001` was absent from `data/canonical-task-registry.json`;
- no `CRYPTO-LIVE-AUTO-001` WorkerCoordinator claim/fence exists in the canonical worker registry, so none is projected or fabricated here;
- active G13/G17/G18 control-plane claims do not collide with this registry/request-staging scope;
- Master Records already provides the non-authorizing canonical work event/custody/reconciliation path;
- the canonical registered-task ingress and resident dispatcher already exist and are reused;
- TV/TVC remains Coinbase credential/provider authority;
- StegFin #84 remains the bounded live-runtime governance decision owner.

## README impact completeness

`material_function_change=false`.

Reason: this change registers one already-existing task and adds one explicit request specification to the already-generalized Canonical Work task ingress. It does not change runtime semantics, interfaces, authority boundaries, evidence semantics, prerequisites, dependencies, failure behavior, or capability meaning. The repository README already documents that Canonical Work ingress accepts multiple explicit tasks that already exist in the canonical Task Registry and that source request staging does not create task identity or execution authority. This follows the same non-material determination already recorded for adding the Runtime Profile Map registered task to the generalized request set.

README update required: `false`.

Evidence:

- `README.md` Canonical Work task-ingress section;
- `docs/CANONICAL_WORK_COORDINATION_RUNTIME_MIRROR_HANDOFF.md` README completeness section;
- `scripts/run_canonical_work_event_bootstrap.py` registered-task checks;
- `control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py` existing request-set consumer.

## Registered task boundary

The canonical task record remains `PROPOSED` source state. It carries no WorkerCoordinator claim/fence and permits only the existing next transition `INGRESS_ADMITTED` through Interlock/InTr.

Runtime requirements deliberately describe the already-owned chain:

`canonical task ingress -> Master Records reconciliation -> WorkerCoordinator admission/claim/fence if independently admitted -> TVC current-iPhone/SKAP/provider evidence -> StegFin #84 bounded decision -> first max-$10 ETH-USD LIMIT/GTC post_only proof -> reconciliation -> next snapshot -> second bounded cycle -> repeat-loop proof`.

## Staged request

Request: `control/resident-execution-request.d/canonical-work-crypto-live-auto-001.json`

Identity:

- request id: `RESIDENT-EXEC-CANONICAL-WORK-CRYPTO-LIVE-AUTO-001`
- task id: `CRYPTO-LIVE-AUTO-001`
- mode: `CANONICAL_WORK_EVENT_BOOTSTRAP`
- authority effect: `NONE_REQUEST_ONLY`
- credential authority: `TV/TVC`
- GitHub token runtime authority: `NONE`
- second machine required: `false`

Expected authentic consumption evidence:

`receipts/sovereign-host/canonical-work-crypto-live-auto-request-consumption.latest.json`

No source merge, CI run, heartbeat reference, task registration, or staged request may be substituted for this authentic consumption receipt.

## Cross-task predicate boundary

`control/cross-task-coordination.d/crypto-live-auto-001-canonical-work-ingress.json` records two exact subject-bound predicates:

1. `canonical_work_request_staged` — source-staging evidence only;
2. `resident_request_consumed` — remains `UNKNOWN` until the exact request is authentically consumed.

The subject is the pair:

`task_id=CRYPTO-LIVE-AUTO-001 + request_id=RESIDENT-EXEC-CANONICAL-WORK-CRYPTO-LIVE-AUTO-001`.

No other resident request may satisfy it.

## Current completion boundary

Source registration/request staging completes when registry validation, cross-task coordination validation, and the focused task-ingress test pass on the merged head.

Live trading activation is not completed by this source work. The next evidence-producing action is authentic resident consumption through the existing dispatcher and Canonical Work consumer, followed by Master Records reconciliation and WorkerCoordinator admission review. Coinbase provider interaction remains downstream and subject to TVC #119 plus StegFin #84.
