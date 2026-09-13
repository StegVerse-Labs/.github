# Site ECE Current Projection — Reusable Task Component Model Handoff

Updated: 2026-09-12
Goal Task ID: `SITE-ECE-CURRENT-PROJECTION-MATERIALIZER-001`
COSV: `71000000102000`
Parent Goal Task: `ECOSYSTEM-CONTINUITY-EVALUATOR-001`
Canonical runtime handoff: `docs/SITE_ECE_CURRENT_PROJECTION_MATERIALIZER_MIRROR_HANDOFF.md`
Status: `ACTIVE / COMPONENTIZED / RUNTIME PREDICATES UNCHANGED`

## Reconciliation result

The existing Goal Task remains valid. The Reusable Task Component decomposition score is `19`, which requires componentization before more task-specific orchestration is added. No new Goal Task is created and no prompt-count, COSV, authority, or runtime-evidence reset occurs.

The task consumes only the reusable capabilities it actually needs. The maximal transport chain is not applicable here.

## Component map

### RTC-EVIDENCE-CUSTODY-004 — Evidence Custody and Reconstruction

- Exists: yes, `data/reusable-transport-component-contract.json`.
- Canonical owner: Master Records.
- Role for this Goal Task: required upstream precondition; do not reimplement custody inside Site.
- Inputs: exact retained ECE evaluation/projection lineage and custody references from the parent ECE cycle.
- Outputs: exact retained bytes/hash/readback/reconstruction evidence sufficient to bind the Site-safe projection to observed reality.
- Preconditions: authentic parent-cycle evidence; no CI/source substitution.
- Authority owner: Master Records for observed-reality custody/reconstruction.
- Expected evidence: exact-byte hash equality, custody record, reconstruction/readback evidence for the same ECE cycle.
- Cardinality: once per ECE cycle consumed by this child.
- Failure semantics: missing/conflicting/unreconstructable evidence blocks materialization; do not synthesize a projection.
- Requirement: REQUIRED PRECONDITION.

### RTC-PUBLISHER-005 — Publication / Distribution Projection

- Exists: yes, `data/reusable-transport-component-contract.json`.
- Canonical execution/publication owner for this Goal Task: existing Site runtime.
- Task binding: `StegVerse-Labs/Site:scripts/materialize_ecosystem_continuity_current.py`.
- Inputs: already-validated Site-safe projection bytes, exact expected SHA-256, cycle projection reference, served Site root.
- Outputs: exact bytes at `data/ecosystem-continuity/current.json` plus a non-authorizing materialization receipt.
- Preconditions: RTC-EVIDENCE-CUSTODY-004 satisfied upstream; ECE projection schema/authority checks pass; source-repository writeback prohibited.
- Authority effect of reusable component: none; Site runtime retains publication authority.
- Expected evidence: `stegverse.site-ecosystem-continuity-materialization-receipt.v1`, exact-byte equality, target readback equality, `live_publication_observed=false` until separately observed.
- Cardinality: optional once per completed ECE cycle when a served Site root is bound.
- Failure semantics: NOT_BOUND when no served root is available; BLOCKED on receipt/ref/hash/schema/path/readback failure; never fall back to stale or synthetic current state.
- Requirement: CONDITIONAL FOR MATERIALIZATION; required for Goal completion.

### Canonical runtime observation capability

- Exists: yes as the model's `runtime_observation` canonical-existing-owner family; no new reusable component is created.
- Canonical owner: observed runtime/public Site evidence surface, with Master Records retaining observed-reality reconstruction where retained.
- Inputs: served `data/ecosystem-continuity/current.json`, expected materialized SHA-256, user-facing continuity page.
- Outputs: independent observation that the served bytes and rendered page correspond to the materialized projection.
- Preconditions: successful RTC-PUBLISHER-005 materialization.
- Authority effect: observation only; does not publish, transition, repair, or verify a user.
- Expected evidence: independently observed served SHA/content and page rendering tied to the same projection identity.
- Cardinality: at least once after materialization; repeatable for freshness/recovery observations.
- Failure semantics: absent/unreachable/mismatched public state leaves `SITE_LIVE_CONTINUITY_PROJECTION_OBSERVED` unsatisfied.
- Requirement: REQUIRED FOR GOAL COMPLETION.

## Task-specific configuration, not reusable orchestration

The following remain Goal Task-specific bindings rather than new reusable components:

- ECE safe-projection schema and allowed finding fields;
- `stegverse.healer-ecosystem-continuity-cycle/v1` field names;
- target relative path `data/ecosystem-continuity/current.json`;
- ECE-specific source-evaluation identity checks;
- the two Goal completion predicates.

The existing Site materializer is therefore treated as the ECE binding/adapter for `RTC-PUBLISHER-005`, not as a new authority-bearing subsystem.

## Components explicitly not selected

This child Goal Task does not require `RTC-MANIFEST-001`, `RTC-GOVERNED-PROCESSING-002`, `RTC-ROUNDTRIP-003`, `RTC-SDK-RETURN-006`, `RTC-STEGVERSE-EGRESS-007`, `RTC-INTERLOCK-INTR-TRANSPORT-008`, or `RTC-FARSIDE-FINAL-009`. Those may exist in the parent ECE or other Goal Tasks, but forcing them here would recreate the maximal-chain ambiguity the component model is intended to remove.

## Authority preservation

Task Registry remains coordination only. WorkerCoordinator retains claim/fence authority when work is claimed. KV/SKAP Vault remains sole user-verification authority. StegOS nodes are interchangeable transport/execution nodes and are not user verifiers. Interlock/InTr remains governed transition/admission authority where an actual governed transition is required. TV/TVC remains credential/provider/release authority. Master Records retains observed-reality custody/reconstruction. HeartBeat remains timing/freshness/liveness/correlation/observability only. GitHub has no runtime authority.

No device-verification policy, process, attestation gate, pinned-device requirement, or device-local user-verification step is introduced.

## Runtime truth preserved

Componentization does not change the current runtime state. Authentic Site-safe projection materialization and independent live Site projection observation remain NOT OBSERVED until authentic evidence exists.

The canonical runtime handoff remains `docs/SITE_ECE_CURRENT_PROJECTION_MATERIALIZER_MIRROR_HANDOFF.md`; this document records architecture composition only.

## Adjacent and dependency tasks

- Parent: `ECOSYSTEM-CONTINUITY-EVALUATOR-001` / COSV `71000000100111`.
- Upstream diagnostic child: `SDK-ECOSYSTEM-DIAGNOSTIC-PROCESSOR-001` / COSV `71000000101000`.
- Existing reusable parent-cycle identity: `RT-ECOSYSTEM-CONTINUITY-EVALUATION-001`.
- No successor Goal Task is required by this reconciliation.

## Remaining Goal Task-specific predicates

1. `AUTHENTIC_SITE_SAFE_PROJECTION_MATERIALIZED`.
2. `SITE_LIVE_CONTINUITY_PROJECTION_OBSERVED`.

Recovery-loop proof remains a parent ECE predicate and is not duplicated into this child.

## README impact

No repository function changed in this reconciliation; the root `.github` README already projects the canonical Reusable Task Component Model. No additional README mutation is required for this child binding.
