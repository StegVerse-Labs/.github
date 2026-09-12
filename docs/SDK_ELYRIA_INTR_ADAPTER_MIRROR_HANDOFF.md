# SDK Elyria Interlock/InTr Adapter Mirror Handoff

Updated: 2026-09-12
Repository: `StegVerse-Labs/.github`
Goal Task ID: `SDK-ELYRIA-INTR-ADAPTER-001`
COSV: `71000000100112`
Status: `ACTIVE / REUSABLE EXTERNAL-ADAPTER DERIVATION MERGED + VALIDATED / AUTHENTIC PUBLIC ELYRIA ROUND TRIP REMAINS`

## Purpose

Derive the Elyria/Veritas-Aegis framework-side translation required to communicate with the already-established StegVerse SDK + Interlock/InTr governed path. This task reuses the existing generalized evaluator/manifest, processor routing, governed ingress/egress, receipt, MIR, and Master Records processes. It does not create a new StegVerse protocol, transition authority, transport authority, receipt system, runtime dispatcher, scheduler, credential route, or custody system.

## Reusable-task basis

Canonical reusable identity:

```text
RT-EXTERNAL-ADAPTER-ESTABLISH-001
```

Its rule applies directly: the adapter is the endpoint-specific translation layer on the external side of an established Interlock/InTr boundary and has `NONE_TRANSLATION_ONLY` authority effect.

No `RT-INTR-PROTOCOL-ESTABLISH-001` derivation was required because the existing generalized evaluator path already provides the normalized StegVerse side:

```text
external framework/test harness
-> stegverse.ingress-manifest.v1 / SDK 0B generalized evaluator surface
-> existing processor/route resolution
-> existing Interlock/InTr governed ingress
-> published processing capability
-> existing governed return
-> SDK result / retained evidence
```

Canonical reusable internal references:

- `StegVerse-org/StegVerse-SDK:docs/FORMAL_TESTING_ROUTE.md`
- `StegVerse-org/StegVerse-SDK:docs/GENERIC_MANIFEST_PROCESSING_CONTRACT.md`
- `StegVerse-org/StegVerse-SDK:stegverse/llm_adapter_bridge.py`
- `StegVerse-org/StegVerse-SDK:ADAPTER_SYSTEM_BOUNDARY_FIXTURE_MIRROR_HANDOFF.md`
- `StegVerse-Labs/.github:data/reusable-task-registry.json#RT-EXTERNAL-ADAPTER-ESTABLISH-001`

## Implemented novel framework-side scope

The merged implementation is limited to the Elyria framework side:

1. validate and preserve the documented public Elyria movement shape without synthesizing favorable authority/standing/evidence/custody fields;
2. preserve StegVerse transition/run identity around the foreign call;
3. normalize Elyria `ADMIT`, `HOLD`, `REFUSE`, and `NO_PROVABLE_ADMISSION` as foreign framework observations, never as InTr authority;
4. preserve Elyria receipt, replay, no-bind, route-closure, and downstream-effect evidence without promoting asserted fields into StegVerse-observed fact;
5. fail closed on missing identity, movement identity mismatch, returned-input mutation, unsupported verdict, malformed replay evidence, or malformed no-bind evidence;
6. use dependency-injected transport rather than creating a new internal or hosted transport plane.

Merged SDK source:

```text
StegVerse-org/StegVerse-SDK#222
exact head: aeb07d41d83c2a6ae5d84d1a2d8db5cbdc4f540b
merge: 41f7c18eaed260d36492e0dd0bcae9c232fb3c77
stegverse/elyria_framework_adapter.py
tests/test_elyria_framework_adapter.py
docs/ELYRIA_INTR_ADAPTER_MIRROR_HANDOFF.md
```

## Validation evidence

The existing `SDK Package Artifact Validation (Non-Authorizing)` workflow was reused and minimally extended to discover the Elyria adapter test; no new workflow was introduced. Final exact-head run `34709179523` succeeded. Its `Validate Elyria framework-side translation binding` step passed along with the pre-existing package/governance/build/install validation steps.

Task registration was merged separately through `StegVerse-Labs/.github#1609` at `42288fc5fece4d836e057b2675f041b99fb58d2a`. After the unrelated PA-001 registry drift was repaired by already-owned PR #1610, the refreshed registration head `43652521bff2d66326752c72bc05e84d4fe932c5` passed Deterministic Repository Suite `34709126129`, Organization Control `34709126149`, and Heartbeat Worker Project `34709126282` before merge.

## README review

`StegVerse-org/StegVerse-SDK/README.md` was reviewed. Its existing `Open testing and governed interoperability` and `Generic manifested-data processing contract` sections already describe the reusable framework-independent path correctly. No Elyria-specific internal route was added because the integration is an instance of that generic contract, not a new StegVerse communication architecture.

## Elyria public evidence boundary

Publicly inspectable Elyria surfaces support movement assessment, receipts, replay, and no-bind evidence. Public material does not expose the private production Veritas substrate. Therefore merged source proves the adapter contract and deterministic framework-side normalization only. It does not yet prove an authentic external network round trip, production Veritas substrate interoperability, Elyria route closure as independently observed fact, or production enforcement.

## Authority boundary

```text
Task Registry              = coordination only
WorkerCoordinator           = claim/fence authority
Interlock/InTr              = governed transition authority
TV/TVC                      = credential/provider/release authority
Master Records              = observed reality / reconstruction authority
Elyria/VA adapter           = NONE_TRANSLATION_ONLY
Elyria verdict              = foreign observation, never StegVerse admission authority
Elyria no-bind/closure data = foreign claim/evidence, not automatically verified closure
GitHub                      = source/validation evidence only; no runtime authority
```

## Current proof boundary

```text
reusable external-adapter identity: REUSED
new InTr protocol created: FALSE
Elyria request translation: MERGED / VALIDATED
Elyria response translation: MERGED / VALIDATED
transition/run identity preservation: MERGED / VALIDATED
Elyria verdict authority non-promotion: MERGED / VALIDATED
receipt/replay/no-bind preservation: MERGED / VALIDATED
route-closure assertion vs StegVerse observation separation: MERGED / VALIDATED
fail-closed identity/schema tests: PASS
README generic contract: REVIEWED / CURRENT
authentic public Elyria two-way transport: NOT OBSERVED
production private Veritas substrate interoperability: NOT CLAIMED
runtime activation: NOT CLAIMED
```

## Exact next sequence

1. Do not add more internal adapter architecture; source-side reusable derivation is complete.
2. Identify a genuinely reachable public Elyria endpoint or an owner-provided public execution surface matching the documented movement-assessment/replay contract.
3. Exercise the merged adapter against that external surface while preserving exact request/response bytes, transport timing, receipt identity, replay identity, and StegVerse transition/run identity.
4. Record Elyria verdict/receipt/replay/no-bind data only as foreign evidence and independently preserve Interlock/InTr admission/return receipts.
5. Only after authentic two-way evidence exists may `AUTHENTIC_TWO_WAY_PUBLIC_ELYRIA_TRANSPORT_EVIDENCE_OBSERVED` be satisfied. Private production Veritas substrate interoperability remains a separate evidence question.

## Manual work

None.
