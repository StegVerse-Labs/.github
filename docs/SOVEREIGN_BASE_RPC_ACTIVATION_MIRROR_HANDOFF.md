# Sovereign Base RPC Activation Mirror Handoff

Updated: 2026-08-15T21:22:00-05:00

## Active goal

```text
goal_id: SHWP-SOVEREIGN-BASE-RPC-ACTIVATION-001
originating_session_goal: Assist the workers and make the StegFin trade path ready using StegVerse-only execution, TV/TVC-only credential authority, no NON-TV/TVC secrets/tokens, and no Render production dependency.
repository: StegVerse-Labs/.github
branch: feat/sovereign-base-rpc-activation-worker
canonical_task: tasks/TASK-2026-0005.json
canonical_runtime_owner: resident sovereign heartbeat / StegVerse-Labs/.github#12
implementation_claim: CLAIMED_FOR_IMPLEMENTATION by this bounded branch only for the missing heartbeat-to-micro-node activation adapter
validation_claim: this branch until repository validation passes
claim_created_at: 2026-08-15T21:22:00-05:00
claim_release_condition: worker, executable handoff, registry fragment, process adapter and deterministic tests are merged and validated; live endpoint activation remains machine-owned
credential_authority: TV/TVC
non_tv_tvc_secret_or_token_allowed: false
github_token_runtime_authority: NONE
render_production_runtime: PROHIBITED
```

## Source of truth read before mutation

- `tasks/TASK-2026-0005.json`
- `handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json`
- `docs/SESSION_ASSISTANCE_SCOPE_MIRROR_HANDOFF.md`
- `control/process-worker-adapters.json`
- `StegVerse-002/micro-node-runtime/docs/SOVEREIGN_BASE_RPC_MIRROR_HANDOFF.md`
- `StegVerse-Labs/TVC/docs/SOVEREIGN_BASE_RPC_ROUTE_MIRROR_HANDOFF.md`
- `StegVerse-Labs/stegfin-governance#60`

## Gap established from live repository state

`TASK-2026-0005` assigns real sovereign Base activation to the resident heartbeat and released micro-node runner/verifier, but the organization process-adapter registry contains no task-specific sovereign Base RPC activation worker. The existing heartbeat can therefore own the task without having a deterministic adapter that discovers an already-materialized micro-node source, probes private Base endpoints, optionally launches an explicitly configured local process, validates `validation_only=false`, and persists a bounded activation receipt.

This branch fills only that missing execution bridge. It does not create a second heartbeat, fetch private source, install a blockchain client from the network, mint route authority, contact a wallet, sign, broadcast, settle, or treat the validation-only reference server as production.

## Intended installed surfaces

```text
docs/SOVEREIGN_BASE_RPC_ACTIVATION_MIRROR_HANDOFF.md
handoffs/SHWP-SOVEREIGN-BASE-RPC-ACTIVATION-001.json
workers/sovereign_base_rpc_activation_worker.py
control/worker-registry.d/sovereign-base-rpc-activation-001.json
control/process-worker-adapters.json
tests/test_sovereign_base_rpc_activation_worker.py
receipts/sovereign-base-rpc-activation/**   # runtime output only
```

## Execution contract

The worker may consume only an already-local `StegVerse-002/micro-node-runtime` tree and a credential-free local runtime descriptor or already-running private endpoint. It must strip credential-like environment variables from child execution. It may read `STEGVERSE_MICRO_NODE_ROOT`, `STEGVERSE_BASE_RPC_URL`, and `STEGVERSE_BASE_RPC_COMMAND` only as local path/endpoint/command descriptors; none may contain credentials. The command is parsed without a shell. The worker emits `BLOCKED` when source, a real endpoint, or a real synchronized local process is absent. It emits `COMPLETE` only after the released micro-node verifier returns a proof with Base chain `0x2105`, all required read methods, `private_endpoint=true`, `validation_only=false`, `credential_requirement=NONE`, `non_tv_tvc_secret_or_token_used=false`, and `passed=true`.

The resulting proof is evidence only. TVC remains the sole route-admission authority. StegFin remains the consumer. Wallet signing/broadcast remain `USER_ONLY`.

## Cross-repository continuation

```text
worker COMPLETE
-> exact proof retained in receipts/sovereign-base-rpc-activation/**
-> StegVerse-Labs/TVC/tasks/TVC-SOVEREIGN-BASE-RPC-ROUTE-003.json evaluates the exact endpoint/proof
-> on ROUTE_ADMITTED, StegVerse-Labs/stegfin-governance#60 consumes the exact endpoint
-> current phone produces precise terminal BLOCKED or WALLET_HANDOFF_READY evidence
```

## Execution ownership and collision partition

```text
MANUAL / SESSION-STARTABLE
manual_execution_allowed: false
scope: source implementation and validation on this branch only

WORKER-OWNED / DO NOT COMPETE
worker_registry_ref: control/worker-registry.d/sovereign-base-rpc-activation-001.json
owner: resident sovereign heartbeat after merge
collision_scope: runtime:sovereign-base-rpc plus receipts/sovereign-base-rpc-activation/**

ESCALATED / AUTHORITY-OWNED
TVC route admission: StegVerse-Labs/TVC
credential authority: TV/TVC
wallet signing/broadcast: USER_ONLY
physical/local synchronized Base process availability: sovereign node runtime owner

COMPLETED / SUPERSEDED
micro-node Base RPC discovery/proof source: COMPLETE_RELEASED
TVC exact route evaluator source: COMPLETE_RELEASED
public RPC resilience source/Site projection: COMPLETE_RELEASED

release_condition: branch implementation validates and merges; live completion still requires a real validation_only=false endpoint proof and TVC ROUTE_ADMITTED
next_executable_action: implement the bounded heartbeat adapter, registry binding and tests, then run repository validation and merge only on PASS
```

## Completion accounting

```text
developed-files: 1/6 = 17%
validation: 0/4 = 0%
integration: 0/3 = 0%
goal-activation: 0% (no real endpoint proof observed)
session-consolidation: preserved in v11/v12 inventories and this handoff
```

## Archive condition

This branch may release its implementation claim after the adapter is merged and validated because live execution is machine-owned. The chat is not permitted to claim production activation until a real synchronized endpoint proof and downstream TVC/StegFin evidence are directly observed.
