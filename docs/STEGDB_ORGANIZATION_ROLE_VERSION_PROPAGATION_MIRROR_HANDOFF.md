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

## Acceptance reconciliation — 2026-10-07
- Exact Organization Role reference binding merged in StegDB PR #33 as `2c13247aa48c707dc4155f2599cdaff44a5a3db8`.
- Canonical handoff reference binding merged in .github PR #2981 as `4fdfd0a07cd37245747d03b8fcd6534ba6600f98`.
- Acceptance evaluation and exemption semantics merged in StegDB PR #34 as `2a81f754a8ffbf580308c6f25daf1409127d2390`.
- `registry/organization-role/acceptance.json` evaluates all 13 acceptance predicates without granting runtime authority.
- `registry/organization-role/exemptions.json` requires exemptions to be explicit, version-bound, scope-bound and non-authorizing; there are no active exemptions.

### Current non-ALLOW acceptance results
1. `EVERY_REGISTERED_ADOPTER_HAS_DECLARED_ROLE_VERSION` = `FAIL_CLOSED` for `GCAT-BCAT-Engine` and `StegGhost`.
   - failed predicate: `REGISTERED_ADOPTER_DECLARED_VERSION_PRESENT`
   - repair: owning Organization publishes an explicit Organization Role declaration or valid version-bound exemption.
   - retry: `MANIFEST_BOUND_CONFORMANCE_RETRY`
   - next attempt: re-evaluate after Organization-owned declaration/exemption evidence is retained.
2. `CONFORMANCE_ATTEMPT_TERMINATES_ALLOW_DENY_OR_FAIL_CLOSED` = `FAIL_CLOSED` because no Organization-owned terminal conformance-attempt evidence has yet been retained for `GCAT-BCAT-Engine`, `StegGhost`, `StegVerse-Labs`, or `SV-LLM`.
   - failed predicate: `ORGANIZATION_OWNED_CONFORMANCE_ATTEMPT_EVIDENCE_PRESENT`
   - repair: materialize the manifest-bound conformance work at each owning Organization and retain its terminal disposition plus organization-ledger evidence.
   - retry: `MANIFEST_BOUND_CONFORMANCE_RETRY`
   - next attempt: evaluate retained Organization-owned evidence; never infer a disposition from repository or StegDB state.

## Current continuation
Materialize the existing non-authorizing manifest-bound conformance work at each owning Organization. Preserve runtime migration as `UNOBSERVED` until an Organization-owned transition produces retained evidence. Do not create direct StegDB mutation authority or treat source-state merges as `ALLOW`.

## Conformance-attempt reconciliation — 2026-10-07
- StegDB PR #35 merged as `2acc6890ef11a48bcfe07264e8f8a155f6c68a13`.
- StegVerse-Labs and StegGhost both have current Organization Role source declarations; their prior missing-declaration classification was stale and is corrected.
- Attempted conformance materialization for GCAT-BCAT-Engine, StegGhost, StegVerse-Labs and SV-LLM terminates `FAIL_CLOSED` in the current execution context wherever an authentic Organization-owned conformance execution surface cannot be reached.
- `materialization: UNOBSERVED` is retained for those attempts and no source/repository state is promoted to runtime migration evidence.

## Concrete GCAT-BCAT-Engine repair surface
The remaining `EVERY_REGISTERED_ADOPTER_HAS_DECLARED_ROLE_VERSION` failure is GCAT-BCAT-Engine only. Its owning `GCAT-BCAT-Engine/.github` already contains:
- `resident-runtime/activation-manifest.json` (blob `29299ce9080d6957b39e1cf5876c9bbd168072b4`), naming this repository as activation and ingress/egress owner;
- `org-boundary/registry/services.json` (blob `108099e925af7e52cbbfe2d5acfe1e0e98d68fbe`);
- `org-boundary/runtime/process_boundary.py` (blob `1b67443a19feed665bcebbc93cf9604a73d6c8e8`).

It does not currently expose the Organization Role declaration or `.stegverse/transition-ledger/org-contract.json`. Its boundary processor currently accepts only `BOUNDARY_LOCAL_DIAGNOSTIC` and returns `endpoint-adapter-not-installed` for other service roles.

Repair is therefore bounded to the owning GCAT `.github`: publish the version-bound Organization Role declaration and organization-ledger contract, register Organization Role conformance on the existing org-boundary, and install/bind the applicable endpoint adapter. Do not create a second ingress. Only a later Organization-owned manifest-bound Interlock/InTr invocation with retained organization-ledger evidence can change runtime migration from `UNOBSERVED`.

## Current continuation
Validate and merge the exact GCAT repair-surface binding in StegDB and this handoff, then materialize that repair through GCAT-BCAT-Engine's owning Organization repository. Preserve explicit `ALLOW | DENY | FAIL_CLOSED` for every attempted transition and never infer runtime migration from repository mutation.
