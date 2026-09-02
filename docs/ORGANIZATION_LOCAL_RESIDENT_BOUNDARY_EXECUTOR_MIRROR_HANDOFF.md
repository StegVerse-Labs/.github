# Organization-Local Resident Boundary Executor Mirror Handoff

Updated: 2026-09-02
Repository: `StegVerse-Labs/.github`
Issue: `#713`
State: HANDOFF_ESTABLISHED / SOURCE_IMPLEMENTATION_PENDING
Credential authority: TV/TVC
GitHub token runtime authority: NONE
Authority effect: NONE

## Goal

Implement the organization-local resident boundary process owned by this organization's `.github` repository.

The process must run only as a sovereign local resident process and provide bounded Interlock/InTr ingress/egress spool handling and durable receipts without turning GitHub, GitHub Actions, HB carrier presence, or request transport into runtime authority.

## Governing constraints

- Read `docs/ORG_MIRROR_HANDOFF.md` and the most specific applicable Interlock/InTr and heartbeat handoffs before mutation.
- Reuse existing organization runtime/transport profiles and WorkerCoordinator admission semantics.
- TV/TVC remains sole credential authority.
- GitHub/GitHub Actions may validate source/evidence but are never production/runtime/control-plane authority.
- HB and HB-derived carrier presence are synchronization/transport evidence only and grant no admission, execution, claim/fence, credential, routing, receiving, transition, publication, custody, or consequence authority.
- Transition-Element-derived standing/effects remain authoritative where applicable.
- No arbitrary command or task transport.
- No network source fetch as execution authority.
- No second scheduler, heartbeat, or worker coordinator.
- Missing local runtime prerequisites fail closed with a machine-actionable next step.

## Required source surfaces

At minimum, implementation should introduce or bind:

```text
workers/organization_local_resident_boundary_executor.py
control/process-worker-adapters.d/organization-local-resident-boundary-executor-001.json
control/worker-registry.d/organization-local-resident-boundary-executor-001.json
control/task-vectors/ORGANIZATION-LOCAL-RESIDENT-BOUNDARY-EXECUTOR-001.json
handoffs/ORGANIZATION-LOCAL-RESIDENT-BOUNDARY-EXECUTOR-001.json
cost-basis/worker-runtime/organization-local-resident-boundary-executor.json
tests/test_organization_local_resident_boundary_executor.py
receipts/organization-local-boundary/**              # runtime output only
spool/organization-local-boundary/ingress/**          # resident-local bounded state
spool/organization-local-boundary/egress/**           # resident-local bounded state
```

Implementation may use different final paths only if current main already contains a canonical equivalent and the handoff is updated to point to that existing owner rather than creating duplicates.

## Runtime contract

```text
resident local Interlock/InTr ingress spool
-> exact packet/profile validation
-> current WorkerCoordinator admission/claim/fence when execution is required
-> bounded local handler
-> durable local receipt
-> exact governed egress packet
-> resident local egress spool
```

Ingress receipt/request existence alone grants no authority. Egress construction likewise grants no publication, network, or external-system authority.

## Required receipt properties

Every durable boundary receipt must preserve at least:

- packet/profile identity;
- exact payload hash;
- relevant carrier-binding identity when present;
- Transition-Element standing/effect basis where applicable;
- WorkerCoordinator claim/fence identity for executed actions;
- credential authority `TV/TVC`;
- GitHub token runtime authority `NONE`;
- explicit authority effect;
- exact disposition;
- no canonical-state-change claim unless independently authorized by the governing subsystem.

## Completion boundary

Source completion requires:

1. scoped worker/adapter/registry/handoff/task-vector/cost-basis surfaces;
2. bounded ingress + egress spool contract;
3. tests for fail-closed profile drift, request-authority confusion, carrier-authority confusion, stale fence, forbidden credentials, and exact receipt reconstruction;
4. current COSV denominator reconciliation;
5. organization-control + Heartbeat validation passing;
6. merge to current main.

Authentic activation remains separate and requires deployment-local evidence proving that the sovereign resident process consumed an admitted ingress item and persisted the expected boundary receipt/egress state.

## Current evidence state

```text
scoped handoff: ESTABLISHED
source implementation: PENDING
source validation: PENDING
merge: PENDING
resident activation: NOT OBSERVED
authentic ingress consumption: NOT OBSERVED
authentic egress persistence: NOT OBSERVED
credential authority: TV/TVC
authority effect: NONE
```

## Next authorized machine action

Inspect current main for reusable organization runtime/transport primitives and implement only the missing bounded resident boundary surfaces above. Do not create a duplicate runtime if a canonical equivalent already exists.
