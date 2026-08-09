# Cross-Repository Dependency Claims Mirror Handoff

## Canonical relationship

`docs/ORG_MIRROR_HANDOFF.md` remains the canonical organization continuation record. This bounded sub-handoff records the completed `StegVerse-Labs/.github` issue #57 integration and its relationship to the canonical heartbeat/worker control plane under issue #12.

## Goal

```text
goal_id: CROSS-REPO-DEPENDENCY-CLAIMS-001
originating_goal: prevent adjacent ChatGPT/session workers in different repositories from independently converging on the same incidental dependency or work surface
repository: StegVerse-Labs/.github
canonical_branch: main
canonical_issue: #57
parent_heartbeat_owner: #12
implementation_claim: COMPLETE_RELEASED
render_dependency: false
```

## Defect corrected

Before this change, `scripts/allocate_claims.py::conflicts()` returned `False` immediately when two claims named different repositories. Repository-local exclusivity therefore could not detect a shared mutable dependency such as `hosting:render` across `StegVerse-Labs/Site` and `StegVerse-Labs/StegCore`.

The corrected allocator checks repository-independent dependency surfaces before repository identity. A shared mutable dependency surface conflicts globally; repository identity no longer bypasses that collision.

## Developed and merged surfaces

```text
scripts/allocate_claims.py
schemas/claim.schema.json
tests/test_cross_repository_dependency_claims.py
.github/workflows/org-control-plane-validate.yml
```

Merge evidence:

```text
issue: StegVerse-Labs/.github#57
PR: StegVerse-Labs/.github#58
merge: 5173d22513c0e3a767703d38d6eebb844ea96a9f
state: MERGED_TO_MAIN
```

## Activated admission contract

- repository-local paths/contracts/release surfaces/capabilities/workflows retain same-repository semantics;
- `scope.dependency_surfaces` is repository-independent and normalized case-insensitively;
- if two claims share a dependency surface and either claim is mutable, they conflict even across different repositories;
- two `shared_read` claims do not take a mutable dependency lock;
- a mutable claim must provide at least one dependency surface or a non-empty `dependency_surface_exempt` reason;
- a queued task missing that declaration remains queued and is projected under `blocked_missing_dependency_declaration`; it is not silently allocated;
- claim-grant events persist admitted dependency surfaces;
- `hosting:render` is a regression fixture only; Render is not authoritative and is not a heartbeat, worker, deployment, or activation dependency.

## Hosted validation evidence

Implementation-head validation:

```text
Validate organization control plane run: 31331101395 SUCCESS
  cross-repository dependency collision enforcement: SUCCESS
  allocator deterministic exercise: SUCCESS
  control-plane invariants: SUCCESS
Heartbeat Worker Project run: 31331101399 SUCCESS
```

Main-branch validation after merge:

```text
Validate organization control plane run: 31331122402 SUCCESS
Heartbeat Worker Project run: 31331122385 SUCCESS
```

The Heartbeat Worker Project main run also completed native heartbeat semantics, worker coordination subsignal/cycle leases, goal-lineage duplicate control, resource authority, checkpoint/fence, convergence, and sovereign host proofs without failure.

## Site defense-in-depth integration

The local Site entry gate was completed separately and remains defense in depth:

```text
StegVerse-Labs/Site issue: #259
StegVerse-Labs/Site PR: #260
merge: c2fa9d436381f13c109125367ce803518d4ff2e4
machine-owned claim transfer commit: 3afba810ded42fd32cba659c6de51612bcfad504
main heartbeat claim-transfer validation run: 31330976764 SUCCESS
machine owner: github-actions:ecosystem-heartbeat-orchestration
claim: SITE-PREWORK-CLAIM-GATE-MACHINE-001
```

Site's gate cannot become a second heartbeat or global registry. The organization allocator is the stronger cross-repository claim authority; Site blocks local mutable PR entry as an additional safety layer.

## Heartbeat and worker continuity

The canonical worker system already has documented heartbeat-cycle activation under `docs/ORG_MIRROR_HANDOFF.md`: `worker_coordination` is ACTIVE and `SHWP-ALL-ORG-FEDERATION-001` is claimed/fenced/executing through `control/worker-registry.json`. This completed claim-admission correction changes the allocator used before task execution and is covered by the Heartbeat Worker Project validation path; it does not require or authorize a second worker registry.

Any later cross-organization adoption discrepancy is observed through the existing all-organization federation task rather than retained by this chat:

```text
task: SHWP-ALL-ORG-FEDERATION-001
handoff: handoffs/SHWP-ALL-ORG-FEDERATION-001.json
registry: control/worker-registry.json
worker: organization-federation-readiness-worker
carrier: worker_coordination heartbeat subsignal
release model: every organization represented; blocked rows retain explicit machine-observable release conditions
```

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

## Completion and archive state

```text
developed_files: 4/4
scaffolding_or_stubs: 0
missing_required_files: 0
validation: 4/4 hosted gates (head control-plane, head heartbeat-worker, main control-plane, main heartbeat-worker)
integration: 3/3 (central allocator, Site defense-in-depth, heartbeat/worker validation path)
goal_activation: 100%
implementation_claim: RELEASED
session_unique_active_claims: 0
```

The originating Render-collision/orchestration requirement is no longer chat-only: the local entry gate and central allocator repair are merged and main-validated, and the existing canonical heartbeat worker registry remains actively claimed/fenced for organization-wide readiness observation. No unresolved implementation, validation, integration, propagation, reconciliation, or observation requirement from this goal requires this conversation to remain open.

```text
MERGED INTO: StegVerse-Labs/.github/docs/CROSS_REPO_DEPENDENCY_CLAIMS_MIRROR_HANDOFF.md
MERGED INTO: StegVerse-Labs/.github/docs/ORG_MIRROR_HANDOFF.md
MERGED INTO: StegVerse-Labs/.github/handoffs/SHWP-ALL-ORG-FEDERATION-001.json
MERGED INTO: StegVerse-Labs/Site/data/session-work-claims.json
```
