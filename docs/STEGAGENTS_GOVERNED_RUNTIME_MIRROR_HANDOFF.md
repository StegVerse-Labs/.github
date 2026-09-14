# StegAgents Governed Runtime Mirror Handoff

Updated: 2026-09-14
Repository: `StegVerse-Labs/.github`
Target runtime path: `StegVerse-Labs/StegAgents` -> `StegVerse-Labs/StegCore/InTr`
Goal Task ID: `STEGAGENTS-GOVERNED-RUNTIME-001`
COSV: `71000000101001`
Status: `ACTIVE / CANONICAL WORK RESIDENT REQUEST STAGED / AUTHENTIC RUNTIME PROOF PENDING`

## Goal

Activate and prove the first governed StegAgents runtime path using the already-registered `CodeRepair-001` governed manifest while reusing the existing WorkerCoordinator, StegCore/InTr, TV/TVC provider boundary if required, and Master Records reconstruction path.

## Proven predecessor and registration

- `STEGAGENTS-GOVERNED-AGENT-REGISTRATION-001` is `RETIRED / COMPLETED`.
- `CodeRepair-001` is `REGISTERED_GOVERNED_PROPOSAL_ONLY`.
- StegAgents source merge: `b768eeeb0ceca14fcfd50ce665cd6c0885e2774f`.
- StegAgents source handoff closure merge: `b639c2674959e3be9fb7a70caa33115c694af764`.
- StegCore 001/002 baseline is `activated`.
- StegAgents/StegCore handshake is `handshake_ready`.
- Runtime Goal Task registration merged through `.github` PR `#1827` as `a06d9d3b8c564f267c2a9b9ffcd9826a798dc168` after Organization Control, Heartbeat and Deterministic validation passed.

Source/CI state is not runtime proof.

## Existing runtime reuse

The runtime task is staged through the already-existing `canonical_work_coordination` resident consumer. No new dispatcher, scheduler, WorkerCoordinator, InTr implementation, provider route, credential path or runtime substrate is introduced.

Staged source surfaces:

- `control/resident-execution-request.d/canonical-work-stegagents-governed-runtime-001.json`
- existing `control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py`, extended with one explicit task subject
- existing `scripts/dispatch_resident_execution_requests.py` selector `canonical_work_coordination`
- existing Canonical Work event bootstrap and stale-registry shard materialization path

The request itself has `authority_effect: NONE_REQUEST_ONLY`, requires no GitHub token, requires no second machine, performs no network source fetch, and keeps TV/TVC as credential authority.

## Reuse-only boundary

Canonical authority remains:

- Task Registry: coordination intent only.
- WorkerCoordinator: execution claim/fence.
- StegCore/InTr: governed ingress/disposition/state-transition authority.
- TV/TVC: provider credential and provider-operation authority.
- KV/SKAP Vault: user-verification authority where applicable.
- Master Records: observed-reality custody/reconstruction.
- GitHub: source/evidence coordination only; runtime authority `NONE`.

## Required runtime evidence chain

```text
canonical runtime task registration
-> canonical_work_coordination resident request consumption
-> exact CodeRepair-001 governed manifest identity
-> current WorkerCoordinator claim/fence
-> governed request identity
-> existing StegAgents proposal path
-> existing StegCore/InTr ingress
-> authentic governance disposition
-> TV/TVC provider operation only if required
-> governed proposal result returned
-> exact evidence retention
-> Master Records reconstruction
-> canonical task reconciliation/egress
```

Required invariants throughout:

```text
proposal_only = true
execution_authority = false
self_authorization_allowed = false
provider credentials visible to StegAgents = false
```

## Current runtime observation

The authorized direct resident-command channel was checked from this session and returned `No devices available`. This is classified only as current reachability evidence. It is not a requirement for a second device, does not mark any canonical substrate unsuitable, and does not substitute for the existing resident-request path.

Authentic current evidence still required:

- WorkerCoordinator claim/fence for `STEGAGENTS-GOVERNED-RUNTIME-001`;
- Canonical Work/InTr ingress consumption for this task;
- governed `CodeRepair-001` request/result evidence;
- TV/TVC provider operation only if actually required;
- Master Records reconstruction.

## Completion predicates

The task may be retired only after authentic current evidence exists for:

1. fresh WorkerCoordinator claim/fence;
2. exact `CodeRepair-001` governed request identity;
3. StegCore/InTr ingress and disposition;
4. proposal-only/no-self-authority invariants;
5. TV/TVC provider operation if model/provider execution is actually required;
6. returned governed proposal receipt;
7. Master Records reconstruction of the exact chain;
8. exact-head validation and merged-main revalidation of any source changes required to support the authentic path.

## Failure handling

A missing predicate is remediation metadata, not permission to fabricate evidence and not justification for creating a duplicate runtime. Continue through the existing authority ceiling and record the first unresolved predicate plus the exact next authorized remediation.

## README decision

No `.github` README change is required for this bounded addition because it does not change repository responsibility or add a new runtime class; it adds one explicit subject to the already-documented Canonical Work resident-consumer mechanism. This handoff remains the canonical task-specific documentation.

## Runtime non-claims

Registration, source preparation, CI, standing requests, fixtures, or workflow success do not prove WorkerCoordinator claim/fence, InTr admission, provider execution, proposal return, KV/SKAP verification, or Master Records reconstruction.

## Manual work

None.
