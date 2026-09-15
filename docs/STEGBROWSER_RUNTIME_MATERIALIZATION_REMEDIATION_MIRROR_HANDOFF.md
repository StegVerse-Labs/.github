# StegBrowser Runtime Materialization Remediation Mirror Handoff

Updated: 2026-09-14

## Task pointer

- Goal Task ID: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- Parent/remediates: `STEG-BROWSER-RESIDENT-CUSTODY-ROOT-OBSERVATION-001`
- Shared runtime-evidence owner: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / TWO-ROUND-TRIP MODEL MERGED+VALIDATED / MANIFEST-DEFINED OWNED PATH / INVOCATION-BOUND MATERIALIZATION REQUIRED / AUTHENTIC RUNTIME EVIDENCE PENDING`
- External/second user-operated device required: `false`

## Critical manifest-path invariant

Any governed Interlock/InTr data transport process leaving the ecosystem requires a manifest. The manifest is the route contract for that invocation.

The manifest defines, before ecosystem egress:

- the outbound Interlock/InTr endpoint;
- the receiver at the other end;
- the declared processing/reflection behavior;
- the return target for the first records/verification return;
- the mirror-processing boundary that originates the second return;
- the endpoint Interlock/InTr used on the ecosystem-return leg;
- the final ecosystem destination.

For this StegBrowser test, the path is owned by StegVerse. The far-end receiver is an owned mirror reflector. Therefore endpoint discovery, receiver discovery, and waiting for an externally available device are not part of this Goal.

```text
MANIFEST_REQUIRED_BEFORE_ECOSYSTEM_EGRESS = true
MANIFEST_IS_TRANSPORT_PATH_CONTRACT = true
OUTBOUND_INTERLOCK_INTR_ENDPOINT_DECLARED_BY_MANIFEST = true
FAR_END_RECEIVER_DECLARED_BY_MANIFEST = true
FAR_END_RECEIVER_ROLE = OWNED_MIRROR_REFLECTOR
MIRROR_PATH_IS_OWNED_DECLARED_PATH = true
ENDPOINT_DISCOVERY_REQUIRED = false
RECEIVER_DISCOVERY_REQUIRED = false
WAIT_FOR_ONLINE_DEVICE = false
STANDING_RESIDENT_SURFACE_REQUIRED = false
PREEXISTING_RUNTIME_CONNECTION_REQUIRED = false
```

The governed path for this Goal is conceptually:

```text
STEGVERSE ECOSYSTEM EGRESS
-> manifest-declared Interlock/InTr endpoint
-> manifest-declared owned mirror receiver
-> declared reflection return
-> records packet returned for recording/verification
-> Master Records recording / reconstruction / applicable processing
-> mirror-processing boundary
-> manifest-declared Interlock/InTr re-entry
-> manifest-declared endpoint Interlock/InTr
-> allowed ecosystem re-entry
```

Interlock/InTr does not discover this route. It evaluates/admit transitions on the route declared by the manifest. Runtime transition variables such as `callable` and `refreshable` therefore govern whether/how the declared path is instantiated for this invocation; they are not destination-discovery variables.

No execution component may substitute an undeclared endpoint or receiver.

## Runtime-materialization invariant

There is no standing StegBrowser runtime device or endpoint expected to be online waiting for work. The manifest declares the path and the selected substrate identifies what may be materialized to execute that declared path.

Correct progression is:

```text
bind complete manifest to active Goal/COSV
-> validate declared endpoint + receiver + return path
-> Interlock/InTr evaluates invocation state for the declared path
-> resolve callable + refreshable
-> materialize/instantiate admitted execution surface as needed
-> establish invocation-bound connection to the manifest-declared path
-> execute governed transport
```

If `callable=true, refreshable=true`, refresh/materialize from current canonical source as part of the invocation. If `callable=true, refreshable=false`, instantiate the allowed connection without an invented refresh requirement. If `callable=false`, the declared invocation path is not callable under that transition and must not be represented as executed.

## Source validation state

PR #1907 repaired binding of `RT-STEGBROWSER-RUNTIME-CONSUMPTION-001` to the active remediation Goal while preserving the retired historical task as lineage only.

PR #1908 corrected the data path to two governed Interlock/InTr round-trip phases.

Validated PR #1908 evidence:

```text
validated head = 947c4c7d0f8b1547dff0c3e303a9dbf4d47860e8
organization-control run = 34914042377 PASS
deterministic repository suite = 34914042375 PASS
heartbeat validation = 34914042368 PASS
merge commit = 0fdac00dd761da61fbd6f2f0e9c5d60463b1b924
```

A follow-on profile correction committed as `134d8b8f77bdd3996fab1f1fa704defaafd5ba09` makes the manifest-defined owned path explicit in `data/goal-task-transport-profiles/STEG-BROWSER-RUNTIME-CONSUMPTION-001.json`. That source correction does not claim runtime execution.

GitHub/CI runtime authority remains `NONE`.

## Current exact runtime condition

```text
AUTHENTIC_MANIFEST_BOUND_INVOCATION_AND_INTR_INGRESS_NOT_YET_OBSERVED
```

The missing evidence is not endpoint discovery or device availability. The missing evidence is execution of the already-declared manifest path through authentic Interlock/InTr admission.

## Round Trip 1 — manifest-defined mirror reflection to records verification

Round Trip 1 follows the manifest-declared outbound endpoint to the manifest-declared owned mirror receiver. The mirror performs the declared reflection behavior and the correlated records packet returns at the declared Interlock/InTr exit to the recording surface.

Required authentic evidence:

```text
MANIFEST_BOUND_TO_INVOCATION = true
DECLARED_ENDPOINT_AND_RECEIVER_VALIDATED = true
GOVERNED_RETURN_PACKET_RECEIVED = true
RECORDS_PACKET_DELIVERED_FOR_RECORDING = true
RETURN_RECORD_DURABLY_RECORDED = true
FIRST_FINAL_ALLOWED_INTR_EXIT_TRANSITION_OBSERVED = true
SUCCESSFUL_RECORDING_VERIFICATION_ROUND_TRIP_IDENTIFIED = true
```

Master Records records/custodies/reconstructs the returned state; it does not become transport authority.

## Between Round Trips — process to declared mirror boundary

After Round Trip 1 is recorded and verified, the returned material proceeds through the applicable record/reconstruction and processing path to the manifest-declared mirror boundary.

A failure here does not erase a completed Round Trip 1, but it prevents initiation/completion of Round Trip 2.

## Round Trip 2 — manifest-defined ecosystem return

The manifest-declared mirror-processing boundary initiates Interlock/InTr again. The governed return follows the manifest-declared endpoint Interlock/InTr and, if allowed, re-enters the declared ecosystem destination.

Required authentic evidence:

```text
MIRROR_BOUNDARY_PROCESSING_COMPLETE = true
MIRROR_BOUNDARY_INTR_REENTRY_OBSERVED = true
ENDPOINT_INTERLOCK_INTR_CALLED = true
ENDPOINT_INTERLOCK_INTR_ALLOWED = true
ECOSYSTEM_REENTRY_FINAL_ALLOWED_TRANSITION_OBSERVED = true
SUCCESSFUL_ECOSYSTEM_RETURN_ROUND_TRIP_IDENTIFIED = true
```

Only after both governed round trips are authentically identified may:

```text
SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIPS_IDENTIFIED = true
```

## Reusable transport composition

- `RTC-MANIFEST-001` — validates/binds the complete transport manifest before ecosystem egress.
- `RT-STEGBROWSER-RUNTIME-CONSUMPTION-001` — bounded execution capability for the active Goal/COSV.
- `RT-SOVEREIGN-SOURCE-REFRESH-001` — selected iff admitted invocation resolves `callable=true AND refreshable=true`.
- `RTC-ROUNDTRIP-003` — repeat count `2` for the declared StegBrowser path.
- `RTC-INTERLOCK-INTR-TRANSPORT-008` — governed transport at required crossings on both declared return lifecycles.
- `RTC-EVIDENCE-CUSTODY-004` — recording/custody/reconstruction between returns.
- `RTC-STEGVERSE-EGRESS-007` — applicable mirror-side second egress transition.
- `RTC-FARSIDE-FINAL-009` — applicable endpoint-side final transition into the ecosystem.

## Corrected Goal Chart

### A0 — Bind and validate manifest

Bind the complete manifest to the active Goal/COSV before ecosystem egress. Validate the manifest-declared Interlock/InTr endpoint, owned mirror receiver, reflection behavior, recording return target, mirror-return origin, endpoint Interlock/InTr, and ecosystem destination.

No endpoint/receiver discovery stage exists.

### A1 — Resolve invocation-bound state for declared path

Interlock/InTr evaluates `callable`, `refreshable`, applicable protocol state, and allowed materialization for the manifest-declared path.

### A2 — Materialize invocation-bound execution surface

Materialize only what the admitted transition permits. The execution surface exists to execute the declared manifest path; it does not choose the path.

### A3 — Establish WorkerCoordinator claim/fence

Require authentic claim/fence for the exact active Goal/COSV invocation.

### A4 — Enter governed Interlock/InTr transport

Admit the manifested invocation onto its declared route and retain authentic ingress evidence.

### A5 — Follow manifest-declared path to owned mirror

Execute only allowed transitions along the declared outbound endpoint/receiver path.

### A6 — Round Trip 1 return to recording

Receive the declared reflected records packet and deliver it through the declared return boundary to recording.

### A7 — Verify Round Trip 1

Durably record the return record and identify `SUCCESSFUL_RECORDING_VERIFICATION_ROUND_TRIP_IDENTIFIED=true`.

### B1 — Record/reconstruct/process toward declared mirror boundary

Process the returned material to the mirror boundary declared by the manifest.

### C1 — Initiate Round Trip 2 from declared mirror boundary

Re-enter Interlock/InTr on the manifest-defined return route.

### C2 — Call declared endpoint Interlock/InTr

The return reaches the endpoint declared by the manifest; the state transition occurs only iff allowed.

### C3 — Re-enter declared ecosystem destination

Observe final allowed ecosystem re-entry and identify `SUCCESSFUL_ECOSYSTEM_RETURN_ROUND_TRIP_IDENTIFIED=true`.

### C4 — Composition transport success

Set `SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIPS_IDENTIFIED=true` only after authentic success evidence for both declared round trips.

## Authority invariants

- Manifest: path declaration/binding; no independent transition authority.
- Task Registry: coordination only.
- Reusable tasks/components: bounded work only.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: transition and governed packet-movement authority on the manifest-declared path.
- TV/TVC: credential/provider authority.
- KV/SKAP Vault: user-verification authority.
- Master Records: recording/custody/reconstruction authority between governed returns; not transport authority.
- HeartBeat: observability/timing/freshness/correlation only.
- Healer: triggered bounded remediation only.
- GitHub/CI: source validation/evidence transport only; runtime authority `NONE`.
- Standing online device: not required and not expected.
- Second user-operated device: not required.

## Manual work

None.
