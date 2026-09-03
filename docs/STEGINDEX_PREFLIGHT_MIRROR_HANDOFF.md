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


## Continuous discovery root-map propagation — 2026-09-03

The organization preflight wrapper now preserves the existing non-secret `STEGVERSE_REPO_ROOTS_JSON` map when it invokes canonical `StegIndex/scripts/preflight.py`.

This closes a source propagation gap:
- the wrapper already used the repository-root map to locate StegIndex;
- previously the child resolver received only `PATH`;
- continuous local-source discovery inside StegIndex therefore could not observe the same already-materialized repository set through this wrapper.

After this change:
- no additional source fetch is introduced;
- no new environment authority is created;
- only the existing non-secret local repository locator map is forwarded;
- capability-risk metadata remains unchanged;
- TV/TVC credential authority remains unchanged;
- GitHub token runtime authority remains NONE.

No authentic resident discovery refresh is claimed by this source propagation change.


## Exact resident operational proof verifier — 2026-09-03

The remaining resident evidence predicates now have an explicit non-authorizing verifier.

Implemented:
- `scripts/consume_one_shot_resident_stack_activation_request.py` records secret-free source-root observation:
  - `resolved_source_roots` as logical root names only;
  - `stegindex_source_root_resolved`;
  - `source_root_resolution_observed`;
- an already-completed one-shot request can re-observe current local source-root availability without re-executing activation;
- `scripts/verify_stegindex_resident_operational_proof.py`;
- `tests/test_stegindex_resident_operational_proof.py`.

The verifier requires BOTH:
1. a resident one-shot consumption receipt proving the local StegIndex source root was actually resolved with no network source fetch and TV/TVC / no-GitHub-token runtime authority preserved;
2. a resident `stegverse.stegindex-resolution-admission-preflight/v1` receipt whose nested preflight has `canonical_resolver_invoked=true` and is not `PREFLIGHT_UNAVAILABLE`.

Output:
- `receipts/sovereign-host/stegindex-resident-operational-proof.latest.json`
- state `COMPLETE` only when both predicates are observed.

This verifier does not create either event, does not rerun a completed resident activation, and does not infer resident proof from source/CI/deployment. `runtime_activation_claimed=false`; authority effect is `NONE_EVIDENCE_VERIFICATION_ONLY`.


## Resident direct-root forwarding repair — 2026-09-03

Live resident-proof reconciliation identified a bounded execution seam in the existing dispatcher environment sanitizer.

The one-shot StegIndex consumer already supports both:
- `STEGVERSE_STEGINDEX_SOURCE_ROOT`;
- `STEGVERSE_REPO_ROOTS_JSON["StegVerse-Labs/StegIndex"]`.

However, `scripts/dispatch_resident_execution_requests.py` forwarded the repository-root map but omitted the direct non-secret `STEGVERSE_STEGINDEX_SOURCE_ROOT` binding. A resident configured with the canonical direct binding and no equivalent root-map entry could therefore lose that locator at the dispatcher boundary and incorrectly produce `SOURCE_ROOTS_PENDING`.

Repair:
- forward `STEGVERSE_STEGINDEX_SOURCE_ROOT` through the existing non-secret resident environment allowlist;
- retain hosted-environment rejection;
- retain GitHub/provider-token stripping;
- retain TV/TVC credential authority and GitHub-token runtime authority NONE;
- add regression coverage proving the direct StegIndex root survives dispatcher sanitization while forbidden tokens do not.

This repair does not create resident evidence, rerun activation, grant authority, introduce network source fetch, or add another scheduler/runtime/device dependency.

Authentic resident materialization and blocker-derived preflight receipt remain separate required observations.


## Resident direct-root forwarding validated closure — 2026-09-03

Canonical repair:
- PR #915
- merge: `8be33ef21e77e8417e0ef71f43dbca3a570a5c89`
- validated head: `cb5387c36b781fd29bd33207342f2719b44a093f`

Observed validation:
- organization control-plane validation `33766137513` — SUCCESS
- Heartbeat Worker Project validation `33766137590` — SUCCESS
- Cross-Framework Current-Basis Resident Request validation `33766137593` — SUCCESS

The direct non-secret `STEGVERSE_STEGINDEX_SOURCE_ROOT` binding is now preserved through resident dispatcher sanitization on canonical main.

This closes the source-level forwarding seam only. It does not establish:
- resident StegIndex materialization;
- one-shot request consumption;
- blocker-derived resolution admission;
- StegIndex resident operational proof COMPLETE.

Current authentic operational predicates therefore remain evidence-only and unresolved until deployment-local resident receipts exist.

## Upstream direct-root propagation closure — 2026-09-03

Tracking: StegVerse-Labs/.github#924.

After dispatcher repair #915, direct-root propagation was audited one boundary farther upstream. The canonical non-secret `STEGVERSE_STEGINDEX_SOURCE_ROOT` locator could still be dropped by service installation or portable refresh bridges even though `STEGVERSE_REPO_ROOTS_JSON` was retained.

This lane preserves the direct locator through:
- `scripts/install_sovereign_heartbeat_service.py`;
- `scripts/install_sovereign_heartbeat_service_base.py`;
- `scripts/refresh_and_dispatch_resident_requests.py`;
- `scripts/refresh_and_execute_resident_task.py`.

The carrier does not receive repository locators. Only the worker/runtime path receives the direct StegIndex source root. Existing credential stripping, hosted-environment rejection, TV/TVC credential authority, no-network-source-fetch rules, and no-second-machine semantics are unchanged.

This remains source propagation only. It does not satisfy either authentic StegIndex #4 resident evidence predicate.

### #926 current-main reconciliation

PR #926 was replayed onto current main `365c983d3c276f204a5d9ef3c3df4dac9c00d0da` after unrelated concurrent organization work advanced main beyond its original base. The replay preserved all intervening main changes and retained only the bounded StegIndex locator propagation/test delta. This reconciliation grants no runtime or authority claim.

