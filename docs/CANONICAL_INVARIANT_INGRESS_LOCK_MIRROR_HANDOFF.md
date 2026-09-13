# Canonical Invariant Ingress Lock Mirror Handoff

Updated: 2026-09-13
Canonical owner: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
Registry: `control/canonical-policy-context-registry.json`
Entrypoint: `scripts/session_build_preflight.py`
Mutation guard: `scripts/validate_source_mutation_preflight.py`
Validation surface: `.github/workflows/org-control-plane-validate.yml`
Authority effect: `NONE_PREWORK_INTERPRETATION_ONLY`

## Purpose

Every StegVerse session, task/COSV continuation, build/implementation pre-work, handoff reconciliation, remediation proposal, source-mutation proposal, and reusable-component decomposition must consume canonical policy context before local interpretation or mutation.

This lock exists because canonical architecture must not be re-derived from task-specific prose after it has already been established.

## Mandatory ingress invariants

1. Canonical source precedes local interpretation.
2. Task-specific wording may parameterize an existing canonical invariant but may not redefine it.
3. A concrete runtime subject, device, repository, worker, provider, or observation target does not create a new architectural role or authority class merely by being named in a task.
4. A local interpretation that conflicts with canonical source is invalid.
5. An existing canonical invariant must be reused, not recreated as new work.
6. Restating an existing canonical invariant is not a new capability and must not by itself create a PR, Goal Task, reusable component, handoff, or policy mutation.
7. A proposed new role, authority owner, identity class, execution owner, verification owner, transport class, or governance role requires evidence that the canonical model lacks an equivalent before source mutation is admissible.
8. When a human correction matches already-canonical truth, the required disposition is `NO_SOURCE_MUTATION_REQUIRED`; the correction does not authorize a second artifact that restates the same invariant.
9. Missing canonical context is an exact dependency. It is never permission to invent replacement semantics.
10. Canonical policy resolution is interpretation-only and grants no execution, claim/fence, credential, transition, custody, publication, release, or user-verification authority.

## Standing device/verifier invariant

The Reusable Task Component Model already establishes the applicable global rule:

- StegOS devices are interchangeable transport/execution nodes.
- Device identity, runtime-subject binding, Secure Enclave identity, transport identity, browser identity, phone identity, or node identity does not become user-verification authority.
- KV/SKAP Vault remains the sole user-verification authority.

A task may name a particular device because that device carries the evidence state being observed or retried. That selection is evidence binding only unless a separate canonical source explicitly assigns another role.

## Ingress enforcement path

`control/canonical-policy-context-registry.json` is consumed by `scripts/session_build_preflight.py`. The registry is required before state interpretation, blocker derivation, remediation proposal, new task creation, source mutation, or architecture reinterpretation. The canonical Reusable Task Component Model is a required global source so its authority/device invariants are resolved automatically rather than re-entered in prompt prose.

If the registry or a required source cannot be resolved, the existing fail-closed disposition remains:

`STOP_AT_CANONICAL_POLICY_DEPENDENCY`

This lock changes interpretation discipline only. It does not modify Interlock/InTr packet admission or any runtime authority owner.

## Repository-side mutation enforcement

The session/build preflight is not sufficient merely as a callable helper because a caller can otherwise bypass it and invoke a repository mutation directly. Source-changing pull requests therefore reuse the existing stable organization-control validation surface to enforce the preflight result before merge.

A protected mutation must carry a changed `receipts/preflight/*.json` receipt that:

- names an existing canonical Goal Task;
- binds the exact PR merge-base commit;
- records a mutation-admissible preflight state;
- lists every globally required canonical policy source plus the Goal Task's declared `canonical_policy_refs`;
- explicitly scopes the files that may be mutated; and
- was committed before the first protected mutation commit.

The guard rejects a receipt introduced in the same commit as the protected mutation. This prevents documentation from being read or a receipt from being manufactured only after implementation has already begun.

Canonical validator:

```text
scripts/validate_source_mutation_preflight.py
```

Regression coverage:

```text
tests/test_source_mutation_preflight_guard.py
```

Existing stable validation surface:

```text
.github/workflows/org-control-plane-validate.yml
```

No additional workflow/dispatcher is created. The repository's workflow-proliferation invariant remains intact.

This enforcement is merge-time completeness only. It does not make GitHub an execution, transition, governance, credential, custody, or runtime authority.

## Task-specific domain policy binding

Task-specific architecture that is not globally applicable must be declared through `canonical_policy_refs` on the canonical task record. Those refs become fail-closed dependencies of the existing preflight rather than relying on a human to restate them in chat.

`STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001` now declares its canonical Device/KV/SKAP handoff plus the KnowledgeVault privacy/state-transition and device-backed-capability handoffs as task policy refs. This means future preflight for that task must resolve the KV state-transition semantics before local implementation reasoning.

## Hard repository bypass condition

Repository validation can reject a noncompliant pull request, but it cannot by itself prevent a caller with direct write permission from writing to an unprotected `main` branch. The final fail-closed condition therefore requires the repository's branch/ruleset configuration to require pull requests and the organization-control validation check for `main`, with direct bypass disabled for ordinary writers.

That repository setting changes no StegVerse runtime authority. It only makes the source-mutation completeness guard unavoidable at the GitHub repository boundary.

## Current validation state

Source implementation is present on branch `enforce-canonical-preflight-before-mutation-001`. Exact-head CI and merge evidence are still required. No runtime or authority claim is created by this source change.
