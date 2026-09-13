# SDK WorkSpace External-Collaboration Component Model Mirror Handoff

Updated: 2026-09-13
Goal Task ID: `SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004`
Canonical runtime handoff: `docs/SDK_WORKSPACE_EXTCOLLAB_AUTHENTIC_RUNTIME_004_MIRROR_HANDOFF.md`
COSV: `71000000100110`
Reusable Task Component Model merge: `b9f8e5153aa1651f2d7f043fb902eacb7c113ed9` (`StegVerse-Labs/.github#1652`)
Status: `ACTIVE / COMPONENT MODEL MERGED + VALIDATED / GOAL COMPONENT PROFILE RECONCILED / RUNTIME TRUTH UNCHANGED`

## Scope

This handoff is the architecture/composition projection for the active Goal Task. It does not replace the canonical runtime-evidence handoff. Runtime truth, current authentic observations, and remaining Goal Task completion predicates remain owned by `docs/SDK_WORKSPACE_EXTCOLLAB_AUTHENTIC_RUNTIME_004_MIRROR_HANDOFF.md`.

The Goal Task remains `SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004`; no new Goal Task is created by componentization. COSV remains `71000000100110`.

## Canonical component sources

```text
data/reusable-task-component-model.json
data/reusable-task-component-decomposition-policy.json
data/reusable-transport-component-contract.json
data/goal-task-transport-profiles/SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004.json
data/goal-task-component-profiles/SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004.json
scripts/evaluate_reusable_task_componentization.py
docs/REUSABLE_TASK_COMPONENT_MODEL_MIRROR_HANDOFF.md
docs/REUSABLE_GOAL_TASK_TRANSPORT_COMPONENTS_MIRROR_HANDOFF.md
```

## Decomposition result

The current process scores `30` under the canonical decomposition policy because it contains repeated subflows, multiple authority crossings, multiple governed round trips, cross-repository/org orchestration, duplicated generic work risk, a long handoff sequence, branching remediation, independently reusable subprocesses, optional subprocesses, and independently provable evidence stages.

Canonical evaluator disposition:

```text
STOP_SCOPE_GROWTH_AND_DECOMPOSE_BEFORE_ADDING_MORE_TASK_SPECIFIC_ORCHESTRATION
```

That disposition is satisfied by the component profile above. It does **not** stop the Goal Task; it stops additional bespoke orchestration and requires reuse of canonical components/owners.

Reconciliation receipt:

```text
receipts/preflight/SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004-COMPONENT-RECONCILIATION-20260913.json
```

## Goal Task -> reusable components -> owner -> evidence

The task now composes these required/conditional capabilities rather than one monolithic sequence:

1. **Current runtime observation** — reuse `heartbeat_runtime/runtime_presence_projection.py`; HeartBeat is observation/timing/freshness/correlation only; expected evidence is an authentic subject-bound `runtime-presence.latest.json`. Absence alone is not a worker failure.
2. **Runtime compatibility/current-observation resolution** — reuse the canonical runtime-profile resolver; authority effect NONE; expected evidence is deterministic candidate/resolution output with exact rejection reason.
3. **Event-ephemeral execution materialization** — reuse the reusable-task ephemeral construct plus existing resident dispatcher; WorkerCoordinator owns claim/fence; runner expiry is normal lifecycle.
4. **Manifest binding** — reuse `RTC-MANIFEST-001`; non-authorizing validation/binding evidence.
5. **Governed processing** — reuse `RTC-GOVERNED-PROCESSING-002`; Interlock/InTr owns governed transitions and WorkerCoordinator retains execution claim/fence authority.
6. **Resident reseal round trip** — parameterized `RTC-ROUNDTRIP-003`; expected authentic reseal receipt.
7. **Resident consent-listener round trip** — parameterized `RTC-ROUNDTRIP-003`; expected authentic listener/loopback-health receipt.
8. **Evidence custody/reconstruction** — reuse repeatable `RTC-EVIDENCE-CUSTODY-004`; Master Records owns custody/reconstruction of observed reality.
9. **Service Gateway callback proof** — reuse existing `StegVerse-org/LLM-adapter#72` and merged three-route implementation; do not create task-local callback transport.
10. **Owner-present provider consent/session** — conditional after custody + callback reachability; KV/SKAP Vault is the sole user-verification authority and TV/TVC owns credential/provider/session authority. No device-local verifier exists.
11. **Authoritative provider-file probe** — parameterized `RTC-ROUNDTRIP-003` plus existing provider adapter; exactly one authoritative metadata probe in the current proof cycle.
12. **SDK return / complete-predicate re-evaluation** — reuse `RTC-SDK-RETURN-006` plus the existing SDK active-probe path.
13. **MIR reporting** — reuse the existing reporting/evidence path; reporting is non-authorizing.
14. **One-current-device proof assembly** — task-specific evidence aggregation only over reusable component receipts; no new runtime, verifier, or second device.
15. **Downstream/public distribution** — reuse `RTC-PUBLISHER-005` plus canonical Publisher/release paths; TV/TVC retains release/provider authority.
16. **Final egress / InTr transport / far-side transition** — reuse `RTC-STEGVERSE-EGRESS-007`, `RTC-INTERLOCK-INTR-TRANSPORT-008`, and `RTC-FARSIDE-FINAL-009` only for targets that actually require that governed far-side transition. The maximal chain is not mandatory for every target.
17. **Terminal cleanup / entropy recovery** — conditionally reuse `data/reusable-task-ephemeral-construct-contract.json` after required recording and Master Records reconstruction.

The machine-readable interface details, inputs, outputs, preconditions, cardinality, failure semantics, and expected evidence are in `data/goal-task-component-profiles/SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004.json`.

## Authority invariants

- Task Registry: coordination only.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: governed transition/admission authority.
- TV/TVC: credential/provider/release authority.
- KV/SKAP Vault: sole user-verification authority.
- StegOS nodes: interchangeable transport/execution nodes, never user verifiers.
- Master Records: observed-reality custody/reconstruction.
- HeartBeat: synchronization/timing/freshness/liveness/state-correlation/observability only.
- GitHub: source/evidence coordination only; runtime authority NONE.

Runtime subject binding, node identity, transport identity, and Secure Enclave identity are never promoted into user verification.

## Reconciliation of this session's prior work

- **Reusable component implementation/reuse:** #1652 component model and transport family; canonical runtime observation; canonical runtime resolver; event-ephemeral execution materialization; transport round trips; evidence custody; SDK return; Publisher/far-side transport.
- **Goal-specific configuration:** the exact external-collaboration component parameters and ordering in the goal component profile.
- **Goal-specific evidence predicates:** the twelve remaining predicates retained unchanged in the canonical task record/runtime handoff.
- **Runtime observation:** latest canonical observation remains the 2026-09-12 negative observation already recorded by the runtime handoff; no evidence class is upgraded here.
- **Duplicate orchestration:** PR #1578's task-local persistent-carrier/WorkerCoordinator self-heal framing is superseded and was closed unmerged. Worker/WorkerCoordinator absence is not itself failure; actual lifecycle fail conditions follow the existing StegDB -> StegHealth path.
- **Obsolete/superseded implementation:** no historical evidence is deleted; obsolete orchestration is retired only as an active continuation path.
- **Novel reusable capability:** none is required for this reconciliation. Callback/correlation, generalized release/propagation, and generalized failure-remediation remain reusable-component candidates in the model but are not instantiated merely for this task because existing canonical owners already satisfy this Goal Task's immediate needs.

## Source validation from #1652

PR #1652 final exact head `075b1e71d0ebe3591899db03d570da79eed5e916` passed:

```text
Validate organization control plane: 34730323940 PASS
Deterministic Repository Suite: 34730323942 PASS
Heartbeat Worker Project validation: 34730323876 PASS
validate-deepseek-resident: 34730323965 PASS
```

PR #1652 then merged at `b9f8e5153aa1651f2d7f043fb902eacb7c113ed9`.

These are source-validation facts only. They prove neither resident runtime execution nor any Goal Task completion predicate.

## Runtime state and next admissible work

Runtime truth is unchanged by componentization. The next admissible work is to use the **existing runtime observation + canonical runtime-resolution components** to obtain an authentic current eligible resident observation. If a current eligible runtime resolves, continue with the two parameterized resident round trips (reseal and consent listener) under ordinary WorkerCoordinator and Interlock/InTr authority. Do not create a persistent WorkerCoordinator requirement, duplicate presence probe, duplicate resolver, hosted fallback, device-local verifier, or second user-operated device.

## README impact

No new repository function is introduced by this reconciliation. PR #1652 already made and documented the material repository-level model change. This handoff/profile update is a task-specific projection and stale-state correction, so the root README requires no further mutation.

## Human action

None.
