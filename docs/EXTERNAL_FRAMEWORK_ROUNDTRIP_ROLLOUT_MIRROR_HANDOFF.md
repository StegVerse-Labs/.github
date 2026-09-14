# External Framework Round-Trip Rollout Mirror Handoff

Updated: 2026-09-13

Parent Goal Task ID: `MIR-CONNECTION-ROUNDTRIP-TECHNICAL-GUIDE-001`
Parent COSV: `50000000100000`
Canonical parent issue: `StegVerse-Labs/Site#1277`
Canonical parent handoff: `StegVerse-Labs/Site/docs/MIR_CONNECTION_ROUNDTRIP_TECHNICAL_GUIDE_MIRROR_HANDOFF.md`
Tracking issue: `StegVerse-Labs/.github#1800` (source-completion issue closed)
Reusable Task ID: `RT-EXTERNAL-FRAMEWORK-ROUNDTRIP-ROLLOUT-001`
Base source merge: `49692b2fe410053fc1b0b83a7d27c39fca887d27`
Elyria conformance merge: `204ae5c26520a33418a805da702a627640a85017`
Source-completion handoff merge: `1cd03b9e1b1b07c9324091f3af99265c78e53c68`
Registry-wide planner merge: `126e1e5833b93febd5aae13529b60cfa2712b6f9`
Admissibility-wiki binding-registry merge: `296de27727418e3871af1787890403ed4eeb7c61`
Admissibility-wiki binding handoff reconciliation merge: `713841a2ef783751c45fab3fdaae72f0f5746e27`
Admissibility-wiki evidence-qualified endpoint merge: `5d3baaeb3175a06ff046826df9e10a2958fb1fe2`
Status: `SOURCE COMPLETE / REGISTRY-WIDE PLANNER MERGED / BINDING REGISTRY MERGED / EVIDENCE-QUALIFIED ENDPOINT ENFORCEMENT REMATERIALIZED ON CURRENT MAIN FOR VALIDATION`

## Purpose

Apply the MIR-proven external connection/round-trip architecture as one reusable registry-driven capability across external frameworks represented in the canonical `StegVerse-Labs/admissibility-wiki` registry without creating per-framework transport, custody, scheduler, WorkerCoordinator, credential, or user-verification implementations.

The parent MIR Goal remains authoritative for MIR-specific transition truth and completion. The reusable rollout is composition/coordination only until a governed invocation actually causes transitions.

## Reused component composition

Required components:

- `RT-EXTERNAL-ADAPTER-ESTABLISH-001`
- `RTC-MANIFEST-001`
- `RTC-GOVERNED-PROCESSING-002`
- `RTC-ROUNDTRIP-003`
- `RTC-EVIDENCE-CUSTODY-004`
- `RTC-SDK-RETURN-006`
- `RTC-STEGVERSE-EGRESS-007`
- `RTC-INTERLOCK-INTR-TRANSPORT-008`

Conditional components:

- `RTC-PUBLISHER-005` where publication/presentation evidence is required;
- `RTC-FARSIDE-FINAL-009` where the foreign system exposes a distinct terminal transition.

MIR remains the reference transition profile. `SDK-ELYRIA-INTR-ADAPTER-001` is the first non-MIR conformance profile.

## Runtime truth and provenance

Executed transitions are runtime truth at their recorded provenance. Mirror/build-test execution is real execution with bounded counterpart provenance; it is not authentic external endpoint substitution. Source, CI, merge, documentation, registry state, and endpoint metadata do not prove a transition that did not occur.

## Registry-wide planning

`.github` PR `#1805` merged the registry-wide planner as `126e1e5833b93febd5aae13529b60cfa2712b6f9` after exact-head Organization Control, Deterministic Repository Suite, and Heartbeat validation passed.

`scripts/plan_external_framework_registry_rollout.py` consumes one exact registry snapshot, exact local manifests, and an optional endpoint map, then emits independent bounded plans for every framework. One ineligible framework does not block unrelated framework entries. The planner has `NONE_PLAN_ONLY` transition effect and performs no external calls.

## Canonical binding registry

`StegVerse-Labs/admissibility-wiki` PR `#137` merged one managed binding slot for every canonical external-framework identity as `296de27727418e3871af1787890403ed4eeb7c61` after full chain-continuation and Goal 5 validation passed. PR `#139` reconciled the source-complete handoff as `713841a2ef783751c45fab3fdaae72f0f5746e27`.

The endpoint overlay intentionally began empty. Documentation/source URLs were not promoted into runtime endpoints.

## Evidence-qualified endpoint invariant

Admissibility-wiki PR `#140` merged as `5d3baaeb3175a06ff046826df9e10a2958fb1fe2` after canonical chain-continuation validation passed. A bound runtime endpoint now requires all of:

```text
runtime_endpoint_ref
endpoint_evidence_ref
endpoint_observed_at
endpoint_evidence_class
```

Bare endpoint strings, missing evidence metadata, evidence without an endpoint, unknown framework IDs, and duplicate identities fail closed in the admissibility-wiki binding source.

The `.github` registry-wide planner previously still accepted a bare string or a dict containing only `runtime_endpoint_ref`. That created a cross-repository enforcement gap: a caller could bypass the evidence qualification merged in admissibility-wiki by supplying a weaker endpoint map directly to the planner.

The first repair attempt was staged as PR `#1806` on head `287fc2d723f5a6893d8589d5c387a6bcfdd2d8de`. Its three repository-wide validations failed at an unrelated Admissible-Existence control-plane defect already present in the then-current base (`SV-KV-AI-PERSISTENCE-001` missing explicit admissible-existence binding). The endpoint-planner tests were not identified as the failure source. Because main advanced with unrelated control-plane reconciliation, the exact endpoint-planner change was rematerialized on current main rather than modifying the unrelated AE lane.

Branch `external-framework-evidence-qualified-planner-v2` closes the endpoint-planner gap on current main. The planner accepts endpoint eligibility only when the same required evidence metadata is present. It records one of these binding states per framework:

```text
EVIDENCE_QUALIFIED_ENDPOINT_BOUND
UNBOUND_NO_RUNTIME_ENDPOINT_REF
UNQUALIFIED_ENDPOINT_REJECTED
ORPHAN_ENDPOINT_EVIDENCE_REJECTED
INVALID_ENDPOINT_BINDING
```

An unqualified endpoint is treated as unavailable for runtime-roundtrip classification rather than becoming `ROUNDTRIP_ELIGIBLE`. Source-crosswalk/translation-only operations remain independent of endpoint availability.

## Fail-closed framework eligibility

Framework invocation eligibility remains:

```text
ROUNDTRIP_ELIGIBLE
SOURCE_ONLY
TRANSLATION_ONLY
RUNTIME_ENDPOINT_UNAVAILABLE
UNSUPPORTED_OPERATION_CLASS
REGISTRY_ENTRY_INVALID
```

A source-blocked, unbound, unqualified, or runtime-unavailable framework stops only that invocation. No synthetic endpoint, hosted fallback, alternate transport, or per-framework Goal Task is authorized.

## Authority separation

- Task Registry: coordination only.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: governed admission/state-transition authority.
- TV/TVC: credential/provider/release authority.
- KV/SKAP Vault: sole user-verification authority.
- Master Records: observed-reality custody/reconstruction authority.
- External framework adapters: translation only; foreign verdicts never become StegVerse authority merely by transport.
- GitHub/source/CI: source/evidence coordination only; runtime authority `NONE`.

## README review

The `.github` root README already documents reusable-task composition, bounded invocation semantics, authority separation, and reuse-over-bespoke-orchestration. This continuation tightens one planner input contract and requires no root README mutation.

## Completion boundary

The base rollout, non-MIR conformance proof, registry-wide planner, canonical framework binding registry, and admissibility-wiki evidence-qualified endpoint source are merged. This continuation is complete when `.github` exact-head validation on current main confirms the planner cannot bypass endpoint evidence qualification and the rematerialized branch merges.

Runtime/transition completion remains invocation-specific. Evidence-qualified endpoint metadata permits consideration for a runtime round trip; it does not prove endpoint authenticity, availability, admission, execution, return, or downstream completion.

## Next admissible work

1. Validate branch `external-framework-evidence-qualified-planner-v2` at exact head.
2. If green, merge it without creating a new Goal Task or reusable component.
3. Populate real endpoint bindings only from independently established current observations.
4. Generate the current registry sweep and retain explicit `SOURCE_ONLY`, `TRANSLATION_ONLY`, `RUNTIME_ENDPOINT_UNAVAILABLE`, or `ROUNDTRIP_ELIGIBLE` outcomes per framework.
5. Continue the parent MIR Goal through retained-return delivery and downstream manifest-selected processing independently of registry-source completion.

## Manual work

None.
