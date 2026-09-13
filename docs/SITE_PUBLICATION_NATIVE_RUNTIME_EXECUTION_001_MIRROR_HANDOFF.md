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
- Exact source-lineage materialization: `INTR-MAT-0e1ba4786b0ea8a00e1f166e`.
- Packet: `INTR-58dec5416bd4358190c11372`.
- Manifest: `sha256:e6bc47580f25296df61d16dfe5a74f3f49fec0dda018c813696195c960e77f09`.
- Parent post-merge handoff reconciliation PR #1483 passed exact-head Heartbeat `34635435820`, Organization Control `34635435835`, and Deterministic Repository Suite `34635435815`, then squash-merged at `4ab13a252eed668f1d828c08bd998b00b54e3c43`.
- Parent `KV-CONNECTION-REVALIDATION-WORKER-001` is retired for prompt-budget continuation; unresolved native-runtime/publication predicates are transferred here.

These source facts do not prove authentic resident ingress, WorkerCoordinator execution, publication, or public equivalence.

## Reusable source-refresh correction

Source refresh is a demonstrated shared capability and is not a task-specific resident-availability gate. The canonical reusable identity is `RT-SOVEREIGN-SOURCE-REFRESH-001`, which consumes `RTC-SOVEREIGN-SOURCE-REFRESH-010` and the existing `scripts/refresh_sovereign_worker_runtime_source.py` implementation through `scripts/trigger_reusable_task.py`.

A consuming Goal Task invokes this reusable task with its already-local `source_root` and existing `runtime_root`. The reusable lifecycle advances until authentic completion or an actual execution/resource boundary and records that boundary. The Goal Task does not first poll for a connected device as a prerequisite.

The neutral scheduler/carrier migration exposed one concrete materialization defect: the existing source refresh copied `scripts/trigger_reusable_task.py` plus reusable-task registry shards but did not materialize `scripts/run_reusable_task_scheduler.py` or `data/reusable-task-scheduler-contract.json` into resident static source. `.github` PR #1782 repaired that gap with `scripts/refresh_sovereign_worker_runtime_source_reusable.py`, a thin adapter that extends only the proven refresher's static-file set and delegates to the same canonical `refresh()` implementation. Exact head `35f5d2f2295849cdee9bd6d01e2006f356bbf060` passed Organization Control `34787496629`, Deterministic Repository Suite `34787496630`, and Heartbeat `34787496613`, then squash-merged at `8c2b40da6e7b1cc2508a5c741567a3825e0eb0f6`.

The adapter is not a second refresher or runtime owner. `RT-SOVEREIGN-SOURCE-REFRESH-001` now uses the adapter as its primary reusable runner while retaining the original refresher and neutral scheduler runner as declared dependencies. Source/CI validation still does not prove that resident refresh has executed.

## Neutral reusable scheduling

Generic reusable-task scheduling is owned by `RT-REUSABLE-TASK-SCHEDULER-001`, with contract `data/reusable-task-scheduler-contract.json` and runner `scripts/run_reusable_task_scheduler.py`. Healer is a consumer/carrier of that capability, not its canonical generic owner.

The neutral scheduler owns due selection, hourly slot identity, bounded retry/backoff, success idempotency, reusable-child invocation, and preservation of authentic child boundary receipts. `.github` PR #1762 exact head `d385fe83087f0096ff48a4690cac541dd93098dd` passed Organization Control `34780694559`, Deterministic Repository Suite `34780694565`, and Heartbeat `34780694531`, then merged at `5b66fe7d6281c92445b9a67881eda666e865c13d`.

Healer was migrated from generic scheduler owner to consumer/carrier in StegVerse-Healer PR #68. Exact head `d095c27cb9ce42da21b0c77eece515e243ef180a` passed Test Readiness `34780841650` and merged at `0084ac3af5db9c29b4c3e74660751b9954317530`.

StegVerse-Healer PR #69 then bound `RT-SOVEREIGN-SOURCE-REFRESH-001` to this Goal Task (`SITE-PUBLICATION-NATIVE-RUNTIME-EXECUTION-001`, COSV `50000000102000`) as a carrier configuration for the neutral scheduler. Exact head `78f26ed6fc3a5e3bfde8f610ad6c36c023183b3e` passed Test Readiness `34780907582` and merged at `1a2bac1a61f97819182a701d91fc91f61f9b0f1e`.

This carrier binding is orchestration support only. Healer is not a runtime authority or scheduling authority. The neutral scheduler remains non-authorizing, and source-refresh scheduling does not prove source refresh or any downstream runtime state.

## Admitted materialization binding

Authentic Universal InTr ingress persists both:

```text
receipts/sovereign-network/site-publication-intr-ingress.latest.json
intr-materialization/<materialization_id>.json
```

`SITE-PUBLICATION-INTR-CONSUMER-001` resolves the opaque materialization id from that local write-once admitted-ingress evidence. The receipt must be `INGRESS_ADMITTED_CANDIDATE_ONLY`, exact-request validated, write-once persisted, non-authorizing, and bound to the exact queued request under the same runtime root.

`STEGVERSE_SITE_PUBLICATION_MATERIALIZATION_ID` is only an optional correlation input. When present, it must equal the locally admitted materialization id; a mismatch fails closed. The environment value cannot substitute for authentic ingress evidence and cannot grant execution, claim/fence, or transition authority.

This supersedes the former manual environment-binding step as the candidate identity source of truth. `.github` PR #1767 merged this source binding at `1d10dd97475c910de83847f7e5344e387dd81cf7` after exact-head Deterministic `34781655303`, Organization Control `34781655347`, and Heartbeat `34781655362` passed.

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
- No device-verification policy/process or device-identity user-verification step exists.
- Do not synthesize, upgrade, or infer runtime/publication evidence from source, scheduling, carrier configuration, or CI state.

## Required evidence chain

1. Consume an authentic neutral-scheduler invocation of `RT-SOVEREIGN-SOURCE-REFRESH-001` for this Goal Task, including the reusable child receipt from the scheduler-materialized resident source.
2. Require an authentic source-refresh completion receipt before dependent runtime work advances; a neutral-scheduler/child boundary receipt preserves unresolved state without device discovery or alternate scheduler creation.
3. Require authentic Universal InTr Site-publication ingress to persist the exact candidate receipt and write-once queue entry under the resident runtime root.
4. Allow the existing WorkerCoordinator to discover `SITE-PUBLICATION-INTR-CONSUMER-001`; checkout/admission must mint a fresh independent claim and fencing generation.
5. The worker resolves the exact materialization from local admitted-ingress evidence and retains candidate-validation evidence for that same fencing generation.
6. Execute one authentic bounded `EVENT_EPHEMERAL` publication lease through the canonical StegOS/InTr runtime owner.
7. Independently observe `/intr/profile`, exact HTTP byte/path hashes, candidate evidence export, and lease closure.
8. Separately admit the final publication transition through Interlock/InTr.
9. Retain publication evidence through Master Records custody/reconstruction.
10. Only after the preceding predicates pass, prove canonical-domain DNS/TLS recovery and public-content equivalence when applicable.

No preceding receipt grants the authority required by a later step.

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

Activation condition is satisfied by merged, exact-head-green parent reconciliation PR #1483. This successor is ACTIVE. Reusable-task registration, neutral scheduling, Healer carrier execution, source binding, admitted-ingress candidate evidence, or scheduler-materialization source repair does not mint runtime authority, claim/fence state, credentials, publication state, or proof.

## Next action

Do not perform connected-device discovery as a prerequisite. The source path is now repaired through PR #1782 and the admitted-ingress source binding is merged through PR #1767. Consume the next authentic neutral-scheduler + `RT-SOVEREIGN-SOURCE-REFRESH-001` receipt from the existing carrier path. If it completes, proceed directly to authentic admitted Site-publication ingress and the already-registered WorkerCoordinator child. If it records a real execution/resource boundary, retain that boundary exactly and remediate only that boundary. Do not create another scheduler, refresher, hosted fallback, manual materialization binding, or second-device path.
