# StegOS / KnowledgeVault InTr Resident Execution Chain Mirror Handoff

Updated: 2026-08-30

```text
repository: StegVerse-Labs/.github
request: control/resident-execution-request.d/stegos-kv-intr-chain-001.json
consumer: scripts/consume_stegos_kv_intr_chain_request.py
state: SOURCE_IMPLEMENTED_PENDING_VALIDATION_MERGE_AND_RESIDENT_CONSUMPTION
credential_authority: TV/TVC
github_token_runtime_authority: NONE
heartbeat_grants_execution_authority: false
second_machine_required: false
authority_effect: NONE_REQUEST_ONLY
```

## Purpose

Close the resident-dispatch gap for the already-built machine-owned chain, without
creating a new task, claim, fence, scheduler, HeartBeat, runtime owner, credential
path, route authority, or transport broker.

```text
SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001
-> SOVEREIGN_RELAY_LEASE_OPEN
-> SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001
-> RELAY_NODE_KV_CONTINUITY_VERIFIED
-> SHWP-DEVICE-KV-INTR-OBSERVATION-001
-> DEVICE_KV_INTR_OBSERVED
```

## Execution contract

The consumer invokes the merged portable targeted execution bridge for exactly one
existing task at a time. It advances only when the preceding canonical terminal
receipt exists locally with the exact required state/transition. A blocked parent
records ATTEMPT_RECORDED and stops; successor evidence is never synthesized.

The portable bridges must forward only non-secret local locators, including
STEGVERSE_STEGOS_ROOT, STEGVERSE_KV_SOURCE_ROOT, and STEGVERSE_RELAY_RUNTIME_BASE.
GitHub tokens and NON-TV/TVC credentials are rejected, and network source fetch is
not authorized.

## Required authentic terminal evidence

```text
receipts/stegos-sovereign-relay/SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001.json
  state=COMPLETED
  transition_id=SOVEREIGN_RELAY_LEASE_OPEN

receipts/stegos-sovereign-relay/SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001.json
  state=COMPLETED
  transition_id=RELAY_NODE_KV_CONTINUITY_VERIFIED

receipts/device-kv-intr/SHWP-DEVICE-KV-INTR-OBSERVATION-001.json
  state=OBSERVED
  transition_id=DEVICE_KV_INTR_OBSERVED
```

## Lifecycle boundary

```text
request merged != resident request consumed
resident request consumed != parent terminal receipt
parent terminal receipt != successor terminal receipt
DEVICE_KV_INTR_OBSERVED != production Interlock global activation
```

Hosted validation may prove the consumer fails closed; it cannot satisfy a runtime
terminal predicate.
