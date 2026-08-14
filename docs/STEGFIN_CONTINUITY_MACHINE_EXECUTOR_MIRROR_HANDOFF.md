# StegFin Continuity Machine Executor Mirror Handoff

Updated: 2026-08-14T18:17:00-05:00

```text
goal_id: STEGFIN-CONTINUITY-MACHINE-EXECUTOR-008
originating_session_goal: G08-STEGFIN-TRADE-READY
repository: StegVerse-Labs/.github
branch: main
canonical_trade_handoff: handoffs/STEGFIN-CONTINUITY-CARRIER-007.json
canonical_worker: workers/stegfin_continuity_carrier_worker_v3.py
credential_authority: TV/TVC
github_token_runtime_authority: NONE
wallet_signing_authority: USER_ONLY
broadcast_authority: USER_ONLY
state: CLAIMED_FOR_IMPLEMENTATION
```

## Gap proved before claim

The canonical trade handoff permits `ANY_AUTHORIZED_STEGVERSE_CONTINUITY_EXECUTOR`, makes the resident heartbeat optional, binds execution to `MACHINE_SCHEDULER_ONLY`, and requires the existing worker itself to acquire the canonical collision-safe continuity claim through `scripts/acquire_stegfin_continuity_claim.py`.

Repository inspection found the worker, process adapter fragment and resident-heartbeat adapter machinery, but no task-specific non-heartbeat machine executor or host-start delivery surface for this HANDOFF_READY continuity task. The generic `ProcessWorkerAdapter` requires a pre-existing task claim/fence before invoking a worker; manufacturing such a claim in a new carrier would violate the trade handoff's `A carrier invents its own claim or fence` failure predicate. Therefore this implementation must **not** mint a replacement claim/fence. It may invoke only the existing self-claiming StegFin continuity worker on an already-declared non-hosted StegVerse node; the worker remains the sole continuity-claim issuer.

## Claim

```text
claim_ref: control/session-implementation-claim-2026-08-14-stegfin-continuity-machine-executor.json
claimant: current ChatGPT continuation session
role: CLAIMED_FOR_IMPLEMENTATION
claim_created_at: 2026-08-14T18:17:00-05:00
claim_expires_at: 2026-08-14T19:17:00-05:00
release_condition: executor + rootless host delivery + tests + deterministic/hosted validation receipt committed; source claim released to canonical machine/TV/TVC owners
```

## Collision exclusions

- no heartbeat state, claim, fence or lease mutation;
- no alternate StegFin continuity claim issuer;
- no alternate TV/TVC provider broker, credential path or runtime observer;
- no provider secret input/export;
- no GitHub token runtime authority;
- no wallet contact/sign/broadcast;
- no mutation inside issue #122 runtime-separation claim;
- no live provider operation from hosted validation or chat.

## Required machine contract

The executor is a **one-shot local host adapter**, not a heartbeat and not an authority source. It must fail closed unless:

1. execution is non-hosted;
2. `/etc/stegverse/node.json` or `~/.stegverse/node.json` is a valid declared StegVerse node marker with TV/TVC credential authority and no GitHub-token requirement;
3. canonical StegFin/TV/TVC source roots are already materialized locally without runtime checkout;
4. the current handoff remains machine-only and the registry worker remains AVAILABLE/HANDOFF_READY without an existing execution claim;
5. a usable canonical transport can be selected by the existing worker (real local TV/TVC Unix socket or existing HTTPS READY evidence);
6. the child environment strips GitHub/provider/wallet/cloud credentials;
7. the existing `stegfin_continuity_carrier_worker_v3.py` acquires the collision-safe continuity claim itself and returns one valid worker response.

On COMPLETE, the executor accepts only `STEGFIN_CONTINUITY_WALLET_HANDOFF_READY` and re-verifies the durable worker receipt has TV/TVC authority, no non-TV/TVC secret/token, no provider-secret export, `signed=false`, and `broadcast=false`.

## Planned source surfaces

```text
scripts/run_stegfin_continuity_machine_executor.py
scripts/install_stegfin_continuity_machine_service.py
tests/test_stegfin_continuity_machine_executor.py
control/stegfin-continuity-machine-executor.json
data/stegfin-continuity-machine-executor/task-state.json
receipts/stegfin-continuity-machine-executor/source-validation-20260814.json
```

The installer may create a rootless native user service only. It may not activate from a hosted environment and may not include credentials. Actual service installation/activation remains an already-authorized StegVerse-node operation; repository validation is not production activation.

## Next executable action

Implement the bounded executor and rootless service delivery, validate all fail-closed boundaries and release this source claim. Actual trade preparation remains machine-owned and may execute only after this source is installed on an authorized node with canonical TV/TVC transport.
