# Sovereign Base RPC Activation Mirror Handoff

Updated: 2026-08-15T21:36:00-05:00

## Active goal

```text
goal_id: SHWP-SOVEREIGN-BASE-RPC-ACTIVATION-001
originating_session_goal: Assist the workers and make the StegFin trade path ready using StegVerse-only execution, TV/TVC-only credential authority, no NON-TV/TVC secrets/tokens, and no Render production dependency.
repository: StegVerse-Labs/.github
branch: main
canonical_task: tasks/TASK-2026-0005.json
canonical_runtime_owner: resident sovereign heartbeat / StegVerse-Labs/.github#12
implementation_claim: COMPLETE_RELEASED
validation_claim: COMPLETE_RELEASED
claim_created_at: 2026-08-15T21:22:00-05:00
claim_released_at: 2026-08-15T21:36:00-05:00
claim_release_condition: SATISFIED_BY_PR_194_MERGE_AND_POST_MERGE_VALIDATION
credential_authority: TV/TVC
non_tv_tvc_secret_or_token_allowed: false
github_token_runtime_authority: NONE
render_production_runtime: PROHIBITED
source_state: COMPLETE_VALIDATED_MERGED_RELEASED
live_activation_state: MACHINE_OWNED_REAL_ENDPOINT_PENDING
```

## Source of truth read before mutation

- `tasks/TASK-2026-0005.json`
- `handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json`
- `docs/SESSION_ASSISTANCE_SCOPE_MIRROR_HANDOFF.md`
- `control/process-worker-adapters.json` plus append-only adapter fragments
- `StegVerse-002/micro-node-runtime/docs/SOVEREIGN_BASE_RPC_MIRROR_HANDOFF.md`
- `StegVerse-Labs/TVC/docs/SOVEREIGN_BASE_RPC_ROUTE_MIRROR_HANDOFF.md`
- `StegVerse-Labs/stegfin-governance#60`

## Gap closed

`TASK-2026-0005` assigned real sovereign Base activation to the resident heartbeat and released micro-node runner/verifier, but the organization process-adapter registry contained no task-specific sovereign Base RPC activation worker. PR #194 installed that missing deterministic execution bridge. The heartbeat can now discover an already-materialized micro-node source, probe a private Base endpoint, optionally launch an explicitly configured credential-free local process, require a passing `validation_only=false` proof, retain bounded evidence, and stop before TVC route authority.

The worker does not create a second heartbeat, fetch private source, install a blockchain client from the network, mint route authority, contact a wallet, sign, broadcast, settle, or treat the validation-only reference server as production.

## Installed primary surfaces

```text
docs/SOVEREIGN_BASE_RPC_ACTIVATION_MIRROR_HANDOFF.md
handoffs/SHWP-SOVEREIGN-BASE-RPC-ACTIVATION-001.json
workers/sovereign_base_rpc_activation_worker.py
control/process-worker-adapters.d/sovereign-base-rpc-activation-001.json
control/worker-registry.d/sovereign-base-rpc-activation-001.json
tests/test_sovereign_base_rpc_activation_worker.py
control/admissible-existence-retrospective-conformance.json
tasks/TASK-2026-0005.json
receipts/sovereign-base-rpc-activation/**   # runtime output only
```

Validation also exposed two pre-existing control-plane integration defects. They were repaired without expanding their authority: the early-adopter worker registry now points at an executable JSON handoff instead of Markdown, and the newly merged external-timing validation workflow is registered in the hygiene registry. The external timing source lane remains COMPLETE_RELEASED and its live owner remains #122.

## Execution contract

The worker may consume only an already-local `StegVerse-002/micro-node-runtime` tree and a credential-free local runtime descriptor or already-running private endpoint. Child execution uses a reconstructed non-secret environment. `STEGVERSE_MICRO_NODE_ROOT`, `STEGVERSE_BASE_RPC_URL`, and `STEGVERSE_BASE_RPC_COMMAND` are local path/endpoint/command descriptors only; credential-bearing endpoint/query/fragment/userinfo or command markers fail closed. The command is launched without a shell.

The worker emits `BLOCKED` when source, a real endpoint, or a synchronized local process is absent. It emits `COMPLETE` only after the released micro-node runner returns a proof with Base chain `0x2105`, all required read methods, `private_endpoint=true`, `validation_only=false`, `credential_requirement=NONE`, `non_tv_tvc_secret_or_token_used=false`, `render_required=false`, and `passed=true`.

The proof is evidence only. TVC remains the sole route-admission authority. StegFin remains the consumer. Wallet signing/broadcast remain `USER_ONLY`.

## Cross-repository continuation

```text
resident sovereign heartbeat
-> SHWP-SOVEREIGN-BASE-RPC-ACTIVATION-001
-> exact validation_only=false proof in receipts/sovereign-base-rpc-activation/**
-> StegVerse-Labs/TVC/tasks/TVC-SOVEREIGN-BASE-RPC-ROUTE-003.json exact evaluator
-> ROUTE_ADMITTED only if TVC independently passes the released contract
-> StegVerse-Labs/stegfin-governance#60 consumes the exact endpoint
-> current phone produces precise terminal BLOCKED or WALLET_HANDOFF_READY evidence
-> signing/broadcast remain USER_ONLY
```

## Validation evidence

```text
PR: StegVerse-Labs/.github#194 MERGED
merge_commit: 380b6f9794520014340ddee671020644632b8131
validated_pr_head: f919a4ccb05a23cce5cb1bc2afd4cc12069162b1
PR Heartbeat Worker Project: 31922179962 SUCCESS / job 95103738416 SUCCESS
PR organization control plane: 31922179974 SUCCESS / job 95103738241 SUCCESS
PR early-adopter validator source: 31922179965 SUCCESS / job 95103738175 SUCCESS
post_merge Heartbeat Worker Project: 31922206593 SUCCESS
post_merge organization control plane: 31922206653 SUCCESS
post_merge organization handoff projection: 31922206725 SUCCESS
anonymous no-GitHub-token checkout: PASS
compile runtime/workers/scripts: PASS
canonical JSON parse: PASS
executable handoffs: PASS
complete deterministic repository tests: 299/299 PASS on validated PR state
new sovereign Base worker tests: 5/5 PASS
heartbeat dry-run non-persistence: PASS
projection rebuild: PASS
workflow non-authorizing proof: PASS
```

The earlier `31921928113` run reached `299/299 PASS` but exposed an existing Markdown `handoff_ref` runtime integration defect. The earlier organization run `31922102455` exposed the newly merged external-timing handoff ownership omission. Both defects were reconciled, and the subsequent PR and post-merge validation paths passed.

## Execution ownership and collision partition

```text
MANUAL / SESSION-STARTABLE
manual_execution_allowed: false
scope: source implementation is COMPLETE_RELEASED; no interactive session should run a competing Base activation lane

WORKER-OWNED / DO NOT COMPETE
worker_registry_ref: control/worker-registry.d/sovereign-base-rpc-activation-001.json
owner: resident sovereign heartbeat
collision_scope: runtime:sovereign-base-rpc plus receipts/sovereign-base-rpc-activation/**
state: MACHINE_OWNED_REAL_ENDPOINT_PENDING

ESCALATED / AUTHORITY-OWNED
TVC route admission: StegVerse-Labs/TVC
credential authority: TV/TVC
wallet signing/broadcast: USER_ONLY
physical/local synchronized Base process availability: sovereign node runtime owner

COMPLETED / SUPERSEDED
local model discovery/launch/inference/proof: COMPLETE_VALIDATED_RELEASED; do not recreate
formal local model stegverse-reference-lm-v1: COMPLETE_VALIDATED_RELEASED; do not recreate
micro-node Base RPC discovery/proof source: COMPLETE_RELEASED
TVC exact route evaluator source: COMPLETE_RELEASED
public RPC resilience source/Site projection: COMPLETE_RELEASED
Base activation worker source: COMPLETE_VALIDATED_MERGED_RELEASED
external timing source lane encountered during validation: COMPLETE_RELEASED; live adoption remains #122

release_condition: source condition SATISFIED; live condition remains a real synchronized validation_only=false Base proof followed by TVC ROUTE_ADMITTED and StegFin current-phone evidence
next_executable_action: resident sovereign heartbeat checks out SHWP-SOVEREIGN-BASE-RPC-ACTIVATION-001 when the sovereign carrier is eligible, resolves already-local micro-node source and credential-free Base endpoint/process descriptors, and persists either precise BLOCKED evidence or a live proof for TVC evaluation
```

## Completion accounting

```text
primary developed files: 8/8 = 100%
scaffolding/stubs: 0
missing primary required files: 0
source validation gates: 5/5 = 100%
source integration: 4/4 = 100%
source release: COMPLETE
live goal activation: 0% until an actual validation_only=false synchronized endpoint proof is observed
session-consolidation: all original/adjacent requirements retained by v11/v12 inventories and canonical specialized owners
```

## Archive condition

This source lane no longer requires a chat/session implementation or validation owner. Live activation is now machine-owned by the resident sovereign heartbeat with an exact receipt path and release condition. Full trade activation is not claimed until the real Base proof, TVC route admission and current-phone terminal evidence exist.


## 2026-08-31 independent resident admission + portable source reconciliation

The historical handoff still described this task as waiting on `SHWP-DURABLE-RUNTIME-ACTIVATION` / G18 and only recognized the legacy `STEGVERSE_MICRO_NODE_ROOT` locator. Both are stale relative to the current separated WorkerCoordinator architecture.

The live contract is now:

```text
admitted independent resident task-control opportunity
-> this task acquires its own fresh claim/fence
-> resolve StegVerse-002/micro-node-runtime from:
     STEGVERSE_MICRO_NODE_RUNTIME_ROOT
     STEGVERSE_MICRO_NODE_ROOT (compatibility)
     STEGVERSE_REPO_ROOTS_JSON
     canonical local workload/source candidates
-> observe credential-free private Base endpoint/process descriptor
-> run released Base proof
-> persist precise BLOCKED or validation_only=false proof
-> TVC evaluates route admission separately
```

G18 terminalization is not an execution prerequisite and no heartbeat event grants authority. The worker remains compatible with the portable resident bundle without requiring Git metadata or a network checkout.

The only authentic live blocker after source availability is a real synchronized private Base endpoint/process that satisfies the released proof contract. Missing endpoint evidence remains a task-local blocker and must not block unrelated resident workers.
