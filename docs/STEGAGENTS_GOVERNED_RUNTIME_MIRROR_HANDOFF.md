# StegAgents Governed Runtime Mirror Handoff

Updated: 2026-09-14
Repository: `StegVerse-Labs/.github`
Target runtime path: `StegVerse-Labs/StegAgents` -> `StegVerse-Labs/StegCore/InTr`
Goal Task ID: `STEGAGENTS-GOVERNED-RUNTIME-001`
COSV: `71000000101001`
Status: `ACTIVE / RUNTIME PROOF PENDING`

## Goal

Activate and prove the first governed StegAgents runtime path using the already-registered `CodeRepair-001` governed manifest while reusing the existing WorkerCoordinator, StegCore/InTr, TV/TVC provider boundary if required, and Master Records reconstruction path.

## Proven predecessor

- `STEGAGENTS-GOVERNED-AGENT-REGISTRATION-001` is `RETIRED / COMPLETED`.
- `CodeRepair-001` is `REGISTERED_GOVERNED_PROPOSAL_ONLY`.
- StegAgents source merge: `b768eeeb0ceca14fcfd50ce665cd6c0885e2774f`.
- StegAgents source handoff closure merge: `b639c2674959e3be9fb7a70caa33115c694af764`.
- StegCore 001/002 baseline is `activated`.
- StegAgents/StegCore handshake is `handshake_ready`.

Source/CI state is not runtime proof.

## Reuse-only boundary

Do not create another agent registry, scheduler, governance engine, credential path, WorkerCoordinator, InTr implementation, provider route, or runtime substrate.

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

No README update is required for this registration-only change. Update the appropriate repository README only if runtime activation adds or materially changes a supported user/developer-facing capability.

## Runtime non-claims

Registration, source preparation, CI, standing requests, fixtures, or workflow success do not prove WorkerCoordinator claim/fence, InTr admission, provider execution, proposal return, KV/SKAP verification, or Master Records reconstruction.

## Manual work

None.
