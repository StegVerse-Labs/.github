# KV-Bound Ephemeral Browser Projection — Reusable Task Component Reconciliation

Updated: 2026-09-12

Goal Task ID: `KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001`
COSV: `50000010100000`
Runtime handoff: `docs/KV_BOUND_EPHEMERAL_BROWSER_PROJECTION_MIRROR_HANDOFF.md`
Status: `ACTIVE / GOAL IDENTITY PRESERVED / COMPONENTIZATION REQUIRED / RUNTIME TRUTH UNCHANGED`

## Canonical model

The Goal Task is reconciled against the Reusable Task Component Model merged through `.github` PR #1652 at `b9f8e5153aa1651f2d7f043fb902eacb7c113ed9`.

Deterministic decomposition score: `30`.
Disposition: `STOP_SCOPE_GROWTH_AND_DECOMPOSE_BEFORE_ADDING_MORE_TASK_SPECIFIC_ORCHESTRATION`.

This changes composition, not Goal Task identity, COSV continuity, or runtime evidence.

## Selected reusable composition

Only capabilities actually required by this goal are selected:

1. `execution_materialization` through the existing reusable ephemeral-construct contract and frozen current-iPhone Site surfaces.
2. `governed_ingress` through the existing Device->KV Interlock/InTr path used by same-device recovery.
3. `RTC-MANIFEST-001` for task/COSV/source/evidence binding.
4. `RTC-INTERLOCK-INTR-TRANSPORT-008` for Device->KV and the existing current-iPhone->TVC governed path; the latter may repeat with the required TVC sequence.
5. `RTC-ROUNDTRIP-003` repeated only as required by the existing TVC sequence.
6. `credential_session` through the existing TV/TVC-owned session/custody implementation; no new session owner is introduced.
7. `framework_provider_adapter` through the existing current-iPhone TVC adapter as task-specific translation only.
8. `evidence_validation` through the existing Site and TVC validators.
9. `runtime_observation` through authentic current-iPhone observation plus the existing TVC runtime observer.
10. `RTC-FARSIDE-FINAL-009` for the final TestFlight release/install transition.
11. `RTC-EVIDENCE-CUSTODY-004` with Master Records as observed-reality custody/reconstruction owner.

Not selected as new active work: Publisher projection, SDK return assembly, separate governed-processing stage, callback-correlation plane, or a new general release-propagation component. Public Site publication is already satisfied evidence and must not be replayed as runtime work.

## Existing components reused

- `data/reusable-task-ephemeral-construct-contract.json`
- `data/reusable-transport-component-contract.json`
- existing Device->KV Interlock/InTr implementation
- existing TVC provider runtime and TVC-owned session/custody path
- existing current-iPhone TVC translation adapter
- existing Site projection/source/result validators
- existing TVC runtime observation owner
- Master Records custody/reconstruction

No genuinely new reusable component is required by this Goal Task.

## Bespoke orchestration reclassification

Historical source and evidence remain preserved. These task-specific surfaces must not grow into generic orchestration owners:

- `StegVerse-Labs/Site:task0011-same-device-kv-recovery.html` -> task-specific composition/rendezvous surface;
- `StegVerse-Labs/Site:stegos-bootstrap/current-iphone-testflight-bootstrap.js` -> frozen task-specific execution composition;
- `StegVerse-Labs/Site:stegos-bootstrap/current-iphone-tvc-provider-client.js` -> task-specific translator under the existing governed TVC protocol;
- `StegVerse-Labs/Site:stegos-bootstrap/current-iphone-testflight.html` -> historical file-selection entrypoint, superseded as the normal runtime-resolution path by same-device recovery;
- retired TASK-2026-0011 one-shot binary relay -> historical exact-byte transport evidence only, not a reusable runtime.

No historical evidence is deleted.

## Authority model

- Task Registry: coordination only.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: governed transition/admission authority.
- TV/TVC: credential/provider/release authority.
- KV/SKAP Vault: sole user-verification authority.
- StegOS devices: interchangeable transport/execution nodes; user-verification authority `NONE`.
- Master Records: observed-reality custody and reconstruction authority.
- HeartBeat: synchronization, timing, freshness, liveness, state correlation, and observability only.
- GitHub: source/evidence coordination only; runtime authority `NONE`.

## Session work classification

Reusable component implementation:
- none newly created; canonical existing components are reused.

Goal-specific configuration:
- TASK-2026-0011 G7/fence7 binding;
- current-iPhone TestFlight projection purpose;
- frozen source/product commitments;
- same-device execution requirement.

Goal-specific evidence predicates already satisfied:
- authentic TASK-2026-0011 G7/fence7 allocation;
- exact frozen Site product merge/publication;
- same-device recovery merge/publication.

Canonical authority invocation:
- WorkerCoordinator claim/fence remains retained evidence;
- future governed transition and TVC release operations remain pending authentic invocation.

Runtime observation:
- `TESTFLIGHT_CURRENT_IPHONE_RUNTIME_OBSERVED` remains unresolved.

Duplicate/obsolete orchestration:
- retired one-shot binary relay;
- saved-file selection flow superseded as normal path by same-device recovery;
- task-specific wrapper/bootstrap/adapter are retained only as parameterized composition surfaces.

Unresolved dependency:
- authentic current-iPhone execution through the existing component composition.

Genuinely novel capability:
- none.

## Remaining Goal Task predicates

Componentization does not complete them. The Goal Task still requires authentic evidence for:

- current-iPhone same-device execution;
- Device->KV InTr admission and verified KV state for this execution;
- successful bounded TVC sequence for this execution;
- final TestFlight release/install observation;
- retained same-device StegOS/StegBrowser runtime observation;
- Master Records custody acceptance and same-execution reconstruction;
- return to the frozen global runtime measurement with authentic evidence only.

## Next admissible work

Do not add new task-specific transport, session, adapter, retry, or evidence-custody machinery.

Continue through the existing public same-device runtime surface and classify any authentic fail-closed result by the owning reusable component. Repair only that owner/component when machine-admissible. Do not synthesize runtime evidence, require a second user-operated device, or introduce device-local user verification.

## README impact

The `.github` root README already contains the canonical Reusable Task Component Model projection from PR #1652. This goal-specific reconciliation does not materially change repository-wide function, so no additional root README mutation is required.
