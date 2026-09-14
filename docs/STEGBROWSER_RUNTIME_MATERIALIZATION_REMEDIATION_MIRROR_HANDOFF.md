# StegBrowser Runtime Materialization Remediation Mirror Handoff

Updated: 2026-09-14

## Task pointer

- Goal Task ID: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- Parent/remediates: `STEG-BROWSER-RESIDENT-CUSTODY-ROOT-OBSERVATION-001`
- Shared runtime-evidence owner: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
- Issue: `StegVerse-Labs/.github#1866`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / REUSABLE-TASK-CENTERED STRUCTURE RECONCILED / AUTHENTIC RT-STEGBROWSER EXECUTION PENDING`
- External/second user-operated device required: `false`

## Healer semantic correction

Healer is **not** the normal carrier, scheduler, recruiter, execution owner, or prerequisite for reusable-task execution.

Healer is a **triggered remediation event**. It applies a bounded remedy only when an observed failure/broken condition satisfies the applicable remediation trigger. After the remedy, control returns to the canonical execution stage that was interrupted. Healer does not establish completion, authority, task state, or normal progression by itself.

Historical Healer work (#81/#82/#83) remains valid as historical bounded repairs to previously observed defects. Those repairs do not make Healer part of the normal execution chain for this Goal.

## Goal Stage Tracker

Use this as the shared progress tracker. A stage advances only from authentic evidence appropriate to that stage. Source/CI state does not prove runtime execution.

- **Stage 1 — Recruit the reusable StegBrowser runtime task**
  - **Task:** Recruit `RT-STEGBROWSER-RUNTIME-CONSUMPTION-001` as the normal reusable work unit for Goal/COSV `40000100100000` through the existing reusable-task mechanism.
  - **Status:** `REGISTERED / AUTHENTIC EXECUTION NOT YET OBSERVED`. The reusable task exists and its runner is bound; no authentic execution receipt is currently established.

- **Stage 2 — Materialize an admitted StegOS execution**
  - **Task:** Materialize the reusable task on an eligible admitted StegOS execution substrate through the existing `SovereignLocalEventRuntimeAdapter` / reusable-task architecture. No named device or external connector is a prerequisite.
  - **Status:** `SOURCE PATH READY / AUTHENTIC EXECUTION PENDING`.

- **Stage 3 — Canonical Work ingress**
  - **Task:** Stage only the runtime-local `PROPOSED` projection required by the reusable runner and enter the existing Canonical Work ingress path.
  - **Status:** `PENDING AUTHENTIC RUNTIME EVIDENCE`. Required evidence includes authentic Canonical Work consumption and governed ingress state.

- **Stage 4 — WorkerCoordinator claim/fence**
  - **Task:** Allow the existing WorkerCoordinator to claim the exact task/COSV-bound work and produce the current authentic claim/fence lineage.
  - **Status:** `PENDING`. `CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED=false`.

- **Stage 5 — Interlock/InTr admission**
  - **Task:** Pass the manifested execution through the existing Interlock/InTr transition path and observe authentic governed admission.
  - **Status:** `PENDING`. `INTR_ADMISSION_OBSERVED=false`.

- **Stage 6 — Execute the StegBrowser runtime-consumption runner**
  - **Task:** Execute `scripts/run_stegbrowser_runtime_consumption_reusable.py` under the admitted reusable-task invocation and observe authentic runtime consumption.
  - **Status:** `PENDING / CURRENT FIRST RUNTIME EXECUTION BOUNDARY`. `runtime_consumption_observed=false`.

- **Stage 7 — Retain exact runtime evidence**
  - **Task:** Retain authentic execution receipts byte-for-byte in the existing resident/evidence custody surface with exact SHA-256 and task/COSV lineage.
  - **Status:** `PENDING AUTHENTIC INPUT`. The retention implementation exists, but authentic retained execution evidence is not yet established.

- **Stage 8 — TVC/runtime continuation where required**
  - **Task:** Invoke the existing StegBrowser TVC source-promotion/runtime continuation only after the required authentic predecessor evidence exists, preserving TV/TVC credential/provider authority.
  - **Status:** `PENDING`.

- **Stage 9 — Immutable observer and owner-ingress evidence**
  - **Task:** Execute the existing immutable observer/readiness path and observe the required `OWNER_INGRESS_READY_OBSERVED` and related runtime evidence where applicable.
  - **Status:** `PENDING`.

- **Stage 10 — Classify and bind retained receipts**
  - **Task:** Run the merged non-authorizing exact receipt verifier/classifier against the authentic retained runtime root and bind every `VALID_BINDABLE` receipt by path, SHA-256, outcome, task/COSV, claim/fence, and transition lineage.
  - **Status:** `VERIFIER MERGED / AUTHENTIC INPUT PENDING`. `.github#1852` is merged and validated.

- **Stage 11 — Master Records reconstruction**
  - **Task:** Reconstruct the exact subject-bound runtime chain through Master Records and preserve observed-reality/provenance authority there.
  - **Status:** `PENDING`. `master_records_reconstruction_observed=false`.

- **Stage 12 — Global runtime evidence measurement**
  - **Task:** Only after authentic retained runtime evidence exists, enter `GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001`, freeze one run ID, and execute the measurement-only convergence pass exactly once.
  - **Status:** `PENDING / NOT ENTERED`.

- **Stage 13 — Goal closure**
  - **Task:** Verify all canonical completion predicates, propagate only applicable evidence to shared-owner lanes, and retire the Goal only from terminal authentic evidence.
  - **Status:** `PENDING`. `completion.claimed=false`; `completion.validated=false`.

## Conditional Healer remediation branch

Healer is outside the normal stage sequence.

If any stage produces an **observed broken condition** that has an authorized bounded remedy:

```text
observed failure/broken condition
-> trigger Healer remediation event
-> apply bounded remedy
-> retain remediation evidence
-> return to the interrupted canonical stage
-> continue/retry only as allowed by that stage
```

No Healer event should be triggered merely because a normal runtime predicate is pending. A pending predicate is not automatically a defect requiring Healer.

## Normal execution/evidence model

```text
RT-STEGBROWSER-RUNTIME-CONSUMPTION-001 recruited
-> reusable-task trigger / neutral scheduler
-> admitted StegOS execution
-> Canonical Work
-> WorkerCoordinator claim/fence
-> Interlock/InTr admission
-> StegBrowser reusable runner
-> retained runtime evidence
-> TVC / immutable observer where applicable
-> exact receipt classifier
-> Master Records reconstruction
-> global measurement
-> Goal closure
```

Healer is intentionally absent from this normal chain.

## Current exact defect

```text
AUTHENTIC_RT_STEGBROWSER_RUNTIME_CONSUMPTION_EXECUTION_NOT_YET_OBSERVED
```

The first question is whether the registered reusable task has been authentically recruited/executed through the canonical runtime path. Do not substitute Healer receipts, source state, CI, connector reachability, or physical-device identity for that execution evidence.

## Authority invariants

- Task Registry: coordination only.
- Reusable task: bounded orchestration/work unit; no independent authority.
- KV/SKAP Vault: sole user-verification authority.
- StegOS devices: interchangeable execution/transport nodes.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: governed transition authority.
- TV/TVC: credential/provider authority where applicable.
- Master Records: observed-reality/reconstruction authority.
- Healer: triggered bounded remediation event only; not normal execution carrier/prerequisite/authority.
- GitHub/CI: source validation/evidence transport only; runtime authority `NONE`.
- External connectors: `NONE_NOT_APPLICABLE` for this Goal.

## Current state

`ACTIVE / CHECKED_OUT / REUSABLE_TASK_REGISTERED / AUTHENTIC_REUSABLE_TASK_EXECUTION_NOT_OBSERVED / CANONICAL_WORK_RUNTIME_CONSUMPTION_NOT_OBSERVED / WORKERCOORDINATOR_CLAIM_FENCE_NOT_OBSERVED / INTR_ADMISSION_NOT_OBSERVED / RECEIPT_CLASSIFIER_MERGED / MASTER_RECORDS_RECONSTRUCTION_NOT_OBSERVED / HEALER_TRIGGERED_REMEDIATION_ONLY / EXTERNAL_CONNECTOR_NOT_APPLICABLE / PHYSICAL_DEVICE_IDENTITY_GATE_PROHIBITED`

## Manual work

None.
