# StegBrowser Runtime Materialization Remediation Mirror Handoff

Updated: 2026-09-14

## Task pointer

- Goal Task ID: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- Parent/remediates: `STEG-BROWSER-RESIDENT-CUSTODY-ROOT-OBSERVATION-001`
- Shared runtime-evidence owner: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
- Issue: `StegVerse-Labs/.github#1866`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / STATE-TRANSITION GC / GOVERNED TRANSPORT BOUNDARY EXPLICIT / AUTHENTIC ROUND-TRIP PENDING`
- External/second user-operated device required: `false`

## Governing GC model

The Goal Chart is a state-transition graph, not a fixed waterfall. Reusable tasks/components are candidates selected from invocation-bound state and transition predicates. Reusable definitions are non-authorizing; WorkerCoordinator, Interlock/InTr, TV/TVC, KV/SKAP Vault, and Master Records retain their existing authority domains.

`callable` and `refreshable` remain invocation-bound state-transition variables. There is no assumed always-on runtime source and no persistent source-freshness completion state.

## Governed transport-boundary correction

The governed Interlock/InTr data-transport lane ends at the final allowed state transition that exits transport after the governed return record has been received and durably recorded.

Required semantics:

- Intermediate Interlock/InTr state transitions may occur locally at either authorized endpoint iff the transition is allowed.
- The governed return packet completes the round-trip transport lifecycle.
- Packet arrival time at the final state-transition boundary is not extended merely because the lifecycle is round-trip.
- Once the return record is received and durably recorded, a successful governed data-transport round trip has been identified.
- At that point the canonical predicate is:

```text
SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIP_IDENTIFIED = true
```

- The final allowed state transition out of the transport lane marks the end of the transport subproblem.
- Master Records ingress, reconstruction, mirroring, reconciliation, persistence, projection, measurement, publication, or any other action after that boundary is a post-transport problem/domain within the larger end-to-end loop.
- A downstream failure after the final transport transition must not be classified as a transport failure.
- Master Records remains observed-reality/custody/reconstruction authority, but Master Records reconstruction is not required to prove transport success.

## Reusable-task/component fit

### Governed transport-loop side

- `RT-STEGBROWSER-RUNTIME-CONSUMPTION-001` — bounded StegBrowser runtime-consumption work selected when its invocation profile matches.
- `RT-SOVEREIGN-SOURCE-REFRESH-001` — selected only when the invocation-bound transition resolves source refresh as applicable (`callable=true` and `refreshable=true` under the current connection transition).
- `RT-INTR-PROTOCOL-ESTABLISH-001` — selected only when no applicable existing InTr protocol resolves for the required governed connection.
- `RTC-ROUNDTRIP-003` — existing reusable governed round-trip component; repeatable according to the Goal's declared transport requirements.
- `RTC-INTERLOCK-INTR-TRANSPORT-008` — existing reusable Interlock/InTr transport component; repeatable where required transitions occur.

`RT-EXTERNAL-FRAMEWORK-ROUNDTRIP-ROLLOUT-001` is not selected for this Goal because its profile is explicitly scoped to registry-selected external frameworks. Its use of `RTC-ROUNDTRIP-003` and `RTC-INTERLOCK-INTR-TRANSPORT-008` confirms that the generic reusable transport components already exist; no new StegBrowser-specific round-trip reusable task is required merely to express this boundary.

### Post-transport side

- `RT-CANONICAL-STATE-RECONCILIATION-001` — reconcile canonical task/claim/evidence projections without overwriting authority domains.
- `RT-MIRROR-HANDOFF-VALIDATION-001` — reconcile continuation/handoff state after material task-state change.
- `RT-STEGINDEX-VALIDATION-001` — conditional when an indexed capability/runtime projection materially changes.
- `RT-README-VALIDATION-001` — conditional when repository behavior/capability documentation materially changes.
- `RT-SESSION-CLOSEOUT-001` — session/handoff-bound maintenance composition only.
- `GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001` — existing canonical runtime-observation component/child, not a `RT-*` reusable identity.

No new reusable task is required by this correction.

## Corrected Goal Chart (GC)

### Domain A — Invocation and governed transport-loop completion

#### Stage A1 — Resolve invocation state and candidate reusable capabilities

- **Task:** Bind the invocation context and evaluate the state variables/capability requirements needed to establish this connection, including `callable`, `refreshable`, applicable protocol resolution, required transport round trip(s), and admissible execution substrate.
- **Reusable overlay:** Candidate `RT-STEGBROWSER-RUNTIME-CONSUMPTION-001`; candidate `RT-SOVEREIGN-SOURCE-REFRESH-001`; conditional `RT-INTR-PROTOCOL-ESTABLISH-001`; transport components `RTC-ROUNDTRIP-003` and `RTC-INTERLOCK-INTR-TRANSPORT-008` according to declared requirements.
- **Authority:** Interlock/InTr owns governed transition admission; reusable definitions do not grant admission.
- **Completion predicates:** invocation-bound transition variables authentically observed; required reusable/component composition resolved without duplicate authority/runtime.
- **Failure ownership:** transition/profile resolution domain. A failure here is not yet a packet-transport failure unless an admitted transport transition has begun.
- **Status:** `PENDING AUTHENTIC TRANSITION EVIDENCE`.

#### Stage A2 — Materialize invocation-bound runtime/source state selected by A1

- **Task:** Materialize only state permitted by the transition. If the admitted state selects refresh, run `RT-SOVEREIGN-SOURCE-REFRESH-001`; if it does not, do not invent a refresh prerequisite.
- **Reusable overlay:** `RT-SOVEREIGN-SOURCE-REFRESH-001` when selected; `RT-STEGBROWSER-RUNTIME-CONSUMPTION-001` remains a candidate bounded work unit.
- **Authority:** Interlock/InTr for transition admissibility; source refresh has authority effect `NONE_LOCAL_SOURCE_REFRESH`.
- **Completion predicates:** selected runtime/source state materialized with authentic receipt/boundary evidence; mutable runtime state preserved where refresh applies.
- **Failure ownership:** runtime/source materialization. Do not classify a source-materialization failure as transport failure before transport starts.
- **Status:** `PENDING A1`.

#### Stage A3 — Claim/fence the derived executable work

- **Task:** WorkerCoordinator claims the exact invocation-bound executable work and establishes fresh claim/fence lineage.
- **Reusable overlay:** selected reusable-task invocation(s) only; no replacement WorkerCoordinator task.
- **Authority:** WorkerCoordinator.
- **Completion predicate:** `CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED = true` for the execution being transported/processed.
- **Failure ownership:** WorkerCoordinator claim/fence domain, not transport unless a transport transition had already begun and the failure is within that lane.
- **Status:** `PENDING`.

#### Stage A4 — Enter governed Interlock/InTr transport

- **Task:** Admit the first transport transition and move the manifested packet into the governed transport lane.
- **Reusable overlay:** `RTC-INTERLOCK-INTR-TRANSPORT-008`; `RTC-ROUNDTRIP-003` when a request/return cycle is required; `RT-INTR-PROTOCOL-ESTABLISH-001` only if protocol resolution was absent.
- **Authority:** Interlock/InTr.
- **Completion predicates:** authentic ingress/admission transition retained; transport correlation identity established.
- **Failure ownership:** governed transport begins here. Failure of an admitted packet to progress through required allowed transport transitions is transport-owned.
- **Status:** `PENDING`.

#### Stage A5 — Execute allowed intermediate endpoint transitions and bounded processing

- **Task:** Permit intermediate state transitions locally at either authorized endpoint iff each transition is allowed; execute the bounded StegBrowser work selected for this invocation where required by the manifested flow.
- **Reusable overlay:** `RT-STEGBROWSER-RUNTIME-CONSUMPTION-001`; repeat `RTC-INTERLOCK-INTR-TRANSPORT-008` at required authority crossings; `RTC-ROUNDTRIP-003` maintains request/return correlation.
- **Authority:** Interlock/InTr for every governed state transition; WorkerCoordinator claim/fence remains binding; TV/TVC only where credential/provider state is required by the invocation.
- **Completion predicates:** required allowed intermediate transitions observed; applicable runtime-consumption predicates observed without creating parallel scheduler/dispatcher/credential/device paths.
- **Failure ownership:** if failure occurs before the final transport exit while packet movement/required transport transition is incomplete, it is transport or the specific authority/component owning the failed in-lane transition. Healer may be triggered only for an observed remediable defect.
- **Status:** `PENDING`.

#### Stage A6 — Complete the governed return packet and durably record the return

- **Task:** Complete the return leg of the governed round trip, receive the governed return packet, and durably record the return record with exact correlation/provenance.
- **Reusable overlay:** `RTC-ROUNDTRIP-003` + `RTC-INTERLOCK-INTR-TRANSPORT-008`; primary runtime task evidence may be carried/correlated but does not redefine transport authority.
- **Authority:** Interlock/InTr for packet movement and transition admission.
- **Completion predicates:** governed return packet received; return record durably recorded; exact request/return correlation retained.
- **Timing rule:** packet arrival time at the final state-transition boundary is the arrival time at that boundary. The fact that the transport lifecycle includes a return leg does not add time after that packet has arrived at the final boundary.
- **Failure ownership:** missing/invalid/unrecorded required return before final transport exit is transport-owned (or the exact in-lane authority/component that failed).
- **Status:** `PENDING`.

#### Stage A7 — Final allowed transport-exit transition / transport subproblem complete

- **Task:** Apply the final allowed state transition that exits the governed transport lane after the return record is received and durably recorded.
- **Reusable overlay:** `RTC-INTERLOCK-INTR-TRANSPORT-008`; `RTC-ROUNDTRIP-003` supplies the completed request/return correlation. No Master Records reconstruction is required to establish this predicate.
- **Authority:** Interlock/InTr.
- **Completion predicates:** final allowed transport-exit transition observed AND return record durably recorded, therefore:

```text
SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIP_IDENTIFIED = true
```

- **Failure ownership:** failure at or before this final required transport transition can be transport-owned. After this transition succeeds, the transport subproblem is closed and later failures must not be back-propagated as transport failures.
- **Status:** `PENDING / TRANSPORT TERMINAL PREDICATE NOT YET OBSERVED`.

### Domain B — Post-transport mirror/reconstruction processing

Domain B begins only after the A7 transport boundary. Its success or failure does not alter `SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIP_IDENTIFIED` for the completed transport instance.

#### Stage B1 — Bind/classify completed transport evidence for downstream use

- **Task:** Classify and bind exact retained transport/runtime receipts for downstream custody/reconstruction and task-state reconciliation.
- **Reusable overlay:** existing non-authorizing receipt classifier; `RT-CANONICAL-STATE-RECONCILIATION-001` where reconciliation is applicable.
- **Authority:** classifier/reconciliation are non-authorizing; they do not prove transport by recreating it. They consume the already-completed transport evidence.
- **Completion predicates:** applicable receipts classified/bound by exact path/hash/correlation/transition lineage; transport terminal predicate preserved as observed at A7.
- **Failure ownership:** evidence classification/reconciliation domain. A B1 failure is not a transport failure.
- **Status:** `CLASSIFIER READY / AUTHENTIC INPUT PENDING`.

#### Stage B2 — Master Records ingress, custody, and reconstruction

- **Task:** Ingest the completed evidence into Master Records custody and reconstruct observed runtime truth/provenance.
- **Reusable overlay:** `RT-CANONICAL-STATE-RECONCILIATION-001` may reconcile projections around the result; no reusable task replaces Master Records.
- **Authority:** Master Records = observed-reality/custody/reconstruction authority.
- **Completion predicates:** required Master Records custody/reconstruction observed for the downstream end-to-end Goal.
- **Failure ownership:** Master Records/post-transport reconstruction. Failure here does not negate A7 transport success.
- **Status:** `PENDING`.

#### Stage B3 — Mirror/reconciliation/persistence/projection actions required by the Goal

- **Task:** Perform only downstream actions selected by current Goal state: mirroring, canonical reconciliation, persistence, projections, applicable TVC/observer continuation, publication, or similar post-transport work.
- **Reusable overlay:** `RT-CANONICAL-STATE-RECONCILIATION-001`; `RT-MIRROR-HANDOFF-VALIDATION-001`; conditional `RT-STEGINDEX-VALIDATION-001`; conditional `RT-README-VALIDATION-001`; any other existing task only if its registered profile matches the actual downstream transition. Do not invent a transport task for downstream processing.
- **Authority:** each downstream authority remains separate (TV/TVC, Master Records, KV/SKAP Vault, publication owner, etc.).
- **Completion predicates:** each selected downstream predicate satisfied independently; none is required to keep A7 transport success true.
- **Failure ownership:** exact downstream domain that failed. Never reclassify as transport failure after A7.
- **Status:** `PENDING / STATE-SELECTED`.

#### Stage B4 — Global runtime evidence measurement where applicable

- **Task:** After required authentic retained evidence exists, enter `GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001`, freeze one run ID, and execute the measurement-only convergence pass exactly once.
- **Reusable overlay:** existing canonical runtime-observation component/child; no new RT required.
- **Authority:** measurement/observation only; no transport authority.
- **Completion predicates:** single frozen measurement run retained and evaluated according to its contract.
- **Failure ownership:** measurement/convergence domain, not transport.
- **Status:** `NOT ENTERED`.

#### Stage B5 — Goal closure / continuation

- **Task:** Reconcile terminal Goal state from A-domain transport proof plus required B-domain downstream predicates; close, retire, or hand off only from authentic evidence.
- **Reusable overlay:** `RT-CANONICAL-STATE-RECONCILIATION-001`, `RT-MIRROR-HANDOFF-VALIDATION-001`, conditional README/StegIndex validation, and `RT-SESSION-CLOSEOUT-001` at session/handoff boundary.
- **Authority:** canonical task coordination only; closure cannot rewrite authority-owned evidence.
- **Completion predicates:** `SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIP_IDENTIFIED=true` where transport is required, plus every independently required post-transport terminal predicate for this Goal.
- **Failure ownership:** Goal/downstream closure domain. Missing downstream closure does not negate transport success.
- **Status:** `PENDING`.

## Failure ownership boundary

```text
BEFORE_OR_AT_FINAL_TRANSPORT_EXIT
  transport/in-lane authority failure may be classified as transport failure

FINAL_ALLOWED_TRANSPORT_EXIT SUCCEEDS
  + governed return record already received and durably recorded
  => SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIP_IDENTIFIED = true
  => transport subproblem CLOSED

AFTER_FINAL_TRANSPORT_EXIT
  Master Records / mirror / reconciliation / persistence / projection /
  measurement / publication / other downstream failure
  => POST_TRANSPORT_FAILURE
  => MUST NOT be classified as transport failure
```

## Conditional Healer remediation branch

Healer is outside both normal domains.

```text
observed remediable failure
-> trigger Healer remediation event for that exact owning domain
-> apply bounded remedy
-> retain remediation evidence
-> return to the interrupted state transition/domain
```

A pending predicate, downstream failure, or transition-variable value does not automatically authorize Healer. Healer never becomes the normal stage owner, scheduler, carrier, prerequisite, transport authority, or reconstruction authority.

## Current exact unresolved predicate

```text
SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIP_IDENTIFIED = false / NOT YET AUTHENTICALLY OBSERVED
```

This replaces the earlier tendency to use Master Records or later downstream completion as proof of transport. The first terminal transport proof now occurs at A7.

## Authority invariants

- Task Registry: coordination only.
- Reusable tasks/components: bounded work/composition only; no independent authority.
- `callable` / `refreshable`: invocation-bound state-transition variables.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: governed transition and packet-movement authority; owns the transport-boundary transitions.
- TV/TVC: credential/provider authority where applicable.
- KV/SKAP Vault: sole user-verification authority.
- Master Records: observed-reality/custody/reconstruction authority after transport; not the authority that proves transport success.
- Healer: triggered bounded remediation only.
- GitHub/CI: source validation/evidence transport only; runtime authority `NONE`.
- External device connector: not applicable.

## Manual work

None.
