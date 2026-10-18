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
  - Every `validation_receipts[].change_digest` must equal `head.change_digest`. Otherwise admission is FAIL_CLOSED CHECK_SKIPPED_OR_UNOBSERVED with failed check RECEIPT_CHANGE_DIGEST_EQUALS_HEAD (TVC#519 code; the predicate keeps it distinct from a skipped check).
  - The earlier form (sha over sorted `{path, blob_digest}`) is kept only as `sv_migration.legacy_change_digest`. When lifting, a receipt is re-expressed in the new form only if the source head digest was the legacy digest of the same content and the receipt bound that value. Every other receipt digest is left as observed.
- **Deleted entries:** the schema and `validate_change` require `blob_digest: null` when `deleted` is true, and a sha256 `blob_digest` otherwise. Any other combination is DENY SV_CHANGE_CONTENT_ENTRY_INVALID. This is the same null that the hashed form already used.

## RF-1..RF-3 (Lane D @1b53fb05)
- **RF-1:** `owning_goal` (stripped) is now part of `issue_id`, so one predicate under two goals stays two issues and both goals appear in `goal_index`. Records whose `owning_goal` is UNKNOWN_NOT_AUTHENTICALLY_OBSERVED are separated by `source_receipt.evidence_locator` (FB-3 below).
- **RF-2:** `data/sv-work-items/surface-aliases.json` (stegverse.sv-surface-aliases/v1) is pinned by git blob in `sv_migration.SURFACE_ALIASES_BLOB`. `load_aliases` refuses any other blob with FAIL_CLOSED SURFACE_ALIAS_TABLE_UNPINNED.
  - It holds three kinds of entry: lane aliases from the Lane D §16 legend (CONS, TRCI, TCP, GI, WBF and ORRD, plus `Site data/session-work-claims.d`), bare names (the Class-column rule) and patch entrypoints (matched by diff preimage index or by the patch's own `_comment`/`_note` target).
  - Each entry is verified against Labs 978b8880, Site 379dba2a or org 40a5d235, and records the object sha.
  - Left UNKNOWN: `patches/D14-*.json-patch.json` (the glob matches two targets). SPPA and "that script" were resolved by FB-1 below.
  - Resolution order: patch entrypoint, then repository path, then lane alias, then bare name, otherwise UNKNOWN.
- **RF-3:** box-local paths are surface kind `NON_REPOSITORY_EVIDENCE`. That covers `patches/`, `/workspace/`, `/tmp/`, `/home/`, any absolute path, and any path outside every supplied repository tree (`--repo-paths`).
  - Such a path is kept for identity but is allowed only in MIGRATED_HISTORICAL records.
  - A NATIVE issue with this kind is denied (DENY SURFACE_NOT_IN_REPOSITORY_TREE), and so is a box-local path disguised under a repository kind.

## FB-1..FB-3 (Lane D #3265 @d1a00300)
- **FB-1:** two aliases added to `surface-aliases.json` (re-pinned in `sv_migration.SURFACE_ALIASES_BLOB`), each with its lane-file line and an object verified at Labs 978b8880:
  - `SPPA` -> `scripts/authorize_site_production_promotion.py` (§18.3 Location, L766-776; blob 0538784f).
  - `that script` -> `scripts/project_worker_claim_into_canonical_task.py` (§16 row L586 names exactly one script; blob 9573c5bb).
  - `#3235 verify workflow` and `allocator workflow` exist only at PR heads (#3235 @50525699, #3241 @e5ba67b2). They are `unresolved_declarations`: path stays UNKNOWN, `resolve_surface` returns UNKNOWN, and `sv_migration.alias_disposition` returns their recorded six-field FAIL_CLOSED SURFACE_ALIAS_TARGET_NOT_ON_BASE, never ALLOW. Shape: `schemas/sv-surface-aliases.v1.schema.json` (new, minimal).
- **FB-2:** `sv_migration.derive_surface_with_class_column(retry_entrypoint, class_cell, repo_paths)` replaces the fallback in Lane D's builder. It runs only when the entrypoint resolves to UNKNOWN and returns `(surface, ["SURFACE_DERIVED_FROM_CLASS_COLUMN"])`; the record carries `migration_flags` (sv-issue.v1, MIGRATED_HISTORICAL only; not part of issue_id), so the surface is marked derived, never observed. Builders pass the cells only.
- **FB-3:** `issue_id` inputs already include `source_receipt_ref`, but for migration evidence that is `migration:<file>@<sha>`: one value for every entry of one lane file. With `violated_invariant.file` at section granularity, the same `failed_predicate`, an UNKNOWN surface and an UNKNOWN goal, two different entries hash identically. Fix (least invasive): only when `owning_goal` is UNKNOWN, `source_receipt.evidence_locator` (the entry's position, e.g. `L1204`) is required (FAIL_CLOSED SV_ISSUE_UNKNOWN_GOAL_UNLOCATED) and hashed as `source_locator`. Known-goal identity bytes are unchanged. `validate_issue_set` refuses any set that repeats an issue_id (FAIL_CLOSED SV_ISSUE_ID_COLLISION), and `merge_issues` never merges two different UNKNOWN-goal bodies.

## TVC#519 alignment (Lane C, TVC head 0f3ce27f)
- **sv-change.v1 tightened:** `content[]` items require `deleted`, and items and `head` set `additionalProperties: false`. `touched_paths` is unique and equals the set of `content[].path`. Migration fills `deleted` from the history when recorded, else `deleted = (blob_digest is null)` (the "null exactly when deleted" rule read backwards). No change_id and no head digest moved.
- **Failure codes:** SIGNOFF_ABSENT -> SIGNOFF_RECEIPT_ABSENT. VALIDATION_NOT_AT_EXACT_HEAD -> CHECK_SKIPPED_OR_UNOBSERVED with failed check RECEIPT_CHANGE_DIGEST_EQUALS_HEAD. The scenario class is now `ASC-RECEIPT_CHANGE_DIGEST_EQUALS_HEAD@transition`. Because two predicates share one code, a candidate carrying only that code is not generalized (PREDICATE_BINDING_UNDECLARED); it must name its predicate.
- **Scenario replay:** `data/admission-scenarios/tvc-replay/sv-changes.jsonl` holds the full known-good NATIVE SV_CHANGE per surface kind, valid under the tightened schema and `validate_change`. `replay-map.jsonl` maps every corpus scenario to `{sv_change_id, current_base, mutation{axis, applies_to SV_CHANGE|REPLAY_INPUT, pointer, operation}, expected disposition/code}`. `admission_inputs(change, current_base)` reproduces each positive control's `observed_inputs` exactly.

## REQUIRED_CHECK_RECEIPTS_ARE_S1_VERIFIER_OUTPUTS_APPENDED_BY_ORG_WRITER
Recorded in `data/sv-work-items/required-checks.json#check_receipt_invariant`:
1. Lane B's NWI-S1 verifier (SV-LLM/.github#46) runs each declared check offline at the exact head and emits a six-field, head-bound receipt with a supplied hb_epoch (`schemas/sv-check-receipt.v1.schema.json`, validator `sv_work_items.validate_check_receipt`).
2. That receipt becomes a LEDGER_RECEIPT only through the org-ledger writer transition (Labs#3255, the writer-only workflow) under the shared lock.
3. The check ids in row SV-CHANGE-REQUIRED-CHECKS-001 are exactly the ids the verifier emits; no other minter exists. Each `checks` entry has `minter: NWI-S1-verifier (SV-LLM/.github#46)` and `appender: org-ledger-writer (Labs#3255)`. A receipt for any other id is FAIL_CLOSED CHECK_ID_UNDECLARED (validate_change, evaluate_admission, validate_check_receipt).
- Until the verifier's receipts are appended, the real row fails closed (`row_status`, `sv_work_items.row_receipt_status`): CHECK_RECEIPT_ABSENT_FROM_LEDGER / REQUIRED_CHECK_HAS_LEDGER_RECEIPT / NWI-S1 verifier emits the check id at the exact head and the org writer appends it / the merge-admission evaluation / StegVerse-org/.github#163 / after Labs#3255 and SV-LLM#46 land and JD-P4-3 settles the epoch.
- No check id is mapped to a CI job, and no new transition is proposed.

## Lane C replay round 2 (TVC#519 head 28699422, 27/30 matched on d2ba0957)
1. **Pinned row blob.** `required_checks_ref.blob_sha` is the git blob of `data/sv-work-items/required-checks.json` as committed (`build_sv_native_fixtures.REQUIRED_CHECKS_BLOB`, computed from the file bytes). request_digest was recomputed for every tvc-replay record. `validate_change` refuses any non-40-hex value as FAIL_CLOSED REQUIRED_CHECKS_ROW_NOT_PINNED (REQUIRED_CHECKS_ROW_RESOLVES), and the schema enforces the same rule. The builder `pin_violations` guard runs in both build and `--check`, and FAILS CLOSED before anything is written if any output contains `WORKTREE` or a non-hex blob. UNKNOWN is accepted only in MIGRATED_HISTORICAL. The migrated changes had recorded `WORKTREE`, which is not an observed blob, so they now carry UNKNOWN_NOT_AUTHENTICALLY_OBSERVED at the new migrated-unknown pointer `/required_checks_ref/blob_sha`. No change_id moved.
2. **Replay rebinding.** Each `replay-map.jsonl` mutation now carries a concrete `value` and `rebind_request_digest`. The flag is true for every SV_CHANGE mutation except the one targeting `/request_digest`, and false for REPLAY_INPUT. `build_sv_native_fixtures.apply_replay_mutation` is the reference apply. `tests/test_sv_lane_c_replay.py` applies every mapping, rebinds the digest, rebuilds `admission_inputs`, and asserts the expected disposition and code for each scenario. Without the rebind, the writer_sessions scenario would hit REQUEST_DIGEST_MISMATCH.
3. **Fixture sign-off receipts.** These follow TVC's seed convention. `tvc-replay/signoff-receipts.jsonl` holds sealed `stegverse.sv-change-signoff-receipt/v0.1` receipts (`schemas/sv-change-signoff-receipt.v0.1.schema.json`), one per required role per known-good change. Each has `fixture_only: true` and `unobserved_fields: [session, disposition]`, because no owner signed anything. `signoffs[].receipt_ref` is the receipt's `receipt_sha256`. `signoff_resolves` counts a sign-off only if a sealed ALLOW receipt matches its role, session and change_digest. `fixture_only` receipts, and validation refs containing `#fixture:`, count only when `fixture_mode` is set (corpus, tests, replay). The real admission path defaults to `fixture_mode=False`, so fixture receipts are never counted as LEDGER_RECEIPT outside fixtures.
   - The MERGE_READY wording was not renamed. `MERGE_READY_REQUIRES_EVERY_JOB_RAN_AND_PASSED` is a predicate id embedded in class and scenario ids, so renaming it would move ids. It is left as is.
4. **Check disposition split.** A DENY receipt yields DENY REQUIRED_CHECK_DENIED (CHECK_PASSES). A FAIL_CLOSED receipt yields FAIL_CLOSED CHECK_SKIPPED_OR_UNOBSERVED (CHECK_RECEIPT_DISPOSITION_IS_ALLOW), and FAIL_CLOSED is checked before DENY. The old code was removed from the code, the corpus, the classes and the bindings.
5. **Validation receipt -> ledger receipt binding.**
   - `ref` = `refs/stegverse/organization-ledger@<commit 40-hex>:receipts/<receipt_sha256 hex>.json`. This is the receipt key from `resident-runtime/ledger_store.receipt_key`, the store behind `resident-runtime/organization_ledger_readback.py`. `org-kernel/organization-ledger/readback.py` does not exist in Labs.
   - `digest` = `'sha256:'` + hex sha256 of canon(receipt object), using the same canonical JSON pin as change_id.
   - `sv_work_items.verify_ledger_receipt_binding(receipt, ledger_objects)` is pure. It works over the bytes a read of the ledger ref returned, keyed `"<commit>:<path>"`, and performs no fetch.
   - A digest mismatch is FAIL_CLOSED LEDGER_RECEIPT_DIGEST_MISMATCH (VALIDATION_RECEIPT_DIGEST_BINDS_LEDGER_RECEIPT).
   - FAIL_CLOSED LEDGER_RECEIPT_UNRESOLVED (VALIDATION_RECEIPT_REF_RESOLVES_ON_ORGANIZATION_LEDGER) covers any of these: an unparsable ref, an absent object, non-JSON bytes, or a stored receipt whose `receipt_sha256` differs from the one its path names.
   - Both refusals carry the six fields with owning goal StegVerse-org/.github#163.

## Harvested: WRITER_EVIDENCE_LOST_BY_SNAPSHOT_RESTORE (org#192 @f108ed0a)
- The case: a box snapshot restore at about 13:55Z on 2026-10-18 erased the local reflog entry for P4's push of f108ed0a to StegVerse-org/.github#192 (13:54:46Z). The commit was re-fetched by sha and its tree verified (tree 32a4e47a, parent af556c9d; touches `resident-runtime/admission_predicate.py` and `tests/test_admission_predicate.py`). No reflog was reconstructed.
- How it entered the corpus: through SCENARIO_CORPUS_APPEND (`build_sv_native_fixtures.harvest_append`: harvest, then generalize, then generate, then corpus_append), not by hand edit.
- Class rule (failed predicate BRANCH_WRITER_IS_BRANCH_OWNER + surface kind transition) maps the case onto the existing `ASC-BRANCH_WRITER_IS_BRANCH_OWNER@transition`. The class therefore goes to v2 (it supersedes v1) and records the case name in `provenance.class_aliases` and `admission_learning.CLASS_ALIASES`. No duplicate class was created.
- New axis: v2 adds `content[*].writer_session.evidence_class`, with per-axis `expected_failure_code` BRANCH_WRITER_UNOBSERVED. The axis comes from the declared secondary binding `admission_learning.SECONDARY_AXES[(BRANCH_WRITER_IS_BRANCH_OWNER, BRANCH_WRITER_UNOBSERVED)]`.
- Coverage gate: for a superseding version, the coverage gate counts the class's existing corpus lines together with the appended ones, and re-evaluates every one of them.
- Expected outcome: FAIL_CLOSED BRANCH_WRITER_UNOBSERVED. It is never ALLOW, and the range base never overrides it.
- Negative controls (`tests/test_sv_lane_c_replay.py`): a tree-verified commit with the range base exactly current still fails closed, whether the writer session is null or filled from the commit author. A forged writer list does not override it either.
- Six fields: the repair is a durable push-time writer receipt (sv-push-receipt, being built by Lane C), with owning goal StegVerse-org/.github#163.
- Source: `source_receipt_ref`/`harvest_receipt_ref` is `orchestrator:2026-10-18T14:31Z:org#192@f108ed0a`. It is flagged in `unobserved_fields` because no ledger receipt is held for it. The push and restore times and the writer are flagged too.

## Check commands live in the row (Lane B NWI-S1, SV-LLM/.github#46 @f8f72487)
- Each check in `required-checks.json#checks` declares `offline_command` (argv, run from the repo root at the exact head, no network), `expected` and `command_paths`.
- A head never declares its own pass criteria. It binds them through `required_checks_ref.blob_sha`.
- `{base_commit}` (registry-generation-fence) is the only argument binding. The verifier supplies it from the local clone and never infers it. None of the commands needs an epoch argument.
- supplied-epoch-binder-check: nothing in this repo performs it, so it is UNKNOWN and FAIL_CLOSED CHECK_COMMAND_UNDECLARED (six fields in `command_status`). validate_check_receipt refuses a receipt for it. (Superseded in round 5: it is now a declared verifier built-in.)
- A command_path absent at the head is FAIL_CLOSED CHECK_COMMAND_ABSENT_AT_HEAD. This is the state of #3225 and #3226 for schema-validate, unit-tests and mutation-negative-suite.
- Both rules are implemented as pure functions: `sv_work_items.check_command` and `check_outcome_matches`.

## Round 3 (no change to sv-change.v1 734968c0 or sv-issue.v1 62ee5307)
- **CHECK_COMMAND_UNDECLARED receipts.** For a declared check id whose row command is UNKNOWN (supplied-epoch-binder-check until round 5; the rule stays generic):
  - `validate_check_receipt` accepts the verifier's explicit FAIL_CLOSED CHECK_COMMAND_UNDECLARED receipt (six fields).
  - It refuses an ALLOW, a DENY, or any other FAIL_CLOSED code for that check, with FAIL_CLOSED CHECK_COMMAND_UNDECLARED.
  - Admission fails closed CHECK_COMMAND_UNDECLARED (CHECK_HAS_OFFLINE_COMMAND), not CHECK_SKIPPED_OR_UNOBSERVED.
  - An id outside the row stays CHECK_ID_UNDECLARED.
  - The registry-generation-fence base is **not** recorded: sv-check-receipt.v1 is `additionalProperties: false`, so a `base_commit` field is refused. Recording it needs a receipt-schema change, which was not made.
- **NATIVE_RECORD_HB_EPOCH_IS_BASE_LEDGER_HEAD_EPOCH** (provisional until JD-P4-3 in round 3; decided in round 5 as the native-record application of ADMISSION_HB_EPOCH_IS_THE_BOUND_LEDGER_HEAD_EPOCH; `data/sv-work-items/invariants.json`):
  - What it checks: a NATIVE record's hb_epoch must equal the hb_epoch of the org-ledger receipt at its base ledger head. The value is read from supplied ledger bytes (`<ledger_head>:HEAD.json` then `<ledger_head>:receipts/<hex>.json`, sealed), never from a clock.
  - Where it runs: `verify_native_hb_epoch`. `validate_change(rec, ledger_objects)` and `validate_issue(rec, ledger_objects)` apply it only when bytes are supplied. Without them, behavior is unchanged.
  - If the source is unobserved: FAIL_CLOSED HB_EPOCH_SOURCE_UNOBSERVED.
  - On a mismatch: DENY HB_EPOCH_MISMATCH (renamed in round 5).
- **CHECK_DERIVED_ISSUES_ARE_DERIVED_FROM_THE_LEDGERED_FAILING_RECEIPT** (`invariants.json`, `required-checks.json#check_derived_issue_rule`):
  - `derive_issue_from_check_receipt(receipt_bytes, ledger_ref, row, observed_base=...)` derives a NATIVE SV_ISSUE from the sealed org-ledger receipt at `ledger_ref`. That receipt's `evidence` is the check receipt.
  - Derived fields:
    - source_receipt: the ledger ref and the receipt_sha256.
    - failed_predicate: the receipt's failed check.
    - surface: `check_command_surface` (argv[1], the unittest module file, or the row file when the command is undeclared).
    - owning_goal: the row's `owning_goal` (#163).
    - violated_invariant: `SV-CHANGE-REQUIRED-CHECKS-001#checks.<check_id>`.
    - resolution_class: B by rule.
    - opened_by_session: the derivation itself.
  - Derivation is idempotent, and the id does not depend on who runs it.
  - If the receipt is not yet ledgered: FAIL_CLOSED SOURCE_RECEIPT_NOT_LEDGERED.

## Round 4: ledger readers follow the real org-ledger layout (Lane D, Labs#3255 @75fc4ddd; runtime files unchanged from main)
- **Org receipt.** `stegverse.organization-transition-receipt/v1` (`resident-runtime/aggregate_repo_transition.py:1073-1089`) is sealed: `receipt_sha256` = sha256 of the canonical body without it.
  - It is stored at `receipts/<hex>.json` (`ledger_store.receipt_key`, `ledger_store.py:49-56`), and `HEAD.json` points to it (`:1092`).
  - It has no `evidence` and no top-level hb_epoch.
  - It carries `boundary_evidence {operation, profile_id, disposition, communication_id}`, the `verify_source` fields including `repo_receipt_sha256` (`:627-651`), and `hb_reference` (`org-kernel/kernel.py:68-74`).
- **Repo receipt.** The org ledger retains the source repo receipt (`stegverse.repo-transition-receipt/v1`, sealed, carrying `$.evidence`: `.stegverse/transition-ledger/emit.py:116-117`) beside the org receipt at `source-receipts/<hex>.json` (`ledger_store.source_key`, `:1064-1066`; `organization_ledger_readback.py:89-91`).
- **NATIVE_RECORD_HB_EPOCH_IS_BASE_LEDGER_HEAD_EPOCH.** `base_ledger_head_epoch` reads HEAD.json, then the sealed org receipt, then `$.hb_reference.epoch`.
  - The epoch must be an int >= 32: not bool, and no coercion from other types. A reference marked `derived_from_clock` is not accepted.
  - It is compared with the record's ASCII-digit hb_epoch by integer value.
  - A missing value or a broken seal gives FAIL_CLOSED HB_EPOCH_SOURCE_UNOBSERVED. A mismatch gives DENY HB_EPOCH_MISMATCH (renamed in round 5).
- **CHECK_DERIVED_ISSUES_ARE_DERIVED_FROM_THE_LEDGERED_FAILING_RECEIPT.** `derive_issue_from_check_receipt(ledger_objects, ledger_ref, row, observed_base=...)` follows: org receipt at the ref (sealed), then `repo_receipt_sha256`, then the repo receipt at `source-receipts/<hex>.json` (sealed), then `$.evidence`.
  - The evidence must self-identify: `$.evidence.schema == stegverse.sv_check_receipt.v1`, or `$.evidence.kind == 'sv_check_receipt'` with the rest being the pinned receipt shape.
  - `boundary_evidence.operation`, when present, must be `sv_check_receipt` (Lane D's append operation).
  - A missing or unsealed org or repo receipt gives FAIL_CLOSED SOURCE_RECEIPT_NOT_LEDGERED. Anything else in the evidence gives FAIL_CLOSED LEDGER_EVIDENCE_NOT_A_CHECK_RECEIPT.
- **verify_ledger_receipt_binding.** The addressing stays `receipts/<hex>.json`. It now also verifies the seal: a receipt that does not hash to its own receipt_sha256 is LEDGER_RECEIPT_UNRESOLVED.
- **Fixtures.** `tests/sv_ledger_fixtures.py` builds receipts in the real layout.
  - It uses the real `aggregate_repo_transition.verify_source`, `kernel.hb_reference(epoch=...)` and the `ledger_store` keys.
  - The append bodies are mirrored line for line (emit.py:116-117; aggregate_repo_transition.py:1073-1089), because the append functions need a store and stamp `observed_at` from the host clock. The fixture uses a constant instead.
  - The round-3 fixtures (top-level hb_epoch, `evidence` on the org receipt) were removed.

## Round 5: ADMISSION_HB_EPOCH_IS_THE_BOUND_LEDGER_HEAD_EPOCH (JD-P4-3, part-decided by invariant, orchestrator 15:09Z)
- **Invariant (decided, partial).** For admission, hb_epoch is observed state: the epoch on the org-ledger head receipt the SV_CHANGE base is bound to (`$.hb_reference.epoch`), read and sealed by Lane C's base-state readback (Labs#3266, `stegverse.sv-change-base-state-readback/v1`: `hb_epoch` slot plus `hb_epoch_source`, sealed by `result_sha256`). The shared supplied-epoch rule (726248a5) still applies to the read value.
  - NATIVE_RECORD_HB_EPOCH_IS_BASE_LEDGER_HEAD_EPOCH is its native-record application and is no longer provisional. The two invariants cross-reference each other in `invariants.json`.
  - Still escalated, and not touched here: minting an epoch for a new ledger append.
- **726248a5.** This is the sha256 of the source segment of `org-kernel/kernel.py::supplied_epoch_failure` (lines 236-269; file blob ffec5d648d7fa4aead1f44f76df936a2da21bb96 at fc19b532). It is not a git object.
  - Full value: 726248a585904b52cfe2eec1754e7ce582f67d6b501bd664bb7bee80bce9b7ef.
  - The same pin is used by SV-LLM/.github#46 (`SHARED_RULE_SHA256`) and Labs#3266 (`SUPPLIED_EPOCH_RULE_SHA256`).
  - `sv_work_items.KERNEL_RULE_SHA256` is recomputed at import. If it differs from the pin, the epoch is unobserved.
- **Predicate.** `sv_work_items.verify_admission_hb_epoch(supplied, readback, ledger_head)` is the in-repo reference of the supplied-epoch-binder-check.
  - **FAIL_CLOSED HB_EPOCH_SOURCE_UNOBSERVED** in any of these cases:
    - no readback, or a readback of another schema;
    - a broken seal;
    - a readback that is not ALLOW (for example, Lane C's refusal for a clock-derived or non-int head epoch);
    - a fixture_only readback outside fixture_mode;
    - a readback bound to another ledger head;
    - no `hb_epoch_source` naming `$.hb_reference.epoch` at that head;
    - a slot that fails 726248a5 (a float or bool, below 32, coerced, or with `derived_from_clock` not exactly false).
  - **DENY HB_EPOCH_MISMATCH** when the SV_CHANGE's hb_epoch is not ASCII digits equal by integer value to the sealed epoch.
    - Nothing the orchestrator or any orchestration file says sets a disposition for HB_EPOCH_MISMATCH, so DENY is kept.
    - Open alignment item: Lane C's uncommitted #3266 worktree refuses its own expected-epoch mismatch as FAIL_CLOSED.
  - `evaluate_admission` applies the predicate where the row requires the binder check (ledger_writer), after the check receipts and before the sign-offs.
  - `admission_inputs` gains `supplied_hb_epoch` and `hb_epoch_readback`. The `transition()` VERIFY and ADMIT steps pass `context["hb_epoch_readback"]`.
- **Code rename.** HB_EPOCH_NOT_BASE_LEDGER_EPOCH is replaced by HB_EPOCH_MISMATCH everywhere in this repo, including the native-record check.
- **Row: verifier built-in.** `supplied-epoch-binder-check` now declares `offline_command {verifier_builtin, verifier_ref: SV-LLM/.github#46, predicate}`, `expected {disposition: ALLOW}`, `command_paths []`, and `predicate_pins.726248a5`.
  - `check_command_rule.verifier_builtin` documents the form.
  - CHECK_COMMAND_ABSENT_AT_HEAD does not apply to built-ins: `check_command` returns ALLOW with `argv` null.
  - A malformed built-in is CHECK_COMMAND_UNDECLARED.
  - The check's command surface is the row file.
  - Its `command_status` (CHECK_COMMAND_UNDECLARED) is removed. The undeclared-receipt rule stays generic, and the tests simulate a future UNKNOWN entry.
- **Corpus.** One new class is added through SCENARIO_CORPUS_APPEND (`build_sv_native_fixtures.epoch_binding_append`, after the harvest): `ASC-ADMISSION_HB_EPOCH_IS_THE_BOUND_LEDGER_HEAD_EPOCH@ledger_writer` v1, by the class rule (predicate plus surface kind). No existing class carries the predicate. It generates:
  - a positive control (the supplied epoch equals the sealed readback epoch): ALLOW;
  - four FAIL_CLOSED HB_EPOCH_SOURCE_UNOBSERVED negatives: no readback, an unsealed readback, `derived_from_clock` true on the epoch source, and a non-int (float) slot;
  - the `supplied_hb_epoch` axis: DENY HB_EPOCH_MISMATCH. An axis may now carry its own code, with its disposition taken from `admission_learning.disposition_of`.
  - The earlier classes are byte-identical.
  - The positive controls carry a fixture readback (`fixture_base_state_readback`: fixture_only, with unobserved fields listed).
  - Replay-map rows carry `hb_epoch_readback`. The readback axes are REPLAY_INPUT; `supplied_hb_epoch` is SV_CHANGE `/hb_epoch` (not part of the request digest).

## Round 5b: the admission epoch binding applies to every admission (decision 15:23Z)
- `supplied-epoch-binder-check` moves to `surface_kinds.all` in the row (removed from `ledger_writer`, where it is now implied), so every SV_CHANGE requires it and carries hb_epoch.
- `evaluate_admission` runs `verify_admission_hb_epoch` for every admission (after the check receipts, before the sign-offs); the ledger_writer gate is gone.
- Corpus and replay regenerated through the existing paths (`build_sv_native_fixtures.py`, SCENARIO_CORPUS_APPEND): every positive control carries the sealed fixture readback (`fixture_only`, `unobserved_fields` as for the fixture sign-offs). Scenario ids unchanged (the 32 earlier ids plus the 6 of round 5); `classes.jsonl` is byte-identical.
- The class stays `ASC-ADMISSION_HB_EPOCH_IS_THE_BOUND_LEDGER_HEAD_EPOCH@ledger_writer`: the class rule keys on (failed predicate, surface kind) of the first observation (org#189 epoch binder gaps, ledger_writer), and `all` is not a surface kind (`sv_work_items.SURFACE_KINDS`). A harvested outcome on another surface would derive a sibling class.
- HB_EPOCH_MISMATCH stays DENY: a sealed epoch that contradicts the record is an observed contradiction, not an unobservation.

## Round 6: the supplied-epoch ruling, and #3264's own SV_CHANGE record
- **Ruling, now the standard** (orchestrator; both verifiers agree on 60 cases): a supplied epoch (the SV_CHANGE's hb_epoch) that fails 726248a5 is DENY HB_EPOCH_MISMATCH. FAIL_CLOSED HB_EPOCH_SOURCE_UNOBSERVED is only for the sealed-source side.
  - `verify_admission_hb_epoch` checks the sealed source first. It then applies `kernel.supplied_epoch_failure` to the supplied value explicitly (the failure is carried in `supplied_epoch_rule`) and compares by integer value.
  - Examples: 'abc', '+33', '31' and '0031' are DENY. '01024' against a sealed 1024 is ALLOW, because 726248a5 accepts leading zeros. An int is DENY because it is not ASCII text.
  - This matches SV-LLM/.github#46 `s1_supplied_epoch_binder.binder_check` @64b90721. The ruling is recorded in invariants.json (`supplied_epoch_ruling`).
- **#3264's own SV_CHANGE record.** No such record is committed in this repository, and none is embedded in the PR body.
  - The record #46 checked is Lane B's verifier-derived `SV-LLM/.github:sandbox/s1-sv-changes/StegVerse-Labs-3264-9338e3e7.json`. Its base_ref is `{git_merge_base_with_main}`, with no ledger_head.
  - A record cannot be committed inside the head it describes: `projection.head_sha` and the content digests would have to include the record itself. So P1 derives it outside the tree, from the local clone, for each pushed head.
  - The derivation:
    - content = `git diff --no-renames <base>..<head>` (blob_digest = sha256 of the head bytes; deleted -> null), every writer_session DECLARED as the author session;
    - base_ref {registry_generation read at the base commit, ledger_head = the observed `refs/stegverse/organization-ledger` of the target repository};
    - hb_epoch = `$.hb_reference.epoch` of the sealed org receipt at that head (HEAD.json -> receipts/<hex>.json, seal verified);
    - required_checks_ref = the row blob at the head.
  - The record goes to the PR body (projection) and to Lane B.

