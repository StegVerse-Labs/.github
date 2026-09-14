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
Status: `SOURCE COMPLETE / REGISTRY-WIDE PLAN GENERATOR STAGED / EXACT-HEAD VALIDATION PENDING`

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

`.github` PR `#1801` added the reusable-task registry shard, deterministic resolver, bounded tests, and this handoff. Exact head `8f280eb3377faabf1be84c5aec726d63ba036a5c` passed Organization Control `34797138353`, Deterministic Repository Suite `34797138357`, and Heartbeat Worker Project validation `34797138326`, then squash-merged as `49692b2fe410053fc1b0b83a7d27c39fca887d27`.

`.github` PR `#1803` proved the non-MIR abstraction against `SDK-ELYRIA-INTR-ADAPTER-001`. Exact head `044eb8ffab71c27494a57a4f770bbb426846d50e` passed Organization Control `34797282370`, Deterministic Repository Suite `34797282389`, and Heartbeat Worker Project validation `34797282383`, then squash-merged as `204ae5c26520a33418a805da702a627640a85017`.

`.github` PR `#1804` reconciled source completion and merged as `1cd03b9e1b1b07c9324091f3af99265c78e53c68` after Organization Control `34797389863`, Deterministic Repository Suite `34797389873`, and Heartbeat `34797389860` passed.

The Elyria conformance proof requires no new Goal Task, no new reusable component, no duplicate Interlock/InTr protocol, and no GitHub runtime authority. It does not satisfy Elyria's separate authentic public two-way transport predicate.

## Registry-wide planning continuation

The next reusable step is staged on branch `external-framework-rollout-registry-sweep` without creating another Goal Task or another transport component.

`script/plan_external_framework_registry_rollout.py` is intentionally represented by the repository path `scripts/plan_external_framework_registry_rollout.py`. It consumes one exact local snapshot of the admissibility-wiki registry, its local manifest tree, and an optional explicit endpoint map. It emits one deterministic aggregate report containing an independent invocation plan for every registry entry.

The sweep has `NONE_PLAN_ONLY` transition effect. It does not contact external endpoints. It does not create a shared batch execution state. Each output row remains a normal bounded invocation of `RT-EXTERNAL-FRAMEWORK-ROUNDTRIP-ROLLOUT-001`, so an invalid/source-blocked/runtime-unavailable framework fails closed without blocking other framework rows.

The staged tests cover mixed eligibility in one registry, missing-manifest isolation, source-blocked isolation, runtime-endpoint absence, one eligible endpoint-bearing framework, and translation-only sweeps that do not require endpoints.

This is the intended mechanism for reducing framework proliferation: one reusable task identity, one registry sweep for planning, and independent framework invocations only when a consuming Goal actually needs a transition.

## README review

The `.github` root `README.md` already documents the Reusable Task Model, Reusable Task Component Model, bounded invocation semantics, authority separation, and reuse-over-bespoke-orchestration rule. The registry sweep remains a plan-only runner under that existing model, so no root README mutation is required.

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

## Completion boundary

The base reusable rollout source is complete and merged. This continuation is complete only when the registry-wide planner, its reusable-task registry declaration, tests, and this handoff pass exact-head repository validation and merge. Runtime/transition completion remains invocation-specific; the registry sweep itself can never satisfy a runtime transition predicate.

## Next admissible work

1. Run exact-head repository validation for branch `external-framework-rollout-registry-sweep`.
2. If green, merge the registry-wide plan generator without creating a new Goal Task.
3. Materialize a current admissibility-wiki registry sweep from an exact local snapshot and use the report to choose independently actionable framework invocations.
4. Preserve `SOURCE_ONLY`, `RUNTIME_ENDPOINT_UNAVAILABLE`, and invalid states as explicit managed outcomes rather than spawning repair sessions for every entry.
5. Continue the parent MIR Goal independently through retained-return delivery and downstream manifest-selected processing/egress/final transitions.

## Manual work

None.
