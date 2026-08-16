# StegFin Early Adopter Contribution Validation Mirror Handoff

Updated: 2026-08-15T21:04:00-05:00

## Goal

`STEGFIN-EARLY-ADOPTER-VALIDATION-WORKER-001`

Provide a StegVerse sovereign/local validation carrier for the private `StegVerse-Labs/stegfin-governance` early-adopter contribution-ledger workstream without introducing GitHub credential authority.

## Why this worker exists

The private StegFin repository's existing GitHub Actions validation workflows intentionally remove `GITHUB_TOKEN` and `GH_TOKEN`, then attempt anonymous checkout. Because the repository is private, checkout fails before source validation begins.

This worker solves that mismatch without weakening the credential policy:

```text
private source materialized through an already-authorized local/TV-TVC path
-> sovereign worker receives local repository path
-> worker proves exact expected source/test Git blob identities
-> worker strips credential-like environment variables from test subprocess
-> focused contribution-ledger tests run locally
-> worker emits deterministic validation receipt
```

The worker never fetches GitHub and never acquires a GitHub token.

## Source workstream

```text
repository: StegVerse-Labs/stegfin-governance
branch: feat/early-adopter-contribution-ledger-v0
PR: #4
handoff: docs/STEGFIN_EARLY_ADOPTER_CONTRIBUTION_MIRROR_HANDOFF.md
ledger_blob: 6557301476c3b7dd42a73d97409c74fc5a604494
test_blob: 380fbb392817f52dad669478b9931865dc850d1b
```

These blob identities bind the worker to the exact ledger and focused tests currently awaiting credential-compliant validation. A source change requires updating the expected binding through a new governed commit; the worker must not silently validate different code.

## Authority boundary

```text
worker validation != merge authority
worker validation != StegCoin issuance
worker validation != StegToken issuance
worker validation != Node Sovereign admission
worker validation != wallet custody
worker validation != signing/broadcast
GitHub token runtime authority: NONE
credential authority: TV/TVC
wallet signing authority: USER_ONLY
broadcast authority: USER_ONLY
```

## Required behavior

1. Require an existing local `stegfin-governance` repository path.
2. Require exact expected blob SHA for `stegwallet/contribution_ledger.py`.
3. Require exact expected blob SHA for `tests/test_contribution_ledger.py`.
4. Refuse source mismatch.
5. Strip credential-like environment variables from the test subprocess.
6. Run only the focused contribution-ledger test file.
7. Emit PASS only on test return code 0.
8. Retain stdout/stderr hashes and bounded tails in the receipt.
9. Never fetch, clone, pull, sign, broadcast, trade, or contact an external provider.

## Installed surfaces

```text
workers/stegfin_early_adopter_contribution_validation_worker.py
control/worker-registry.d/stegfin-early-adopter-contribution-validation-001.json
tests/test_stegfin_early_adopter_contribution_validation_worker.py
```

## Current state

```text
HANDOFF_INSTALLED: COMPLETE
WORKER_SOURCE: COMPLETE
REGISTRY_BINDING: COMPLETE
AUTHORIZED_LOCAL_PRIVATE_SOURCE_PATH_OBSERVED: FALSE
LIVE_LOCAL_VALIDATION_RECEIPT: PENDING
worker_registry_state: HANDOFF_READY
worker_status: AVAILABLE
blocker: AUTHORIZED_LOCAL_PRIVATE_SOURCE_PATH_NOT_YET_OBSERVED
credential_authority: TV/TVC
github_token_runtime_authority: NONE
```

The current registry fragment `control/worker-registry.d/stegfin-early-adopter-contribution-validation-001.json` is authoritative over stale implementation-branch prose. It binds the worker only to an already materialized authorized local private source and does not grant network-fetch or source-mutation authority.

## Execution ownership and collision partition

### MANUAL / SESSION-STARTABLE

```yaml
- task_id: STEGFIN-EARLY-ADOPTER-VALIDATION-SOURCE-CHECK
  execution_owner: validation session only for public control-plane worker source/tests when explicitly claimed
  claim_state: UNCLAIMED_VALIDATION_ONLY
  worker_registry_ref: control/worker-registry.d/stegfin-early-adopter-contribution-validation-001.json
  manual_execution_allowed: true
  collision_scope: public worker source/test validation only; excludes private StegFin source mutation, trade/wallet paths, issuance, custody, signing and broadcast
  release_condition: worker source/tests are validated and evidence is durably recorded, then validation claim releases
  next_executable_action: validate only if current public worker source lacks directly inspectable PASS evidence; do not access private source through GitHub credentials
```

### WORKER-OWNED / DO NOT COMPETE

```yaml
- task_id: STEGFIN-EARLY-ADOPTER-VALIDATION-WORKER-001
  execution_owner: stegfin-early-adopter-contribution-validation-worker
  claim_state: HANDOFF_READY_MACHINE_OWNED
  worker_registry_ref: control/worker-registry.d/stegfin-early-adopter-contribution-validation-001.json
  manual_execution_allowed: false
  collision_scope: exact-bound focused validation of already materialized authorized local StegFin source only
  release_condition: eligible StegVerse sovereign/local source path is observed, exact ledger/test blobs match, focused tests execute with credentials stripped, and deterministic PASS/FAIL_CLOSED receipt is retained
  next_executable_action: wait for an authorized local private source path; when present, execute the registered worker without network fetch
```

### ESCALATED / AUTHORITY-OWNED

```yaml
- task_id: STEGFIN-EARLY-ADOPTER-PRIVATE-SOURCE-MATERIALIZATION
  execution_owner: TV/TVC-authorized StegVerse source/materialization authority
  claim_state: AUTHORITY_OWNED_BLOCKED
  worker_registry_ref: canonical TV/TVC contracts + StegVerse-Labs/stegfin-governance contribution handoff
  manual_execution_allowed: false
  collision_scope: authorized private-source availability only; no GitHub credential workaround and no worker-side clone/fetch
  release_condition: exact authorized local private stegfin-governance source path is materialized and visible to the worker
  next_executable_action: materialize source only through an already-authorized StegVerse/TV-TVC path; otherwise remain BLOCKED
```

### COMPLETED / SUPERSEDED

```yaml
- task_id: STEGFIN-EARLY-ADOPTER-VALIDATION-WORKER-SOURCE
  execution_owner: StegVerse-Labs/.github
  claim_state: COMPLETE_INSTALLED
  worker_registry_ref: control/worker-registry.d/stegfin-early-adopter-contribution-validation-001.json
  manual_execution_allowed: false
  collision_scope: worker implementation, registry binding and deterministic source tests already installed
  release_condition: SATISFIED for installed source surfaces
  next_executable_action: NONE_SOURCE_INSTALLATION
```

## Next executable actions

The machine-owned worker remains fail-closed until an eligible StegVerse sovereign/local surface already contains the exact authorized private StegFin source. It then validates the exact bound blobs, strips credential-like environment variables, runs focused tests, and emits its receipt. No GitHub token, Render/provider runtime, wallet secret, signing, broadcast, trade, or external provider contact is permitted.
