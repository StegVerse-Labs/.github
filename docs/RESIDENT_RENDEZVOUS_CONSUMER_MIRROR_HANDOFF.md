# Sovereign Resident Rendezvous Consumer Mirror Handoff

Updated: 2026-08-30
Repository: StegVerse-Labs/.github
Issue: #578
Branch: feature/resident-rendezvous-consumer-578
State: SOURCE_IMPLEMENTATION_IN_PROGRESS
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
