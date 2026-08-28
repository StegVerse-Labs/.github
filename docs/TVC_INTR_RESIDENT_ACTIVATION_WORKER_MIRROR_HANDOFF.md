# TVC Coinbase Interlock/InTr Resident Activation Worker Mirror Handoff

Updated: 2026-08-28
Repository: `StegVerse-Labs/.github`
Branch: `feat/tvc-intr-resident-activation-worker-20260828`
State: SOURCE_IN_VALIDATION / RUNTIME_NOT_OBSERVED

## Goal

Close the machine-ownership seam between genuine sovereign WorkerCoordinator activation and the already-built TVC Coinbase resident Interlock/InTr activation lane.

Canonical upstream authority remains:

- `handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json`
- `StegVerse-Labs/TVC/tasks/TVC-COINBASE-RESIDENT-ACTIVATION-091.json`
- `StegVerse-Labs/TVC/docs/TVC_COINBASE_IPHONE_SKAP_ACTIVATION_MIRROR_HANDOFF.md`

## Installed source surfaces

```text
handoffs/TVC-COINBASE-INTR-RESIDENT-ACTIVATION-001.json
control/worker-registry.d/tvc-coinbase-intr-resident-activation-001.json
control/process-worker-adapters.d/tvc-coinbase-intr-resident-activation-001.json
workers/tvc_coinbase_intr_resident_activation_worker.py
tests/test_tvc_coinbase_intr_resident_activation_worker.py
cost-basis/worker-runtime/tvc-coinbase-intr-resident-activation.json
```

## Execution contract

The WorkerCoordinator successor is independently claimable only after the durable sovereign runtime is genuinely active. It never receives HeartBeat progression authority and never reuses the G18 claim/fence.

The worker:

1. rejects hosted execution surfaces;
2. rejects GitHub/provider credential environment values;
3. requires resident root authority;
4. observes current TVC readiness before mutating anything;
5. reuses an already-valid recipient key stack when the only blocker is missing/stale public route evidence;
6. runs `activate_coinbase_intr_resident.py` only when the resident stack itself requires activation and both real Gateway staging/KV custody roots are present;
7. optionally obtains a fresh public route receipt through the sovereign node advertisement using `observe_coinbase_service_gateway_route.py`;
8. requires `READY_FOR_OWNER_INGRESS`;
9. emits the local Site owner-ingress projection through `project_coinbase_owner_ingress_site_config.py`;
10. never mutates the Site repository and never accepts provider credential values.

Non-secret deployment bindings are:

```text
STEGVERSE_REPO_ROOTS_JSON or STEGVERSE_TVC_ROOT
STEGVERSE_COINBASE_GATEWAY_STORAGE_ROOT
STEGVERSE_KV_CUSTODY_ROOT
STEGVERSE_COINBASE_PUBLIC_NODE_URL
```

## Authority boundary

```text
credential_authority: TV/TVC
provider_operation_authority: NONE
site_repository_mutation_authority: NONE
heartbeat_progression_authority: NONE
github_token_runtime_authority: NONE
third_party_primary_runtime: false
second_user_operated_machine_required: false
```

## Runtime non-claims

No sovereign WorkerCoordinator activation is claimed by source merge or CI.
No resident root/systemd activation is claimed.
No real recipient key/liveness is claimed.
No public Gateway route is claimed.
No `READY_FOR_OWNER_INGRESS` receipt is claimed.
No iPhone credential ingress, double-Interlock production receipt chain, provider observation, order, settlement or reconciliation is claimed.

## Completion transition

`TVC_INTR_READY_FOR_OWNER_INGRESS`

This transition requires a genuine resident TVC stack, fresh public route observation, and local Site owner-ingress projection while provider operation authority remains false.

## Successor

Only after that transition may the current owner-authorized iPhone use the trusted browser sealing surface. Credential plaintext is never an input to this WorkerCoordinator task.
