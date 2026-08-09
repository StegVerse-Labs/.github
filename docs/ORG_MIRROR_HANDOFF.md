# StegVerse-Labs Organization Mirror Handoff

## Authority

This is the canonical StegVerse-Labs organization continuation/exit record. Repository-local `*_MIRROR_HANDOFF.md` files remain authoritative for repository-local implementation evidence. Machine-readable state under `control/`, `handoffs/`, `management/`, `receipts/`, `checkpoints/`, `authorizations/`, `schemas/`, and `events/` supersedes chat history.

## Active goal and ownership

```text
goal_id: CROSS-REPO-DEPENDENCY-CLAIMS-001
originating_goal: prevent adjacent sessions/workers in different repositories from independently converging on the same incidental dependency or work surface
repository: StegVerse-Labs/.github
canonical_branch: main
canonical_owner: StegVerse-Labs/.github#12
completion_issue: StegVerse-Labs/.github#57 CLOSED_COMPLETED
completion_pr: StegVerse-Labs/.github#58 MERGED
merge: 5173d22513c0e3a767703d38d6eebb844ea96a9f
render_dependency: false
current_state: COMPLETE_MERGED_MAIN_VALIDATED
thread_archive_ready: true
```

The previous `WORKER-COORDINATION-SUBSIGNAL-CYCLE-LEASE` goal remains complete and is the activated worker substrate. This goal corrected the execution-entry allocator defect discovered after adjacent sessions independently converged on Render-related work.

## Canonical architecture

There is one canonical StegVerse heartbeat and one canonical worker registry.

```text
heartbeat runtime: heartbeat_runtime.engine_v9.HeartbeatRuntime
heartbeat runner: scripts/run_heartbeat_runtime.py
worker coordination subsignal: control/heartbeat-subsignals.json#worker_coordination
worker registry: control/worker-registry.json
active claims: control/claims-active.json
claim allocator: scripts/allocate_claims.py
claim contract: schemas/claim.schema.json
Master Records projection: control/heartbeat-master-records-projection.json
organization federation handoff: handoffs/SHWP-ALL-ORG-FEDERATION-001.json
```

Heartbeat cycles carry worker coordination. Heartbeat carriage does not grant execution authority; admitted task authority, capability matching, claim/fence state, policy continuity, bounded resource windows, and dependency-surface admission remain separate controls.

Cross-repository collision authority is centralized in the allocator. Repository-local entry gates may add defense in depth but may not become second global registries or second heartbeat authorities.

## Completed protocol capabilities

### Worker coordination substrate

The heartbeat-cycle worker correction remains merged and activation-observed:

```text
PR: StegVerse-Labs/.github#56
merge: a58b370480982ddc69333cde41370fa671eca060
worker_coordination.state: ACTIVE
```

Observed federation worker lease:

```text
task_id: SHWP-ALL-ORG-FEDERATION-001
goal_id: ALL-ORG-HEARTBEAT-FEDERATION-001
worker_id: organization-federation-readiness-worker
worker_instance_id: organization-federation-readiness-worker-HB11-G17
claim_id: SHWP-SHWP-ALL-ORG-FEDERATION-001-G17
fencing_token: 17
lease_start_cycle: 11
lease_end_cycle_exclusive: 267
assigned_cycles: 256
current_transition: FEDERATION_READY_WITH_MACHINE_BLOCKERS
```

### Cross-repository dependency-surface claims

Before merge `5173d22513c0e3a767703d38d6eebb844ea96a9f`, `scripts/allocate_claims.py::conflicts()` returned no conflict whenever two claims named different repositories. That repository-first rule allowed adjacent tasks to compete for the same external/runtime/deployment surface.

Corrected surfaces:

```text
scripts/allocate_claims.py
schemas/claim.schema.json
tests/test_cross_repository_dependency_claims.py
.github/workflows/org-control-plane-validate.yml
docs/CROSS_REPO_DEPENDENCY_CLAIMS_MIRROR_HANDOFF.md
```

Current invariant:

```text
repository identity does not bypass dependency-surface ownership
```

The allocator evaluates normalized `scope.dependency_surfaces` before repository identity. Shared mutable dependency surfaces conflict globally. A mutable claim with neither `dependency_surfaces` nor a non-empty `dependency_surface_exempt` reason remains queued and is reported under `blocked_missing_dependency_declaration`; it is not silently allocated.

The regression suite proves `StegVerse-Labs/Site` and `StegVerse-Labs/StegCore` cannot simultaneously acquire mutable `hosting:render` claims. Render is a regression fixture, not heartbeat authority, worker authority, deployment authority, or an activation prerequisite.

### Site defense in depth

```text
StegVerse-Labs/Site issue: #259 CLOSED_COMPLETED
PR: #260 MERGED
merge: c2fa9d436381f13c109125367ce803518d4ff2e4
claim registry: StegVerse-Labs/Site/data/session-work-claims.json
machine claim: SITE-PREWORK-CLAIM-GATE-MACHINE-001
machine owner: github-actions:ecosystem-heartbeat-orchestration
machine-claim transfer commit: 3afba810ded42fd32cba659c6de51612bcfad504
completion handoff: StegVerse-Labs/Site/docs/SESSION_PREWORK_CLAIMS_MIRROR_HANDOFF.md
```

Site's gate owns local admission/orchestration only. It cannot mint product execution authority or replace the organization allocator.

## Validation evidence

Cross-repository allocator implementation head:

```text
Validate organization control plane: run 31331101395 SUCCESS
Heartbeat Worker Project: run 31331101399 SUCCESS
```

Main after PR #58 merge:

```text
Validate organization control plane: run 31331122402 SUCCESS
Heartbeat Worker Project: run 31331122385 SUCCESS
```

The main Heartbeat Worker Project re-proved native heartbeat semantics, worker coordination subsignal/cycle leases, ambiguity-safe executor discovery, blocked recheck/human authority boundaries, bounded goal lineage/duplicate control, bounded resource authority, checkpoints/fencing, capability profiles, fail-closed convergence, sovereign heartbeat host semantics, and current successor posture.

Site local/main validation:

```text
branch heartbeat orchestration: 31330859460 SUCCESS
branch Site Handoff Orchestrator: 31330859465 SUCCESS
branch Site Bootstrap Validate: 31330859473 SUCCESS
branch Session Retirement Validate: 31330859476 SUCCESS
post-merge main heartbeat: 31330951273 SUCCESS
machine-claim transfer heartbeat: 31330976764 SUCCESS
```

The final handoff contract is itself validated by Org Aggregation Check and Org Continuation Check; no archive claim is valid while either is failing.

## Human authority boundary — durable runtime activation

Sovereign continuous-carrier activation remains a separate production goal:

```text
owner: StegVerse-Labs/.github#12
handoff: handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json
state: BLOCKED_RUNTIME_ACTIVATION
block: SOVEREIGN_NODE_RUNTIME_NOT_YET_OBSERVED
```

Production activation requires one StegVerse-owned or federated node to prove native service registration, continuous runtime from durable local storage, heartbeat epoch advancement under runtime-v9 timing authority, heartbeat-owned worker checkpoint response, controlled restart, no epoch/registry regression, no duplicate heartbeat/claim/fence split brain, and durable registry/event/cost/receipt/checkpoint reconstruction after restart.

This separate block does not invalidate the documented-worker archival alternative because heartbeat-owned workers have already been observed as claimed, fenced, and cycle-leased through the canonical registry.

## Cross-repository dependencies / propagation

Canonical organization-wide readiness continuation:

```text
task: SHWP-ALL-ORG-FEDERATION-001
handoff: handoffs/SHWP-ALL-ORG-FEDERATION-001.json
registry: control/worker-registry.json
receipt: receipts/organization-federation/SHWP-ALL-ORG-FEDERATION-001.json
worker: organization-federation-readiness-worker
carrier: worker_coordination heartbeat subsignal
```

The federation receipt represents all 14 canonical organizations with zero unassigned organizations. Blocked organizations retain machine-observable release conditions:

```text
AaCT-E: CONNECTOR_WRITE_AUTHORITY -> integration gains push authority or an AaCT-E-owned relay appears
ECAT-ICAT-Formal: NO_REPOSITORY -> organization exposes a repository capable of canonical handoff/adapter ownership
Infrastructure-Continuity-Ventures: NO_REPOSITORY -> organization exposes a repository capable of canonical handoff/adapter ownership
Triad-Test: NO_REPOSITORY -> organization exposes a repository capable of canonical handoff/adapter ownership
```

Master Records custody/reconstruction continuation remains distinct from execution authority:

```text
source: control/heartbeat-master-records-projection.json
destination: master-records/orchestration
consumer handoff: master-records/orchestration/WORKER_LIFECYCLE_CUSTODY_MIRROR_HANDOFF.md
hosted destination validation: machine-owned runner release condition retained by destination
```

Downstream heartbeat-cycle lease migration remains owned by `StegVerse-Labs/admissibility-wiki` issue #50 and its canonical mirror handoff. No second heartbeat or duplicate worker registry is authorized downstream.

## Collision and authority boundaries

- One canonical heartbeat only.
- One canonical worker registry only.
- Repository identity never bypasses a declared global dependency-surface collision.
- GitHub Actions cron is validation/evidence carriage, not heartbeat cadence.
- Render is not a heartbeat, worker, or activation dependency.
- Cloudflare is not heartbeat or worker activation authority.
- Heartbeat carriage does not grant task authority.
- Worker capability matching does not grant authorization.
- Master Records custody is reconstructive evidence, not execution authority.
- A blocked worker remains blocked while its lease is carried.
- Do not duplicate all-organization federation work outside `SHWP-ALL-ORG-FEDERATION-001`.

## Session consolidation

```text
SITE-259-PREWORK-CLAIM-ENFORCEMENT
  owner: StegVerse-Labs/Site/data/session-work-claims.json#SITE-PREWORK-CLAIM-GATE-MACHINE-001
  state: COMPLETE_MERGED_MACHINE_OWNED
  evidence: Site PR #260; run 31330976764 SUCCESS
  unique chat work: none

CROSS-REPO-DEPENDENCY-CLAIMS-001
  owner: docs/CROSS_REPO_DEPENDENCY_CLAIMS_MIRROR_HANDOFF.md
  issue: #57 CLOSED_COMPLETED
  state: COMPLETE_MERGED_MAIN_VALIDATED
  evidence: PR #58 merge 5173d225; runs 31331122402 and 31331122385 SUCCESS
  unique chat work: none

ALL-ORG-HEARTBEAT-FEDERATION-001
  owner: handoffs/SHWP-ALL-ORG-FEDERATION-001.json
  state: MACHINE_OWNED_ACTIVE_WITH_BLOCKERS
  next: heartbeat rechecks explicit organization release conditions

SHWP-DURABLE-RUNTIME-ACTIVATION
  owner: handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json + issue #12
  state: DISTINCT_PRODUCTION_ACTIVATION_GOAL
  next: sovereign continuous-carrier and restart/reconstruction proof
```

Session goal denominator for the orchestration-collision correction:

```text
required Site developed/integration surfaces: 6
required organization developed/integration surfaces: 5
required hosted validation groups: 10
required machine-owned continuation transfers: 2
required unique session goals transferred/completed: 5
```

Current completion:

```text
Site developed/integration surfaces: 6/6
organization developed/integration surfaces: 5/5
hosted validation groups: 10/10
machine-owned continuation transfers: 2/2
session goals transferred/completed: 5/5
scaffolding/stubs in required correction set: 0
missing required correction files: 0
session unique active claims: 0
current correction goal activation: 100%
thread_archive_ready: true
```

MERGED INTO: `StegVerse-Labs/.github/docs/ORG_MIRROR_HANDOFF.md`

MERGED INTO: `StegVerse-Labs/.github/docs/CROSS_REPO_DEPENDENCY_CLAIMS_MIRROR_HANDOFF.md`

MERGED INTO: `StegVerse-Labs/.github/handoffs/SHWP-ALL-ORG-FEDERATION-001.json`

MERGED INTO: `StegVerse-Labs/Site/data/session-work-claims.json#SITE-PREWORK-CLAIM-GATE-MACHINE-001`
