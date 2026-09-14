# External Framework Round-Trip Rollout Mirror Handoff

Updated: 2026-09-13

Parent Goal Task ID: `MIR-CONNECTION-ROUNDTRIP-TECHNICAL-GUIDE-001`
Parent COSV: `50000000100000`
Canonical parent issue: `StegVerse-Labs/Site#1277`
Canonical parent handoff: `StegVerse-Labs/Site/docs/MIR_CONNECTION_ROUNDTRIP_TECHNICAL_GUIDE_MIRROR_HANDOFF.md`
Tracking issue: `StegVerse-Labs/.github#1800`
Reusable Task ID: `RT-EXTERNAL-FRAMEWORK-ROUNDTRIP-ROLLOUT-001`
Base source merge: `49692b2fe410053fc1b0b83a7d27c39fca887d27`
Elyria conformance merge: `204ae5c26520a33418a805da702a627640a85017`
Status: `SOURCE COMPLETE / ELYRIA NON-MIR CONFORMANCE MERGED / REGISTRY-SELECTED INVOCATION READY`

## Purpose

Convert the already-generalized MIR external connection/round-trip architecture into one registry-driven reusable task that can be invoked for external frameworks represented in the canonical `StegVerse-Labs/admissibility-wiki` external-framework registry.

The current parent MIR handoff remains authoritative for MIR-specific transition truth and completion. This reusable task generalizes framework selection and composition without creating a new execution, transition, credential, publication, custody, scheduler, WorkerCoordinator, user-verification, or runtime authority.

## Reused component composition

Required reusable components:

- `RT-EXTERNAL-ADAPTER-ESTABLISH-001`
- `RTC-MANIFEST-001`
- `RTC-GOVERNED-PROCESSING-002`
- `RTC-ROUNDTRIP-003`
- `RTC-EVIDENCE-CUSTODY-004`
- `RTC-SDK-RETURN-006`
- `RTC-STEGVERSE-EGRESS-007`
- `RTC-INTERLOCK-INTR-TRANSPORT-008`

Conditional components:

- `RTC-PUBLISHER-005` only where the framework/consumer contract requires publication/presentation evidence;
- `RTC-FARSIDE-FINAL-009` only where the foreign system exposes a distinct final-state transition that must be observed separately from the round-trip response.

MIR is the reference transition profile. `SDK-ELYRIA-INTR-ADAPTER-001` is the first non-MIR conformance profile and selects exactly the eight required components while correctly leaving Publisher and far-side-final conditional.

## Runtime truth and provenance

The rollout preserves the canonical MIR rule:

> executed transitions are runtime truth at their recorded provenance.

A bounded external-framework mirror/build-test execution is a real executed transition with its recorded counterpart provenance. It is not equivalent to authentic external endpoint substitution. Source, CI, or merge state alone does not prove an unexecuted transition.

## Invocation model

One invocation binds exactly one framework registry entry and one bounded operation to:

```text
goal_task_id
cosv_task_vector
framework_registry_ref
framework_id
framework_version_or_revision
operation_class
runtime_endpoint_ref
source_evidence_ref
counterpart_provenance
```

The invocation preserves exact task/run/framework identity across manifested intake, governed processing, outbound InTr movement, foreign response, return movement, SDK return assembly, optional Publisher projection, egress, and Master Records custody/reconstruction.

`runtime_endpoint_ref` is an invocation input, not registry authority. Supplying it makes a sourced framework eligible to attempt a round trip; it does not prove endpoint authenticity, availability, transition admission, or success.

## Canonical admissibility-wiki registry semantics

The current registry schema is `0.4`. Registry entries provide `framework_id`, status, manifest path, source reference, and bounded testbench state. Framework manifests bind source/version/boundary, claims/non-claims, transition mapping, SPE/ecosystem overlap, fail-closed conditions, and explicit authority boundaries.

The resolver consumes a local exact registry snapshot plus the exact selected manifest. It does not fetch external URLs or infer execution authority from compatibility metadata.

## Fail-closed framework eligibility

Every selected framework is classified into exactly one state:

```text
ROUNDTRIP_ELIGIBLE
SOURCE_ONLY
TRANSLATION_ONLY
RUNTIME_ENDPOINT_UNAVAILABLE
UNSUPPORTED_OPERATION_CLASS
REGISTRY_ENTRY_INVALID
```

A source-blocked or runtime-unavailable framework stops only that invocation. It does not authorize substitute endpoints, synthetic foreign responses, hosted fallback, or a new transport stack, and it does not block unrelated framework entries.

## Source and validation history

`.github` PR `#1801` added the reusable-task registry shard, deterministic resolver, bounded tests, and this handoff. Exact head `8f280eb3377faabf1be84c5aec726d63ba036a5c` passed:

- Organization Control `34797138353`;
- Deterministic Repository Suite `34797138357`;
- Heartbeat Worker Project validation `34797138326`.

It squash-merged as `49692b2fe410053fc1b0b83a7d27c39fca887d27`.

`.github` PR `#1803` then proved the non-MIR abstraction against the existing `SDK-ELYRIA-INTR-ADAPTER-001` component profile. Exact head `044eb8ffab71c27494a57a4f770bbb426846d50e` passed:

- Organization Control `34797282370`;
- Deterministic Repository Suite `34797282389`;
- Heartbeat Worker Project validation `34797282383`.

It squash-merged as `204ae5c26520a33418a805da702a627640a85017`.

The Elyria conformance proof requires no new Goal Task, no new reusable component, no duplicate Interlock/InTr protocol, and no GitHub runtime authority. It does not satisfy Elyria's separate authentic public two-way transport predicate.

## README review

The `.github` root `README.md` already documents the Reusable Task Model, Reusable Task Component Model, bounded invocation semantics, authority separation, and reuse-over-bespoke-orchestration rule. No root README mutation is required.

## Authority separation

- Task Registry: coordination only.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: governed admission/state-transition authority.
- TV/TVC: credential/provider/release authority.
- KV/SKAP Vault: sole user-verification authority.
- Master Records: observed-reality custody/reconstruction authority.
- External framework adapters: translation only; foreign verdicts/receipts never become StegVerse authority.
- GitHub/source/CI: source/evidence coordination only; runtime authority `NONE`.

## No-duplication rule

This reusable task must not create or own a second InTr transport/protocol, SDK return implementation, Publisher implementation, custody system, scheduler/resident executor, WorkerCoordinator, credential route, device/user-verification mechanism, or per-framework Goal Task when a reusable invocation is sufficient.

## Source completion boundary

All source-completion predicates for the reusable rollout are now satisfied:

1. reusable-task registry shard — merged;
2. deterministic framework-registry resolution and eligibility classification — merged;
3. plan/invocation construction bound to framework/task/run identity — merged;
4. eligible and fail-closed path tests — merged;
5. MIR reference profile plus non-MIR Elyria conformance — merged;
6. README/handoff reconciliation — complete;
7. exact-head validation — complete.

Runtime/transition completion remains invocation-specific. An executed mirror transition satisfies only the transition it actually caused at its recorded provenance; authentic endpoint substitution and later downstream transitions remain separate predicates.

## Next admissible work

Use `RT-EXTERNAL-FRAMEWORK-ROUNDTRIP-ROLLOUT-001` for registry-selected framework invocations instead of creating per-framework transport implementations. Classify each framework from the current admissibility-wiki registry, advance independently eligible entries, and preserve exact fail-closed states for ineligible entries. The parent MIR Goal remains ACTIVE for its own operational return-object delivery, downstream processing/egress/final transitions, and authentic MIR endpoint substitution.

## Manual work

None.
