# TVC Coinbase Interlock/InTr Resident Activation Worker Mirror Handoff

Updated: 2026-08-28
Repository: `StegVerse-Labs/.github`
Branch: `feat/tvc-intr-resident-activation-worker-20260828`
State: SOURCE_MERGED_VALIDATED / RUNTIME_NOT_OBSERVED

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
or canonical Gateway aliases: STEGVERSE_SERVICE_GATEWAY_STORAGE_ROOT / STEGVERSE_HIL_STORAGE_ROOT
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


## 2026-08-28 source release and runtime-binding reconciliation

Initial worker registration merged through PR #358:

```text
merge: 847a147c6aead7656ce1ac37f5fe515dac8c9d98
organization control-plane validation: 33146078300 SUCCESS
heartbeat worker validation: 33146078317 SUCCESS
```

The worker now reuses the Gateway's already-canonical non-secret storage-root binding when present:
`STEGVERSE_SERVICE_GATEWAY_STORAGE_ROOT`, with `STEGVERSE_HIL_STORAGE_ROOT` retained as the Gateway's existing compatibility alias. `STEGVERSE_COINBASE_GATEWAY_STORAGE_ROOT` remains an explicit TVC override.

The shared KV custody root is intentionally still explicit as `STEGVERSE_KV_CUSTODY_ROOT`: current canonical source does not establish one universal production shared-KV filesystem path, and the worker must not guess or silently bind a different vault.

This reconciliation reduces deployment configuration duplication without expanding credential, filesystem, provider, Site, or HeartBeat authority.


## 2026-08-31 sovereign bootstrap -> TVC/SKAP successor binding

The sovereign runtime bootstrap now immediately advances the admitted TVC/SKAP resident activation task after G18 activation verification succeeds.

Source:
- `scripts/bootstrap_sovereign_runtime.py::_advance_tvc_skap_successor`
- target task: `TVC-COINBASE-INTR-RESIDENT-ACTIVATION-001`
- execution path: materialized `scripts/run_worker_runtime.py --task-id TVC-COINBASE-INTR-RESIDENT-ACTIVATION-001`

This closes the scheduler-latency seam where a successfully activated sovereign runtime could otherwise wait for a later generic WorkerCoordinator pass before SKAP activation was attempted.

Authority remains unchanged:
- WorkerCoordinator must admit the task under its own fresh independent claim/fence.
- G18 claim/fence reuse is prohibited.
- HeartBeat grants no execution authority.
- TV/TVC remains sole credential authority.
- No GitHub token or provider credential is required or forwarded.
- A successful G18 bootstrap does not by itself claim `READY_FOR_OWNER_INGRESS`; the TVC worker must still produce authentic recipient-key/liveness, storage-binding, TLS/public-route and readiness evidence.

Validation coverage is added in `tests/test_bootstrap_sovereign_runtime.py`.

The next live transition is now one continuous machine sequence:

```text
sovereign bootstrap
-> G18 activation proof PASS
-> immediate independent TVC/SKAP WorkerCoordinator cycle
-> TVC resident recipient/key/liveness + Gateway route work
-> READY_FOR_OWNER_INGRESS when its predicates are genuinely satisfied
```


## 2026-08-31 portable sovereign control-plane bundle

The resident control plane can now be transported to a StegDeploy sovereign substrate as one local bundle without requiring an adjacent Git checkout or any network source fetch.

Source:
- `scripts/package_sovereign_control_plane_bundle.py`
- schema: `stegverse.sovereign-control-plane-bundle/v1`
- validation: `tests/test_package_sovereign_control_plane_bundle.py`

The bundle contains the canonical runtime/control-plane source needed by the local bootstrap and carries per-file SHA-256 commitments plus a bundle SHA-256 receipt. It excludes mutable runtime receipt/event/checkpoint surfaces and grants no claim, fence, heartbeat, credential, route, provider, or execution authority.

Intended deployment chain:

```text
canonical .github control plane
-> portable local bundle
-> StegDeploy local materialization
-> bootstrap_sovereign_runtime.py
-> native WorkerCoordinator
-> G18 verification
-> immediate TVC/SKAP successor cycle
```

This removes the incidental-adjacent-checkout assumption from the deployment architecture. TV/TVC remains sole credential authority and GitHub remains source provenance only.

## 2026-08-31 portable TVC/Healer resident source closure

The portable sovereign resident stack now includes both `StegVerse-Healer` and `StegVerse-Labs/TVC` as verified local source trees. StegDeploy binds the materialized TVC tree as `STEGVERSE_TVC_ROOT`, the Healer tree as `STEGVERSE_HEALER_ROOT`, and includes both in `STEGVERSE_REPO_ROOTS_JSON`.

This removes the prior possibility that the resident TVC/SKAP successor or HIL lifecycle consumer would be reached by WorkerCoordinator while the required TVC source was absent from the portable deployment.

No TVC credential values are bundled. No GitHub token or network source acquisition is introduced. `TVC_INTR_READY_FOR_OWNER_INGRESS` still requires authentic resident execution, TLS/public-route evidence, and readiness receipts.
