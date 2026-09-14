# StegBrowser Transport Boundary Implementation Mirror Handoff

Updated: 2026-09-14

## Task pointer

- Goal Task ID: `STEG-BROWSER-TRANSPORT-BOUNDARY-IMPLEMENTATION-001`
- Parent Goal: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / SOURCE SEMANTICS CORRECTED / CI AND MERGE NOT YET VALIDATED`
- Implementation branch: `stegbrowser-transport-boundary-contract`
- Pull request: `StegVerse-Labs/.github#1901`

## Scope

Implement and validate the corrected transport boundary without claiming runtime execution from source or CI.

Transport succeeds only when the governed return packet has been received, the return record durably recorded, and the final allowed Interlock/InTr state transition exiting transport has been observed. At that boundary:

```text
SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIP_IDENTIFIED = true
```

Master Records ingress/custody/reconstruction, mirroring, reconciliation, persistence, projection, measurement, publication, or any later action is post-transport and cannot retroactively negate the transport predicate.

`callable` and `refreshable` remain invocation-bound Interlock/InTr state-transition variables. Healer remains triggered remediation only.

## Round-trip lifecycle correction

The StegBrowser runtime-consumption composition contains **one governed round-trip lifecycle**, not two independent round-trip goals.

The following are internal transition groups within that single lifecycle:

- `canonical_work_ingress_and_resident_consumption`
- `tvc_source_promotion_and_runtime_observation`

They may contain multiple allowed Interlock/InTr state transitions and repeated uses of the transport component as required by the state graph, but they do **not** increment the `RTC-ROUNDTRIP-003` lifecycle count.

Canonical profile semantics on branch `stegbrowser-transport-boundary-contract` are therefore:

```text
governed_round_trip_lifecycle_count = 1
RTC-ROUNDTRIP-003 repeat count = 1
internal transition group count = 2
internal transition groups are separate round-trip goals = false
```

The reusable transport contract now distinguishes lifecycle repeat count from internal transition groups. Profiles may explicitly set `governed_round_trip_lifecycle_count` and `round_trip_internal_transition_groups`. Legacy `required_round_trips` length remains a compatibility fallback for profiles not yet migrated; it must not override an explicit lifecycle count.

## Implementation set

- `data/reusable-transport-component-contract.json`
  - encode terminal transport boundary and success predicate;
  - distinguish governed round-trip lifecycle count from internal transition groups;
  - mark `RTC-EVIDENCE-CUSTODY-004` as post-transport and non-authorizing for transport success;
  - preserve Interlock/InTr transport authority and Master Records reconstruction authority.
- `data/goal-task-transport-profiles/STEG-BROWSER-RUNTIME-CONSUMPTION-001.json`
  - declare one governed round-trip lifecycle;
  - classify the two named requirements as internal transition groups;
  - set `RTC-ROUNDTRIP-003` repeatability to `1`;
  - split `transport_phase_components` from `post_transport_components`;
  - bind the terminal transport predicate;
  - preserve invocation-bound callable/refreshable selection.
- `tests/test_stegbrowser_transport_boundary_contract.py`
  - deterministic assertions for the terminal boundary, failure ownership, Master Records separation, callable/refreshable semantics, and single-lifecycle/multiple-transition-group semantics.

## Completion predicates

- `TRANSPORT_TERMINAL_CONTRACT_ENCODED`
- `RTC_EVIDENCE_CUSTODY_CLASSIFIED_POST_TRANSPORT`
- `STEGBROWSER_PROFILE_SPLITS_TRANSPORT_AND_POST_TRANSPORT_COMPONENTS`
- `SINGLE_GOVERNED_ROUND_TRIP_LIFECYCLE_SEMANTICS_ENCODED`
- `INTERNAL_TRANSITION_GROUPS_DO_NOT_INCREMENT_ROUND_TRIP_COUNT`
- `CALLABLE_REFRESHABLE_REMAIN_INVOCATION_BOUND`
- `POST_TRANSPORT_FAILURE_CANNOT_NEGATE_TRANSPORT_SUCCESS`
- `DETERMINISTIC_TESTS_PASS`
- `SOURCE_CHANGE_MERGED`

## Current state

The source semantics are implemented on branch `stegbrowser-transport-boundary-contract` through head `2952b36e8e562b3acbb26c5c9883ac5b2922653a`.

PR #1901 is open and mergeable. No GitHub Actions run was observed yet for that exact head when last checked, so deterministic CI validation and merge remain unproven. Runtime transport success remains separately unclaimed.

README was checked for task-specific `RTC-ROUNDTRIP-003` / `required_round_trips` repeat-count semantics; no stale task-specific wording was found that required a README content change for this correction.

## Authority / failure boundaries

- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: governed transition and packet movement authority.
- TV/TVC: credential/provider authority.
- KV/SKAP Vault: user-verification authority.
- Master Records: observed-reality/custody/reconstruction authority after transport; not transport-success authority.
- Healer: triggered bounded remediation only.
- GitHub/CI: source validation/evidence transport only; runtime authority `NONE`.

## Manual work

None.
