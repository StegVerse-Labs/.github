# StegFin Continuity Carrier Mirror Handoff

## Active goal

```text
goal_id: STEGFIN-CONTINUITY-CARRIER-007
parent_goal: STEGFIN-BASE-ROUNDTRIP-001
repository: StegVerse-Labs/.github
state: ACTIVE_VALIDATION
preferred_carrier: resident sovereign heartbeat
preferred_carrier_required: false
credential_authority: TV/TVC
wallet_authority: USER_ONLY
```

This handoff supersedes the assumption that physical sovereign-node activation is a hard prerequisite for producing a governed StegFin wallet handoff.

## Continuity invariant

A carrier provides compute only. It never provides trade, credential, signing, broadcast, custody or route authority. If the resident heartbeat is unavailable, the control plane may admit the registered continuity worker on another authorized StegVerse carrier. The user is not required to start infrastructure.

## Execution ownership and collision partition

### MANUAL / SESSION-STARTABLE

```text
task_id: NONE
execution_owner: NONE
claim_state: NOT_APPLICABLE
worker_registry_ref: control/worker-registry.d/stegfin-continuity-carrier-007.json
manual_execution_allowed: false
manual_allowed_role: NONE
collision_scope: stegfin:base-validation-entry:0xA503DCe5471492bbA2D06e9f78F4d9D6Bcc852aA:12.50-USDC-WETH
release_condition: NOT_APPLICABLE
next_executable_action: NONE
```

### WORKER-OWNED / DO NOT COMPETE

```text
task_id: STEGFIN-CONTINUITY-CARRIER-007
execution_owner: stegfin-continuity-carrier-worker on any authorized StegVerse continuity carrier
claim_state: MACHINE_CLAIM_ON_EXECUTION
worker_registry_ref: control/worker-registry.d/stegfin-continuity-carrier-007.json
manual_execution_allowed: false
manual_allowed_role: NONE
collision_scope: stegfin:base-validation-entry:0xA503DCe5471492bbA2D06e9f78F4d9D6Bcc852aA:12.50-USDC-WETH
release_condition: WALLET_HANDOFF_READY, fail-closed receipt, or resident worker ownership of the same lineage
next_executable_action: scheduler admits process:stegfin-continuity-carrier-v1; worker acquires collision claim and runs bounded continuity pretrade
```

`STEGFIN-LIVE-ENTRY-003` and `STEGFIN-LIVE-PRETRADE-005` remain exclusive whenever either has an active claim/fence on this transaction lineage. Continuity acquisition is denied in that state.

### ESCALATED / AUTHORITY-OWNED

```text
task_id: TVC-PROVIDER-OPERATION-BROKER-003
execution_owner: StegVerse-Labs/TVC + TV/TVC runtime authority
claim_state: SOURCE_IMPLEMENTED_VALIDATION_PENDING
worker_registry_ref: StegVerse-Labs/TVC/tasks/TVC-PROVIDER-OPERATION-BROKER-003.json
manual_execution_allowed: false
manual_allowed_role: NONE
collision_scope: provider-operation:base.quote.0x
release_condition: carrier-neutral TV/TVC broker source validation + live broker endpoint observation
next_executable_action: validate/activate TVC broker on any authorized continuity runtime
```

TV/TVC exclusively owns provider credential use. USER_ONLY exclusively owns wallet signing/broadcast. Master Records owns durable reconstruction/custody evidence.

### COMPLETED / SUPERSEDED

```text
task_id: G18_AS_HARD_STEGFIN_PRECONDITION
execution_owner: SUPERSEDED
claim_state: COMPLETE_SUPERSEDED_FOR_TRADE_GATE
worker_registry_ref: handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json
manual_execution_allowed: false
manual_allowed_role: NONE
collision_scope: none; G18 remains a separate resilience goal
release_condition: already superseded for bounded trade preparation
next_executable_action: continue G18 independently for continuous resident operation
```

## Machine path

```text
registered continuity worker
-> collision-safe continuity claim
-> credential-free Inventory N
-> canonical 12.50-USDC request
-> TVC preparation gate / quote lease
-> TV/TVC provider-operation broker (HTTPS or local private broker)
-> quote / allowance / risk / simulation
-> WALLET_HANDOFF_READY
-> STOP
-> USER_ONLY wallet action
```

The worker adapter allowlist contains only local source locations, local state locations and `STEGVERSE_TV_TVC_BROKER_ENDPOINT`, which is non-secret service configuration. No GitHub token, provider API key, wallet key, bearer token or cloud credential is accepted.

## Canonical source

```text
handoffs/STEGFIN-CONTINUITY-CARRIER-007.json
workers/stegfin_continuity_carrier_worker.py
scripts/acquire_stegfin_continuity_claim.py
control/worker-registry.d/stegfin-continuity-carrier-007.json
control/process-worker-adapters.d/stegfin-continuity-carrier-007.json
cost-basis/worker-runtime/stegfin-continuity-carrier.json
StegVerse-Labs/stegfin-governance/task-state/STEGFIN-CONTINUITY-CARRIER-007.json
StegVerse-Labs/TVC/tasks/TVC-PROVIDER-OPERATION-BROKER-003.json
```

## Completion

Source integration is installed. Remaining release work is deterministic validation of the continuity worker/claim/broker contracts and live observation of an authorized TV/TVC broker endpoint. A live quote or wallet handoff must not be claimed before those runtime receipts exist.
