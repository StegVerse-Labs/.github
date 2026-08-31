# Sovereign Resident Rendezvous Consumer Mirror Handoff

Updated: 2026-08-30
Repository: StegVerse-Labs/.github
Issue: #578
Merged PR: #584\nMerge: 91bf9a7314313f989bd8e5e8008887a647e30cd9
State: SOURCE_MERGED_VALIDATED / RESIDENT_REFRESH_ACTIVATION_OPEN
Authority effect: NONE
Runtime activation claimed: false

## Goal

Give an already-running sovereign resident an outbound-only way to receive bounded StegVerse Service Gateway resident intents, eliminating the need for an interactive session to possess a direct server-control connector.

## Canonical upstream

- StegVerse-org/LLM-adapter#240
- docs/RESIDENT_RENDEZVOUS_SERVICE_GATEWAY_MIRROR_HANDOFF.md
- scripts/dispatch_resident_execution_requests.py
- scripts/consume_stegos_kv_intr_chain_request.py
- control/resident-execution-request.d/stegos-kv-intr-chain-001.json

## Execution sequence

```text
resident oscillator/native service
  -> GET one request for this node from Service Gateway
  -> validate schema / TTL / exact request digest
  -> validate exact allowlisted consumer + task + mode
  -> atomically materialize local resident request
  -> invoke existing dispatcher with --only-consumer stegos_kv_intr_chain
  -> read local dispatch/chain receipts
  -> post bounded acknowledgement
```

No received request can create a claim or fence. WorkerCoordinator remains the only task admission authority.

## Fail-closed invariants

- no arbitrary command or argv transport;
- no source fetch or source replacement;
- no GitHub token/runtime authority;
- no NON-TV/TVC credential;
- no secret-bearing request;
- stale/replayed/digest-mismatched request rejected;
- local request file may only be replaced by identical bytes or a distinct later request after the previous request is acknowledged/expired;
- acknowledgement never substitutes for authentic local terminal evidence.

## Initial scope

Only:

```text
consumer=stegos_kv_intr_chain
task_id=SHWP-STEGOS-KV-INTR-CHAIN-001
mode=STEGOS_KV_INTR_CHAIN
```

## Lifecycle

```text
IMPLEMENTED: IN_PROGRESS
VALIDATED: false
MERGED: false
DEPLOYED: false
ACTIVATED: false
OBSERVED: false
COMPLETE: false
```


## Merge evidence

```text
issue: #578 CLOSED_BY_MERGE
PR: #584 MERGED
merge: 91bf9a7314313f989bd8e5e8008887a647e30cd9
validated head: 8eea81ce2831cd8d2061d872eca66ebaa3c2d1c4
Heartbeat Worker Project: 33351750512 SUCCESS
Validate organization control plane: 33351750524 SUCCESS
Cross-Framework Current-Basis Resident Request Validation: 33351750493 SUCCESS
```

The continuous sovereign WorkerCoordinator source now polls the non-authorizing rendezvous when its non-secret Gateway URL/node selector are installed. The missing interactive SSH/server-control surface is no longer part of the steady-state execution contract. The current resident still has to refresh/deploy this merged source once before the rendezvous can be observed live.


## 2026-08-31 request-003 rendezvous propagation — issue #654

The canonical Device-KV resident intent is now `RESIDENT-EXEC-STEGOS-KV-INTR-CHAIN-003`.

Resident rendezvous local materialization permits only the bounded historical migration:
```text
001 -> 003
002 -> 003
```
provided the execution contract remains identical for schema, state, task, mode, entrypoint, credential/authority flags, and the canonical three-step chain. The prior local request is archived write-once before replacement and verified after write.

No unrelated request id, task, mode, command, credential, or step vector may be substituted. This is request continuity only; it does not create WorkerCoordinator claim/fence, execution authority, HB progression authority, or runtime evidence.
