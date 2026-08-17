# TVC Repository Broker Validation Carrier Mirror Handoff

## Canonical authority

```text
goal_id: TVC-REPOSITORY-BROKER-VALIDATION-CARRIER-001
repository: StegVerse-Labs/.github
branch: main
originating_goal: eliminate the unbound TV/TVC-owned local validation carrier blocking StegVerse-Labs/TVC PR #20 and downstream private StegCore validation
canonical_owner: StegVerse-Labs/.github heartbeat worker runtime for validation carrier only
upstream_owner: StegVerse-Labs/TVC PR #20 / TVC-GITHUB-REPOSITORY-OPERATION-BROKER-001
credential_authority: TV/TVC
non_tv_tvc_secret_or_token_allowed: false
render_required: false
implementation_claim: RELEASED_TO_MACHINE_WORKER
validation_claim: MACHINE_OWNED
```

## Installed surfaces

```text
handoffs/SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001.json
workers/tvc_repository_broker_validation_worker.py
control/worker-registry.d/tvc-repository-broker-validation-001.json
control/process-worker-adapters.d/tvc-repository-broker-validation-001.json
tests/test_tvc_repository_broker_validation_worker.py
receipts/tvc-repository-broker-validation/**   # runtime output
```

The worker does not implement or duplicate the TVC repository broker. It only locates an exact clean local TVC source root and executes the already-installed TVC task:

```text
python tools/task_dispatcher.py tvc.github_repository_operation_broker.verify
```

The validation subprocess receives no `GITHUB_TOKEN`, `GH_TOKEN`, `GITHUB_PAT`, `TVC_EPHEMERAL_GITHUB_TOKEN`, provider, cloud, wallet, seed, mnemonic, or private-key environment variable. TV/TVC remains credential authority. The worker performs no network fetch and grants no merge, repository mutation, provider, wallet, signing, broadcast, release, local-model, or StegGate authority.

## Current exact source binding

```text
TVC repository: StegVerse-Labs/TVC
PR: #20
branch: feat/github-repository-operation-broker-001
expected_head: 6209396bc9846ec5f301b24d3b6f0207e571af1d
upstream handoff: docs/GITHUB_REPOSITORY_OPERATION_BROKER_MIRROR_HANDOFF.md
upstream task: tasks/TVC-GITHUB-REPOSITORY-OPERATION-BROKER-001.json
```

If PR #20 head changes before validation, the worker fails closed with `EXACT_TVC_SOURCE_NOT_MATERIALIZED` until this binding is deliberately advanced to the reviewed new head. It must not silently validate a different commit.

## Execution states

```text
HANDOFF_READY
  worker registered and process adapter enabled

BLOCKED
  exact locally materialized TVC source is absent or dirty

FAILED
  exact source exists but the repository-native validation task fails or returns malformed/unsafe evidence

COMPLETED
  exact source validates with dispatcher status=ok and result.result=PASS and all credential/disclosure booleans false
```

## Downstream release chain

```text
carrier receipt COMPLETED
-> TVC integration authority may admit PR #20 after its own branch/task/claim consistency check
-> formalism TVC transport worker may mark broker standing CANONICAL_VALIDATED
-> StegCore private-source bridge may use TVC MATERIALIZE_SOURCE_ARCHIVE
-> StegCore PR #141 sovereign validation executes
-> only actual PASS permits StegCore merge/consumer release
```

No downstream state is inferred from this handoff alone.

## Validation

Repository tests for this carrier verify the exact head binding, credential stripping, adapter env allowlist, registry declarations, and absence of source-fetch transport in the worker. Runtime validation still requires a heartbeat execution opportunity with exact local TVC source.

## Completion inventory

```text
developed files: 5/5
scaffolding/stubs: 0
missing required files: 0
static/unit validation: pending repository test execution
runtime carrier receipt: 0/1
TVC PR #20 admission: 0/1
StegCore downstream source-materialization release: 0/1
session-specific validation-carrier requirement transferred: complete
```

## Archive condition

This support lane is archive-safe only after the worker registration is validated and all unique session requirements are durably transferred. Product activation remains separate. A runtime BLOCKED state does not authorize a PASS claim; the exact local-source release condition must remain machine-observable in the handoff and receipt.
