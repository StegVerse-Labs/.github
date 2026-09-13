# Site Publication Native Runtime Component Model Mirror Handoff

Updated: 2026-09-13
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
RT-SOVEREIGN-SOURCE-REFRESH-001
  -> RTC-SOVEREIGN-SOURCE-REFRESH-010
-> GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001
-> WorkerCoordinator fresh claim/fence authority invocation
-> RTC-GOVERNED-PROCESSING-002
-> REUSABLE-TASK-EPHEMERAL-CONSTRUCT-V1
-> RTC-PUBLISHER-005
-> RTC-STEGVERSE-EGRESS-007
-> RTC-INTERLOCK-INTR-TRANSPORT-008 (repeatable)
-> GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001 (publication observation)
-> RTC-EVIDENCE-CUSTODY-004
```

The exact materialization, packet, manifest, child worker registration, and publication-specific `/intr/profile` plus byte/path equivalence checks remain Goal Task-specific configuration.

## Source-refresh reusable-task correction

`RTC-SOVEREIGN-SOURCE-REFRESH-010` is now consumed through durable reusable identity `RT-SOVEREIGN-SOURCE-REFRESH-001`, defined in `source-bundles/reusable-task-registry.d/RT-SOVEREIGN-SOURCE-REFRESH-001.json` and executed through the existing reusable-task constructor/trigger lifecycle.

The reusable task reuses `scripts/refresh_sovereign_worker_runtime_source.py`; it creates no new source transport, runtime owner, scheduler, credential route, claim authority, or transition authority.

Resident/runtime availability is an execution boundary handled by the reusable-task lifecycle. It is **not** a Goal Task-specific prerequisite that this task should manually rediscover by polling for a connected device before source-refresh invocation. A reusable invocation advances until authentic completion or the exact real boundary and records the resulting receipt chain.

Registry shard discovery is additive and fail-closed: `data/reusable-task-registry.json` remains canonical baseline identity source, while `source-bundles/reusable-task-registry.d/*.json` adds independently resolvable identities and duplicate identities across the two surfaces are rejected.

## Existing components reused

- Canonical runtime observation: `GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001`.
- Governed processing: `RTC-GOVERNED-PROCESSING-002`.
- Bounded ephemeral execution lifecycle: `data/reusable-task-ephemeral-construct-contract.json`.
- Publisher projection: `RTC-PUBLISHER-005`.
- StegVerse egress: `RTC-STEGVERSE-EGRESS-007`.
- Governed transport/admission: `RTC-INTERLOCK-INTR-TRANSPORT-008`.
- Evidence custody/reconstruction: `RTC-EVIDENCE-CUSTODY-004` with Master Records.

Not selected: fresh manifest intake, generic provider/framework round trip, SDK return assembly, and far-side final transition. TV/TVC credential/session issuance remains conditional on the publication runtime actually requiring it.

## Authority separation

- Task Registry: coordination only.
- Reusable task identities/components: non-authorizing composition and bounded orchestration only.
- WorkerCoordinator: fresh claim/fence authority.
- Interlock/InTr: state-transition/admission authority.
- TV/TVC: credential/provider/release authority when required.
- KV/SKAP Vault: sole user-verification authority.
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

All remain false until authentic evidence exists. Reusable-task registration or source validation does not promote them.

## Duplicate orchestration superseded

Do not add a task-specific connected-device gate before source refresh, source refresher, runtime observer, generic InTr transport/admission adapter, hosted runtime fallback, or second user-operated-device path.

## Next admissible work

Trigger `RT-SOVEREIGN-SOURCE-REFRESH-001` for this Goal Task with the already-local canonical source root and existing sovereign runtime root. Consume its authentic completion or boundary receipt. Only after an authentic source-refresh completion receipt exists may dependent WorkerCoordinator claim/fence and exact-materialization processing advance.
