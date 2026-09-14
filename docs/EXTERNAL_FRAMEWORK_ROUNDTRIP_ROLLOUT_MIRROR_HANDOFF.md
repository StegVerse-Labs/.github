# External Framework Round-Trip Rollout Mirror Handoff

Updated: 2026-09-13

Parent Goal Task ID: `MIR-CONNECTION-ROUNDTRIP-TECHNICAL-GUIDE-001`
Parent COSV: `50000000100000`
Tracking issue: `StegVerse-Labs/.github#1800`
Reusable Task ID: `RT-EXTERNAL-FRAMEWORK-ROUNDTRIP-ROLLOUT-001`
Status: `SOURCE CONTRACT STAGED / VALIDATION AND REGISTRY INTEGRATION PENDING`

## Purpose

Convert the already-generalized MIR external connection/round-trip architecture into one registry-driven reusable task that can be invoked for external frameworks represented in the canonical admissibility-wiki external-framework registry.

This reusable task is orchestration/composition only. It creates no execution, transition, credential, publication, custody, scheduler, WorkerCoordinator, user-verification, or runtime authority.

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

MIR is the reference transport profile. `SDK-ELYRIA-INTR-ADAPTER-001` is the preferred non-MIR conformance profile because it already reuses the same core component families and preserves foreign verdicts as non-authorizing observations.

## Invocation model

One invocation binds exactly one framework registry entry and one bounded operation to:

```text
goal_task_id
cosv_task_vector
framework_registry_ref
framework_id
framework_version_or_revision
operation_class
source_evidence_ref
```

The invocation must preserve exact task/run/framework identity across manifested intake, governed processing, outbound InTr movement, foreign response, return movement, SDK return assembly, optional Publisher projection, egress, and Master Records custody/reconstruction.

## Fail-closed framework eligibility

Every selected framework is classified into exactly one current eligibility state:

```text
ROUNDTRIP_ELIGIBLE
SOURCE_ONLY
TRANSLATION_ONLY
RUNTIME_ENDPOINT_UNAVAILABLE
UNSUPPORTED_OPERATION_CLASS
REGISTRY_ENTRY_INVALID
```

A non-runnable framework does not authorize substitute endpoints, synthetic foreign responses, hosted fallback, or a new transport stack. The invocation records its exact fail-closed state and terminates without blocking independent framework entries.

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

This reusable task must not create or own a second:

- InTr transport/protocol;
- SDK return implementation;
- Publisher implementation;
- evidence-custody system;
- scheduler or resident executor;
- WorkerCoordinator;
- credential route;
- device/user-verification mechanism;
- per-framework Goal Task when a reusable invocation is sufficient.

## Completion boundary

Source completion for this reusable task requires:

1. reusable-task registry shard and canonical registry integration;
2. deterministic framework-registry resolution and eligibility classification source;
3. invocation-manifest construction bound to framework/task/run identity;
4. tests covering eligible, source-only, translation-only, runtime-unavailable, unsupported-operation and invalid-entry paths;
5. conformance against MIR plus at least one non-MIR profile, preferably Elyria;
6. README/handoff reconciliation;
7. exact-head validation and merge.

Authentic runtime completion is independent and requires framework-specific observed request/response/custody evidence. Source/CI/merge does not satisfy runtime predicates.

## Current next action

Validate current MIR and Elyria contracts against this abstraction; inspect the canonical admissibility-wiki external-framework registry schema; then implement the smallest deterministic registry resolver and invocation builder needed to prove one eligible and one fail-closed framework path without changing any authority boundary.

## Manual work

None.
