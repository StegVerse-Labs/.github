# HB Runtime Presence / Resident Observability Mirror Handoff

Repository: `StegVerse-Labs/.github`
Updated: 2026-09-02
Issue: #814
State: SOURCE_IMPLEMENTED_VALIDATION_PENDING
Authority effect: NONE

## Purpose

Provide one reusable, organization-resident observability contract for every StegVerse consumer lane that needs to answer:

- which resident/node is this;
- whether a resident process has been authentically observed and is current;
- which HB reference establishes observation-time freshness;
- which governed request was admitted;
- which resident/receiver consumed it;
- which execution/state transition occurred;
- which authentic receipt proves it;
- where retained evidence lives;
- whether replay/reconstruction is proven.

This is not another heartbeat, worker, scheduler, task authority, or session-local runtime.

## Canonical inputs

Existing sources are consumed without widening their authority:

- `heartbeat_runtime/independent_oscillator.py` / org-kernel `hb_reference()`;
- `control/heartbeat-carrier-runtime-state.json` historical/persisted observation;
- `control/worker-runtime-state.json` historical/persisted worker observation;
- `control/worker-control-plane-coordination.json`;
- `resident-runtime/activation-manifest.json`;
- existing resident request/consumption/targeted-execution receipts under `receipts/sovereign-host/`;
- lane-specific InTr ingress/egress and state-transition receipts;
- lane-specific Master Records replay/reconstruction receipts.

## Authority rule

HB/current-reference derivation and HB-derived carrier state grant no execution, admission, credential, routing, transition, claim/fence, receiving, publication, custody, or consequence authority.

Presence/freshness is observation only.

A request is not consumed until a direct consumer receipt exists.
A receiver is not READY until direct readiness evidence exists.
A transition is not executed until a direct execution/state receipt exists.
Reconstruction is not proven until a direct reconstruction receipt exists.

## Consumer binding for this session

Current session consumer:
`StegVerse-Labs/Site/docs/MY_KV_PERSONAL_FORM_PROFILE_MIRROR_HANDOFF.md`

Distinct unresolved predicates:

1. current-iPhone `PERSONAL_FORM_PROFILE` governed request consumption + exact readback;
2. current-iPhone subsequent `PROFILE_READ`;
3. authentic KV -> SKAP Vault custody for the signing profile;
4. later exact-document signing receipt when a filing is actually approved for signature.

The first two are current-device DEVICE_KV observations. The third consumes the existing canonical KV/SKAP InTr path. None requires a new heartbeat implementation.

## Completion boundary

Source completion:
- shared projection contract/parser installed;
- fail-closed tests prove stale repository snapshots do not become current runtime;
- consumer can bind its predicate names to canonical receipt classes.

Runtime completion:
- authentic machine-produced receipts populate the applicable existing paths and the shared projection reports them without inference.

Source/CI/merge do not satisfy runtime completion.


## Shared projection implementation — issue #814

Implemented on `feature/hb-runtime-presence-observability-814`:

- `heartbeat_runtime/runtime_presence_projection.py`
- `scripts/project_hb_runtime_presence.py`
- `tests/test_runtime_presence_projection.py`

Resident materialization integration:
- `scripts/bootstrap_sovereign_runtime.py`
- `scripts/install_sovereign_heartbeat_service.py`
- `scripts/refresh_sovereign_worker_runtime_source.py`

The projector reads runtime-local evidence only. It never marks resident liveness from HB progression alone. `runtime_alive_observed=true` requires a direct deployment-local activation receipt whose predicates include both `native_service_active=true` and `continuous_runtime_live=true`.

Request, consumption, execution, and reconstruction remain four independent evidence slots. A present HB signal cannot satisfy the execution or reconstruction slots.

## KnowledgeVault recovery/provider consumer binding

Consumer repositories:
- `StegVerse-Labs/continuity-vault-kit`
- `StegVerse-Labs/Site`

Current missing predicate chain:

```text
TVC-owned provider session active
-> exact provider-root materialization observed
-> authentic node-origin MY_KV_INSTALLATION_STATUS request
-> DEVICE_KV consumption observed
-> HB-derived KV->DEVICE return recovered exactly
-> retained device-kv-query-response receipt
-> Site readback/sync observation
-> recovery/provider reconstruction
```

Existing canonical owners are reused:
- provider root: `docs/PERSONAL_KV_PROVIDER_ROOT_MIRROR_HANDOFF.md`
- DEVICE_KV request/return: `docs/DEVICE_KV_QUERY_RESPONSE_MIRROR_HANDOFF.md`
- HB/InTr transport: `docs/HB_INTR_DERIVED_CARRIER_MIRROR_HANDOFF.md`
- resident runtime: HeartBeat-separated native `WorkerCoordinator`
- credential authority: TV/TVC

No KnowledgeVault-specific heartbeat, scheduler, resident executor, signal protocol, or credential broker is authorized.

## Source lifecycle

```text
shared projection implementation: IMPLEMENTED_ON_BRANCH
resident install/refresh integration: IMPLEMENTED_ON_BRANCH
hosted validation: PENDING
merged: NO
runtime projection observed: NO
KnowledgeVault provider session observed: NO
KnowledgeVault DEVICE_KV installation-status consumption observed: NO
KnowledgeVault HB-derived return observed: NO
Site readback observed: NO
authority_effect: NONE_OBSERVATION_ONLY
```
