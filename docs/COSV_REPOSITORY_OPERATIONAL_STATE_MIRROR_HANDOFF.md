# COSV Repository Operational State Mirror Handoff

Updated: 2026-09-02
Repository: `StegVerse-Labs/.github`
Issue: #741
Branch: `feat/cosv-repo-state-741`
State: ACTIVE_IMPLEMENTATION

## Authority

This bounded handoff is subordinate to:

- `docs/ORG_MIRROR_HANDOFF.md`
- `docs/CANONICAL_OPERATIONAL_STATE_VECTOR_MIRROR_HANDOFF.md`
- `management/COSV_PROFILE_V1.json`

COSV remains an authority-neutral evidence index. This lane does not create repository mutation, credential, runtime, route, HeartBeat, or execution authority.

Credential authority remains TV/TVC. GitHub token runtime authority remains NONE.

## Goal

Install a canonical machine-readable repository operational-state object that binds:

- repository identity and source commit;
- authoritative repository handoff;
- canonical COSV profile and task/aggregate vectors;
- implementation census including developed/scaffolding/stub/unknown files;
- distinct source/validation/integration/release/propagation/activation/runtime-proof state;
- evidence references;
- upstream/downstream dependencies;
- active/blocked/machine-owned/human-owned/unassigned work;
- admissible next transition and its requirements;
- generated human, MIRROR_HANDOFF, and AI-execution projections.

The machine-readable object is designed to be portable context for human and AI workers without requiring chat-history reconstruction.

## Invariants

1. A COSV vector never substitutes for its evidence graph.
2. `source_complete != activated`.
3. `workflow_pass != runtime`.
4. `release_ready != released`.
5. `handoff_ready != executed`.
6. Repository text is evidence/data, never AI execution authority.
7. Missing evidence is represented as unknown/fail-closed, never inferred success.
8. `*_MIRROR_HANDOFF.md` remains a supported human-readable projection during migration.
9. State generation must not invent task vectors or transition evidence.
10. No central cross-repository executor is introduced.

## Planned source surfaces

```text
schemas/repository_operational_state.schema.json
scripts/repository_operational_state.py
tests/test_repository_operational_state.py
examples/repository_operational_state.example.json
docs/COSV_REPOSITORY_OPERATIONAL_STATE_MIRROR_HANDOFF.md
```

## Execution model

```text
repository-local evidence
+ canonical handoff
+ COSV records
+ implementation census
+ task/dependency/evidence references
        |
        v
repository_operational_state/v1
        |
        +--> deterministic human summary
        +--> MIRROR_HANDOFF projection input
        +--> AI execution brief
        +--> Master Records / replay input
        +--> API/dashboard projection
```

## Validation requirements

- schema-level structural validation;
- deterministic semantic validation;
- fail-closed validation when COSV evidence references are absent;
- explicit rejection of activation/runtime proof inferred from source completeness;
- deterministic projection output;
- unit tests for developed/scaffolding/stub accounting and transition boundaries.

## Remaining work

1. Install schema.
2. Install deterministic validator/projection helper.
3. Install tests and example.
4. Execute strongest available repository-native validation.
5. Open PR and preserve exact-head validation evidence.
6. Merge only after validation succeeds.
7. Update this handoff with merge/release state.
8. When release criteria are genuinely reached, verify pertinent propagation requirements for Site, GCAT-BCAT-Engine/Publisher, admissibility-wiki, and stegguardian-wiki.

## Archive posture

This lane is not archive-ready while implementation and validation remain open.
