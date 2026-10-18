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

## Record modes and schema fixes SF-1..SF-10 (from Lane D's migration fixtures, laned/s0-lane-d-migration-fixtures @76f06381)
- `record_mode: NATIVE | MIGRATED_HISTORICAL` (both record kinds).
  - **NATIVE:** every field is observed, and the record carries no `unknown_fields`, `migration_provenance` or `migration_flags`.
  - **MIGRATED_HISTORICAL:** `UNKNOWN_NOT_AUTHENTICALLY_OBSERVED` is allowed only at the pointers in the schema's `x-migrated-unknown-allowed`, and every one is listed in `unknown_fields` (`sv_work_items.mode_check`). `/projection` is a non-authority view and is not scanned.
  - A MIGRATED_HISTORICAL record is never admissible. ADMIT, and VERIFY too, returns FAIL_CLOSED `HISTORICAL_RECORD_NOT_ADMISSIBLE` (predicate ADMITTED_RECORDS_ARE_NATIVE) with all six fields. This is enforced in `transition()` before any injected evaluator runs, and again inside `evaluate_admission`.
  - Such a record becomes NATIVE only through `SV_ISSUE_SUPERSEDE` / `SV_CHANGE_SUPERSEDE` with a NATIVE successor whose `supersedes` names the predecessor's digest. Flipping the mode in place fails, because the sentinels and the seal no longer verify.
- **SF-1:** `hb_epoch` may be UNKNOWN only when migrated.
- **SF-2:** `change_id = "svc:" + sha256(canon({target_repository, base_ref, content: [{path, blob_digest, deleted}] sorted by path}))`.
  - Writer evidence is not part of the identity.
  - The helper is `sv_work_items.change_identity`, and the derivation is published in the schema's `x-derivation`.
- **SF-3:** `resolution_class` may be UNKNOWN only when migrated. The builder no longer defaults to B: it uses the class the source table states, or UNKNOWN. This corrects 12 of the 20 P1 migration issues, which had been defaulted to B.
- **SF-4:** `resolves` needs at least one item for NATIVE. A migrated record may have an empty list, and must then carry `migration_flags: [RESOLVES_NOT_RECORDED]`.
- **SF-5:** a validation receipt is `{check_id, disposition, change_digest, evidence_class: LEDGER_RECEIPT | OBSERVED_ARTIFACT, ref, digest}`.
  - Only a LEDGER_RECEIPT with its `ref` under `refs/` counts toward VERIFIED.
  - A check that has only artifact evidence is CHECK_SKIPPED_OR_UNOBSERVED, with `artifact_only` set.
- **SF-6:** `writer_session` is `{session | null, evidence_class: DECLARED | OBSERVED_COMMIT_TRAILER | UNKNOWN_NOT_AUTHENTICALLY_OBSERVED}`.
  - UNKNOWN (with a null session) fails BRANCH_WRITER_IS_BRANCH_OWNER as `BRANCH_WRITER_UNOBSERVED`, at PROPOSE and at admission.
  - Neither DECLARED nor OBSERVED_COMMIT_TRAILER is an authenticated identity, because every session pushes as one account. That stays open as JDQ **Q-WRITER-IDENTITY**:
    - INVARIANT CHECKED: BRANCH_WRITER_IS_BRANCH_OWNER.
    - QUESTION: which receipt authenticates a per-path writer session (a session-signed commit trailer, or a WorkerCoordinator claim receipt per push)?
    - FEEDBACK OUTPUT: a WRITER_SESSION_RECEIPT evidence class.
- **SF-7:** `issue_id = "svi:" + sha256(canon({violated_invariant{repository,file,rule_id}, failed_predicate, surface, source_receipt_ref}))`. It hashes no free text.
  - Reworded restatements merge into one record under `restatements[]`.
  - `surface` is a new required field `{kind, path}`. A migrated record may have UNKNOWN there. Migration derives it from the first repository path in `retry_entrypoint` (`sv_migration.derive_surface`).
- **SF-8:** `owning_goal` (and `disposition.owning_existing_goal`) may be UNKNOWN only when migrated.
- **SF-9:** each canonical coordination task has exactly one work-items record: `{schema, coordination_task_id, goal_index, work_items}`.
  - `goal_index` is the multi-goal index, mapping `owning_goal` to work item ids. Migrated items with an UNKNOWN goal are indexed under that key on the same record.
  - The helper is `sv_work_items.work_items_record`, and the schema states this in `x-carrier`.
- **SF-10:** `migration_provenance {original_base_observed, original_base_ref | null, migrated_at_base}` is required when migrated.
  - `original_base_ref` is null exactly when `original_base_observed` is false.
  - `migrated_at_base` must equal `observed_base` / `base_ref`.
- **Tooling:**
  - `resident-runtime/schema_subset.py` is a stdlib JSON-schema subset validator. It refuses any keyword it does not implement.
  - `resident-runtime/sv_migration.py` holds the published lift rules.
  - `scripts/evaluate_migration_fixtures.py --fixtures DIR` lifts a fixture set written against 1673cb5f and reports each listed gap as CLEARED or REMAINS.

## change_id canonical serialization (Lane C amendment)
- **Pinned serialization.** It is set in `sv-change.v1#/properties/change_id/x-canonical-serialization` and in `sv_work_items.CANONICAL_SERIALIZATION` / `canon()`: JSON with sort_keys, separators `(',', ':')`, UTF-8, ensure_ascii false, and no trailing newline.
- **Hashed form** (`change_identity_input`): `{target_repository, base_ref, content}`.
  - `base_ref` is hashed as recorded and must keep both `registry_generation` and `ledger_head`. If either is missing, the result is DENY SV_CHANGE_BASE_UNBOUND.
  - `content` is `[{path, blob_digest, deleted}]` sorted by path. `deleted` counts only when it is boolean true, and a deleted entry hashes `blob_digest: null`.
- **change_id** = `"svc:" + lowercase hex sha256(serialized bytes)`.
- **Known-answer vector** (`tests/test_sv_record_modes.py::test_change_id_known_answer`):
  - Input: target `StegVerse-Labs/.github`; base `{registry_generation 319, ledger_head a5bb54d81893b392a3ce28182986fc39857807e1}`; content `schemas/é.json` with digest `sha256:b…b` (64×b), plus `docs/old.md` deleted.
  - Serialized form: 342 bytes, starting `{"base_ref":{"ledger_head":"a5bb54d8…","registry_generation":319},"content":[{"blob_digest":null,"deleted":true,"path":"docs/old.md"},…`
  - change_id: `svc:b1f56ebe998a4a0896e8f3f18ef76abe65f6f6bd0c613fa04e50291025300239`
- **OBSERVED_ARTIFACT** counts as UNKNOWN for VERIFIED. A check with only artifact evidence is FAIL_CLOSED CHECK_SKIPPED_OR_UNOBSERVED. It is never a pass, and it never hides a ledger refusal.

## head.change_digest and deleted entries
- **head.change_digest** = `"sha256:" + sha256` over the same canonical bytes as `change_id` (`sv_work_items.change_digest(record)`). So `head.change_digest[7:] == change_id[4:]`, and the digest now moves with `target_repository` and `base_ref` as well as content. For the known-answer vector it is `sha256:b1f56ebe998a4a0896e8f3f18ef76abe65f6f6bd0c613fa04e50291025300239`.
  - A record whose head digest differs from this is FAIL_CLOSED SV_CHANGE_DIGEST_MISMATCH.
  - Every `validation_receipts[].change_digest` must equal `head.change_digest`. Otherwise admission is FAIL_CLOSED VALIDATION_NOT_AT_EXACT_HEAD.
  - The earlier form (sha over sorted `{path, blob_digest}`) is kept only as `sv_migration.legacy_change_digest`. When lifting, a receipt is re-expressed in the new form only if the source head digest was the legacy digest of the same content and the receipt bound that value. Every other receipt digest is left as observed.
- **Deleted entries:** the schema and `validate_change` require `blob_digest: null` when `deleted` is true, and a sha256 `blob_digest` otherwise. Any other combination is DENY SV_CHANGE_CONTENT_ENTRY_INVALID. This is the same null that the hashed form already used.

## RF-1..RF-3 (Lane D @1b53fb05)
- **RF-1:** `owning_goal` (stripped) is now part of `issue_id`, so one predicate under two goals stays two issues and both goals appear in `goal_index`. **Known limit:** records whose `owning_goal` is UNKNOWN_NOT_AUTHENTICALLY_OBSERVED all share that one value, so they can still collide.
- **RF-2:** `data/sv-work-items/surface-aliases.json` (stegverse.sv-surface-aliases/v1) is pinned by git blob in `sv_migration.SURFACE_ALIASES_BLOB`. `load_aliases` refuses any other blob with FAIL_CLOSED SURFACE_ALIAS_TABLE_UNPINNED.
  - It holds three kinds of entry: lane aliases from the Lane D §16 legend (CONS, TRCI, TCP, GI, WBF and ORRD, plus `Site data/session-work-claims.d`), bare names (the Class-column rule) and patch entrypoints (matched by diff preimage index or by the patch's own `_comment`/`_note` target).
  - Each entry is verified against Labs 978b8880, Site 379dba2a or org 40a5d235, and records the object sha.
  - These are left UNKNOWN: SPPA (no declared path), "that script" (an anaphora), and `patches/D14-*.json-patch.json` (the glob matches two targets).
  - Resolution order: patch entrypoint, then repository path, then lane alias, then bare name, otherwise UNKNOWN.
- **RF-3:** box-local paths are surface kind `NON_REPOSITORY_EVIDENCE`. That covers `patches/`, `/workspace/`, `/tmp/`, `/home/`, any absolute path, and any path outside every supplied repository tree (`--repo-paths`).
  - Such a path is kept for identity but is allowed only in MIGRATED_HISTORICAL records.
  - A NATIVE issue with this kind is denied (DENY SURFACE_NOT_IN_REPOSITORY_TREE), and so is a box-local path disguised under a repository kind.
