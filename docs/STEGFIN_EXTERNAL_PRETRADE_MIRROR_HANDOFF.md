# StegFin External Pretrade Mirror Handoff

## Canonical ownership

```text
goal_id: STEGFIN-BASE-ROUNDTRIP-001
task_id: STEGFIN-LIVE-PRETRADE-005
originating_goal: Make the first governed 12.50 USDC -> WETH Base validation entry trade-ready after fresh Inventory N, stopping at USER_ONLY wallet handoff.
repository: StegVerse-Labs/.github
branch: main
canonical_product_owner: StegVerse-Labs/stegfin-governance
canonical_runtime_owner: resident sovereign heartbeat
credential_authority: TV/TVC
route_authority: StegVerse-Labs/TVC
wallet_signing_authority: USER_ONLY
broadcast_authority: USER_ONLY
implementation_claim: RELEASED_TO_MACHINE_OWNER
claim_created_at: 2026-08-12T20:32:00Z
claim_released_at: 2026-08-12T21:01:40Z
claim_release_evidence: e1f79c1fcdbc23706569a1d19f5e69eaedb7ae60 + workflow runs 31640451274,31640451338,31640451256,31640451342 SUCCESS
```

This is the canonical `.github` continuation record for the external Base/0x pretrade executor. It is distinct from `handoffs/SHWP-STEGFIN-SOVEREIGN-TRADING-001.json`, which is an internal zero-external-cost market/reconstruction proof and has no external Base/0x authority.

## Execution ownership and collision partition

### MANUAL / SESSION-STARTABLE

```text
manual_execution_allowed: false
worker_registry_ref: control/worker-registry.d/stegfin-live-pretrade-005.json
collision_scope: STEGFIN-LIVE-PRETRADE-005 and process:stegfin-live-pretrade-v1; sessions may observe validated evidence but may not manually invoke provider capability, vault, wallet signing, broadcast, or duplicate the worker
release_condition: none; this bucket intentionally contains no production execution authority
next_executable_action: no session action; observe only unless the canonical machine worker emits a fail-closed receipt naming a repository-owned defect
```

### WORKER-OWNED / DO NOT COMPETE

```text
manual_execution_allowed: false
worker_registry_ref: control/worker-registry.d/stegfin-live-pretrade-005.json
collision_scope: fresh Inventory N -> canonical validation request -> TVC preparation -> TV/TVC registry approval -> TVC base.quote.0x route -> quote lease -> E1 -> inherited-FD vault capsule -> canonical WALLET_HANDOFF_READY
release_condition: heartbeat advances beyond HB29, STEGFIN-LIVE-ENTRY-003 emits unexpired fresh Inventory N, and this successor receives a new fenced heartbeat claim
next_executable_action: resident sovereign heartbeat admits STEGFIN-LIVE-PRETRADE-005 at release priority and runs workers/stegfin_external_pretrade_worker.py
```

### ESCALATED / AUTHORITY-OWNED

```text
manual_execution_allowed: false
worker_registry_ref: control/worker-registry.d/stegfin-live-pretrade-005.json
collision_scope: provider capability and credential material remain exclusively TV/TVC plus the existing vault inherited-file-descriptor boundary; wallet signature and broadcast remain USER_ONLY
release_condition: TV/TVC route/lease/capability evidence is valid and governed preparation reaches the user-controlled wallet boundary
next_executable_action: if TV/TVC capability is missing or invalid, TV/TVC/vault owns repair; if wallet action is required, automation stops and waits for USER_ONLY authority
```

### COMPLETED / SUPERSEDED

```text
manual_execution_allowed: false
worker_registry_ref: control/worker-registry.d/stegfin-live-pretrade-005.json
collision_scope: duplicate dynamic validation-request generation, session-owned executor implementation, and descriptive local-runtime/model selection are excluded from this workstream
release_condition: duplicate request builder removed at a579b86a768da42c1757cf71b4c41b2db35b16b1; executor validated and released at e1f79c1fcdbc23706569a1d19f5e69eaedb7ae60; local-model implementation COMPLETE_RELEASED in StegVerse-002/micro-node-runtime
next_executable_action: consume configs/base_validation_entry_trade_request.json unchanged and let the resident heartbeat continue the released machine path; do not recreate any completed capability
```

## Convergence record

A concurrent StegFin readiness lane completed source hardening while this executor was being installed. The canonical request is consumed unchanged from:

```text
StegVerse-Labs/stegfin-governance/configs/base_validation_entry_trade_request.json
StegVerse-Labs/stegfin-governance/task-state/STEGFIN-LIVE-ENTRY-003-READINESS.json
StegVerse-Labs/stegfin-governance/scripts/check_live_entry_trade_readiness.py
```

The temporary duplicate `scripts/build_sovereign_validation_trade_request.py` was removed at `a579b86a768da42c1757cf71b4c41b2db35b16b1`. Unique work retained from this session was the resident machine executor; that integration is now validated and released to the canonical machine owner.

## Installed and validated executor

```text
StegVerse-Labs/.github/workers/stegfin_external_pretrade_worker.py
StegVerse-Labs/.github/handoffs/STEGFIN-LIVE-PRETRADE-005.json
StegVerse-Labs/.github/control/worker-registry.d/stegfin-live-pretrade-005.json
StegVerse-Labs/.github/control/process-worker-adapters.d/stegfin-live-pretrade-005.json
StegVerse-Labs/.github/cost-basis/worker-runtime/stegfin-live-pretrade.json
StegVerse-Labs/.github/scripts/run_heartbeat_runtime.py
StegVerse-Labs/stegfin-governance/configs/base_validation_entry_trade_request.json
StegVerse-Labs/stegfin-governance/scripts/check_live_entry_trade_readiness.py
StegVerse-Labs/stegfin-governance/scripts/build_tv_tvc_registry_approval.py
StegVerse-Labs/stegfin-governance/scripts/build_sovereign_live_pretrade_e1.py
StegVerse-Labs/stegfin-governance/scripts/run_tv_tvc_sovereign_pretrade.py
StegVerse-Labs/TVC/scripts/tvc_stegwallet_trading_gate_cli.py
StegVerse-Labs/TVC/scripts/tvc_resolve_provider_capability.py
StegVerse-Labs/TVC/scripts/tvc_issue_stegwallet_quote_lease.py
```

Execution sequence:

```text
fresh unexpired Inventory N
-> canonical base_validation_entry_trade_request.json
-> canonical TVC preparation gate
-> TV/TVC fenced trust-registry approval
-> canonical TVC base.quote.0x route resolution
-> existing <=300-second single-use TVC quote lease
-> sealed E1/relationship standing
-> existing TV/TVC/vault inherited-FD capsule launch
-> quote / allowance / gas-risk / read-only simulation
-> canonical check_live_entry_trade_readiness.py convergence
-> WALLET_HANDOFF_READY
-> STOP at USER_ONLY wallet action
```

The worker never reads the provider capability value. It may only confirm that the TV/TVC-managed protected capability file is a regular non-symlink file with safe permissions before TVC admission. The value is opened only by the existing StegFin TV/TVC/vault launcher and delivered by inherited file descriptor.

## Credential boundary

No GitHub token, PAT, provider API key/token value, wallet private key, seed phrase, mnemonic, wallet password, cloud credential, alternate vault, alternate TVC resolver, alternate heartbeat, signer or broadcaster is accepted. Base read-only RPC remains the credential-free registry-pinned `https://mainnet.base.org`. Provider credential authority is TV/TVC only; wallet signing and broadcast remain USER_ONLY.

## Local model/runtime requirement

The former descriptive “select a local model/runtime” step and formal local-model-development requirement are `COMPLETE_RELEASED` in `StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md`. That implementation includes repository-developed `stegverse-reference-lm-v1`, executable local discovery, private launch, real inference, measured latency/usage, proof, and optional locally materialized Ollama/llama.cpp discovery without hosted fallback. Do not duplicate it.

## Validation evidence

All validation lanes for the released executor integration passed on `e1f79c1fcdbc23706569a1d19f5e69eaedb7ae60`:

```text
Heartbeat Worker Project: run 31640451274 SUCCESS
Validate organization control plane: run 31640451338 SUCCESS
Org Continuation Check: run 31640451256 SUCCESS
Org Aggregation Check: run 31640451342 SUCCESS
```

The validation workflows use anonymous checkout / no GitHub credential token authority. Hosted validation is non-authorizing; it validates source/control-plane integration only.

## Current blocker and machine continuation

Direct canonical heartbeat state remains HB29. `SHWP-DURABLE-RUNTIME-ACTIVATION` is already `MACHINE_OWNED_BOUND_G18`; this session must not duplicate it.

```text
condition: SOVEREIGN_NODE_DECLARATION_NOT_PRESENT / heartbeat still HB29
owner: SHWP-DURABLE-RUNTIME-ACTIVATION / G18 / resident sovereign heartbeat
release_condition: node-local activation.latest.json satisfies the nine activation predicates, restart/reconstruction continuity passes, heartbeat advances beyond HB29, then STEGFIN-LIVE-ENTRY-003 emits fresh complete unexpired Inventory N
human_action_required: false
missing_implementation: false
```

If the TV/TVC capability is then absent, owner is `StegVerse-Labs/TV + StegVerse-Labs/TVC + existing vault boundary`; no chat/operator credential path is authorized.

## Cross-repository propagation

No Site, Publisher, admissibility-wiki or stegguardian-wiki propagation is authorized from source integration alone. Re-evaluate only after real wallet-handoff and round-trip/reconstruction release evidence exists.

## Session consolidation

```text
local-model implementation: MERGED INTO StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md
Inventory-N implementation: MACHINE_OWNED / DO NOT COMPETE
canonical exact trade request/readiness checker: MERGED INTO StegFin canonical readiness lane
provider resolver/quote lease: COMPLETE_RELEASED / DO NOT DUPLICATE
external Base pretrade executor: COMPLETE_VALIDATED / RELEASED_TO_MACHINE_OWNER
sovereign carrier activation: MACHINE_OWNED G18 / DO NOT COMPETE
internal sovereign trading proof: DISTINCT MACHINE_OWNED task
session_unique_work_remaining: false
```

## Completion accounting

```text
developed_files: 12/12
scaffolding_or_stubs: 0
missing_required_files: 0
validation: 12/12
integration: 12/12 source/control-plane integration
live_goal_activation: 0/1 wallet handoff because heartbeat remains HB29
session_consolidation: COMPLETE
archive_condition: SATISFIED; remaining live activation is durably machine-owned and requires no information from this chat
```
