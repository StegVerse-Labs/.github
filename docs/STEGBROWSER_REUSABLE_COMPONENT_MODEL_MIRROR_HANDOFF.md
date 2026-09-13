# StegBrowser Reusable Task Component Model Reconciliation

Updated: 2026-09-12

## Canonical identity

- Goal Task ID: `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`
- COSV vector: `40000100100000`
- Canonical Task Registry record: `data/canonical-task-records/STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json`
- Runtime truth handoff: `docs/STEGBROWSER_EPHEMERAL_RUNTIME_BINDING_MIRROR_HANDOFF.md`
- Reusable model: `data/reusable-task-component-model.json`
- Decomposition policy: `data/reusable-task-component-decomposition-policy.json`
- Transport profile: `data/goal-task-transport-profiles/STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json`

The existing Goal Task remains valid. Componentization does not create a replacement Goal Task, does not change COSV continuity, and does not alter the Goal Task's completion predicates.

## Decomposition disposition

The current process exceeds the `13+` decomposition threshold. Active signals are repeated subprocesses, multiple authority crossings, multiple governed round trips, cross-repository spread, long independently evidenced handoff stages, branching remediation, independently reusable subflows, optional subflows, and independently provable evidence stages.

Disposition:

`STOP_SCOPE_GROWTH_AND_DECOMPOSE_BEFORE_ADDING_MORE_TASK_SPECIFIC_ORCHESTRATION`

This stops additional bespoke orchestration only. It does not stop the Goal Task.

## Goal Task component map

### RTC-MANIFEST-001 — Manifest Intake and Binding

- Status: existing reusable component; required.
- Canonical owner: Reusable Task Component transport family; Task Registry remains coordination-only.
- Inputs: Goal Task ID, COSV, exact resident selector `stegbrowser_tvc_source_promotion`, pinned TVC SHA, declared evidence requirements.
- Outputs: task/COSV-bound invocation inputs and required evidence declaration.
- Preconditions: canonical task registration and valid component profile.
- Authority owner: none; component is non-authorizing.
- Evidence: manifest/task/COSV/selector binding and exact input commitments.
- Cardinality: once per invocation composition.
- Failure semantics: fail closed on incomplete/mismatched binding; repair manifest/profile without minting authority.

### RTC-GOVERNED-PROCESSING-002 — Governed Processing

- Status: existing reusable component; required.
- Canonical implementation/owner: existing Canonical Work + resident dispatch processing; execution authority remains outside the component.
- Inputs: admitted task-bound work and exact selector.
- Outputs: bounded processing result and downstream candidate state.
- Preconditions: applicable WorkerCoordinator claim/fence and Interlock/InTr admission when the transition requires them.
- Authority owner: WorkerCoordinator for claim/fence; Interlock/InTr for governed transition.
- Evidence: canonical-work consumption, resident-dispatch result, dedicated StegBrowser source-promotion receipt.
- Cardinality: repeat where distinct governed processing stages require it.
- Failure semantics: incomplete evidence remains incomplete; no synthetic success.

### RTC-ROUNDTRIP-003 — Governed Round Trip

- Status: existing reusable component; required and repeatable.
- Required instances for this Goal:
  1. resident TVC source-promotion/materialization/rebind cycle;
  2. Apple SKAP credential/provider-operation cycle;
  3. Facebook publication/readback cycle;
  4. LinkedIn publication/readback cycle.
- Inputs/outputs: stage-specific request, correlation, response/readback, and receipt-chain extension.
- Preconditions: stage-specific admission and credential/session availability.
- Authority owner: Interlock/InTr for governed transitions; TV/TVC for credential/provider operations.
- Evidence: independent request/response/readback receipts per instance.
- Failure semantics: one failed round trip does not authorize or fabricate another; retry/reentry is stage-specific.

### RTC-INTERLOCK-INTR-TRANSPORT-008 — Interlock/InTr Transport

- Status: existing reusable component; required and repeatable.
- Canonical owner: Interlock/InTr.
- Inputs: task-bound transition candidate and exact transport payload.
- Outputs: admitted/rejected transition plus transport receipt.
- Preconditions: valid transition request and applicable authority state.
- Authority owner: Interlock/InTr.
- Evidence: admission/transition receipts bound to exact task/operation.
- Failure semantics: DENY/absence remains a real boundary; transport presence itself grants no authority.

### Ephemeral execution materialization / terminal cleanup

- Status: existing reusable contract; required.
- Canonical contract: `data/reusable-task-ephemeral-construct-contract.json`.
- Existing implementation owners: StegBrowser/StegOS retained node + ephemeral browser lease, Canonical Work resident surfaces, current-iPhone signing executor where applicable.
- Inputs: invocation-specific parameters and admitted work.
- Outputs: bounded runner/session, chained receipts, runner expiry, residual recording when required.
- Preconditions: applicable admission before runner materialization.
- Authority owner: WorkerCoordinator and Interlock/InTr remain external authorities; the reusable construct mints none.
- Evidence: runner/session materialization, bounded execution, expiry/destruction, residual recording when needed.
- Failure semantics: stop at real authority/evidence/external-resource/human boundary; no duplicate scheduler/runtime plane.

### Credential/session handling

- Status: existing canonical owner; required conditionally for Apple and external social-provider operations.
- Canonical owner: TV/TVC; user-verification state originates only from KV/SKAP Vault.
- Inputs: operation scope, provider identity, exact credential reference, KV/SKAP-backed user-verification state when applicable.
- Outputs: bounded credential/session issuance or provider-operation eligibility.
- Preconditions: TV/TVC policy plus applicable Interlock/InTr admission.
- Evidence: SKAP custody/session receipt, provider-operation receipt, zero credential export.
- Failure semantics: missing credential/session is a real boundary; never fall back to GitHub secrets or device-local verification.

### RTC-PUBLISHER-005 — Publisher Projection

- Status: existing reusable component; required for the social-publication portion only.
- Canonical implementation owners: StegSocials + StegBrowser provider-specific publication entrypoints; TV/TVC retains provider/release authority where applicable.
- Inputs: approved publication payload and bounded provider session.
- Outputs: external platform object identity, canonical URL, visibility/readback evidence.
- Preconditions: working admitted runtime and provider session.
- Evidence: authentic Facebook/LinkedIn object creation plus readback.
- Cardinality: once per selected provider publication; providers are independent branches.
- Failure semantics: one provider may remain incomplete without fabricating the other.

### RTC-EVIDENCE-CUSTODY-004 — Evidence Custody and Reconstruction

- Status: existing reusable component; required.
- Canonical owner: Master Records.
- Inputs: authentic component receipts and final provider/readback evidence.
- Outputs: custody, readback, reconstruction confirmation.
- Preconditions: authentic evidence exists.
- Evidence: Master Records custody/reconstruction receipts.
- Failure semantics: source/CI cannot substitute for custody; no entropy recovery before required reconstruction.

### RTC-STEGVERSE-EGRESS-007 / RTC-FARSIDE-FINAL-009

- Status: existing reusable components; required only where this Goal crosses from StegVerse state into Apple/social-provider state and requires an externally observable final transition.
- Canonical authority: Interlock/InTr governs the StegVerse-side transition; provider/far-side state remains externally observed and TV/TVC governs credential/provider release.
- Evidence: final local egress transition receipt plus provider-side object/state/readback receipt.
- Failure semantics: local egress does not prove provider success; provider success does not retroactively authorize local transition.

### RTC-SDK-RETURN-006

- Status: existing reusable component; not applicable.
- Reason: this Goal Task does not return a result through the SDK.

## Session-work classification

Work already completed in this session is reconciled as follows:

- Canonical StegBrowser/StegOS substrate selection and Remote Computer semantics: reusable/global Task Registry invariant and Goal-specific configuration; not new runtime authority.
- PR #1634 substrate correction: Goal-specific Task Registry/handoff reconciliation using the global substrate model.
- PR #1644 global enforcement: reusable Task Registry process/invariant applied to existing and future runtime-capable tasks.
- `stegbrowser_tvc_source_promotion` exact dispatch path and dedicated receipt binding: existing governed-processing/evidence-validation implementation; do not extend with another task-specific dispatcher.
- TVC source materialization/restart path: existing execution-materialization/provider-runtime implementation; reuse it.
- Apple SKAP and App Store Connect path: existing TV/TVC credential/session/provider implementation; reuse it.
- Facebook/LinkedIn publication callers: existing Publisher/provider-specific implementations; reuse them.
- publication custody/readback: existing Master Records custody/reconstruction responsibility; reuse it.
- Remote Computer discovery: runtime observation only; not a reusable execution authority, task predicate, or second-machine dependency.

No historical evidence is deleted. No completed source work is upgraded to authentic runtime evidence.

## Duplicate orchestration disposition

Do not add another task-specific scheduler, resident dispatcher, TVC promotion bridge, credential resolver, provider session manager, publication transport, custody writer, or Remote Computer execution class for this Goal.

The historical ordered handoff remains useful as runtime truth, but architecture is now represented as component composition. Any future generic adapter/transport/correlation implementation must first be reconciled against these reusable owners.

No currently merged task-specific implementation is deleted in this reconciliation because the existing implementations are the canonical execution owners consumed by the reusable component composition; they are reclassified as component implementations rather than duplicated.

## Remaining Goal-specific predicates

Component reuse does not satisfy these predicates. Authentic evidence is still required for:

- resident source revision at execution;
- Canonical Work/resident consumption and exact `stegbrowser_tvc_source_promotion` dispatch;
- dedicated current-dispatch-bound TVC consumption receipt;
- pinned TVC materialization and same-primary-runtime restart;
- simultaneous `8765/8775` observation;
- Apple `OWNER_INGRESS_READY`;
- real KV/SKAP-backed Apple credential custody/session;
- current-iPhone cryptographic signing;
- TVC Build Upload and TestFlight installation;
- current-iPhone resident discovery;
- Interlock/InTr admission receipts;
- WorkerCoordinator claim/fence evidence where execution requires it;
- authentic Facebook publication and readback;
- authentic LinkedIn publication and readback;
- terminal browser/provider-session destruction;
- Master Records custody/reconstruction.

## Runtime truth

No authentic runtime predicate advances through this componentization. Source construction and CI validation remain source/process evidence only. The runtime truth remains in `docs/STEGBROWSER_EPHEMERAL_RUNTIME_BINDING_MIRROR_HANDOFF.md`.

## Next admissible work

After this component projection is merged and validated, continue the same Goal Task at its first missing authentic evidence boundary. Use existing Canonical Work/resident processing and `stegbrowser_tvc_source_promotion`; do not add new orchestration. Once authentic execution reaches later stages, invoke only the reusable components required for that stage and preserve independent evidence boundaries.

Manual work: none.
