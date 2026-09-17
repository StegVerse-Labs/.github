# Canonical Master Records state-transition custody mirror handoff

Updated: 2026-09-17
Goal Task ID: `CANONICAL-MASTER-RECORDS-STATE-TRANSITION-CUSTODY-001`
Parent Goal Task ID: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV ID: `50000000100000`
Status: `ACTIVE / CANONICAL CONTRACT MATERIALIZED / ECOSYSTEM ADOPTION PENDING`

## Correction

Master Records custody/reconstruction is not a test-only or MIR-specific diagnostic mechanism. It is a canonical consequence of governed state transition.

The canonical machine progression contract already states:

```text
observe current state
-> propose exact next transition
-> Interlock/InTr governance now
-> TV/TVC now if required
-> retain ALLOW/DENY receipt
-> ALLOW: execute/consume
-> retain execution state receipt
-> reconstruct current state
-> continue
```

This task makes the custody/reconstruction portion explicit and reusable across all StegVerse transition consumers.

## Canonical invariant

For every observed governed state transition:

```text
current governance decision
-> transition occurs or fails closed
-> canonical transition/state receipt is retained
-> exact receipt is submitted to Master Records
-> Master Records retains and reconstructs current state
-> only then may the next machine-owned governed transition advance
```

Decision receipts, execution-state receipts, and fail-closed/failure receipts are all canonical state evidence. A missing transition is never fabricated merely to maintain a sequence.

## Separation of powers

- Interlock/InTr: transition admission/state-transition authority.
- TV/TVC: credential authority where required.
- execution surface: performs only the admitted consequence.
- Master Records: canonical observed-reality custody and reconstruction.
- Master Records does not grant transition, credential, execution, route, or governance authority.
- reconstruction cannot infer missing authorization from downstream evidence.

## MIR reconciliation

The recent MIR live-transition probe is retained only as temporary conformance/break-localization instrumentation. It must not become the architectural mechanism responsible for recording state.

MIR must consume the same canonical transition-receipt/custody path as every other StegVerse workload. Its state sequence remains useful for validating adoption, but MIR-specific monkey-patching or probe fanout is not the source of canonical custody semantics.

## Required implementation work

1. Inventory existing state-receipt emitters and Master Records custody adapters across `.github`, StegOS, Site, Interlock/InTr, and existing resident consumers.
2. Materialize one reusable canonical state-transition custody API/contract rather than task-specific packet fanout.
3. Bind Interlock/InTr decisions, execution states, and fail-closed consequences to that API.
4. Convert MIR to consume the canonical path; retain its diagnostic wrapper only for validation until equivalent canonical receipts prove every transition.
5. Validate compatibility with the historically successful StegVerse-002 event-driven route.
6. Propagate the canonical contract to other governed state-transition consumers without creating another scheduler, runtime, WorkerCoordinator, transition authority, or custody authority.

## Completion boundary

Completion requires source adoption plus authentic evidence showing a governed transition sequence where every observed state transition reaches Master Records custody/reconstruction through the canonical path. Task-specific tests alone do not satisfy runtime completion.
