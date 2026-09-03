# StegIndex Mandatory Preflight Mirror Handoff

Status: SOURCE_MERGED_CONSUMER + RESOLUTION_ADMISSION_INTEGRATION_BRANCH
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
