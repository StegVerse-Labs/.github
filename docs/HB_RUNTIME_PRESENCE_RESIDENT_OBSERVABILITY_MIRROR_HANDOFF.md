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
