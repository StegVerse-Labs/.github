# Universal System Work Interlock Mirror Handoff

Updated: 2026-09-04
Organization: StegVerse-Labs
Repository: StegVerse-Labs/.github
Goal: UNIVERSAL-WORK-INTERLOCK

## Source of truth

This file is the bounded continuation record for requiring Interlock + InTr ingress and egress around all governed system work. Organization-level runtime boundary authority remains `ORG_RESIDENT_RUNTIME_INTR_BOUNDARY_MIRROR_HANDOFF.md` and `org-runtime/interlock-intr.json`.

## Problem

System work has been able to accumulate as sessions, repository tasks, failure emails, runtime observations, implementation changes, custody work, publication work, and handoff updates without every transition being represented through a common ingress/egress boundary. That makes it difficult to distinguish productive expansion from systemic stagnation, correlate repeated failure manifestations, identify shared blockers, and reconstruct why work entered or left a governed state.

## Required universal work topology

Every admitted unit of system work must be representable as:

```text
source stimulus
-> INGRESS INTERLOCK
-> InTr materialization
-> canonical work identity / dependency / authority context
-> WorkerCoordinator admission or explicit non-execution classification
-> governed work transitions
-> completion | blocked | failed | superseded | deferred
-> EGRESS INTERLOCK
-> InTr materialization
-> receiving consumer / next owner / closure projection
```

The rule applies to, at minimum:

- ChatGPT/session-originated implementation work
- repository task admission and completion
- cross-repository and cross-organization handoffs
- runtime requests and runtime receipts
- GitHub failure/problem email normalization and incident promotion
- custody/reconstruction work
- publication/admissibility/Guardian propagation
- user action requests and fulfillment receipts
- defect promotion from repeated session/blocker/failure convergence
- release/tag/readiness transitions

## Ingress minimum record

Each work ingress must preserve enough data to reconstruct why the work entered the system:

- work_id / correlation_id
- source type and source identity
- originating session/task/issue/email/runtime event when available
- normalized goal
- affected organization/repository/component
- dependency set
- known blocker set
- requested authority/effect
- applicable TV/TVC or other authority references
- duplicate/convergence references
- source timestamp
- source evidence/hash references where available
- explicit nonclaims

## Egress minimum record

Each work egress must preserve enough data to reconstruct what happened to the admitted work:

- work_id / correlation_id
- terminal or transfer state
- exact result/evidence references
- files/modules changed where applicable
- validation/runtime/custody evidence separately classified
- unresolved blockers
- next owner / receiving surface
- downstream propagation targets
- human action required, if any
- closure reason
- egress timestamp
- authority effect

## Convergence-pressure integration

Session backlog, normalized GitHub failure emails, repeated blockers, repeated human requests, and runtime failures are evidence inputs, not independent task authorities.

When multiple ingress records normalize to the same unresolved predicate, the system should promote one ecosystem-level incident/defect and bind all dependent work identities to it. Duplicate remediation must not silently proceed around an active authoritative owner.

Repair of the promoted defect must trigger reevaluation of dependent work before new human requests or duplicate implementation lanes are created.

## Authority boundary

Interlock/InTr records and carriers do not self-grant execution, credential, admission, publication, custody, or transition authority. HB-derived carriers remain synchronization/reference transport only. TV/TVC remains credential authority. GitHub token runtime authority remains NONE.

## Implementation targets

Destination `StegVerse-Labs/.github`:

- universal work ingress/egress schema
- work correlation registry
- convergence/incident normalization model
- WorkerCoordinator admission hooks
- GitHub failure-email incident adapter
- session/handoff work adapter
- validator requiring ingress before governed work execution and egress before closure/transfer
- cross-repository propagation contract

Destination participating repositories:

- repository-local adapters that expose work/event profiles to the organization boundary
- no independent replacement of the canonical organization Interlock/InTr owner

## Completion predicates

1. Every governed work item has a stable work/correlation identity.
2. Every admitted work item has an ingress Interlock/InTr materialization.
3. Every terminal/transfer state has an egress Interlock/InTr materialization.
4. Cross-session and GitHub-failure convergence can be queried by correlation/dependency.
5. Duplicate work can be detected before conflicting implementation begins.
6. Human action requests are represented once and shared by dependent work.
7. Closure/transfer cannot be called complete without egress evidence.
8. No authority is inferred from GitHub, CI, HB, handoffs, or source state.

## Remaining files/modules to install

Destination `StegVerse-Labs/.github`:

- `schemas/universal-work-interlock.schema.json`
- canonical work correlation/incident registry
- ingress/egress emitter + validator
- GitHub failure-email normalization adapter
- session/handoff ingress adapter
- dependent-work reevaluation hook

## Archive readiness

Not archive-ready until the universal work ingress/egress contract is machine-enforced and at least one real end-to-end work item has both ingress and egress materializations through the canonical Interlock/InTr boundary.
