# StegFin External Pretrade Mirror Handoff

## Canonical execution ownership

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
active_implementation_claim: THIS_SESSION_DISTINCT_INTEGRATION_LANE
claim_created_at: 2026-08-12T20:32:00Z
claim_release_condition: successor handoff + worker + registry + process-adapter fragment + deterministic validation are committed, then ownership transfers to resident heartbeat
```

This handoff is the canonical `.github` continuation record for the external Base/0x pretrade successor. It does not supersede `handoffs/SHWP-STEGFIN-SOVEREIGN-TRADING-001.json`, which is a separate zero-external-cost internal-market activation proof and grants no external Base/0x authority.

## Upstream source of truth

```text
StegVerse-Labs/stegfin-governance/docs/STEGFIN_MIRROR_HANDOFF.md
StegVerse-Labs/stegfin-governance/task-state/STEGFIN-LIVE-ENTRY-003.json
StegVerse-Labs/.github/handoffs/STEGFIN-LIVE-ENTRY-003.json
StegVerse-Labs/TVC/docs/PROVIDER_CAPABILITY_RESOLUTION_MIRROR_HANDOFF.md
StegVerse-Labs/TV/docs/STEGWALLET_TRADING_POLICY_MIRROR_HANDOFF.md
StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md
```

## Dependency and authority partition

`STEGFIN-LIVE-PRETRADE-005` is not eligible until `STEGFIN-LIVE-ENTRY-003` has emitted a fresh complete `STEGFIN_INVENTORY_N_OBSERVED` receipt after sovereign-carrier activation. The successor receives its own heartbeat claim/fence. It preserves the predecessor Inventory-N claim/fence as upstream lineage; it must never reuse an old fence as the new execution claim.

The successor may:

- discover already-materialized local StegFin, TV and TVC trees;
- derive the exact 12.50-USDC validation request from canonical StegFin config;
- invoke the canonical TVC preparation gate;
- build the TV/TVC-authenticated trust-registry approval;
- ask TVC to resolve nonsecret `base.quote.0x` routing;
- request the existing single-use <=300-second TVC quote lease;
- build sealed E1/relationship standing;
- invoke the existing StegFin TV/TVC/vault inherited-file-descriptor launcher;
- inspect the resulting governed pretrade status and wallet-handoff bundle;
- persist only nonsecret heartbeat receipts.

It may not:

- read, hash, print, copy, export or persist provider credential values;
- accept GitHub tokens, provider API keys, wallet private keys, seed phrases or wallet passwords;
- use GitHub Actions as production runtime authority;
- create a second TVC route resolver, vault, heartbeat, scheduler, signer or broadcaster;
- sign or broadcast wallet transactions;
- infer transaction settlement from preparation evidence.

Provider capability material is managed only by TV/TVC and the existing vault boundary. The heartbeat orchestrator may test only whether the canonical protected capability file is present with safe permissions before asking TVC to admit the provider inventory. The value remains unread by the heartbeat worker and is opened only by the released StegFin launcher inside the TV/TVC/vault inherited-FD boundary.

## Canonical implementation surfaces

```text
StegVerse-Labs/stegfin-governance/scripts/build_sovereign_validation_trade_request.py
StegVerse-Labs/stegfin-governance/scripts/build_tv_tvc_registry_approval.py
StegVerse-Labs/stegfin-governance/scripts/build_sovereign_live_pretrade_e1.py
StegVerse-Labs/stegfin-governance/scripts/run_tv_tvc_sovereign_pretrade.py
StegVerse-Labs/TVC/scripts/tvc_stegwallet_trading_gate_cli.py
StegVerse-Labs/TVC/scripts/tvc_resolve_provider_capability.py
StegVerse-Labs/TVC/scripts/tvc_issue_stegwallet_quote_lease.py
StegVerse-Labs/.github/workers/stegfin_external_pretrade_worker.py
StegVerse-Labs/.github/handoffs/STEGFIN-LIVE-PRETRADE-005.json
StegVerse-Labs/.github/control/worker-registry.d/stegfin-live-pretrade-005.json
StegVerse-Labs/.github/control/process-worker-adapters.d/stegfin-live-pretrade-005.json
```

## Machine states

The worker must return only machine-observable `COMPLETE`, `BLOCKED`, `RETRY`, or `FAILED` equivalents through the standard worker response contract. Missing local source, absent Inventory N, absent/protection-invalid TV/TVC provider capability, denied TVC route, denied TVC preparation, expired/refused quote lease, failed quote/allowance/simulation, or missing wallet handoff are never success.

Success for this task is **wallet-handoff readiness**, not settlement:

```text
pretrade decision: USER_SWAP_SIGNATURE_REQUIRED or exact-allowance USER_ONLY handoff
wallet_handoff_bundle: PRESENT + hash-bound
signed: false
broadcast: false
settled: false
credential_authority: TV/TVC
github_token_required: false
```

## Local model/runtime requirement

The session requirement to replace descriptive local-runtime selection and formally develop the model locally is already `COMPLETE_RELEASED` in `StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md`. Do not duplicate that implementation. Live activation remains machine-owned by `StegVerse-Labs/.github#60` after HB29.

## Validation commands

```text
python -m unittest -q tests.test_stegfin_external_pretrade_worker
python -m unittest -q tests.test_process_worker_adapter_fragments
python scripts/run_heartbeat_runtime.py --dry-run --cycles 1
```

Hosted workflow success is not a production prerequisite. Direct resident heartbeat observation remains the activation proof.

## Blocker and release conditions

Current blocker:

```text
condition: SOVEREIGN_CARRIER_NOT_YET_ACTIVE
observed_heartbeat_epoch: 29
owner: SHWP-DURABLE-RUNTIME-ACTIVATION / G18 / resident sovereign heartbeat
release_condition: heartbeat advances beyond HB29 with terminal sovereign carrier proof, then STEGFIN-LIVE-ENTRY-003 emits fresh complete Inventory N
```

After Inventory N, any missing non-exportable 0x provider capability is owned by `StegVerse-Labs/TV + StegVerse-Labs/TVC + existing vault boundary`, with release condition `runtime-secrets/provider_0x exists locally, is not a symlink, is a regular file, and has no group/other permission bits`. No other secret/token path is authorized.

## Cross-repository propagation

No Site, Publisher, admissibility-wiki or stegguardian-wiki propagation is authorized from source integration alone. Re-evaluate propagation only after a real governed wallet handoff and subsequent round-trip/reconstruction release criteria are satisfied.

## Session-consolidation state

```text
local-model implementation requirement: MERGED_INTO StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md
Inventory-N implementation: MACHINE_OWNED / DO_NOT COMPETE
provider route resolver: COMPLETE_RELEASED / DO NOT DUPLICATE
external Base pretrade successor: CLAIMED_FOR_INTEGRATION by this session until installed/validated, then MACHINE_OWNED
internal sovereign trading activation: DISTINCT MACHINE_OWNED task; not merged
```

## Completion accounting

```text
developed_files: 6/10 at claim creation
validation: 4/10
integration: 5/10
goal_activation: 0/1 live wallet handoff
archive_condition: all source integration committed and transferred to resident heartbeat, with no chat-only requirement remaining
```
