# Cross-Repository Dependency Claims Mirror Handoff

## Canonical relationship

`docs/ORG_MIRROR_HANDOFF.md` remains the canonical organization continuation record. This bounded sub-handoff owns `StegVerse-Labs/.github` issue #57 until merge and activation evidence are folded back into the parent.

## Active goal

```text
goal_id: CROSS-REPO-DEPENDENCY-CLAIMS-001
originating_goal: prevent adjacent ChatGPT/session workers in different repositories from independently converging on the same incidental dependency or work surface
repository: StegVerse-Labs/.github
branch: fix/cross-repo-dependency-claims-57
canonical_issue: #57
parent_heartbeat_owner: #12
implementation_claim: CLAIMED_FOR_IMPLEMENTATION
claim_created_at: 2026-08-09T19:12:14Z
claim_release_condition: merge + hosted validation + canonical heartbeat/worker task continuation evidence
render_dependency: false
```

## Defect proven from main

Before this change, `scripts/allocate_claims.py::conflicts()` returned `False` immediately when two claims named different repositories. Repository-local exclusivity therefore could not detect a shared mutable dependency such as `hosting:render` across `StegVerse-Labs/Site` and `StegVerse-Labs/StegCore`.

## Developed surfaces

```text
scripts/allocate_claims.py
schemas/claim.schema.json
tests/test_cross_repository_dependency_claims.py
```

## Admission contract

- repository-local paths/contracts/release surfaces/capabilities/workflows retain their existing same-repository semantics;
- `scope.dependency_surfaces` is repository-independent and normalized case-insensitively;
- if two claims share a dependency surface and either is mutable, they conflict even across different repositories;
- two `shared_read` claims do not take a mutable dependency lock;
- a mutable claim must provide at least one dependency surface or a non-empty `dependency_surface_exempt` reason;
- a queued task missing that declaration is retained in the queue and reported under `blocked_missing_dependency_declaration`; it is not silently allocated;
- claim-grant events persist the admitted dependency surfaces;
- `hosting:render` is only a regression fixture/key; this task does not make Render authoritative or required.

## Collision boundaries

```text
one canonical heartbeat only
one canonical worker registry only
no second scheduler
no deployment authority
no product execution authority
no change to issue #12 sovereign-carrier activation criteria
no duplicate all-organization federation worker
```

## Validation

Required deterministic commands:

```text
python -m unittest tests.test_cross_repository_dependency_claims -v
python -m unittest discover -s tests -v
```

Required hosted evidence: existing heartbeat/worker protocol workflow must execute the new test and existing regression suite successfully on the implementation head and again on main after merge.

## Integration relationship

Site PR #260 and `StegVerse-Labs/Site/data/session-work-claims.json` provide Site-local admission. This issue #57 implementation is the stronger organization allocator contract for cross-repository collision prevention. After activation, the Site machine-owned claim may remain as defense in depth but must not be treated as a second heartbeat or competing global registry.

## Archive condition

The originating session is not archive-complete from branch implementation alone. It becomes transferable when this implementation is merged and validated, or when the canonical heartbeat worker/task registry contains an activated machine-owned continuation with this exact cross-repository collision requirement and a machine-observable release condition.

## Progress

```text
developed_files: 3/3
scaffolding_or_stubs: 0
validation: pending hosted execution
integration: allocator + claim schema integrated; heartbeat workflow validation pending
goal_activation: 55%
```
