# HB Runtime Presence / Resident Observability Mirror Handoff

Repository: `StegVerse-Labs/.github`
Updated: 2026-09-02
State: SHARED_CONTRACT_SOURCE_INITIALIZATION
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


## 2026-09-02 shared source implementation and first consumer binding

Installed shared source:
- `org-kernel/runtime_observability.py`
- `schemas/hb-runtime-resident-observability.schema.json`
- `management/HB_RUNTIME_PRESENCE_RESIDENT_OBSERVABILITY_CONTRACT.json`
- `scripts/project_runtime_observability.py`
- `org-kernel/tests/test_runtime_observability.py`

First consumer binding:
- `control/runtime-observability-consumers/site-my-kv-personal-form-profile.json`
- consumer: `StegVerse-Labs/Site/docs/MY_KV_PERSONAL_FORM_PROFILE_MIRROR_HANDOFF.md`

Direct repository-state inspection at 2026-09-02T16:59:00-05:00 found:
- canonical HB reference derivation available from HB32 anchor;
- inspection-time deterministic reference: HB 87474032;
- persisted carrier observation remains HB31 with `last_cycle_at=2026-08-18T19:47:00Z`;
- persisted worker observation remains `runtime_tick=2`, `CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION`, same last-cycle timestamp;
- no current resident-process liveness is inferred from those stale persisted snapshots;
- canonical resident request dispatcher/consumer and KV->SKAP InTr source already exist;
- authentic current-iPhone Personal Form Profile write/readback and SKAP signing-profile custody are not observed.

The shared projection is deliberately fail-closed: HB progression, activation source presence, worker leases, or evidence-file presence do not promote request consumption, receiver readiness, execution/state transition, or reconstruction.

No hosted validation run was exposed for the new source commits at inspection time. No CI/runtime PASS is claimed.

## TVC semantic boundary

The current TVC credential-model consistency lane still prohibits session-inferred generalized credential/vault/signing-manager expansion. Therefore this consolidation does not add a new TVC e-signature credential class.

The consumer may store a non-secret `skap://signing/<profile-id>` reference in KV source, but authentic SKAP signing-profile custody remains blocked until an exact TV/TVC credential-class contract is admitted under the existing consistency process.

## Current runtime predicates for My KV consumer

1. `PERSONAL_FORM_PROFILE_WRITE_CONSUMED`
2. `PERSONAL_FORM_PROFILE_EXACT_READBACK_VERIFIED`
3. `PERSONAL_FORM_PROFILE_READ_OBSERVED`
4. `SKAP_SIGNING_PROFILE_CUSTODY_OBSERVED`

The first three can be satisfied only by the current registered iPhone/device-local DEVICE_KV execution. The fourth must consume the existing canonical KV->SKAP InTr path under TV/TVC authority.


## Shared projection implementation — issue #814

Implemented on current-main successor branch `feature/hb-runtime-presence-observability-814-v2`:

- `heartbeat_runtime/runtime_presence_projection.py`
- `scripts/project_hb_runtime_presence.py`
- `tests/test_runtime_presence_projection.py`

Resident materialization integration:
- `scripts/bootstrap_sovereign_runtime.py`
- `scripts/install_sovereign_heartbeat_service.py`
- `scripts/refresh_sovereign_worker_runtime_source.py`

The projector reads runtime-local evidence only. It never marks resident liveness from HB progression alone. `runtime_alive_observed=true` requires a direct deployment-local activation receipt whose predicates include both `native_service_active=true` and `continuous_runtime_live=true`.

Request, consumption, execution, and reconstruction remain independent evidence slots. A present HB signal cannot satisfy execution or reconstruction.

### KnowledgeVault consumer binding

KnowledgeVault cross-platform recovery and Personal-KV provider binding consume this shared contract.

Exact unresolved chain:

```text
TVC-owned provider session active
-> exact provider-root materialization observed
-> authentic node-origin MY_KV_INSTALLATION_STATUS request
-> DEVICE_KV receiver consumption observed
-> HB-derived KV->DEVICE return recovered exactly
-> retained device-kv-query-response receipt
-> Site readback/sync observation
-> recovery/provider reconstruction
```

No KnowledgeVault-specific heartbeat, scheduler, resident executor, signal protocol, provider credential path, or credential broker is authorized.

Source lifecycle at this entry:
- shared projection implementation: IMPLEMENTED_ON_BRANCH
- resident install/refresh integration: IMPLEMENTED_ON_BRANCH
- hosted validation: PENDING
- merged: NO
- authentic runtime projection: NOT OBSERVED
- KnowledgeVault provider session: NOT OBSERVED
- KnowledgeVault DEVICE_KV installation-status consumption: NOT OBSERVED
- KnowledgeVault HB-derived return: NOT OBSERVED
- Site readback: NOT OBSERVED
- authority effect: NONE_OBSERVATION_ONLY


## Source validation and merge — 2026-09-02

Current-main rematerialization PR #822 validated exact head `62d43b39312124a468c29ce1149be680a3d78738`:

- Heartbeat Worker Project - Validation Only / No GitHub Token Authority: `33688645541` SUCCESS
- Validate organization control plane - No GitHub Token Authority: `33688645512` SUCCESS
- Cross-Framework Current-Basis Resident Request Validation (Non-Authorizing): `33688645518` SUCCESS

Merged as `6358375c81fedb579cb6fcac59946268ea485ebb`.

Lifecycle distinction:

```text
shared projection implementation: IMPLEMENTED
resident install/refresh integration: IMPLEMENTED
hosted validation: PASS
merged: YES
runtime projection observed from deployment-local resident: NO
resident alive/current for any consumer inferred from merge: NO
KnowledgeVault provider session observed: NO
KnowledgeVault DEVICE_KV installation-status consumption observed: NO
KnowledgeVault HB-derived return observed: NO
Site readback observed: NO
authority_effect: NONE_OBSERVATION_ONLY
```

PR #817 remains historical validated-but-unmerged predecessor evidence and was closed after current-main conflict reconciliation.
