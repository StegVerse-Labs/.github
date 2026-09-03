# StegIndex Mandatory Preflight Mirror Handoff

Status: SOURCE_MERGED_VALIDATED_MANDATORY_PREFLIGHT
Updated: 2026-09-02
Repository: StegVerse-Labs/.github
Origin: StegVerse-Labs/.github#841
Index owner: StegVerse-Labs/StegIndex
Index integration owner: StegVerse-Labs/StegIndex#1

## Goal

Require a StegIndex capability/predicate resolution before a StegVerse session, worker, or build lane treats an unresolved condition as a generic implementation/runtime-evidence blocker or creates duplicate capability work.

## Implementation

- `control/stegindex-preflight-policy.json`
- `scripts/run_stegindex_preflight.py`
- `tests/test_stegindex_preflight.py`

The preflight consumes an already-local canonical StegIndex source rooted by:

`STEGVERSE_STEGINDEX_SOURCE_ROOT`

It performs no network fetch and requires no GitHub/provider credential.

## Resolution semantics

The result distinguishes:
- matching reusable capabilities;
- current lifecycle/evidence posture;
- exact missing predicate;
- canonical satisfier/owner;
- invocation surface;
- whether machine continuation is required;
- whether a generic blocker is even permitted.

An unavailable StegIndex source is `PREFLIGHT_UNAVAILABLE`, not evidence that the requested capability is unimplemented.

## Authority

StegIndex and this preflight grant NO execution, admission, claim/fence, credential, routing, transition, publication, custody, or consequence authority.

`credential_authority: TV/TVC`
`github_token_runtime_authority: NONE`
`authority_effect: NONE_READ_RESOLVE_ONLY`

## Completion boundary

Source completion requires deterministic tests and merge.

Operational adoption additionally requires materializing canonical StegIndex source into the applicable resident/session execution surface and invoking this preflight from the entry paths that create new work or blocker classifications.

No source/CI/merge result constitutes runtime evidence.


## Automatic resolution-task admission integration — 2026-09-02

The blocker-to-resolution path now performs a StegIndex preflight before admitting a generated successor task.

Implementation:
- `heartbeat_runtime/engine_v10.py::_run_stegindex_preflight`
- `heartbeat_runtime/engine_v10.py::_admit_resolution_task`
- `tests/test_fail_closed_resolution_escalation.py`

Behavior:
1. resolve canonical StegIndex from `STEGVERSE_STEGINDEX_SOURCE_ROOT` or the existing `STEGVERSE_REPO_ROOTS_JSON` map;
2. invoke `StegIndex/scripts/preflight.py` through the merged local consumer;
3. persist `receipts/stegindex-preflight/<parent>-HB<epoch>-<digest>.json`;
4. include that receipt in the generated resolution task source/evidence refs;
5. expose duplicate-implementation and machine-continuation posture in the admission event;
6. if the canonical index is not locally materialized, record `PREFLIGHT_UNAVAILABLE` and explicitly preserve `source_unavailable_is_implementation_missing=false`.

This integration does not infer that a missing StegIndex source means the requested capability is absent, and it performs no network fetch.

Operationally mandatory resolution still depends on canonical StegIndex being present in the local repository-root map; source-level receipt enforcement is now implemented.


## Portable resident materialization integration — 2026-09-02

The complete resident stack now treats canonical StegIndex source as a required non-secret local source root.

Implemented:
- `scripts/package_sovereign_control_plane_bundle.py --stegindex-root`
- bundle path `vendor/StegIndex/**`
- minimum required StegIndex source:
  - `STEGINDEX_MIRROR_HANDOFF.md`
  - `scripts/preflight.py`
  - `registry/capabilities.json`
  - `registry/predicates.json`
- `scripts/activate_resident_stack.py --stegindex-root`
- `scripts/consume_one_shot_resident_stack_activation_request.py` root key `stegindex`
- canonical repository-map key `StegVerse-Labs/StegIndex`

Missing StegIndex source produces `SOURCE_ROOTS_PENDING`; it is not reclassified as evidence that some requested capability is absent.

The bundle remains local source transport only:
`network_fetch_required=false`
`bundle_grants_authority=false`
`github_token_runtime_authority=NONE`
`credential_authority=TV/TVC`

Authentic resident materialization/execution is not claimed by this source change.


## Current-main merge receipt — 2026-09-02

Canonical current-main integration:
- PR #888
- merge: `db333d153709a862dad712424f06c2c7249257a0`
- organization control-plane validation: `33713693057` SUCCESS
- Heartbeat Worker Project validation: `33713692880` SUCCESS
- complete deterministic repository test suite: SUCCESS

This merge preserves the separately merged session/build pre-work boundary on current main and adds:
- blocker-derived resolution admission preflight receipts;
- canonical repository-root-map StegIndex discovery;
- portable `vendor/StegIndex/**` source packaging;
- StegIndex as a required complete one-shot resident-stack source root.

Source state:
`MANDATORY_PREFLIGHT_SOURCE_MERGED_VALIDATED`

Authentic resident state:
`STEGINDEX_RESIDENT_MATERIALIZATION_NOT_YET_OBSERVED`
`STEGINDEX_RESOLUTION_ADMISSION_PREFLIGHT_RECEIPT_NOT_YET_OBSERVED`

The unobserved resident predicates remain evidence requirements only. They do not reopen the merged source implementation and do not imply a missing StegIndex capability.


## Capability-risk admission observability — 2026-09-03

The canonical blocker-derived resolution admission path now carries StegIndex capability-risk metadata into the existing admission event without changing task authority or scheduler behavior.

Implemented:
- `scripts/run_stegindex_preflight.py` preserves a stable empty `capability_risk` shape when canonical StegIndex is unavailable;
- `heartbeat_runtime/engine_v10.py` exposes:
  - `stegindex_risk_transition_surfaces`;
  - `stegindex_risk_required_governance`;
  - `stegindex_risk_authority_effect`;
- deterministic tests cover canonical passthrough and unavailable-source event shape.

This is observability only. The risk metadata does not:
- add required capabilities to a generated task;
- alter claim/fence ownership;
- grant execution or transition authority;
- create network/runtime dependencies;
- make third-party reference content executable.

The admission event can now reveal both the exact predicate/continuation posture and the transition surfaces/governance considerations associated with the requested capability.

Runtime activation claim: NONE.
Authority effect: NONE_READ_RESOLVE_ONLY.
