# Local Source-Generation Executor Mirror Handoff

Updated: 2026-08-14T17:03:00-05:00

## Source of truth

```text
organization: StegVerse-Labs
repository: .github
branch: main
goal_id: LOCAL-SOURCE-GENERATION-EXECUTOR-001
originating_session_goal: G11-RECURSIVE-SELF-BUILD-PROOF + G10-GENERALIZED-OWNER-MUTATION-EXECUTOR
issue: #144
parent_goal: ADMISSIBLE-SOURCE-GENERATION-CAPABILITY-ACTIVATION-001
canonical_binder: SHWP-ADMISSIBLE-SOURCE-GENERATION-CAPABILITY-001
canonical_local_model_owner: StegVerse-002/micro-node-runtime
canonical_ae_authority: StegVerse-Labs/StegCore
credential_authority: TV/TVC
github_token_runtime_authority: NONE
non_TV_TVC_secret_or_token_allowed: false
state: CLAIMED_FOR_IMPLEMENTATION
```

This task implements only the missing bounded **local generation execution** slice behind the already-existing AE source-generation binder. It does not replace or modify the canonical source-generation capability binder, StegCore Admissible-Existence/StegGate semantics, the sovereign local model/runtime, TV/TVC repository transport, heartbeat claim/fence state, or any provider/wallet authority.

## Session-goal membership

This worker is eligible for assistance because it is directly traceable to the current session inventory:

```text
G10-GENERALIZED-OWNER-MUTATION-EXECUTOR
G11-RECURSIVE-SELF-BUILD-PROOF
```

No worker outside the current session goal inventory may be selected by this session.

## Existing canonical inputs — READ ONLY

```text
ADMISSIBLE_SOURCE_GENERATION_CAPABILITY_MIRROR_HANDOFF.md
control/admissible-source-generation-capability.json
workers/admissible_source_generation_capability_worker.py
StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md
StegVerse-002/micro-node-runtime/tools/run_sovereign_model.py
StegVerse-002/micro-node-runtime/micro_node/local_model_runtime.py
```

The existing binder already validates the final `stegverse.local-source-generation-result/v0.1` and emits the downstream owner-source packet. This task must therefore generate that exact input contract rather than create a competing binder.

## Active implementation claim

```text
claim_ref: control/session-implementation-claim-2026-08-14-local-source-generation-executor.json
claimant: current ChatGPT continuation session
role: CLAIMED_FOR_IMPLEMENTATION
claim_created_at: 2026-08-14T17:03:00-05:00
claim_expires_at: 2026-08-14T20:03:00-05:00
release_condition: bounded executor, registry/adapter/task-state, tests and validation receipt are committed and the implementation claim is released to the canonical machine owner
```

Collision exclusions:

```text
- all #137 binder/policy/worker semantics except read-only contract consumption
- canonical StegCore AE/StegGate semantics
- StegVerse-002/micro-node-runtime model/runtime source
- TVC #19/#20 credential-bearing repository transport
- .github #122 heartbeat/control-plane refactor
- live worker claim/fence/lease/runtime state
- provider/wallet/signing/broadcast authority
```

## Required execution contract

The executor MUST fail closed unless **both** capability evidence inputs are explicit and activated:

```text
stegverse:capability:formalism-source-generation:v1 -> ACTIVATED + activation proof + integration evidence
stegverse:capability:sovereign-local-model:v1 -> ACTIVATED + activation proof + integration evidence
```

Availability of a model binary, repository source, worker, heartbeat, local endpoint, or model output cannot infer activation.

The bounded path is:

```text
admitted owner implementation manifest
-> exact owner/base/source hash binding
-> discover/reuse canonical local runtime root or already-running loopback endpoint
-> launch canonical StegVerse local runtime only when needed
-> deterministic JSON generation request
-> strict JSON-only response
-> scope/hash/size validation
-> stegverse.local-source-generation-result/v0.1
-> non-secret runtime/usage/teardown proof
-> existing SHWP-ADMISSIBLE-SOURCE-GENERATION-CAPABILITY-001 binder
```

## Security and lifetime

```text
allowed endpoint: loopback only
allowed lifetime: ONE_SHOT_OPERATION | SHORT_LIVED_WORKER
persistent execution: false
credential authority: TV/TVC
GitHub/provider/wallet credential input: forbidden
non-TV/TVC secret or token: forbidden
provider secret export: forbidden
repository mutation authority: none
wallet authority: none
```

Environment passed to any local runtime process must be an allowlist and must not include GitHub/provider/wallet/authorization/private-key/token/secret material.

## Required implementation surfaces

```text
LOCAL_SOURCE_GENERATION_EXECUTOR_MIRROR_HANDOFF.md
control/local-source-generation-executor.json
control/session-implementation-claim-2026-08-14-local-source-generation-executor.json
handoffs/SHWP-LOCAL-SOURCE-GENERATION-EXECUTOR-001.json
control/worker-registry.d/local-source-generation-executor-001.json
control/process-worker-adapters.d/local-source-generation-executor-001.json
workers/local_source_generation_executor.py
tests/test_local_source_generation_executor.py
data/local-source-generation-executor/task-state.json
receipts/local-source-generation-executor/*
```

## Validation requirements

```text
1 below-ACTIVATED source-generation capability fails closed
2 below-ACTIVATED local-model capability fails closed
3 missing activation/integration proofs fail closed
4 non-loopback endpoints fail closed
5 secret-bearing runtime environment is never forwarded
6 deterministic request binds manifest/base/source hashes
7 malformed or non-JSON model output fails closed
8 out-of-scope file path fails closed
9 file-count and byte limits enforced
10 valid bounded fixture emits exact generation-result + non-secret runtime/usage/teardown proof
```

Synthetic ACTIVATED evidence may appear only in unit-test fixtures; no durable production receipt may invent activation evidence.

## Next executable action

Implement the new bounded executor and its machine registration/test surfaces without touching collision-owned #137 binder semantics. Validate source behavior deterministically, then release this claim. Actual resident execution remains subordinate to canonical AE activation and machine admission.

## Archive condition

This task is not archive-safe while this claim is active. Completion of this implementation also does not by itself complete G11: a resident end-to-end source packet -> TVC owner mutation -> validation/merge -> re-observation cycle is still required.
