# NWI-S0 native work items and G5 stage gate (P1, StegVerse-org/.github#163)

Author session: P1 Ecosystem AI Lane (d8cbc58c). Invariants: WORK_ITEMS_ARE_TASK_REGISTRY_NATIVE, STAGE_GATES_ARE_ADMITTED_TRANSITIONS, ADMISSION_SCENARIOS_LEARN_FROM_OBSERVED_OUTCOMES. Local draft; nothing here is applied, and no registry generation moves.

## Home and reuse
- SV_ISSUE and SV_CHANGE are record kinds inside STEGVERSE-CANONICAL-WORK-COORDINATION-001 (`docs/CANONICAL_WORK_COORDINATION_SYSTEM_MIRROR_HANDOFF.md`). They are not a new repository or a parallel pipeline. Each lifecycle state maps to a `coordination_state` (`data/sv-work-items/lifecycle-transitions.json#canonical_coordination_state`).
- CLAIMED projects a WorkerCoordinator claim and fence through `scripts/project_worker_claim_into_canonical_task.py::worker_projection` (blob 9573c5bb). It is not a second claim path.
- Receipts come from the existing `.stegverse/transition-ledger/emit.py::append` (f2de8a1a), called with the supplied epoch. The organization ledger aggregates them. Stage outcomes go out as `stegverse.organization-transition-request/v1` bodies for `.stegverse/transition-requests/`.
- The epoch rule is `org-kernel/kernel.py::supplied_epoch_failure` (Labs ffec5d64 L236). It is byte-identical to the copy in org `resident-runtime/aggregate_repo_transition.py` (89be8754).
- Schema owner: repo-standards `schemas/task-registry.schema.json` (65a4a7ca), bundled with org#150. `schemas/canonical-task-work-items.v1.schema.json` is the proposed `work_items[]` field. It merges Claude's #160 6249905378 proposal, keyed by native id, with GitHub numbers as projection fields and no owner-approval flag.

## Files
- `schemas/sv-issue.v1`, `sv-change.v1` (Lane C consumer schema + B1-B7), `canonical-task-work-items.v1`, `admission-corpus.v1` (A1-A7).
- `resident-runtime/sv_work_items.py`: validators, `admission_inputs` and the native predicate, which Lane C's reference implementation can replace by injection. Also lifecycle `transition`/`record`, `claim_projection` and `work_items_projection`.
- `resident-runtime/admission_learning.py`: harvest, generalize, generate, SCENARIO_CORPUS_APPEND, ADMISSION_MISS, and the derived miss counts.
- `resident-runtime/stage_gate.py` plus `data/sv-work-items/stages/NWI-S0..S4.json`: G5. There is no skipping, an observed failure drops back one stage, and thresholds are read only from the manifests. The S2 and S3 values are null and fail closed as STAGE_THRESHOLD_UNDECLARED.
- `data/sv-work-items/required-checks.json`, row SV-CHANGE-REQUIRED-CHECKS-001 (B7). It is the native successor of ST019-MERGE-ADMISSION-001 `required_status_checks`, which is GitHub-bound.
- Migration fixtures:
  - `data/sv-work-items/migration/sv-issues.jsonl`: 20 issues, derived from the P1 FAIL_CLOSED register and the org#189 binder check. The sources are copied under `sources/`.
  - `sv-changes.jsonl`: Labs#3225, #3226 and #3234, plus the local org epoch-binder repair dd8bfd02.
- Seed corpus: `data/admission-scenarios/classes.jsonl` (10 classes) and `corpus.jsonl` (26 scenarios). Each class was appended through SCENARIO_CORPUS_APPEND. `scripts/build_sv_native_fixtures.py --check` re-derives all of it.

## Q-SCENARIO-GENERALIZATION (answered from invariants, class D)
- **G1.** Class identity is the pair (failed_predicate, surface kind). The six-field schema makes failed_predicate the stable check, while failure_code and the source PR are members of the class. Labs#3245 and SDK#533 are therefore one class.
- **G2.** Mutation axes are the observed-input fields the failed predicate reads, with one mutation-negative per axis (TVC#527 pattern). An undeclared predicate fails closed with PREDICATE_BINDING_UNDECLARED.
- **G3.** Each class has a positive control, the known-good fixture for its surface. A class that never fires, or that refuses known-good input, is DENIED.
- **S1.** Surface kinds are workflow, transition, schema, ledger_writer, registry and doc. Workflow paths are the ones `control/workflow-surface-registry.json` requires to be registered. Coverage is required for every kind except doc.
- **Residual (class C, JDQ).**
  - INVARIANT CHECKED: six-field schema; workflow-surface registry 976b3684.
  - QUESTION: is surface kind the right granularity, or should a class be scoped to path globs within a kind?
  - FEEDBACK OUTPUT: a `surfaces[].glob` rule in admission-corpus.v1.

## Q-SV-NATIVE-BOOTSTRAP (partly decided)
- **Decided (D):**
  - Genesis is a FROM_HEAD append on the existing organization ledger, not GENESIS. `aggregate_repo_transition.append` DENYs ORG_LEDGER_GENESIS_ON_NON_EMPTY_LEDGER.
  - The writer is the organization's own ledger writer under ORGANIZATION_LEDGER_LOCK, triggered by a committed `.stegverse/transition-requests/` file. TVC TRANSITION_LEDGER_MIRROR_HANDOFF d50a6255: "No lane does it." Ledger dispatch is never grantable.
  - The registry moves by exactly gen+1 under the session_mutation_generation_fence.
- **Undecided (C):**
  - INVARIANT CHECKED: org-contract `write_mode: MANIFEST_DIRECTED_APPEND`; org `organization-ledger-transition.yml` (triggered by a push to main of `.stegverse/transition-requests/**`); NG.
  - QUESTION: the genesis request and these record kinds must reach main before the native path exists. Is that last landing a projection-era admission (TVC#519) by declaration, and which receipt marks it as the end of the GitHub-authority era?
  - FEEDBACK OUTPUT: a BOOTSTRAP_SELF_ADMISSION invariant plus the NWI genesis request file.
