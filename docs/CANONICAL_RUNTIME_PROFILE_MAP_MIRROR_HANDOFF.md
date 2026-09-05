# Canonical Runtime Profile Map Mirror Handoff

Updated: 2026-09-04
Repository: `StegVerse-Labs/.github`
Goal: `STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001`
Status: `SOURCE_IMPLEMENTED_RESIDENT_BUILD_STAGED_RUNTIME_RECEIPT_PENDING`

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
5. **Freshness is first class.** Runtime observations carry timestamps/refs where available. The generated map classifies observation freshness as `CURRENT`, `STALE`, `UNKNOWN`, or `CONFLICT`; stale is not equivalent to unavailable and unknown is not false.
6. **No inferred runtime completion.** Repository source, merge, CI, deployment, heartbeat progression, handoff prose, or profile declarations are never converted into proof of current process execution.
7. **Deterministic matching.** Candidate selection uses explicit capabilities, environment, direction, mutation/deployment classes, and optional current-observation requirements. No opaque ranking grants authority.
8. **Negative requirements are preserved.** A profile that cannot satisfy a required mutation, deployment, sovereignty, direction, capability, or current-observation property is rejected explicitly.
9. **Collision-safe coordination.** Runtime selection remains downstream of canonical task/dependency/claim reconciliation; the map does not bypass WorkerCoordinator.
10. **Projection provenance is retained.** Every map entry carries source refs sufficient to trace the declaration/observation back to its canonical owner.
11. **No secret material.** Runtime roots may be symbolic; credentials, tokens, secret paths, and provider secrets are forbidden from the map and validator.
12. **Machine-generated canonical projection.** The checked-in map is a bootstrap source projection. Authentic generated projections are produced by the builder from the source catalog and canonical control surfaces; generated entries are not manually authoritative.
13. **Monotonic projection generations.** Resident builds increment the prior checked-in/runtime generation instead of silently replacing history with generation 1.
14. **Receipted projection integrity.** A validated map can emit an exact-byte SHA-256 projection receipt suitable for later Master Records custody without treating that custody as runtime authority.

## Canonical surfaces

- `schemas/runtime-profile-map.schema.json`
- `control/runtime-profile-sources.json`
- `control/runtime-profile-map.json`
- `scripts/build_runtime_profile_map.py`
- `scripts/validate_runtime_profile_map.py`
- `scripts/query_runtime_profile_map.py`
- `scripts/match_runtime_profile.py`
- `scripts/emit_runtime_profile_map_receipt.py`
- `tests/test_runtime_profile_map.py`

Resident continuation surfaces:

- `control/resident-execution-request.d/runtime-profile-map-build-001.json`
- `control/resident-execution-request.d/consume-runtime-profile-map-build.py`
- resident dispatcher selector `runtime_profile_map`

## Profile model

Each profile carries stable identity/class, component/repository identity, declared capabilities/effect class, mutation/deployment flags, environment/direction declarations, HB/oscillator relationship, WorkerCoordinator relationship, InTr relationship, runtime-root symbol, required predicates, explicit observed predicates/evidence, observation freshness, task selectors where explicit, authority nonclaims, and source provenance.

## Source catalog and generated projection

`control/runtime-profile-sources.json` is the small canonical source catalog. The builder currently consumes:

- canonical resident carrier contract;
- WorkerCoordinator capability profiles;
- WorkerCoordinator runtime registry as a required source dependency;
- shared Universal InTr profiled ingress source;
- Canonical Work runtime profile;
- every JSON runtime-observability consumer currently present under `control/runtime-observability-consumers/`.

Missing required sources fail closed. Source presence never becomes process-liveness proof.

The checked-in `control/runtime-profile-map.json` is intentionally a bootstrap source projection with `generated_at=null` and declared-only state. The resident builder is authoritative for producing the complete generated projection from current local source and observations.

## Deterministic task/runtime compatibility

`match_runtime_profile.py` evaluates every profile against explicit requirements and returns reasons for rejection, including missing capabilities, environment mismatch, direction mismatch, mutation/deployment incompatibility, and missing current observation when explicitly required.

A compatible result is only a routing candidate. It still requires:

```text
canonical task / Master Records reconciliation
-> dependency + incident reconciliation
-> runtime-profile compatibility
-> WorkerCoordinator admission and current claim/fence
-> current applicable transition governance / Interlock-InTr
-> execution
```

`data/task-coordination-policy.json` now includes the runtime-profile map as the canonical discovery/compatibility projection and places runtime-profile resolution before claim/fence acquisition in new-session execution selection.

## Resident build path

A bounded non-authorizing resident request is staged for `STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001`. The existing resident dispatcher now registers selector `runtime_profile_map`.

The consumer lives in `control/resident-execution-request.d`, so existing sovereign source refresh materializes the consumer/request without expanding the resident script manifest. On resident consumption it:

```text
validates exact REQUESTED object
-> copies only required map/control/source surfaces from already-local canonical source
-> verifies SHA-256 exact-copy equality
-> runs build_runtime_profile_map.py
-> runs validate_runtime_profile_map.py
-> runs emit_runtime_profile_map_receipt.py
-> writes runtime-profile-map-build-request-consumption.latest.json
```

No GitHub/network source fetch, credentials, second machine, HB progression, oscillator progression, task admission, or claim/fence minting occurs in this consumer.

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

## Completion predicates

1. Schema, source catalog, canonical bootstrap projection, builder, validator, query, matcher, receipt emitter and tests exist. **SOURCE COMPLETE**
2. HB32/oscillator authority boundary is represented correctly. **SOURCE COMPLETE**
3. Worker capability profiles are normalized without turning capability availability into authority. **SOURCE COMPLETE**
4. Universal InTr and Canonical Work profile relationships are represented. **SOURCE COMPLETE**
5. Runtime-observability consumers are normalized without inventing process liveness and with explicit freshness semantics. **SOURCE COMPLETE**
6. Candidate matching rejects incompatible requirements deterministically. **SOURCE COMPLETE**
7. Canonical task coordination references the runtime-profile map as discovery input only. **SOURCE COMPLETE**
8. Canonical task registry contains this bounded workstream. **SOURCE COMPLETE**
9. Resident request/consumer/dispatcher path exists for authentic map build, validation and receipting. **SOURCE COMPLETE**
10. One admitted resident build produces `runtime-profile-map-build-request-consumption.latest.json` plus a validated projection receipt. **RUNTIME PENDING**
11. The authentic projection/receipt is reconciled/custodied as appropriate without creating runtime authority. **RUNTIME/CUSTODY PENDING**

## Runtime status

No runtime-complete claim is made. Source implementation and resident dispatch wiring are present, but the authentic resident build receipt has not been observed in this session.

Expected resident evidence:

- `receipts/sovereign-host/runtime-profile-map-build-request-consumption.latest.json`
- `receipts/runtime-profile-map/runtime-profile-map.latest.json`
- generated `control/runtime-profile-map.json` with non-null `generated_at`

## Human action

None currently required. Remaining work is machine-owned resident execution and evidence reconciliation.

## Archive readiness

All source design and continuation state is captured here and in the canonical task registry. The workstream is not runtime-complete until completion predicates 10-11 are evidenced.
