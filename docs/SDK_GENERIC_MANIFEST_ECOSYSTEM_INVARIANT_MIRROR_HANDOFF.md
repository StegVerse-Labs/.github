# SDK Generic Manifest Ecosystem Invariant — Mirror Handoff

Updated: 2026-09-12
Goal Task ID: `SDK-GENERIC-MANIFEST-ECOSYSTEM-INVARIANT-005`
Parent Task ID: `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003`
COSV ID: `71000000100110`
Issue: `StegVerse-Labs/.github#1615`
Status: `ACTIVE / ARCHITECTURAL VALIDATION + REMEDIATION`

## System-wide invariant under validation

Every StegVerse processing action is manifest-driven. Processing semantics are selected only by an admitted manifest's declared `processing.capability` bound to `processing.route_id` and an installed admissible route.

Source identity, provider identity, framework identity, adapter identity, transport identity, model identity, subsystem identity, response class, file type, or prior result may contribute provenance/policy evidence but MUST NOT independently select processing semantics.

Adapters may translate protocol/framing and preserve source-native artifacts, but MUST delegate processing selection into the canonical SDK manifest ingress/route-resolution machinery. Adapters MUST NOT create parallel processor-selection, governance, custody, credential, or routing authority.

## Why this task exists

A conversational failure mode exposed an architectural validation gap: assertions about ecosystem invariants were accepted and repeated before checking canonical implementation surfaces. This task makes architectural-claim validation explicit and repairs discovered implementation skew.

The predecessor task `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003` retired at prompt ceiling with `DOWNSTREAM_PROPAGATION_COMPLETE` still unresolved. This task continues that unresolved architectural portion; it does not resurrect the retired task.

## Evidence observed at task creation

### PASS — SDK generic manifest contract

`StegVerse-org/StegVerse-SDK/stegverse/manifest_contract.py`
- requires non-empty `processing.capability`;
- requires non-empty `processing.route_id`;
- rejects route-id mismatch.

`StegVerse-org/StegVerse-SDK/stegverse/governance_ingress_runtime.py`
- compares `processing.route_id` with resolved route;
- compares `processing.capability` with resolved route processor capability;
- fails closed on mismatch.

### VIOLATION / architectural skew — LLM Adapter governed ingress

`StegVerse-org/LLM-adapter/llm_adapter/governed_manifest_ingress.py`
- accepts an injected `governance_handler`;
- directly invokes `governance_handler(canonical_manifest)`;
- therefore the adapter surface is governance-hardwired rather than delegating generic processor selection through canonical SDK route resolution.

### VIOLATION / architectural skew — Site MIR return adapter

`StegVerse-Labs/Site/assets/mir-accounting-return-v1.js`
- hardwires `RESPONSE_CLASS = MIR_HISTORICAL_ACCOUNTING`;
- hardwires `PROFILE_NAME = SDK:EvaluatorReviewIngress`;
- hardwires the `evaluator-read-review` route before generic SDK manifest processing;
- therefore MIR source/response class currently predetermines processor destination.

### PARTIAL / requires boundary classification — TVC MIR provider broker

TVC correctly constrains credentials/provider operations, but the MIR provider-specific operation profile must be examined to distinguish credential/transport admission from processing-semantic selection. Provider-operation constraints may remain provider-specific, but they MUST NOT replace canonical manifest-declared processing selection for ecosystem processing.

## Required inventory

Classify representative surfaces as `PASS`, `PARTIAL`, `VIOLATION`, or `NOT_PROVEN`:

1. StegVerse SDK manifest ingress + processor registry/runtime.
2. LLM Adapter manifest ingress/egress.
3. Site external-return adapters including MIR.
4. TVC provider-operation broker and provider profiles.
5. StegCore manifested transaction/governance entry.
6. StegOS/Continuity resident dispatcher and InTr materialization entry.
7. Master Records custody/reconstruction interfaces.
8. Shared-document/external-collaboration ingestion.
9. Provider/framework adapters including Elyria and future integrations.
10. Session-originated execution boundary, documented separately from non-session external ingress.

## Remediation contract

For every VIOLATION:

```text
source-native external/internal artifact
-> canonical stegverse.ingress-manifest.v1 admission/canonicalization
-> processing.capability
-> processing.route_id
-> installed-route resolution/admissibility
-> processor-specific route
-> canonical transitions/custody/receipts
-> return projection
```

No adapter may replace the middle four steps with source/type/provider-specific processor selection.

## Architectural-claim validation gate

Before declaring a StegVerse architectural rule already system-wide, require:

1. canonical contract/task/handoff evidence;
2. implementation evidence from the owning core surface;
3. search of representative downstream adapters/consumers for contradictory routing behavior;
4. explicit counterexample search;
5. runtime evidence when the claim concerns enforcement rather than source construction;
6. classification as `PROVEN`, `PARTIAL`, `CONTRADICTED`, or `NOT_PROVEN`.

A user assertion or conversational correction is an architectural hypothesis until this gate is satisfied. It may guide the investigation but MUST NOT be reported as existing ecosystem fact without evidence.

## Completion predicates

- ecosystem inventory completed across required surfaces;
- all discovered source/type/provider-driven processor-selection violations remediated or explicitly blocked/fail-closed;
- LLM Adapter delegates processing selection to canonical SDK machinery;
- MIR return enters canonical SDK manifest ingress before route selection;
- regression tests detect capability/route mismatch and direct identity-driven routing shortcuts;
- downstream propagation evidence reconciled with predecessor task;
- representative runtime evidence demonstrates canonical manifest-driven route resolution on at least one non-governance and one governance path;
- no claim of system-wide enforcement until all predicates above are satisfied.

## Authority boundaries

- SDK manifest/processor contract: processing declaration + route-resolution contract owner.
- Interlock/InTr: transition transport/admission, not processor-selection authority.
- TV/TVC: credential authority, not processor-selection authority.
- Adapters: protocol/framing only.
- StegCore/other processors: execute only after admitted manifested route selection.
- GitHub Actions: validation/evidence transport only; runtime authority NONE.
- Heartbeat: observability only.

## Next continuation

1. Complete repo-wide evidence inventory.
2. Patch LLM Adapter hardwired governance ingress to delegate to canonical SDK route resolution without breaking governance compatibility.
3. Patch MIR return path so source-native MIR artifact is first represented by canonical SDK ingress manifest; evaluator-read-review becomes a manifest-selected route for the current test, not a source-derived route.
4. Add cross-repository regression evidence and reconcile canonical task record.
