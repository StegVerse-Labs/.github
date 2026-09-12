# SDK Elyria Interlock/InTr Adapter Mirror Handoff

Updated: 2026-09-12
Repository: `StegVerse-Labs/.github`
Goal Task ID: `SDK-ELYRIA-INTR-ADAPTER-001`
COSV: `71000000100112`
Status: `ACTIVE / FRAMEWORK-SIDE ADAPTER DERIVATION STARTED`

## Purpose

Derive the Elyria/Veritas-Aegis framework-side translation required to communicate with the already-established StegVerse SDK + Interlock/InTr governed path. This task must reuse the existing generalized evaluator/manifest, processor routing, governed ingress/egress, receipt, MIR, and Master Records processes. It must not create a new StegVerse protocol, transition authority, transport authority, receipt system, runtime dispatcher, scheduler, credential route, or custody system.

## Reusable-task basis

Canonical reusable identity:

```text
RT-EXTERNAL-ADAPTER-ESTABLISH-001
```

Its rule applies directly: the adapter is the endpoint-specific translation layer on the external side of an established Interlock/InTr boundary and has `NONE_TRANSLATION_ONLY` authority effect.

No `RT-INTR-PROTOCOL-ESTABLISH-001` derivation is presently required because the existing generalized evaluator path already provides the normalized StegVerse side:

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
- `StegVerse-org/StegVerse-SDK:stegverse/llm_adapter_bridge.py` as a strict identity/authority-preserving adapter pattern
- `StegVerse-org/StegVerse-SDK:ADAPTER_SYSTEM_BOUNDARY_FIXTURE_MIRROR_HANDOFF.md` as a direct external-packet preservation pattern
- `StegVerse-Labs/.github:data/reusable-task-registry.json#RT-EXTERNAL-ADAPTER-ESTABLISH-001`

## Novel scope only

The only new implementation surface is the Elyria framework side:

1. translate a normalized/manifested StegVerse external-framework request into the public Elyria Admission Runtime movement shape;
2. preserve transition/run/source identity across the call;
3. normalize Elyria `ADMIT`, `HOLD`, `REFUSE`, and `NO_PROVABLE_ADMISSION` as foreign framework observations, never as InTr authority;
4. preserve Elyria receipt, replay, no-bind, route-closure, and downstream-effect evidence without promoting asserted fields into StegVerse-observed fact;
5. fail closed on identity mismatch, unsupported verdict, malformed evidence, or attempted authority escalation;
6. return the normalized foreign-evidence result through the existing StegVerse governed return path.

## Elyria public evidence boundary

Publicly inspectable Elyria surfaces support movement assessment, receipts, replay, and no-bind evidence. Public material does not expose the private production Veritas substrate. Therefore this task may prove public-framework protocol compatibility and bounded conformance only; it must not claim production Veritas substrate interoperability, route closure, or production enforcement without authentic evidence.

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

## Initial acceptance predicates

```text
EXISTING_STEGVERSE_GOVERNED_PATH_REUSED
NO_DUPLICATE_INTR_PROTOCOL_CREATED
ELYRIA_REQUEST_TRANSLATION_BOUND
ELYRIA_RESPONSE_TRANSLATION_BOUND
TRANSITION_AND_RUN_IDENTITY_PRESERVED
ELYRIA_VERDICT_REMAINS_NON_AUTHORIZING
ELYRIA_RECEIPT_REPLAY_NOBIND_EVIDENCE_PRESERVED
ROUTE_CLOSURE_ASSERTION_DISTINGUISHED_FROM_STEGVERSE_OBSERVATION
FAIL_CLOSED_IDENTITY_AND_SCHEMA_TESTS_PASS
README_AND_HANDOFF_CURRENT
AUTHENTIC_TWO_WAY_PUBLIC_ELYRIA_TRANSPORT_EVIDENCE_NOT_CLAIMED_UNTIL_OBSERVED
```

## Immediate implementation sequence

1. Reuse the existing SDK adapter bridge pattern rather than creating a new transport stack.
2. Add only the Elyria public-framework codec/binding and framework-specific fixtures/tests in `StegVerse-org/StegVerse-SDK`.
3. Keep transport dependency-injected so source validation can run without inventing hosted runtime authority.
4. Exercise deterministic fake-transport fixtures first for request/response/error semantics.
5. Add authentic public Elyria round-trip evidence only when an actual external endpoint execution is observed; source tests alone must not claim it.
6. Maintain the SDK README and this handoff with exact evidence.

## Current proof boundary

```text
reusable external-adapter identity: FOUND / REUSE REQUIRED
generalized evaluator ingress: EXISTING
processor/route resolution: EXISTING
Interlock/InTr governed ingress/egress: EXISTING / REUSE REQUIRED
strict adapter identity/authority pattern: EXISTING
Elyria framework-side binding: NOT YET IMPLEMENTED
authentic Elyria round trip: NOT YET OBSERVED
production Veritas substrate interoperability: NOT CLAIMED
```

## Manual work

None.
