# External Framework Round-Trip Rollout Mirror Handoff

Updated: 2026-09-13

Parent Goal Task ID: `MIR-CONNECTION-ROUNDTRIP-TECHNICAL-GUIDE-001`
Parent COSV: `50000000100000`
Canonical parent issue: `StegVerse-Labs/Site#1277`
Canonical parent handoff: `StegVerse-Labs/Site/docs/MIR_CONNECTION_ROUNDTRIP_TECHNICAL_GUIDE_MIRROR_HANDOFF.md`
Tracking issue: `StegVerse-Labs/.github#1800`
Reusable Task ID: `RT-EXTERNAL-FRAMEWORK-ROUNDTRIP-ROLLOUT-001`
Status: `SOURCE CONTRACT + DETERMINISTIC RESOLVER STAGED / VALIDATION PENDING`

## Purpose

Convert the already-generalized MIR external connection/round-trip architecture into one registry-driven reusable task that can be invoked for external frameworks represented in the canonical `StegVerse-Labs/admissibility-wiki` external-framework registry.

The current parent MIR handoff is authoritative for this continuation. It establishes that MIR is a profile over a framework-neutral external counterpart mirror and that executed transitions are runtime truth at their stated provenance. This reusable task preserves that model rather than creating a new runtime-evidence taxonomy.

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

MIR is the reference transition profile. `SDK-ELYRIA-INTR-ADAPTER-001` is the preferred non-MIR conformance profile because it already reuses the same core component families and preserves foreign verdicts as non-authorizing observations.

## Runtime truth and provenance

The rollout uses the same rule as the canonical MIR handoff:

> executed transitions are runtime truth at their recorded provenance.

Therefore a bounded external-framework mirror/build-test execution is a real executed transition with counterpart provenance such as `EXTERNAL_FRAMEWORK_MIRROR_BUILD_TEST`; it is not equivalent to authentic external endpoint substitution, but it must not be relabeled as "no runtime evidence" merely because later transitions remain incomplete.

Source, CI, or merge state alone does not prove an unexecuted transition.

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

The invocation must preserve exact task/run/framework identity across manifested intake, governed processing, outbound InTr movement, foreign response, return movement, SDK return assembly, optional Publisher projection, egress, and Master Records custody/reconstruction.

`runtime_endpoint_ref` is an invocation input rather than registry authority. Supplying it makes a sourced framework eligible to attempt a round trip; it does not prove endpoint authenticity, availability, transition admission, or success.

## Canonical admissibility-wiki registry semantics

Current registry schema version is `0.4`. Registry entries provide `framework_id`, status, manifest path, source reference and bounded testbench state. The associated framework manifest schema requires source/version/boundary, claims/non-claims, transition-table mapping, SPE overlap, ecosystem overlap, fail-closed conditions and explicit authority boundaries.

The reusable resolver consumes a local exact copy/snapshot of the registry plus the exact selected manifest. It does not fetch external URLs or infer execution authority from a compatibility entry.

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

Examples:

- entries whose status/source version still requires an official source or artifact package classify `SOURCE_ONLY`;
- source/crosswalk-only requests classify `TRANSLATION_ONLY` even if an endpoint reference is present;
- a sourced framework requested for runtime round trip without a current endpoint reference classifies `RUNTIME_ENDPOINT_UNAVAILABLE`;
- a sourced framework with a supplied endpoint reference may classify `ROUNDTRIP_ELIGIBLE`, which is plan eligibility only and grants no transition or execution authority.

A non-runnable framework does not authorize substitute endpoints, synthetic foreign responses, hosted fallback, or a new transport stack. The invocation records its exact fail-closed state and terminates without blocking independent framework entries.

## Source surfaces staged in PR #1801

- `source-bundles/reusable-task-registry.d/RT-EXTERNAL-FRAMEWORK-ROUNDTRIP-ROLLOUT-001.json`
- `scripts/resolve_external_framework_roundtrip_rollout.py`
- `tests/test_external_framework_roundtrip_rollout_contract.py`
- this handoff

The resolver deterministically:

1. requires the selected framework id to resolve exactly once;
2. validates the required manifest shape and rejects external-authority promotion;
3. classifies source sufficiency and requested operation class;
4. requires an explicit current endpoint reference for runtime-round-trip eligibility;
5. binds exact entry and manifest SHA-256 digests, Goal/COSV, operation class and counterpart provenance;
6. emits plan-only authority/effect fields set to `NONE`;
7. preserves the MIR transition-truth rule.

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

1. reusable-task registry shard;
2. deterministic framework-registry resolution and eligibility classification source;
3. plan/invocation construction bound to framework/task/run identity;
4. tests covering eligible, source-only, translation-only, runtime-unavailable, unsupported-operation and invalid-entry paths;
5. conformance against MIR plus at least one non-MIR profile, preferably Elyria;
6. README/handoff reconciliation;
7. exact-head validation and merge.

Runtime/transition completion is invocation-specific. An executed mirror transition may satisfy the transition it actually caused at mirror provenance; authentic endpoint substitution and later downstream transitions remain separate predicates.

## Current next action

Run exact-head repository validation on PR #1801. If source validation passes, reconcile README impact and add the minimum parent-MIR cross-reference needed to make this reusable identity discoverable without changing the parent Goal identity. Then make the PR non-draft and merge only with exact-head evidence.

## Manual work

None.
