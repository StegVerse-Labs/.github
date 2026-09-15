# StegBrowser Runtime Materialization Remediation Mirror Handoff

Updated: 2026-09-14

## Task pointer

- Goal Task ID: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- Parent/remediates: `STEG-BROWSER-RESIDENT-CUSTODY-ROOT-OBSERVATION-001`
- Shared runtime-evidence owner: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / MANIFEST-BOUND OWNED MIRROR PATH MERGED+VALIDATED / A0 SOURCE-BINDING READY / AUTHENTIC INTR INGRESS + ROUND-TRIP EVIDENCE PENDING`
- External/second user-operated device required: `false`
- External connected runtime required: `false`
- External runtime discovery permitted as a prerequisite: `false`

## Canonical manifest-path invariant

Every governed Interlock/InTr transport process leaving the ecosystem is manifest-defined before egress. The manifest is the route contract; runtime execution does not discover or substitute its endpoint or receiver.

For this Goal the canonical manifest is:

`control/transport-manifests/STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001.json`

It declares:

- outbound ecosystem boundary: `STEGVERSE_ECOSYSTEM`;
- outbound Interlock/InTr endpoint: `STEGVERSE_OWNED_INTR_EGRESS_ENDPOINT`;
- far-end receiver: `STEGVERSE_OWNED_MIRROR_REFLECTOR`;
- receiver role: `OWNED_MIRROR_REFLECTOR`;
- expected action: `REFLECT_DECLARED_RECORDS_PACKET`;
- Round Trip 1 return target: `MASTER_RECORDS_RECORDING_SURFACE`;
- between-trip processing boundary: `STEGVERSE_OWNED_MIRROR_BOUNDARY`;
- Round Trip 2 Interlock/InTr endpoint: `STEGVERSE_OWNED_INTR_ECOSYSTEM_RETURN_ENDPOINT`;
- Round Trip 2 final receiver: `STEGVERSE_ECOSYSTEM`.

`endpoint_discovery_required=false`, `receiver_discovery_required=false`, and undeclared endpoint/receiver substitution is prohibited.

## Source implementation and validation

PR #1907 repaired reusable-task binding to the active remediation Goal.

PR #1908 established the correct two governed round-trip model:

1. Round Trip 1 returns the correlated records packet for recording/verification.
2. Master Records/reconstruction/mirror processing occurs between trips.
3. Round Trip 2 begins at the mirror boundary and returns through endpoint Interlock/InTr into the ecosystem.

PR #1910 makes A0 executable and manifest-bound:

- adds the canonical route manifest;
- binds `RT-STEGBROWSER-RUNTIME-CONSUMPTION-001` to `scripts/run_stegbrowser_manifest_bound_runtime.py`;
- validates exact Goal/COSV and exact owned endpoint/receiver path;
- fail-closes on endpoint or receiver substitution;
- writes `MANIFEST_BOUND_TO_INVOCATION` evidence;
- binds the manifest SHA-256 into `STEGVERSE_REUSABLE_TASK_INVOCATION_ID` before invoking the existing runtime runner;
- adds deterministic regression tests.

Validated PR #1910 evidence:

```text
validated head = dc0b1c0d6c5f5146a05c7125412e753ef267eaec
organization-control run = 34918148488 PASS
deterministic repository suite = 34918148475 PASS
heartbeat validation = 34918148535 PASS
merge commit = ba838f6fa960b7d3e6ff87d69f7a3d683f306fad
```

GitHub/CI runtime authority remains `NONE`.

## Runtime invocation model — no external connected runtime

There is no standing device, attached machine, remote host, pre-existing resident surface, or external runtime connection that is expected to appear now or later for this Goal.

The execution surface is created as part of the governed invocation itself.

Canonical progression:

```text
bind exact manifest to Goal/COSV
-> canonical resident execution request
-> existing StegVerse resident dispatcher / organization-local resident boundary
-> validate declared path
-> resolve invocation-bound callable/refreshable against that path
-> materialize ADMITTED-EPHEMERAL-STEGOS-NODE as part of this invocation
-> establish Interlock/InTr ingress on the declared route
-> execute Round Trip 1 to the declared owned mirror and recording return
-> verify durable Round Trip 1 record
-> process to declared mirror boundary
-> execute Round Trip 2 through declared endpoint Interlock/InTr
-> re-enter declared ecosystem destination
```

The current canonical resident request already declares:

```text
selected_execution_substrate = ADMITTED-EPHEMERAL-STEGOS-NODE
manual_device_prerequisite = false
second_machine_required = false
network_source_fetch_allowed = false
```

`callable` and `refreshable` govern whether/how the already-declared path and invocation-local execution surface are instantiated. They do not discover a destination, device, host, or remote runtime.

The existing organization-local resident boundary is the reusable Interlock/InTr ingress/egress execution boundary. It must be reused rather than creating a duplicate hosted carrier/runtime.

Canonical existing surfaces include:

```text
control/resident-execution-request.d/canonical-work-stegbrowser-runtime-consumption-001.json
scripts/install_and_run_canonical_work_event_bootstrap.py
scripts/dispatch_resident_execution_requests.py
scripts/refresh_and_execute_resident_task.py
workers/organization_local_resident_boundary_executor.py
```

Do not query Remote Desktop/device connectivity, Render, or another hosted carrier as a prerequisite for this Goal. Those are not part of the StegBrowser execution model.

## Current authentic evidence condition

```text
AUTHENTIC_MANIFEST_BOUND_INVOCATION_AND_INTR_INGRESS_NOT_YET_OBSERVED
```

No runtime completion predicate is promoted from source or CI.

The remaining work is to bind the already-existing StegBrowser resident request into the existing resident dispatcher/boundary path and retain authentic invocation-local evidence from that path. Absence of an external connected runtime is not a condition and must not be recorded as a failure, prerequisite, or pending dependency.

## Goal Chart

### A0 — Bind and validate manifest

Bind the complete manifest to the active Goal/COSV. Validate exact declared outbound endpoint, owned mirror receiver, reflection behavior, Round Trip 1 recording return, mirror boundary, Round Trip 2 endpoint, and ecosystem receiver. No discovery stage exists.

### A1 — Submit canonical resident invocation

Use the canonical StegBrowser resident execution request and existing StegVerse resident dispatcher. The request invokes the already-declared path; it does not locate an external runtime.

### A2 — Resolve invocation-bound state and materialize ephemeral execution surface

Interlock/InTr resolves `callable`, `refreshable`, and applicable transition state for the manifest-declared path. If admitted, materialize `ADMITTED-EPHEMERAL-STEGOS-NODE` as part of this invocation. No pre-existing online device, host, or runtime is expected.

### A3 — Establish WorkerCoordinator claim/fence

Require authentic current claim/fence for the exact Goal/COSV invocation.

### A4 — Admit Interlock/InTr ingress

Use the existing organization-local resident boundary to enter the declared path and retain authentic ingress evidence.

### A5 — Follow declared owned mirror path

Move through allowed transitions to `STEGVERSE_OWNED_MIRROR_REFLECTOR` and execute the declared reflection.

### A6 — Round Trip 1 return to recording

Return the correlated records packet to `MASTER_RECORDS_RECORDING_SURFACE`.

### A7 — Verify Round Trip 1

Require:

```text
MANIFEST_BOUND_TO_INVOCATION = true
GOVERNED_RETURN_PACKET_RECEIVED = true
RECORDS_PACKET_DELIVERED_FOR_RECORDING = true
RETURN_RECORD_DURABLY_RECORDED = true
FIRST_FINAL_ALLOWED_INTR_EXIT_TRANSITION_OBSERVED = true
SUCCESSFUL_RECORDING_VERIFICATION_ROUND_TRIP_IDENTIFIED = true
```

### B1 — Record/reconstruct/process to mirror boundary

Master Records and the exact processing owners advance the returned material to `STEGVERSE_OWNED_MIRROR_BOUNDARY`.

### C1 — Initiate Round Trip 2

Re-enter Interlock/InTr from the declared mirror boundary.

### C2 — Call declared endpoint Interlock/InTr

Use `STEGVERSE_OWNED_INTR_ECOSYSTEM_RETURN_ENDPOINT`; transition occurs iff allowed.

### C3 — Re-enter ecosystem

Require authentic allowed transition into `STEGVERSE_ECOSYSTEM` and set `SUCCESSFUL_ECOSYSTEM_RETURN_ROUND_TRIP_IDENTIFIED=true`.

### C4 — Composition success

Set `SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIPS_IDENTIFIED=true` only after authentic success for both declared round trips.

## Out-of-scope defect remediation exception branch

Canonical contract:

`data/out-of-scope-remediation-request-contract.json`

This branch may be entered from any GC transition only after an actual broken condition is observed. A pending predicate alone is not a defect and does not trigger this branch.

```text
X1 observed broken condition
-> X2 retain exact failure evidence and classify owning domain
-> require OUT_OF_SCOPE_FOR_CURRENT_GOAL=true
-> X3 classify whether the foreign defect blocks the current transition
-> X4 emit StegVerse-Healer remediation evaluation request with AUTHORITY_TRANSFER=NONE
-> request emission does NOT trigger Healer
-> X5 StegVerse-Healer independently evaluates authorized remediation triggers
-> if nonblocking: continue unrelated current-Goal GC transitions
-> if blocking and an authorized bounded remedy is completed: return to the interrupted GC transition
```

Required routing predicates:

```text
OBSERVED_BROKEN_CONDITION = true
EXACT_FAILURE_EVIDENCE_RETAINED = true
OWNING_DOMAIN_CLASSIFIED = true
OUT_OF_SCOPE_FOR_CURRENT_GOAL = true
HEALER_REMEDIATION_REQUEST_EMITTED = true
AUTHORITY_TRANSFER = NONE
HEALER_TRIGGERED_BY_REQUEST_EMISSION = false
```

## Authority invariants

- Manifest: path declaration/binding only.
- Task Registry: coordination only.
- Reusable tasks/components: bounded work only.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: transition and governed packet-movement authority on the manifest-declared path.
- TV/TVC: credential/provider authority.
- KV/SKAP Vault: user-verification authority.
- Master Records: recording/custody/reconstruction authority between governed returns; not transport authority.
- HeartBeat: observability only.
- Healer: independent trigger evaluation and triggered bounded remediation only; remediation-request receipt alone grants no authority and is not a trigger.
- GitHub/CI: source validation/evidence transport only; runtime authority `NONE`.
- Standing online device: not required or expected.
- External connected runtime: not required or expected.
- Second user-operated device: not required.

## Manual work

None.
