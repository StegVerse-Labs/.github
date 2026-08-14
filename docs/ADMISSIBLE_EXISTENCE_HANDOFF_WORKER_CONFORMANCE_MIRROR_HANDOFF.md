# Admissible-Existence Handoff + Worker Conformance Mirror Handoff

## Source of truth

```text
organization: StegVerse-Labs
repository: .github
branch: feat/ae-handoff-worker-conformance-gate
goal_id: AE-HANDOFF-WORKER-CONFORMANCE-001
canonical_semantics: StegVerse-Labs/StegCore@7d94908be562f9f9ace05877d4507dc68c984e06 + c63b4cce408bc8b3a9c33c6417d96d959678ac19
credential_authority: TV/TVC
github_token_runtime_authority: NONE
```

## Purpose

Create one canonical organization verification process for both executable HANDOFF records and Worker Task Registry records so recently completed, current, and future task state cannot drift from StegCore Admissible-Existence semantics.

The gate verifies the lifecycle distinction:

```text
DECLARED -> STANDING -> ADMISSIBLE -> ACTIVATED -> SUSPENDED/SUPERSEDED/TERMINATED
```

`COMPLETED`, source presence, validation success, or repository merge never imply `ACTIVATED`. Activation requires explicit integration evidence and an activation proof. Blocked ADMISSIBLE capability state requires a durable continuation owner.

## Installed surfaces

```text
control/admissible-existence-conformance-policy.json
scripts/validate_admissible_existence_conformance.py
.github/workflows/validate-ae-handoff-worker-conformance.yml
docs/ADMISSIBLE_EXISTENCE_HANDOFF_WORKER_CONFORMANCE_MIRROR_HANDOFF.md
```

The workflow also executes the pre-existing ownership and executable-handoff validators before AE conformance validation.

## Coverage

The validator scans:

1. `handoffs/*.json` with `stegverse.executable-handoff/v0.1`;
2. `control/worker-registry.json` tasks;
3. `control/worker-registry.d/*.json` task fragments;
4. explicit `admissible_existence` contracts where present.

Historical/pre-policy records are projected conservatively: completion defaults to ADMISSIBLE, never ACTIVATED. New or materially updated task records must carry an explicit `admissible_existence` block under the organization policy.

## First consumer binding

`STEGFIN-CONTINUITY-CARRIER-007` is the first cross-surface exemplar. Its executable HANDOFF and worker-registry fragment both identify:

```text
capability_id: stegverse:capability:stegfin-continuity-pretrade:v1
phase: ADMISSIBLE
blocker: WALLET_HANDOFF_READY_NOT_YET_OBSERVED
credential_authority: TV/TVC
github_token_runtime_authority: NONE
```

This prevents the 7/8 source/integration maturity state from being represented as ACTIVATED before the real machine-owned `WALLET_HANDOFF_READY` proof exists.

## Verification procedure

```text
python3 scripts/validate_handoff_execution_ownership.py
python3 scripts/validate_executable_handoffs.py
python3 scripts/validate_admissible_existence_conformance.py
```

The hosted workflow performs anonymous public source fetch with empty GitHub permissions and explicitly rejects GitHub/PAT/TVC credential environment variables. Hosted validation grants no production authority.

## Execution ownership and collision partition

### MANUAL / SESSION-STARTABLE

```yaml
- task_id: AE-HANDOFF-WORKER-CONFORMANCE-001
  execution_owner: bounded organization validation/reconciliation lane
  claim_state: CLAIMED_ON_BRANCH
  worker_registry_ref: NONE
  manual_execution_allowed: true
  collision_scope: conformance policy, validator, credential-clean validation workflow, and explicit AE metadata only
  release_condition: validation passes and canonical merge completes
  next_executable_action: run PR validation and merge if green
```

### WORKER-OWNED / DO NOT COMPETE

No runtime, heartbeat, TV/TVC provider, wallet, or trade-execution worker scope is modified by this task.

### ESCALATED / AUTHORITY-OWNED

TV/TVC remains sole credential/route authority. USER_ONLY remains wallet signing/broadcast authority.

### COMPLETED / SUPERSEDED

Existing ownership, active-worker, and executable-handoff validators remain canonical and are composed into this gate rather than replaced.

## Release condition

This goal is complete when the policy, validator, workflow, and StegFin exemplar bindings are merged after passing organization validation. Future task writers must conform to the explicit AE contract; legacy records remain visible through conservative projection until migrated.
