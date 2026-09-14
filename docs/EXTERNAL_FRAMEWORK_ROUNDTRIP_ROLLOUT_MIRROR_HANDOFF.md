# External Framework Round-Trip Rollout Mirror Handoff

Updated: 2026-09-14

Parent Goal Task ID: `MIR-CONNECTION-ROUNDTRIP-TECHNICAL-GUIDE-001`
Parent COSV: `50000000100000`
Canonical parent issue: `StegVerse-Labs/Site#1277`
Canonical parent handoff: `StegVerse-Labs/Site/docs/MIR_CONNECTION_ROUNDTRIP_TECHNICAL_GUIDE_MIRROR_HANDOFF.md`
Reusable Task ID: `RT-EXTERNAL-FRAMEWORK-ROUNDTRIP-ROLLOUT-001`
Base source merge: `49692b2fe410053fc1b0b83a7d27c39fca887d27`
Elyria conformance merge: `204ae5c26520a33418a805da702a627640a85017`
Registry-wide planner merge: `126e1e5833b93febd5aae13529b60cfa2712b6f9`
Admissibility-wiki binding-registry merge: `296de27727418e3871af1787890403ed4eeb7c61`
Admissibility-wiki binding handoff reconciliation merge: `713841a2ef783751c45fab3fdaae72f0f5746e27`
Admissibility-wiki evidence-qualified endpoint merge: `5d3baaeb3175a06ff046826df9e10a2958fb1fe2`
Status: `SOURCE COMPLETE / EVIDENCE-QUALIFIED ENDPOINT PLANNER REPAIR REMATERIALIZED FROM CURRENT MAIN / EXACT-HEAD VALIDATION PENDING`

## Purpose

Apply the MIR-proven connection/round-trip architecture as one reusable registry-driven capability across canonical admissibility-wiki external frameworks without creating per-framework transport, custody, scheduler, WorkerCoordinator, credential, user-verification, or Goal Task implementations.

The parent MIR Goal remains authoritative for MIR runtime transition truth. This reusable rollout is coordination/source logic until an actual governed invocation causes transitions.

## Composition and authority

Required reusable components remain `RT-EXTERNAL-ADAPTER-ESTABLISH-001`, `RTC-MANIFEST-001`, `RTC-GOVERNED-PROCESSING-002`, `RTC-ROUNDTRIP-003`, `RTC-EVIDENCE-CUSTODY-004`, `RTC-SDK-RETURN-006`, `RTC-STEGVERSE-EGRESS-007`, and `RTC-INTERLOCK-INTR-TRANSPORT-008`. `RTC-PUBLISHER-005` and `RTC-FARSIDE-FINAL-009` remain conditional.

Task Registry is coordination only; WorkerCoordinator owns claim/fence; Interlock/InTr owns governed admission/state transitions; TV/TVC owns credentials/provider release; KV/SKAP Vault is sole user-verification authority; Master Records owns observed-reality custody/reconstruction; external adapters translate only; GitHub/source/CI grants no runtime authority.

## Evidence-qualified endpoint invariant

Admissibility-wiki PR `#140` merged the canonical endpoint evidence contract. A runtime endpoint may be considered bound only when all four fields are present:

```text
runtime_endpoint_ref
endpoint_evidence_ref
endpoint_observed_at
endpoint_evidence_class
```

Documentation/source URLs must not be inferred as runtime endpoints. Bare endpoint strings, endpoint-only objects, orphan evidence, invalid objects, and unbound entries fail closed.

The merged `.github` registry planner still accepted weaker bare or endpoint-only input. Branch `external-framework-evidence-qualified-planner-v3`, created from current `main` after stale PRs `#1806` and `#1807` were superseded without merge, closes that cross-repository bypass without carrying unrelated control-plane changes.

The planner records one binding state per framework: `EVIDENCE_QUALIFIED_ENDPOINT_BOUND`, `UNBOUND_NO_RUNTIME_ENDPOINT_REF`, `UNQUALIFIED_ENDPOINT_REJECTED`, `ORPHAN_ENDPOINT_EVIDENCE_REJECTED`, or `INVALID_ENDPOINT_BINDING`. Only an evidence-qualified endpoint can feed runtime-roundtrip eligibility. Source-crosswalk operations remain independent of endpoint availability.

Framework invocation eligibility remains `ROUNDTRIP_ELIGIBLE`, `SOURCE_ONLY`, `TRANSLATION_ONLY`, `RUNTIME_ENDPOINT_UNAVAILABLE`, `UNSUPPORTED_OPERATION_CLASS`, or `REGISTRY_ENTRY_INVALID`. One failing framework remains isolated to that invocation.

## Runtime truth

Executed transitions are runtime truth at their recorded provenance. Source, CI, merge, registry entries, endpoint metadata, or a successful plan do not prove endpoint authenticity, availability, admission, execution, return, SDK processing, custody, or final egress.

The real admissibility-wiki endpoint overlay remains intentionally empty until independently observed current endpoint evidence exists.

## README review

The root README already defines reusable-task/component composition, bounded invocation semantics, authority separation, and reuse-over-bespoke orchestration. No README mutation is required for this bounded planner input-contract repair.

## Completion boundary

This source continuation completes only after exact-head repository validation passes and the current-main repair merges. Runtime completion remains invocation-specific.

After source completion, generate the canonical source-crosswalk sweep across all registry identities and preserve explicit source-only/translation-only/runtime-unavailable outcomes. Runtime roundtrip is permitted only for the independently evidence-qualified subset. Continue the parent MIR retained-return delivery and downstream SDK/Master Records/Publisher/egress transitions independently.

## Manual work

None.
