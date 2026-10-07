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

## Current continuation
Implement the smallest compatible StegDB registry extension and evaluator first. Do not broaden into a replacement propagation runtime. Update StegDB README so "pushes correctness outward" cannot be read as direct mutation authority.
