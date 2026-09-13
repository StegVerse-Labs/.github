# KV-Bound Ephemeral Browser Projection — Reusable Task Component Reconciliation

Updated: 2026-09-12

Goal Task ID: `KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001`
COSV: `50000010100000`
Runtime handoff: `docs/KV_BOUND_EPHEMERAL_BROWSER_PROJECTION_MIRROR_HANDOFF.md`
Status: `ACTIVE / GOAL IDENTITY PRESERVED / COMPONENTIZATION MERGED AND VALIDATED / RUNTIME TRUTH UNCHANGED`

## Canonical model and merge state

The Reusable Task Component Model is canonical through `.github` PR #1652 at merge commit `b9f8e5153aa1651f2d7f043fb902eacb7c113ed9`.

This Goal Task's reconciliation merged through `.github` PR #1679 at merge commit:

```text
f76bc12fcb516e68f3acf9ec5b6252e526478bbe
```

Exact reconciliation head:

```text
d66c8832de479b33473cdfd447d1bf0efa9b1689
```

Exact-head validation passed before merge:

```text
organization control                 34731043513 PASS
deterministic repository suite       34731043374 PASS
Heartbeat/repository validation      34731043427 PASS
```

Deterministic decomposition score: `30`.
Disposition: `STOP_SCOPE_GROWTH_AND_DECOMPOSE_BEFORE_ADDING_MORE_TASK_SPECIFIC_ORCHESTRATION`.

This changes implementation composition only. It does not restart, rename, duplicate, close, or complete the Goal Task, and it does not change COSV continuity or runtime truth.

## Goal Task -> reusable components -> owners -> evidence

Only capabilities actually required by this goal are selected.

### Execution materialization

Existing reusable family: `data/reusable-task-ephemeral-construct-contract.json`.

Task-specific inputs are TASK-2026-0011 G7/fence7 continuity, current-device KV state, and the frozen Site TestFlight source commitments. The existing same-device wrapper and frozen bootstrap consume these inputs; they are composition surfaces, not new reusable orchestration owners.

Expected evidence is the authentic KV projection/admission result, exact source validation, and an authentic signing result or exact fail-closed result. WorkerCoordinator retains claim/fence authority; this family is non-authorizing.

### Governed ingress and transport

Existing canonical owner: Interlock/InTr.

`RTC-INTERLOCK-INTR-TRANSPORT-008` is selected for the Device->KV transition and reused for the already-established current-iPhone->TVC governed path as required by the existing TVC sequence.

Inputs are purpose-bound requests and prior component evidence. Outputs are governed transition/transport receipts. Failure remains local to the failed component instance and may be re-entered only after its precondition is restored.

### Manifest binding

Existing component: `RTC-MANIFEST-001`.

It binds Goal Task/COSV, TASK-2026-0011 G7/fence7 lineage, frozen source identity, and required evidence declarations. It grants no authority.

### Provider round trips and credential/session handling

Existing transport component: repeatable `RTC-ROUNDTRIP-003`.
Existing credential/provider/release owner: TV/TVC.
Existing task-specific translator: the current-iPhone TVC provider client under the established provider-operation protocol.

The number of provider round trips is determined by the existing TVC reconciliation sequence; no maximal chain is forced when fewer operations are sufficient. Each round trip requires its own correlated authentic result. The translator does not inherit TV/TVC or Interlock/InTr authority and must not grow generic credential, transport, retry, or release orchestration.

### Evidence validation

Existing Site/TVC validators are reused for purpose/schema parity, frozen-byte/hash checks, provider-result correlation, signing-result checks, and runtime-result classification. Validation grants no authority and may not upgrade source/CI/publication evidence into runtime evidence.

### Far-side final transition

Existing component: `RTC-FARSIDE-FINAL-009`, selected only for the final TestFlight release/install transition. TV/TVC remains release authority. A component receipt does not authorize the following runtime observation.

### Runtime observation

Existing owners/surfaces are reused: authentic established-current-iPhone observation and the existing TVC runtime observation owner. Runtime observation is evidence only and does not mint authority.

### Evidence custody and reconstruction

Existing component: `RTC-EVIDENCE-CUSTODY-004`.
Canonical owner: Master Records.

Inputs are the authentic claim/fence, KV admission/projection evidence, provider-operation chain, signing/release evidence, and same-device runtime observation. Completion requires Master Records custody acceptance and same-execution reconstruction confirmation.

## Components intentionally not selected

- separate governed-processing stage;
- Publisher projection;
- SDK return assembly;
- unrelated StegVerse final-egress transition;
- asynchronous callback-correlation plane;
- new general release-propagation component.

Public Site product and same-device-wrapper propagation are already satisfied historical evidence and are not replayed as active runtime components.

## Existing components reused

- `data/reusable-task-ephemeral-construct-contract.json`;
- `data/reusable-transport-component-contract.json`;
- existing Device->KV Interlock/InTr implementation;
- existing current-iPhone->TVC governed path;
- existing TV/TVC provider runtime and TV/TVC-owned credential/session/release path;
- existing current-iPhone TVC translation adapter;
- existing Site/TVC evidence validators;
- existing TVC runtime observer;
- Master Records custody/reconstruction.

No genuinely new reusable component is required by this Goal Task.

## Bespoke orchestration superseded as ownership

Historical source and evidence remain preserved. These task-specific surfaces are configuration/provenance surfaces and must not grow into generic orchestration owners:

- `StegVerse-Labs/Site:task0011-same-device-kv-recovery.html` -> same-device task composition/rendezvous;
- `StegVerse-Labs/Site:stegos-bootstrap/current-iphone-testflight-bootstrap.js` -> frozen task-specific execution composition;
- `StegVerse-Labs/Site:stegos-bootstrap/current-iphone-tvc-provider-client.js` -> provider-specific translation under the existing governed TVC protocol;
- `StegVerse-Labs/Site:stegos-bootstrap/current-iphone-testflight.html` -> historical saved-file entrypoint, superseded as the normal runtime-resolution surface by same-device recovery;
- retired TASK-2026-0011 one-shot binary relay -> historical exact-byte transport evidence only.

No historical evidence is deleted.

## Authority invariants

- Task Registry: coordination only.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: governed transition/admission authority.
- TV/TVC: credential/provider/release authority.
- KV/SKAP Vault: sole user-verification authority.
- StegOS devices: interchangeable transport/execution nodes; user-verification authority `NONE`.
- Master Records: observed-reality custody and reconstruction authority.
- HeartBeat: synchronization, timing, freshness, liveness, state correlation, and observability only.
- GitHub: source/evidence coordination only; runtime authority `NONE`.

## Remaining Goal Task predicates

Componentization does not complete them. Authentic evidence remains required for:

- current-iPhone same-device execution;
- Device->KV InTr admission and verified KV state for this execution;
- the bounded TV/TVC provider/release sequence actually required by this execution;
- final TestFlight release/install observation;
- retained same-device StegOS/StegBrowser runtime observation;
- Master Records custody acceptance and same-execution reconstruction;
- return to the frozen global runtime measurement using authentic evidence only.

## Next admissible work

The reconciliation itself is merged and source-validated. Normal Goal Task execution resumes through the existing public same-device runtime surface. Any authentic fail-closed result must be classified to the owning reusable component and remediated there; do not create parallel task-specific transport, session, adapter, retry, runtime, or custody machinery.

Do not synthesize evidence, require a second user-operated device, or introduce device-local user verification.

## README impact

The `.github` root README already contains the canonical Reusable Task Component Model projection from PR #1652. This goal-specific reconciliation does not materially change repository-wide function, so no additional root README mutation is required.
