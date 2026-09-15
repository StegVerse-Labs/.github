# StegBrowser Manifest Interlock/InTr Ingress Execution Mirror Handoff

Updated: 2026-09-15
Repository: `StegVerse-Labs/.github`

## Task pointer

- Goal Task ID: `STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001`
- Parent Goal: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / A1-A4 SOURCE MERGED+VALIDATED / NATIVE SOURCE-PACKAGE REPAIR MERGED+VALIDATED / AUTHENTIC SOURCE-PACKAGE RELAY+RESIDENT LOCALIZATION+A1-A4 EXECUTION PENDING`
- Node/Interlock source repair: PR `#1923`, validated head `f7b6cb86b9fff9fbeb1817e45920acc2effc200f`, merge `0098bc793865fd1db835c400b502dad5f8a5e32d`.
- Single-path A1-A4 reconciliation: PR `#1929`, validated head `60e7246e326d32d17525d83783c38c5e21528ff0`, merge `a4c2d173aad04219795e44d2051703accd404c9c`.
- Native source-package repair: PR `#1941`, validated head `7bd0527413aa22b54e079546bd5b5e16810d83dd`, merge `8eb3afd480b9670ab9e8c44c01825a2934d04289`.
- PR #1941 exact-head validation: organization control `34984618386`, deterministic repository suite `34984618375`, Heartbeat validation `34984619006` — all SUCCESS.
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
-> existing /intr/source-package ingress
-> write-once source package retention
-> materialize_into_source(STEGVERSE_HEARTBEAT_SOURCE_ROOT)
-> next resident worker source refresh
-> resident request dispatch
```

PR #1941 repaired the only proven source-package defect: the default package omitted the one-shot StegBrowser request bytes introduced by commit `19935454...`. The first implementation attempt redundantly included the already-canonical A0-A4 runner chain and exact-head deterministic validation rejected the resulting ~951 KiB package against the existing 512 KiB relay envelope. The relay bound was preserved. The final validated repair carries only the actual new request delta while the runner/consumer path remains the previously merged/validated canonical source.

The source-package ingress contract requires the existing TVC relay origin and authorization ID, validates exact payload SHA-256, writes the content-addressed package once, and materializes it into the declared `STEGVERSE_HEARTBEAT_SOURCE_ROOT`. It explicitly does not mint claims/fences, grant execution authority, perform a network source fetch, or commit the later runtime transition.

PR #1941 proves source package construction/coverage only. It does not prove package relay, `/intr/source-package` admission, resident source materialization, source refresh, request dispatch, request consumption, or A0-A4 execution.

## Current authentic predicates

```text
SOURCE_PACKAGE_REPAIR_MERGED_VALIDATED = true
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

`CONTROL_PLANE_SOURCE_PACKAGE_RELAY_AND_RESIDENT_LOCALIZATION_NOT_YET_OBSERVED`

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

Use only the existing governed `RTC-INTERLOCK-INTR-TRANSPORT-008 / TVC` relay for the exact validated control-plane source package containing the unchanged nonce request. Do not create another request or transport. Retain the authentic `stegverse.control-plane-source-package-ingress/v1` receipt and require `SOURCE_MATERIALIZED_VERIFIED`; then require the next resident source-refresh receipt to show a source state containing the unchanged request, follow the same cycle through resident dispatch and canonical-work consumption, and only then verify/promote A0-A4 from same-invocation receipts.

## README review

README reviewed for this bounded internal source-package coverage repair; no byte change required because public runtime/authority semantics did not change.

## Manual work

None.
