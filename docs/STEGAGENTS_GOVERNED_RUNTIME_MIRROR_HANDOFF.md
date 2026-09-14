# StegAgents Governed Runtime Mirror Handoff

Updated: 2026-09-14
Repository: `StegVerse-Labs/.github`
Target runtime path: `StegVerse-Labs/StegAgents` -> `StegVerse-Labs/StegCore/InTr`
Goal Task ID: `STEGAGENTS-GOVERNED-RUNTIME-001`
COSV: `71000000101001`
Status: `ACTIVE / ROUTING READY / RESIDENT PATH MERGED / WARRANT+POLICY FAIL-CLOSED REPAIR IN VALIDATION / AUTHENTIC RUNTIME PROOF PENDING`

## Canonical state

- Task Registry remains `ACTIVE / UNCLAIMED`.
- `CodeRepair-001` remains `REGISTERED_GOVERNED_PROPOSAL_ONLY`.
- exact governed manifest Git blob: `061649a4b0b43c01f3009ed3e6c8c4829559fb5b`.
- runtime profile generation `2` resolves to `canonical-work-coordination-runtime-v1`; resolution grants no authority.
- portable targeted resident selector repair is merged as `.github` PR `#1845` / `4b13c020ed249b82ffe24cd5939cfffe2534601e`.
- StegAgents warrant/policy enforcement repair is merged as `StegAgents` PR `#18` / `c82caae4c8c4cf82d40f352528269823d853f788` after CI `34873634596`, Test Readiness `34873634603`, and Cross-Agent Authority Validation `34873634684` all passed.

## Independent warrant/policy reconciliation

The registered manifest explicitly requires:

```text
warrant_required = true
policy_bundle_required = true
```

Independent review found that the pre-repair governed CodeRepair runtime validated proposal-only and authority invariants but did not enforce those two requirements before proposal construction. The WorkerCoordinator executable handoff and `canonical-task:` policy reference are not substitutes for them.

StegAgents' existing live-run contract defines the required governance inputs:

```text
STEGVERSE_WARRANT_JSON
TV_POLICY_BUNDLE_SHA256
TV_WARRANT_ISSUER_PUBKEY_B64
TV_WARRANT_MAX_TTL_SECONDS  # optional; default 900
```

The existing `src/warrant_verify.py` verifies Ed25519 signature, validity/TTL, pinned policy bundle SHA-256, repository claim, and commit claim. PR `StegAgents#18` now invokes that verifier before deterministic CodeRepair proposal construction and exposes only non-secret verification metadata into the governed request/result. Raw warrant/key material is not retained in proposal evidence.

The `.github` worker/adaptor repair on this lineage requires `warrant_verified=true` and `policy_bundle_verified=true` before WorkerCoordinator may report `COMPLETED`, and carries the existing StegAgents warrant/policy environment names into the process adapter/targeted consumer. This does not mint a warrant, grant execution authority, or create a provider credential route.

## Authority interpretation

- WorkerCoordinator claim/fence = execution delegation/fencing evidence; **not** a TV execution warrant.
- canonical Task Registry ref = coordination/task identity; **not** a pinned policy bundle.
- TV-issued signed warrant + pinned policy-bundle hash = separately required governance-admission evidence for this governed agent.
- StegCore/InTr remains transition/disposition authority.
- TV/TVC remains provider credential/provider-operation authority if a provider is ever required.
- KV/SKAP remains user-verification authority where applicable.
- Master Records remains observed-reality custody/reconstruction authority.
- GitHub/CI has runtime authority `NONE`.

No provider operation is required for the deterministic CodeRepair proof.

## Existing resident path

```text
resident source refresh
-> portable exact selector steagents_governed_runtime_targeted
-> generic resident dispatcher
-> targeted StegAgents consumer
-> refresh_and_execute_resident_task.py
-> WorkerCoordinator claim/fence
-> process:stegagents-governed-runtime-v1
-> exact manifest verification
-> TV warrant + pinned policy verification
-> deterministic proposal construction
-> SDK / StegCore/InTr governance
-> proposal returned with no consequential execution
-> claim-bound receipt
-> Master Records custody + same-run reconstruction
-> WorkerCoordinator reconciliation/egress
```

No second dispatcher, scheduler, WorkerCoordinator, runtime profile, InTr implementation, provider route, agent registry, or second-device dependency is introduced.

## Completion predicates

Authentic completion requires all of the following continuously:

1. targeted resident request consumption;
2. fresh current WorkerCoordinator claim/fence;
3. authentic TV-issued execution warrant verified for the actual local StegAgents repository/commit;
4. pinned TV policy bundle verified against the warrant;
5. exact manifest blob `061649a4b0b43c01f3009ed3e6c8c4829559fb5b`;
6. governed request identity continuous;
7. `proposal_only=true`;
8. `execution_authority=false`;
9. `self_authorization_allowed=false`;
10. authentic StegCore/InTr disposition;
11. no unauthorized provider operation and no provider credentials visible to StegAgents;
12. governed proposal returned without consequential execution;
13. exact claim-bound receipt retained;
14. Master Records custody `RECORDED` and same-run reconstruction with matching identities;
15. WorkerCoordinator reconciliation/egress complete;
16. exact-head and merged-main validation complete.

## Current authentic evidence

No authentic runtime promotion is warranted. Current canonical WorkerCoordinator projection remains claimless/unclaimed, and no claim-bound governed runtime receipt or Master Records same-run reconstruction receipt has been observed for this goal. The signed TV warrant/policy binding has also not been observed in authentic resident execution.

The source repairs do not prove runtime execution.

## First unresolved predicate

The execution sequence still reaches resident consumption before WorkerCoordinator/warrant verification, so the first unobserved runtime predicate remains:

```text
AUTHENTIC_TARGETED_RESIDENT_REQUEST_CONSUMPTION_OBSERVED
```

The next mandatory downstream predicates are fresh WorkerCoordinator claim/fence followed by authentic TV warrant and pinned-policy verification. A consumed request without those downstream proofs must fail closed and cannot complete the goal.

## Next machine-owned remediation

Run the already-existing resident selector path. On the resulting WorkerCoordinator attempt, require authentic TV-issued warrant/policy inputs and the merged StegAgents `c82caae4c8c4cf82d40f352528269823d853f788` gate. If the existing resident path cannot provide those required governance inputs, fail closed and remediate their carriage on this same lineage; do not mint a warrant in GitHub and do not treat WorkerCoordinator delegation as a warrant substitute.

## README decision

No new `.github` README capability text is required. Existing README semantics already cover targeted task/COSV execution and separated authority. The material runtime requirement itself is documented in the owning StegAgents README; this change makes the governed CodeRepair path enforce that existing requirement.

## Manual work

None.
