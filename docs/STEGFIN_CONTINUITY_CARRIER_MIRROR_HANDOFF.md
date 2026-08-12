# StegFin Continuity Carrier Mirror Handoff

## Active goal

```text
goal_id: STEGFIN-CONTINUITY-CARRIER-007
parent_goal: STEGFIN-BASE-ROUNDTRIP-001
repository: StegVerse-Labs/.github
state: ACTIVE_INTEGRATION
preferred_carrier: resident sovereign heartbeat
preferred_carrier_required: false
credential_authority: TV/TVC
wallet_authority: USER_ONLY
```

This handoff supersedes the assumption that a physical sovereign-node activation is a hard prerequisite for producing a governed StegFin wallet handoff.

## Continuity invariant

A carrier provides compute only. It never provides trade, credential, signing, broadcast, custody or route authority.

If the resident heartbeat is unavailable, another authorized StegVerse execution carrier may run the exact bounded StegFin continuity path so long as it acquires the collision scope first and preserves the same TV/TVC and USER_ONLY boundaries.

The resident heartbeat remains preferred for continuous operation and long-lived state, but its absence must not stop a bounded live trade preparation whose evidence can be reconstructed and committed afterward.

## Execution ownership and collision partition

### MANUAL / SESSION-STARTABLE

```text
task_id: STEGFIN-CONTINUITY-CARRIER-007
execution_owner: first authorized StegVerse continuity carrier acquiring the validation-entry collision scope
claim_state: UNCLAIMED_SESSION_STARTABLE
worker_registry_ref: control/worker-registry.json
manual_execution_allowed: true
manual_allowed_role: bounded observation/pretrade preparation to USER_ONLY wallet handoff
collision_scope: stegfin:base-validation-entry:0xA503DCe5471492bbA2D06e9f78F4d9D6Bcc852aA:12.50-USDC-WETH
release_condition: WALLET_HANDOFF_READY, fail-closed receipt, or resident/federated worker acquisition of the same lineage
next_executable_action: acquire a collision-safe continuity claim and invoke StegVerse-Labs/stegfin-governance/scripts/run_continuity_pretrade.py
```

A session may not invent a claim/fence. The claim must be persisted by the continuity/control-plane authority before the runner starts.

### WORKER-OWNED / DO NOT COMPETE

`STEGFIN-LIVE-ENTRY-003` and `STEGFIN-LIVE-PRETRADE-005` remain exclusive whenever either has an active claim/fence on this transaction lineage. A continuity claim must yield before any provider operation when that condition is observed.

### ESCALATED / AUTHORITY-OWNED

- TV/TVC exclusively owns provider route/lease/credential use.
- The vault broker exclusively owns provider-secret use.
- USER_ONLY exclusively owns wallet signing and broadcast.
- Master Records remains the reconstruction/custody authority for durable evidence.

### COMPLETED / SUPERSEDED

`SHWP-DURABLE-RUNTIME-ACTIVATION` remains the preferred continuous heartbeat-carrier task, but its completion is no longer a hard dependency for bounded StegFin Inventory-N/pretrade preparation.

## Transport

Canonical quote-broker abstraction now supports:

```text
local preferred transport: absolute Unix socket
continuity transport: HTTPS TV/TVC broker endpoint
consumer credentials: NONE
operation authority: bounded TVC single-use lease
provider credential: TV/TVC/vault only
```

The HTTPS TV/TVC broker is not allowed to accept bearer/API/GitHub/wallet credentials from the consumer. TLS service identity/private material, when used, belongs to TV/TVC deployment authority rather than StegFin.

## Canonical source

```text
StegVerse-Labs/stegfin-governance/docs/STEGFIN_CONTINUITY_CARRIER_MIRROR_HANDOFF.md
StegVerse-Labs/stegfin-governance/task-state/STEGFIN-CONTINUITY-CARRIER-007.json
StegVerse-Labs/stegfin-governance/scripts/run_continuity_pretrade.py
StegVerse-Labs/stegfin-governance/stegwallet/vault_broker_client.py
StegVerse-Labs/stegfin-governance/stegwallet/vault_broker_https_service.py
```

## Completion

The design correction is complete when collision-safe claim issuance is installed, continuity runner contract tests pass, the canonical StegFin mirror references this fallback, and the hard G18 prerequisite is removed from live-goal completion accounting.
