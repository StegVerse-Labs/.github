# Site Publication Native Runtime Component Model Mirror Handoff

Updated: 2026-09-12
Repository: `StegVerse-Labs/.github`
Goal Task ID: `SITE-PUBLICATION-NATIVE-RUNTIME-EXECUTION-001`
COSV: `50000000102000`
Canonical runtime handoff: `docs/SITE_PUBLICATION_NATIVE_RUNTIME_EXECUTION_001_MIRROR_HANDOFF.md`
Status: `ACTIVE / COMPONENTIZED / RUNTIME EVIDENCE UNCHANGED`

## Identity

The existing Goal Task remains canonical. No successor or duplicate Goal Task is created. Parent remains `KV-CONNECTION-REVALIDATION-WORKER-001`; child runtime task remains `SITE-PUBLICATION-INTR-CONSUMER-001`.

## Decomposition decision

The canonical evaluator signals for this task are repeated subflow, multiple authority crossings, cross-repository spread, handoff-sequence growth, independent reusability, optional subflow presence, and independent evidence predicates. Score: `21`. Decision: `STOP_SCOPE_GROWTH_AND_DECOMPOSE_BEFORE_ADDING_MORE_TASK_SPECIFIC_ORCHESTRATION`.

## Selected reusable composition

```text
RTC-SOVEREIGN-SOURCE-REFRESH-010
-> GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001
-> WorkerCoordinator fresh claim/fence authority invocation
-> RTC-GOVERNED-PROCESSING-002
-> REUSABLE-TASK-EPHEMERAL-CONSTRUCT-V1
-> RTC-PUBLISHER-005
-> RTC-STEGVERSE-EGRESS-007
-> RTC-INTERLOCK-INTR-TRANSPORT-008 (repeatable: bounded publication transition + final publication transition)
-> GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001 (publication observation)
-> RTC-EVIDENCE-CUSTODY-004
```

The exact materialization, packet, manifest, child worker registration, and publication-specific `/intr/profile` plus byte/path equivalence checks remain Goal Task-specific configuration. They are not new generic orchestration owners.

## New reusable component

`RTC-SOVEREIGN-SOURCE-REFRESH-010` is a reusable wrapper around the already-existing `scripts/refresh_sovereign_worker_runtime_source.py`. It creates no new source transport, runtime owner, credential path, claim authority, or transition authority. It only standardizes stable inputs/outputs/evidence for the already-shared local refresh operation.

## Existing components reused

- Canonical runtime observation: `GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001`.
- Governed processing: `RTC-GOVERNED-PROCESSING-002`.
- Bounded ephemeral execution lifecycle: `data/reusable-task-ephemeral-construct-contract.json`.
- Publisher projection: `RTC-PUBLISHER-005`.
- StegVerse egress: `RTC-STEGVERSE-EGRESS-007`.
- Governed transport/admission: `RTC-INTERLOCK-INTR-TRANSPORT-008`.
- Evidence custody/reconstruction: `RTC-EVIDENCE-CUSTODY-004` with Master Records.

Not selected: fresh manifest intake, generic provider/framework round trip, SDK return assembly, and far-side final transition. TV/TVC credential/session issuance remains conditional on the canonical publication runtime actually requiring it.

## Authority separation

- Task Registry: coordination only.
- WorkerCoordinator: fresh claim/fence authority.
- Interlock/InTr: state-transition/admission authority.
- TV/TVC: credential/provider/release authority when required.
- KV/SKAP Vault: sole user-verification authority; this task currently selects no user-verification step.
- StegOS devices: interchangeable transport/execution nodes, never user verifiers.
- Master Records: observed-reality custody/readback/reconstruction.
- HeartBeat: timing, freshness, liveness, correlation, and observability only.
- GitHub: source/evidence coordination only; runtime authority `NONE`.

## Goal-specific predicates preserved

```text
SOVEREIGN_SOURCE_REFRESH_OBSERVED
FRESH_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED
RUNTIME_WORKER_EXECUTION_OBSERVED
BOUNDED_EVENT_EPHEMERAL_LEASE_EXECUTION_OBSERVED
PUBLIC_HTTPS_INTR_PROFILE_OBSERVED
EXACT_HTTP_BYTE_PATH_EQUIVALENCE_OBSERVED
LEASE_CLOSURE_OBSERVED
FINAL_PUBLICATION_TRANSITION_ADMITTED
DNS_TLS_RECOVERY_PROVEN
```

All remain false. Componentization does not promote any runtime evidence class.

Required component evidence for evidence-chain closure is separately tracked as Master Records publication-evidence custody acceptance and reconstruction confirmation. This does not replace or synthesize any Goal Task runtime predicate.

## Duplicate orchestration superseded

Do not add a task-specific source refresher, runtime observer, generic InTr transport/admission adapter, hosted runtime fallback, or second user-operated-device path. The existing child worker remains task-specific configuration atop reusable components; historical source and evidence remain preserved.

## Next admissible work

Observe an authentic authorized resident reconnect. Then invoke `RTC-SOVEREIGN-SOURCE-REFRESH-010` against already-local canonical source, obtain a fresh WorkerCoordinator claim/fence for `SITE-PUBLICATION-INTR-CONSUMER-001`, bind only `INTR-MAT-0e1ba4786b0ea8a00e1f166e`, and continue through the selected components one independently evidenced transition at a time.
