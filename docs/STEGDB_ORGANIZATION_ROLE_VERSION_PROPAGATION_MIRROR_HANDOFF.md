# StegDB Organization Role Version Propagation Mirror Handoff

Goal Task ID: `STEGDB-ORGANIZATION-ROLE-VERSION-PROPAGATION-001`
COSV: `20000000100000`
Coordination: `ACTIVE / CHECKED_OUT`
Owner: `StegVerse-Labs/StegDB`

## Goal
Make StegDB the durable ecosystem registry for Organization Role versions, version-bound reference coordinates, adopter declarations, migrations, conformance findings and exemptions.

## Authority boundary
- Task Registry owns task identity, lifecycle, COSV and collision state.
- StegDB owns non-authorizing Organization Role version/adoption/migration/conformance state and deterministic drift comparison.
- Interlock/InTr owns consequential transition/admission.
- Each Organization owns repository-local implementation and runtime reality in its organization ledger.
- TV/TVC owns credentials.
- Master Records owns organization-record custody and reconstruction only.
- StegDB MUST NOT directly install or mutate adopter repositories.

## ACTIONS BY MANIFEST
A version advance is durable state. StegDB compares the canonical adopter denominator and emits `VERSION_DIVERGENCE_DETECTED` plus an exact, non-authorizing conformance-work specification. Existing manifest-bound ingress/materialization resolves the destination and exposes work to the owning organization. The owning organization evaluates current state and every attempted consequential transition terminates `ALLOW | DENY | FAIL_CLOSED`. Unavailable receivers use `DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION`; no external machine, listener or session is awaited.

## Required registry model
- versions: version_id, contract_digest, version-bound implementation/reference coordinates, superseded version, migrations, effective transition.
- adoptions: canonical ecosystem-derived adopter denominator, organization, declared version, implementation coordinates, latest disposition/evidence, exemption ref.
- migrations: from/to version, predicates, manifest template, repair owner, retry entrypoint.
- conformance: append/reconstructable findings with a current projection; findings never erase prior evidence.

## Initial divergence vector
- newer implementation: `StegVerse-org/.github`, including LedgerStore-backed organization-ledger mechanics.
- stale compatibility artifact: `StegVerse-Labs/.github:data/organization-role-deployment/packet.v1.json`, hard-coded to the historical Labs reference.
- downstream drift target: `SV-LLM/.github`.
Expected finding: `VERSION_DIVERGENCE_DETECTED`, with exact affected adopters and manifest-bound conformance work.

## Acceptance
1. STEGDB_HAS_VERSIONED_ORGANIZATION_ROLE_REGISTRY
2. CANONICAL_REFERENCE_COORDINATES_ARE_VERSION_BOUND_STEGDB_STATE_AND_REPOSITORY_LOCAL_PACKETS_CANNOT_OVERRIDE_THEM
3. ORGANIZATION_ROLE_ADOPTER_DENOMINATOR_IS_DERIVED_FROM_CANONICAL_ECOSYSTEM_STATE
4. EVERY_REGISTERED_ADOPTER_HAS_DECLARED_ROLE_VERSION
5. ROLE_VERSION_ADVANCE_DETERMINISTICALLY_IDENTIFIES_STALE_ADOPTERS
6. STALE_ADOPTER_PRODUCES_MANIFEST_BOUND_CONFORMANCE_WORK
7. CONFORMANCE_ATTEMPT_TERMINATES_ALLOW_DENY_OR_FAIL_CLOSED
8. NON_ALLOW_INCLUDES_FAILED_PREDICATE_REPAIR_RETRY_AND_NEXT_ATTEMPT
9. EXEMPTION_IS_EXPLICIT_VERSION_BOUND_AND_NON_AUTHORIZING
10. NO_EXTERNAL_MACHINE_LISTENER_OR_SESSION_IS_AWAITED
11. LABS_DEPLOYMENT_PACKET_IS_PROJECTION_OR_DEPRECATED_AS_CANONICAL_REFERENCE
12. SV_LLM_DRIFT_IS_DETECTED_FROM_CANONICAL_STATE
13. NO_SECOND_TASK_OR_TRANSITION_AUTHORITY_IS_CREATED

## Reconciled source state — 2026-10-07
- StegDB Organization Role registry/evaluator merged through PR #29 as `a69f53c510e4794aac7d7b8219ddea6ec8260aff`.
- Exact SV-LLM SOURCE_IMPLEMENTED adoption lineage and organization-contract evidence merged through StegDB PR #30 as `e40c9d9b200cabd44def99835b1f9eb700ae44e5`.
- Labs deployment packet is now a StegDB projection and deprecated as canonical reference through .github PR #2978 as `27149bde855593f974d50f0fc76d06cf803e060c`.
- These are repository/source-state observations. They do **not** establish that SV-LLM or another adopter has completed the current Organization Role runtime migration.

## Runtime migration boundary
Runtime migration remains `UNOBSERVED` until the owning Organization performs a manifest-bound transition through Interlock/InTr and supplies the resulting Organization-owned disposition and organization-ledger evidence. Repository merge state, StegDB findings, compatibility-packet projection, or source declarations MUST NOT be promoted to runtime migration evidence.

Until that evidence exists, StegDB may retain `VERSION_DIVERGENCE_DETECTED` and emit non-authorizing conformance work. It may not directly mutate the adopter or infer `ALLOW`.

## Exact version-bound reference
- StegVerse-org Organization Role reference commit: `ac0f2d96e3339974005f746ba89024c420b55019` (current main at verification).
- Reference path: `resident-runtime/organization_egress_boundary.py`.
- Git blob: `536d77031842e22da0d9a23d76bbc36619636d96`.
- UTF-8 file bytes: `44937`.
- SHA-256 contract digest: `sha256:902bea00cdd2f4260fd01565b2beef6b1346f1d28d5540877ecb80b090723695`.
- This binding is source/version evidence only and is explicitly not runtime migration evidence.

## Current continuation
Validate and merge the exact reference binding in StegDB and this canonical handoff. Continue Organization-owned manifest-bound conformance work for stale/missing adopters without inferring runtime migration from repository state; every consequential attempt must terminate `ALLOW | DENY | FAIL_CLOSED`.
