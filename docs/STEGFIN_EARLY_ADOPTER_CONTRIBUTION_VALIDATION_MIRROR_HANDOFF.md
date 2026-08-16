# StegFin Early Adopter Contribution Validation Mirror Handoff

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

## Installation surfaces

```text
workers/stegfin_early_adopter_contribution_validation_worker.py
control/worker-registry.d/stegfin-early-adopter-contribution-validation-001.json
tests/test_stegfin_early_adopter_contribution_validation_worker.py
```

## Execution ownership

```yaml
task_id: STEGFIN-EARLY-ADOPTER-VALIDATION-WORKER-001
execution_owner: stegfin-early-adopter-contribution-validation-worker
manual_session_execution_allowed: false
parallel_safety: DISTINCT_FROM_TRADE_AND_WALLET_WORKERS
requires_local_private_source: true
network_fetch_allowed: false
credential_authority: TV/TVC
github_token_runtime_authority: false
completion_condition: exact-bound focused tests PASS on an authorized sovereign/local source checkout and receipt is reconciled into the StegFin contribution handoff
```

## Current state

```text
HANDOFF_INSTALLED: pending branch commit
WORKER_SOURCE: pending
REGISTRY_BINDING: pending
DETERMINISTIC_TESTS: pending
MERGED: pending
LIVE_LOCAL_VALIDATION_RECEIPT: pending
```
