# Reusable Task Component Model Mirror Handoff

Updated: 2026-09-12
Repository: `StegVerse-Labs/.github`
Consuming Goal Task: `SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004`
COSV: `71000000100110`
Status: `ACTIVE / MERGED + VALIDATED / CONSUMER RECONCILIATION IN PROGRESS`

## Canonical source

The Reusable Task Component Model is canonical on `main` through PR #1652 at merge commit `b9f8e5153aa1651f2d7f043fb902eacb7c113ed9`.

Canonical sources:

- `data/reusable-task-component-model.json`
- `data/reusable-task-component-decomposition-policy.json`
- `scripts/evaluate_reusable_task_componentization.py`
- `data/reusable-transport-component-contract.json`
- `data/reusable-task-ephemeral-construct-contract.json`

PR #1652 exact head `075b1e71d0ebe3591899db03d570da79eed5e916` passed all required exact-head lanes:

- Organization Control `34730323940` PASS
- Deterministic Repository Suite `34730323942` PASS
- Heartbeat Worker Project `34730323876` PASS

These validate source/process architecture only; they do not prove runtime execution or downstream state changes.

## Composition rule

A Goal Task keeps its identity and declares only required capabilities. Composition reuses canonical components, allows repeatable components, preserves authority boundaries, and does not force optional components into unrelated tasks. Missing required components fail closed. Component reuse never mints authority.

## Decomposition rule

Evaluate componentization at task creation, scope change, new repositories/authorities/providers/round trips/runtime paths/remediation branches, handoff updates, before prompt 10, and before release-ready classification. Scores 13+ stop further task-specific orchestration growth until the flow is expressed through reusable components.

## Authority invariants

- Task Registry: coordination only.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: governed transition/admission authority.
- TV/TVC: credential/provider/release authority.
- KV/SKAP Vault: sole user-verification authority.
- StegOS devices: interchangeable transport/execution nodes, not user verifiers.
- Master Records: observed reality, custody, reconstruction.
- HeartBeat: timing, freshness, liveness, correlation, observability only.
- GitHub: source/evidence coordination only.

Runtime subject, node, transport, Secure Enclave, or device identity never becomes user-verification authority.

## Consumer reconciliation

`SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004` remains the active Goal Task and retains COSV `71000000100110`. Its runtime handoff remains runtime truth. The task must reuse the merged transport family and existing runtime-observation, execution-materialization, credential/session, evidence-validation, and Master Records custody/reconstruction owners before adding any task-specific machinery.

The long handoff-only execution chain is no longer the primary architecture representation. It is replaced conceptually by selected reusable components plus task-specific completion predicates. Historical evidence is preserved.

## Runtime boundary

Componentization does not change the current runtime evidence class. Source/CI/merge/static compatibility remain insufficient to prove resident execution, admission, claim/fence, provider action, callback, custody, reconstruction, publication, far-side transition, cleanup, or end-to-end completion.

## Human action

None.
