# StegBrowser Manifest Interlock/InTr Ingress Execution Mirror Handoff

Updated: 2026-09-15
Repository: `StegVerse-Labs/.github`

## Task pointer

- Goal Task ID: `STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001`
- Parent Goal: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / A1-A4 SOURCE MERGED+VALIDATED / NATIVE SOURCE-PACKAGE REPAIR MERGED+VALIDATED / SOURCE-PACKAGE RELAY PROFILE REPAIR MERGED+VALIDATED / AUTHENTIC SOURCE-PACKAGE RELAY+RESIDENT LOCALIZATION+A1-A4 EXECUTION PENDING`
- Node/Interlock source repair: PR `#1923`, validated head `f7b6cb86b9fff9fbeb1817e45920acc2effc200f`, merge `0098bc793865fd1db835c400b502dad5f8a5e32d`.
- Single-path A1-A4 reconciliation: PR `#1929`, validated head `60e7246e326d32d17525d83783c38c5e21528ff0`, merge `a4c2d173aad04219795e44d2051703accd404c9c`.
- Native source-package repair: PR `#1941`, validated head `7bd0527413aa22b54e079546bd5b5e16810d83dd`, merge `8eb3afd480b9670ab9e8c44c01825a2934d04289`.
- Source-package relay profile repair: StegOS issue `#391`, PR `#392`, validated head `7fb5c4e2f8345c440c0fabe8408220529e1b7f7b`, merge `b04cfb473399ba31fc5e69cb1674823c17a7e549`, StegOS CI run `34988828837` SUCCESS.
- Issue `#1918`: `CLOSED / SOURCE DEFECT COMPLETE`; authentic runtime evidence remains separate.

## Canonical path

```text
manifest
-> A1 registered/profile-derived StegVerse Node + Interlock/InTr invocation state
-> A2 governed InTr materialization/admission
-> A2.1 bounded invocation lease/state binding
-> A2.2 EVENT_EPHEMERAL StegOS materialization
-> A3 WorkerCoordinator claim/fence
-> A4 exact governed Interlock/InTr ingress
-> Round Trip 1
-> Master Records / mirror processing
-> Round Trip 2
-> ecosystem re-entry
```

No external runtime/device/host discovery stage, second runtime, second dispatcher, second scheduler, alternate receiver, endpoint discovery, or second user-operated device prerequisite exists.

## One-shot native invocation request

The already-issued request remains immutable:

```text
canonical request commit = 19935454cd8c68000b3a0fd70478b0d89d5cd622
invocation_request_nonce = STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z
requested_test_scope = A0_A4_SINGLE_INVOCATION
requested_invocation_count = 1
```

No second request may be emitted or substituted.

## Native source localization

`refresh_sovereign_worker_runtime_source.py` is intentionally transport-free. It copies static source only from an already-local canonical source and writes `source_git_head`; it performs no fetch/pull and receives no network authority.

The existing canonical localization mechanism is:

```text
RT-CONTROL-PLANE-SOURCE-PACKAGE-001
-> exact content-addressed stegverse.control-plane package
-> existing RTC-INTERLOCK-INTR-TRANSPORT-008 / TVC relay
-> existing StegOS sovereign relay egress executor
-> source-package profile adapter
-> existing /intr/source-package ingress
-> write-once source package retention
-> materialize_into_source(STEGVERSE_HEARTBEAT_SOURCE_ROOT)
-> next resident worker source refresh
-> resident request dispatch
```

PR #1941 repaired the package coverage defect by carrying the unchanged one-shot request without expanding the 512 KiB relay envelope.

StegOS PR #392 repaired the next exact composition defect. The existing sovereign relay executor and generic HIL round-trip adapter used `application/octet-stream` and validated `stegverse.hil-intr-materialization-ingress/v1`, while `/intr/source-package` requires `application/json`, `X-StegVerse-Transport-Origin: TVC_RELAY_EGRESS`, and returns `stegverse.control-plane-source-package-ingress/v1`. PR #392 added only a profile adapter around the existing `execute_relay_egress()` implementation. It requires exact TVC authorization/payload binding, `SOURCE_MATERIALIZED_VERIFIED`, exact `source_identity`, `network_source_fetch_performed=false`, `claim_or_fence_minted=false`, TV/TVC credential authority, and GitHub runtime authority `NONE`. It does not create another transport, runtime, scheduler, dispatcher, receiver, endpoint, device path, credential path, or execution authority.

No retained authentic invocation was found binding the built `RT-CONTROL-PLANE-SOURCE-PACKAGE-001` artifact through TVC bounded authorization into the merged StegOS source-package relay profile. Therefore source/CI/merge evidence does not prove relay or ingress.

## Current authentic predicates

```text
SOURCE_PACKAGE_REPAIR_MERGED_VALIDATED = true
SOURCE_PACKAGE_RELAY_PROFILE_REPAIR_MERGED_VALIDATED = true
SOURCE_PACKAGE_RELAY_OBSERVED = false
SOURCE_PACKAGE_INTR_INGRESS_OBSERVED = false
RESIDENT_SOURCE_MATERIALIZATION_OBSERVED = false
RESIDENT_SOURCE_GIT_HEAD_OBSERVED = false
RESIDENT_REQUEST_DISPATCH_OBSERVED = false
RESIDENT_REQUEST_CONSUMPTION_OBSERVED = false
RUNTIME_CONNECTION_TRANSITION_VARIABLES_OBSERVED = false
STEGVERSE_NODE_BOUND_TO_INVOCATION = false
INTERLOCK_BOUND_TO_NODE_AND_MANIFEST = false
INTR_MATERIALIZATION_ADMITTED = false
INVOCATION_SCOPED_LEASE_ESTABLISHED = false
EVENT_EPHEMERAL_STEGOS_RUNTIME_MATERIALIZED = false
EXECUTION_TIME_RUNTIME_IDENTITY_BOUND = false
CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED = false
ORGANIZATION_LOCAL_INTR_INGRESS_RECEIPT_VERIFIED = false
AUTHENTIC_INTR_INGRESS_OBSERVED = false
ROUND_TRIP_1_STARTED = false
```

Current exact condition:

`SOURCE_PACKAGE_BUILD_TO_TVC_AUTHORIZATION_AND_EXISTING_RELAY_EXECUTOR_INVOCATION_NOT_YET_BOUND_OR_OBSERVED`

Source/CI/GitHub state cannot promote any runtime predicate.

## Authority boundaries

- Manifest: route declaration/binding only.
- StegVerse Node: continuity/admission anchor only.
- Interlock/InTr: transition and governed packet-movement authority.
- Lease: bounded invocation scope only.
- EVENT_EPHEMERAL StegOS runtime: compute/materialization only.
- WorkerCoordinator: claim/fence authority.
- TV/TVC: credential and relay authorization authority.
- Master Records: observed-reality custody/reconstruction authority.
- GitHub/CI: source validation/evidence only; runtime authority `NONE`.
- Healer: triggered remediation only.

## Immediate continuation

Trace the existing same-execution composition from the retained `RT-CONTROL-PLANE-SOURCE-PACKAGE-001` result into the already-existing TVC bounded relay authorization and the merged StegOS `execute_control_plane_source_package_relay()` adapter. If that producer-to-executor binding is absent, repair only that binding; do not add another transport or request. Then require an authentic `stegverse.control-plane-source-package-ingress/v1` receipt with `state=SOURCE_MATERIALIZED_VERIFIED`, exact source identity, exact authorization ID, and exact payload hash before advancing to worker-source-refresh, resident request dispatch, canonical-work consumption, and A0-A4.

## README review

README reviewed for the bounded profile adapter; no byte change required because public runtime/authority topology did not change.

## Manual work

None.
