# Site Publication Native Runtime Execution Mirror Handoff

Updated: 2026-09-13
Repository: `StegVerse-Labs/.github`
Canonical issue: `#1486`
Goal Task ID: `SITE-PUBLICATION-NATIVE-RUNTIME-EXECUTION-001`
Parent Goal Task ID: `KV-CONNECTION-REVALIDATION-WORKER-001`
Child runtime task: `SITE-PUBLICATION-INTR-CONSUMER-001`
COSV: `50000000102000`
Status: `ACTIVE`

## Purpose

Own only the genuinely remaining authentic native-runtime and publication-evidence phase after the parent goal reached its 20/20 prompt ceiling. Do not re-open completed source-registration or CI-repair work.

## Inherited validated source truth

- `.github` PR #1398 merged at `7444aefbdd2c644c46ae105192af4a524ef02172` after exact-head Heartbeat `34615815337`, Deterministic Repository Suite `34615815364`, and Organization Control `34615815476` passed.
- Canonical Site source boundary: `StegVerse-Labs/Site@bc1ee7257ebc64f77dab3f0b746bb3a86a279b6c`.
- Exact admitted materialization: `INTR-MAT-0e1ba4786b0ea8a00e1f166e`.
- Packet: `INTR-58dec5416bd4358190c11372`.
- Manifest: `sha256:e6bc47580f25296df61d16dfe5a74f3f49fec0dda018c813696195c960e77f09`.
- Parent post-merge handoff reconciliation PR #1483 passed exact-head Heartbeat `34635435820`, Organization Control `34635435835`, and Deterministic Repository Suite `34635435815`, then squash-merged at `4ab13a252eed668f1d828c08bd998b00b54e3c43`.
- Parent `KV-CONNECTION-REVALIDATION-WORKER-001` is retired for prompt-budget continuation; unresolved native-runtime/publication predicates are transferred here.

## Reusable source-refresh correction

Source refresh is a demonstrated shared capability and is not a task-specific resident-availability gate. The canonical reusable identity is `RT-SOVEREIGN-SOURCE-REFRESH-001`, which consumes `RTC-SOVEREIGN-SOURCE-REFRESH-010` and the existing `scripts/refresh_sovereign_worker_runtime_source.py` implementation through `scripts/trigger_reusable_task.py`.

A consuming Goal Task invokes this reusable task with its already-local `source_root` and existing `runtime_root`. The reusable lifecycle advances until authentic completion or an actual execution/resource boundary and records that boundary. The Goal Task does not first poll for a connected device as a prerequisite.

## Neutral reusable scheduling

Generic reusable-task scheduling is owned by `RT-REUSABLE-TASK-SCHEDULER-001`, with contract `data/reusable-task-scheduler-contract.json` and runner `scripts/run_reusable_task_scheduler.py`. Healer is a consumer/example of that capability, not its canonical generic owner.

This scheduler is conditional orchestration support for this Goal Task, not a new completion predicate. It may visit `RT-SOVEREIGN-SOURCE-REFRESH-001` when a schedule/carrier selects that invocation, but scheduling does not prove source refresh or any downstream runtime state.

## Authority boundaries

- GitHub runtime authority: `NONE`.
- Reusable task/component/scheduler orchestration: non-authorizing.
- Worker claim/fence authority: existing `WorkerCoordinator` only.
- Transition authority: Interlock/InTr.
- Credential authority: TV/TVC.
- User verification authority: KV/SKAP Vault only.
- Hosted-provider runtime: prohibited/not required.
- Second user-operated device: prohibited/not required.
- Do not synthesize, upgrade, or infer runtime/publication evidence from source, scheduling, or CI state.

## Required evidence chain

1. Invoke `RT-SOVEREIGN-SOURCE-REFRESH-001` with the already-local canonical source root and existing sovereign runtime root; consume its authentic completion or boundary receipt.
2. Require an authentic source-refresh completion receipt before dependent runtime work advances.
3. Target `SITE-PUBLICATION-INTR-CONSUMER-001` through the existing WorkerCoordinator so checkout/admission mints a fresh independent claim and fencing generation.
4. Bind only `STEGVERSE_SITE_PUBLICATION_MATERIALIZATION_ID=INTR-MAT-0e1ba4786b0ea8a00e1f166e` for that fenced invocation.
5. Retain the authentic candidate-validation receipt and fencing generation.
6. Execute one authentic bounded `EVENT_EPHEMERAL` publication lease through the canonical StegOS/InTr runtime owner.
7. Independently observe `/intr/profile`, exact HTTP byte/path hashes, candidate evidence export, and lease closure.
8. Separately admit the final publication transition.
9. Only after the preceding predicates pass, prove canonical-domain DNS/TLS recovery and public content equivalence.

## Predicates currently false

```text
sovereign source refresh observed after #1398 = false
fresh WorkerCoordinator claim/fence observed = false
runtime worker execution observed = false
bounded EVENT_EPHEMERAL lease execution observed = false
public HTTPS /intr/profile observed = false
exact HTTP byte/path equivalence observed = false
lease closure observed = false
final publication transition admitted = false
DNS/TLS recovery proven = false
```

## Activation

Activation condition is satisfied by merged, exact-head-green parent reconciliation PR #1483. This successor is ACTIVE. Reusable-task registration, scheduling, or invocation does not mint runtime authority, claim/fence state, credentials, publication state, or proof.

## Next action

Complete validation of `RT-REUSABLE-TASK-SCHEDULER-001` as the neutral scheduling owner and migrate generic consumers away from owning duplicate scheduling semantics. For this Goal Task, continue to require an authentic `RT-SOVEREIGN-SOURCE-REFRESH-001` completion receipt before fresh WorkerCoordinator claim/fence and all dependent publication evidence.
