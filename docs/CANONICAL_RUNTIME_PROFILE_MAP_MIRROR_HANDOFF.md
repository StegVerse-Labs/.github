# Canonical Runtime Profile Map Mirror Handoff

Updated: 2026-09-04
Repository: `StegVerse-Labs/.github`
Goal: `STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001`
Status: `SOURCE_IMPLEMENTATION_IN_PROGRESS`

## Parent authority and adjacent systems

This bounded workstream is subordinate to the repository-wide resident-runtime and coordination authority already expressed by:

- `control/canonical-resident-carrier-contract.json`
- `docs/CANONICAL_WORK_COORDINATION_SYSTEM_MIRROR_HANDOFF.md`
- `docs/CANONICAL_WORK_COORDINATION_RUNTIME_MIRROR_HANDOFF.md`
- `control/worker-capability-profiles.json`
- `control/worker-registry.json`
- `control/runtime-observability-consumers/`
- `workers/universal_intr_profiled_ingress.py`

It MUST NOT create a second heartbeat, oscillator, scheduler, WorkerCoordinator, ingress server, credential authority, task registry, or runtime authority.

## Purpose

Create one canonical machine-readable projection answering:

> What execution/runtime substrates exist, what declared capabilities and transition surfaces do they expose, what runtime predicates/evidence describe their current observed condition, and which canonical tasks can safely consider them as candidates?

The map is a discovery/reconciliation surface. It is not an execution authority and cannot turn availability, capability matching, source presence, service presence, heartbeat progression, or prior receipts into authorization.

## Best-practice design rules

1. **One map, many source authorities.** The map projects source facts; it does not replace the source systems that own them.
2. **Declared capability and observed runtime state are separate.** A profile may be declared but not observed; an observation may be stale; neither implies authority.
3. **Authority remains external to discovery.** Capability matching never grants task admission, WorkerCoordinator claim/fence, InTr admission, credential access, deployment authority, or consequence authority.
4. **HB/oscillator semantics are explicit.** HB32 + independent 100 Hz / 10 ms oscillator is recorded as reference/carrier substrate only.
5. **Freshness is first class.** Runtime observations carry timestamps/refs where available; stale or absent observations become `UNKNOWN` rather than guessed state.
6. **No inferred runtime completion.** Repository source, merge, CI, deployment, heartbeat progression, handoff prose, or profile declarations are never converted into proof of current process execution.
7. **Deterministic matching.** Candidate selection uses explicit capabilities, environment, direction, mutation/deployment classes, and predicates. No opaque ranking grants authority.
8. **Negative requirements are preserved.** A profile that cannot satisfy a required mutation, deployment, sovereignty, or ingress property must be rejected explicitly.
9. **Collision-safe coordination.** Runtime selection remains downstream of canonical task/dependency/claim reconciliation; the map does not bypass WorkerCoordinator.
10. **Projection provenance is retained.** Every map entry carries source refs sufficient to trace the declaration/observation back to its canonical owner.
11. **No secret material.** Runtime roots may be symbolic; credentials, tokens, secret paths, and provider secrets are forbidden from the map.
12. **Machine-generated canonical projection.** The checked-in map is generated from a small source catalog plus canonical control surfaces; hand edits to generated entries are not authoritative.

## Canonical surfaces

- `schemas/runtime-profile-map.schema.json`
- `control/runtime-profile-sources.json`
- `control/runtime-profile-map.json`
- `scripts/build_runtime_profile_map.py`
- `scripts/validate_runtime_profile_map.py`
- `scripts/query_runtime_profile_map.py`
- `scripts/match_runtime_profile.py`

## Profile model

Each profile carries:

- stable `profile_id` and `profile_class`;
- component/entity and repository identity;
- declared capabilities and effect class;
- mutation/deployment flags;
- runtime/substrate refs;
- HB/oscillator relationship;
- InTr ingress/egress relationship;
- WorkerCoordinator relationship;
- required predicates;
- observed predicates/evidence refs;
- freshness state;
- environment/sovereignty constraints;
- task selectors/correlation refs where explicit;
- non-authority invariants;
- source provenance.

## Initial projection scope

The first map generation covers the canonical resident substrate, WorkerCoordinator capability profiles, the shared Universal InTr ingress profile, Canonical Work coordination, and registered runtime-observability consumers. Additional product/runtime repos may register profiles through the source catalog without creating another map.

## Coordination-system relationship

The intended decision sequence is:

```text
canonical task registry
-> Master Records reconciliation
-> dependency / incident reconciliation
-> runtime-profile candidate query
-> deterministic compatibility result
-> WorkerCoordinator admission / claim-fence authority
-> governed execution
-> Master Records evidence
-> task-state reconciliation
```

A runtime-profile match is therefore a candidate-routing fact only.

## Runtime status

Source implementation is not authentic runtime proof. Until the builder/validator execute in an admitted environment and current observations are materialized, the checked-in map is a source projection with explicit `UNKNOWN`/declared-only semantics where needed.

## Completion predicates

1. Schema, source catalog, canonical projection, builder, validator, query and matcher exist.
2. HB32/oscillator authority boundary is represented correctly.
3. Worker capability profiles are represented without turning capability availability into authority.
4. Universal InTr and Canonical Work profile relationships are represented.
5. Runtime-observability consumers can be normalized without inventing process liveness.
6. Candidate matching rejects incompatible requirements deterministically.
7. Canonical task coordination references this map as discovery input only.
8. One admitted runtime build/validation produces an authentic projection receipt before runtime-complete status is claimed.

## Human action

None required for source implementation.
