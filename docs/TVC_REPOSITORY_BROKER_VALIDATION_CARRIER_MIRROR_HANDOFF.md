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
validation_claim: VALIDATED_REPOSITORY_INTEGRATION_MACHINE_RUNTIME_PENDING
```

## Installed surfaces

```text
handoffs/SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001.json
workers/tvc_repository_broker_validation_worker.py
control/worker-registry.d/tvc-repository-broker-validation-001.json
control/process-worker-adapters.d/tvc-repository-broker-validation-001.json
tests/test_tvc_repository_broker_validation_worker.py
control/admissible-existence-retrospective-conformance.json
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
observed_current_PR_head: 6209396bc9846ec5f301b24d3b6f0207e571af1d
upstream handoff: docs/GITHUB_REPOSITORY_OPERATION_BROKER_MIRROR_HANDOFF.md
upstream task: tasks/TVC-GITHUB-REPOSITORY-OPERATION-BROKER-001.json
```

If PR #20 head changes before runtime validation, the worker fails closed with `EXACT_TVC_SOURCE_NOT_MATERIALIZED` until this binding is deliberately advanced to the reviewed new head. It must not silently validate a different commit.

## Execution ownership and collision partition

### MANUAL / SESSION-STARTABLE

```text
manual_execution_allowed: false
worker_registry_ref: control/worker-registry.d/tvc-repository-broker-validation-001.json
collision_scope: tvc:github-repository-operation-broker:validation
release_condition: none; this bucket contains no manually executable action
next_executable_action: NONE_MANUAL
```

A chat/session may inspect evidence and repair this carrier's own declarative defects, but it must not directly substitute itself for the heartbeat worker or execute credential-bearing TVC transport.

### WORKER-OWNED / DO NOT COMPETE

```text
manual_execution_allowed: false
worker_registry_ref: control/worker-registry.d/tvc-repository-broker-validation-001.json
collision_scope: tvc:github-repository-operation-broker:validation
release_condition: receipts/tvc-repository-broker-validation/SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001.json state=COMPLETED for the exact pinned TVC PR #20 head
next_executable_action: heartbeat scheduler admits SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001 and invokes process:tvc-repository-broker-validation-v1
```

The registered worker owns exact local-source discovery plus deterministic execution of the already-installed TVC verifier. No session may compete for the same validation receipt.

### ESCALATED / AUTHORITY-OWNED

```text
manual_execution_allowed: false
worker_registry_ref: control/worker-registry.d/tvc-repository-broker-validation-001.json
collision_scope: tvc:github-repository-operation-broker:integration
release_condition: validation carrier receipt COMPLETED, followed by TVC repository-owner admission decision for PR #20
next_executable_action: StegVerse-Labs/TVC canonical integration authority reviews the exact PASS receipt and admits or retains PR #20 according to its handoff
```

Credential-bearing source materialization and any repository integration remain TV/TVC/repository-owner authority, not this worker's authority.

### COMPLETED / SUPERSEDED

```text
manual_execution_allowed: false
worker_registry_ref: control/worker-registry.d/tvc-repository-broker-validation-001.json
collision_scope: tvc:github-repository-operation-broker:validation
release_condition: terminal PASS receipt retained and downstream TVC admission state recorded, or this lane is explicitly superseded by a narrower canonical machine-owned validation carrier
next_executable_action: release this worker claim and allow the existing formalism TVC transport consumer plus StegCore private-source validation task to observe the downstream release
```

Completion of this validation carrier grants no transport, credential, merge, model, wallet, signing, broadcast, or runtime authority.

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

## Validation evidence

The first repository-wide validation after installation exposed two carrier-integration bookkeeping defects, not TVC broker code failures: the AE retrospective denominator did not classify the newly registered task, and this mirror handoff lacked the organization-required execution-ownership partition. The denominator was reconciled at `d14f36f2ad06368c98fbdb245d0f68ecbdae99c2`; the ownership partition was installed at `5b560bc826ad2e4dc4385ead37b0bbeb4f9bc07e`; explicit AE task-conformance bindings were then installed in the handoff/registry ending at `871e764b1a09550dd6ad8fccf18e377981286d4b`.

Final inspected validation on `871e764b1a09550dd6ad8fccf18e377981286d4b`:

```text
Heartbeat Worker Project - Validation Only / No GitHub Token Authority
run: 32065432398
job: 95496297296
result: SUCCESS
complete deterministic repository test suite: SUCCESS
credential-clean anonymous checkout: SUCCESS
executable handoff validation: SUCCESS
heartbeat dry-run carrier-only/non-mutating proof: SUCCESS

Validate organization control plane - No GitHub Token Authority
run: 32065432433
job: 95496297459
result: SUCCESS
handoff execution ownership: SUCCESS
Admissible-Existence handoff/worker-registry conformance: SUCCESS
canonical heartbeat carrier contract: SUCCESS
runtime/control-plane semantic separation: SUCCESS
cross-repository collision enforcement: SUCCESS
allocator dry-run without persistence authority: SUCCESS
JSON/JSONL and no-authority workflow checks: SUCCESS
```

These workflows are validation surfaces only and grant no production runtime, repository, transport, credential, model, or trade authority. Repository integration is validated. Runtime carrier execution remains separately required on an admitted heartbeat opportunity with exact locally materialized TVC source.

## Completion inventory

```text
developed files: 7/7
scaffolding/stubs: 0
missing required files: 0
repository integration validation: 2/2 PASS on inspected final implementation head
runtime carrier receipt: 0/1
TVC PR #20 admission: 0/1
StegCore downstream source-materialization release: 0/1
session-specific validation-carrier requirement transferred: complete
```

## Archive condition

This support lane has no remaining chat-only design requirement: implementation, collision partition, AE conformance, validation commands, owner, runtime release condition, and downstream continuation are durably recorded. Product activation remains incomplete until the machine-owned runtime receipt, TVC admission, and StegCore downstream sovereign validation occur. A runtime BLOCKED state does not authorize a PASS claim.
