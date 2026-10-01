# Organization Role — per-organization deployment

Packet: `ORGANIZATION-ROLE-DEPLOYMENT-PACKET-001` (`data/organization-role-deployment/packet.v1.json`)
Declaration: `ORGANIZATION-ROLE-RUNTIME-REALITY-DEPLOYMENT-001`
Evidence class: `SOURCE_IMPLEMENTED`. No runtime observation, no goal closure, and no mutation of any other organization is claimed.

`ORGANIZATION-ROLE-RUNTIME-REALITY-DEPLOYMENT-001` says the Organization Role deploys **per organization, in each organization's own `.github`**. It did not say how. This is the how — the generalized sequence, not a procedure for one organization.

## Why this is a packet rather than a sweep

Each organization's `.github` is its own repository under its own owner. A session reaches exactly the repositories selected when it started, plus what it can attach afterwards — and a repository whose name begins with `.` cannot be attached mid-session at all. So one session cannot deploy across organizations, however the work is sequenced. The deployable unit is therefore one organization per session, and what travels between sessions is this packet.

## Running it

From a session with the target organization's `.github` checked out:

```
python3 scripts/verify_organization_role_deployment.py --org-root <path-to-that-checkout>
```

It reads source only: no connection, no receiver, no device inventory, no authority. Exit `0` means deployed. Exit `1` prints one finding per gap, each carrying `failure_code`, `failed_predicate`, `required_evidence_or_repair`, `retry_entrypoint`, `owning_existing_goal` and `next_attempt`. Work the findings, re-run, and the exit status is the completion test.

The verifier lives in `StegVerse-Labs/.github`, which is public. A session working in another organization can read it without attaching anything.

## Target state

Four artifacts, described exactly in the packet's `target_state`:

1. **`.stegverse/transition-ledger/org-contract.json`** — consumes **both** `stegverse.repo-transition-receipt/v1` and `stegverse.canonical-state-transition-receipt/v1`; declares the organization scope rule; preserves the source transition receipt; and carries the Organization Role fields (`runtime_reality_authority: Organization`, ledger root as locus, ledger lock, manifest-directed append, master-records as released-batch recorder that does not gate the organization's reality, `always_on_receiver_required: false`).

2. **`resident-runtime/aggregate_repo_transition.py`** — its source verifier accepts every schema the contract's `consumes` names, rather than one hard-coded schema, and binds a canonical state transition by its own digest instead of relabelling it a repository transition. `StegVerse-Labs`' `verify_source` is the implementation to copy.

3. **`data/organization-role-runtime-reality-deployment.json`** — the organization's own copy of the declaration, with its own name and deployment scope.

4. **`data/organization-role-exemption-register.json`** — opens empty, and refuses the justifications the standard already forbids.

## The contract generalization is due on its own

An organization whose contract consumes repository receipts only has no path from a canonical governed transition to an organization receipt. Such a transition is **dropped, not recorded** — which contradicts the organization scope rule the same contract is meant to declare. That gap exists whether or not the role change is deployed, and it should be closed first.

It is live in `StegVerse-org`: the SDK lives there and, as of `StegVerse-org/StegVerse-SDK` #416, manifests canonical state transitions through Interlock/InTr. Under the scope rule each should emit an organization receipt. None currently can.

## Reference implementation

`StegVerse-Labs/.github` on `main`, deployed in PR #2899. The contract, the aggregator's `verify_source`, the declaration, the exemption register and the enforcing validator are all there to copy from rather than re-derive.

## Measured state

`organization_register` in the packet records what was observed and when, per organization — `DEPLOYED` for `StegVerse-Labs`, `RECORDING_MECHANISM_PRESENT_ROLE_NOT_DEPLOYED` for `StegVerse-org` at commit `ef34106`, and the organizations not yet measured. It is an observation record, not an instruction to any organization.

## What this packet does not do

It mutates no other organization, claims no runtime observation, grants no transition, execution, custody or credential authority, requires no external machine or second device, and closes no goal.
