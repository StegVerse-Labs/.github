# External Framework Round-Trip Rollout Mirror Handoff

Updated: 2026-09-14

Parent Goal Task ID: `MIR-CONNECTION-ROUNDTRIP-TECHNICAL-GUIDE-001`
Parent COSV: `50000000100000`
Canonical parent issue: `StegVerse-Labs/Site#1277`
Canonical parent handoff: `StegVerse-Labs/Site/docs/MIR_CONNECTION_ROUNDTRIP_TECHNICAL_GUIDE_MIRROR_HANDOFF.md`
Tracking issue: `StegVerse-Labs/.github#1800` (source-completion issue closed)
Reusable Task ID: `RT-EXTERNAL-FRAMEWORK-ROUNDTRIP-ROLLOUT-001`
Status: `SOURCE COMPLETE / REGISTRY-WIDE PLANNER MERGED / EVIDENCE-QUALIFIED ENDPOINT ENFORCEMENT MERGED / RUNTIME INVOCATIONS REMAIN EVIDENCE-GATED`

## Purpose

Use one registry-driven reusable round-trip task for external frameworks represented in the canonical `StegVerse-Labs/admissibility-wiki` external-framework registry. This surface must not create one Goal Task, transport stack, scheduler, WorkerCoordinator, credential route, custody implementation, user-verification mechanism, or runtime plane per framework.

The parent MIR handoff remains authoritative for MIR-specific runtime transition truth. This handoff owns only reusable framework-resolution/planning source state.

## Reused component composition

Required reusable components:

```text
RT-EXTERNAL-ADAPTER-ESTABLISH-001
RTC-MANIFEST-001
RTC-GOVERNED-PROCESSING-002
RTC-ROUNDTRIP-003
RTC-EVIDENCE-CUSTODY-004
RTC-SDK-RETURN-006
RTC-STEGVERSE-EGRESS-007
RTC-INTERLOCK-INTR-TRANSPORT-008
```

Conditional components remain `RTC-PUBLISHER-005` and `RTC-FARSIDE-FINAL-009` only where the consuming contract requires them. MIR is the reference profile; `SDK-ELYRIA-INTR-ADAPTER-001` is the first non-MIR conformance profile and does not create a second transport or Goal.

## Runtime truth

Executed transitions are runtime truth only at their recorded provenance. Source, CI, merge state, framework metadata, endpoint metadata, or a generated plan cannot prove an unexecuted transition or authentic foreign endpoint substitution.

## Invocation and eligibility

Each invocation binds one canonical framework identity and operation to the existing reusable task. Eligibility remains one of:

```text
ROUNDTRIP_ELIGIBLE
SOURCE_ONLY
TRANSLATION_ONLY
RUNTIME_ENDPOINT_UNAVAILABLE
UNSUPPORTED_OPERATION_CLASS
REGISTRY_ENTRY_INVALID
```

The registry-wide planner fails closed per framework invocation and never creates shared batch runtime state.

A runtime endpoint can make a sourced runtime-roundtrip invocation eligible only when the endpoint binding contains all of:

```text
runtime_endpoint_ref
endpoint_evidence_ref
endpoint_observed_at
endpoint_evidence_class
```

Bare endpoint strings, endpoint-only objects, orphan evidence, and malformed bindings fail closed. Documentation/source URLs may not be inferred as runtime endpoints. Endpoint evidence still does not prove authenticity, availability, authorization, admission, execution, or return success.

## Source and validation history

```text
.github#1801
  exact head: 8f280eb3377faabf1be84c5aec726d63ba036a5c
  org control: 34797138353 SUCCESS
  deterministic suite: 34797138357 SUCCESS
  heartbeat validation: 34797138326 SUCCESS
  merge: 49692b2fe410053fc1b0b83a7d27c39fca887d27

.github#1803
  exact head: 044eb8ffab71c27494a57a4f770bbb426846d50e
  org control: 34797282370 SUCCESS
  deterministic suite: 34797282389 SUCCESS
  heartbeat validation: 34797282383 SUCCESS
  merge: 204ae5c26520a33418a805da702a627640a85017

.github#1804
  org control: 34797389863 SUCCESS
  deterministic suite: 34797389873 SUCCESS
  heartbeat validation: 34797389860 SUCCESS
  merge: 1cd03b9e1b1b07c9324091f3af99265c78e53c68

.github#1805 — registry-wide planner
  exact head: 07ddf0f43b31fc83d159c0e805eb78089f9de6d0
  merge: 126e1e5833b93febd5aae13529b60cfa2712b6f9

.github#1811 — evidence-qualified endpoint enforcement in planner
  exact head: e39e9c4641d5d3a4f89f5d5268cc9dc28c79b3e0
  org control: 34813982926 SUCCESS
  deterministic suite: 34813982664 SUCCESS
  heartbeat validation: 34813982738 SUCCESS
  merge: ebdaab4d7b35e9b46f37bd2d187a4d4aff31622c
```

The corresponding admissibility-wiki binding registry and evidence-qualified endpoint contract are merged. Its live endpoint overlay remains intentionally empty until current independently observed endpoints map to exact canonical framework identities.

## Authority separation

Task Registry is coordination only; WorkerCoordinator owns claim/fence; Interlock/InTr owns governed transition admission; TV/TVC owns credential/provider authority; KV/SKAP Vault owns user verification; Master Records owns observed-reality custody/reconstruction; GitHub/source/CI has runtime authority `NONE`.

## No-duplication rule

Do not create a second InTr implementation, SDK return implementation, Publisher implementation, custody system, scheduler/resident executor, WorkerCoordinator, credential route, device/user-verification mechanism, or per-framework Goal Task when this reusable invocation model is sufficient.

## Completion boundary

Reusable rollout source completion is satisfied. The registry-wide planner and endpoint-evidence qualification are merged and validated. Runtime/transition completion remains invocation-specific and cannot be satisfied by this handoff or by generated plans.

## Next admissible work

1. Consume exact admissibility-wiki registry snapshots through the merged planner.
2. Preserve explicit `SOURCE_ONLY`, `TRANSLATION_ONLY`, `RUNTIME_ENDPOINT_UNAVAILABLE`, and invalid dispositions independently.
3. Keep runtime-roundtrip eligibility fail-closed until an exact framework identity has an evidence-qualified current endpoint binding.
4. Advance only eligible invocations through the existing Interlock/InTr-governed reusable component composition.
5. Continue the parent MIR Goal independently through retained-return delivery and downstream manifest-selected processing, return binding, egress, and final transitions.

## Manual work

None.
