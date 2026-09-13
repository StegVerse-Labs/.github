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

Generic reusable-task scheduling is owned by `RT-REUSABLE-TASK-SCHEDULER-001`, with contract `data/reusable-task-scheduler-contract.json` and runner `scripts/run_reusable_task_scheduler.py`. Healer is a consumer/carrier of that capability, not its canonical generic owner.

The neutral scheduler now owns due selection, hourly slot identity, bounded retry/backoff, success idempotency, reusable-child invocation, and preservation of authentic child boundary receipts. `.github` PR #1762 exact head `d385fe83087f0096ff48a4690cac541dd93098dd` passed Organization Control `34780694559`, Deterministic Repository Suite `34780694565`, and Heartbeat `34780694531`, then merged at `5b66fe7d6281c92445b9a67881eda666e865c13d`.

Healer was migrated from generic scheduler owner to consumer/carrier in StegVerse-Healer PR #68. Exact head `d095c27cb9ce42da21b0c77eece515e243ef180a` passed Test Readiness `34780841650` and merged at `0084ac3af5db9c29b4c3e74660751b9954317530`.

StegVerse-Healer PR #69 then bound `RT-SOVEREIGN-SOURCE-REFRESH-001` to this Goal Task (`SITE-PUBLICATION-NATIVE-RUNTIME-EXECUTION-001`, COSV `50000000102000`) as a carrier configuration for the neutral scheduler. Exact head `78f26ed6fc3a5e3bfde8f610ad6c36c023183b3e` passed Test Readiness `34780907582` and merged at `1a2bac1a61f97819182a701d91fc91f61f9b0f1e`.

This carrier binding is orchestration support only. Healer is not a runtime authority or scheduling authority. The neutral scheduler remains non-authorizing, and source-refresh scheduling does not prove source refresh or any downstream runtime state.

## Authority boundaries

- GitHub runtime authority: `NONE`.
- Reusable task/component/scheduler orchestration: non-authorizing.
- Healer role for reusable scheduling: carrier/consumer only.
- Worker claim/fence authority: existing `WorkerCoordinator` only.
- Transition authority: Interlock/InTr.
- Credential authority: TV/TVC.
- User verification authority: KV/SKAP Vault only.
- Hosted-provider runtime: prohibited/not required.
- Second user-operated device: prohibited/not required.
- Do not synthesize, upgrade, or infer runtime/publication evidence from source, scheduling, carrier configuration, or CI state.

## Required evidence chain

1. Consume an authentic neutral-scheduler invocation of `RT-SOVEREIGN-SOURCE-REFRESH-001` for this Goal Task, including the reusable child receipt.
2. Require an authentic source-refresh completion receipt before dependent runtime work advances; a neutral-scheduler/child boundary receipt preserves the unresolved state without device discovery or alternate scheduler creation.
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

Activation condition is satisfied by merged, exact-head-green parent reconciliation PR #1483. This successor is ACTIVE. Reusable-task registration, neutral scheduling, Healer carrier execution, or source binding does not mint runtime authority, claim/fence state, credentials, publication state, or proof.

## Next action

Do not perform connected-device discovery as a prerequisite. Observe/consume the next authentic neutral-scheduler + `RT-SOVEREIGN-SOURCE-REFRESH-001` receipt produced by the existing resident carrier path. If the child source-refresh receipt satisfies the reusable source-refresh completion predicates, advance directly to fresh WorkerCoordinator claim/fence for `SITE-PUBLICATION-INTR-CONSUMER-001`. If the child records a real execution/resource boundary, retain that exact boundary and continue independent admissible work without creating another scheduler, refresher, hosted fallback, or second-device path.
