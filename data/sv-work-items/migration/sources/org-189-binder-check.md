# org/.github#189 (40a5d235): which binders accept the supplied-epoch append contract

Read-only check. I pushed nothing, opened no PRs and posted no comments. Everything ran in local scratch worktrees under /tmp/b189. Evidence is in `/workspace/p1/components/build/evidence/org-40a5d235/`.

**The contract under test (40a5d235).**
- `aggregate_repo_transition.append` (L378) raises `OrgLedgerEpochRefused` before it opens the store (L391-393). The exception is a SystemExit subclass, and its `.refusal` carries the six fields: HB_EPOCH_NOT_SUPPLIED or HB_EPOCH_INVALID, predicate SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH, owning goal INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001.
- `observation_window.open_window` (L224) raises `WindowEpochRefused` with the same six fields, from `_reference` (L198-221).
- The epoch rule is `supplied_epoch_failure` (L56-90). An epoch passes only as ASCII `[0-9]+` with an integer **value** of at least 32 (the HB32 anchor). The rule checks the value, not the digit count. An int is read as its decimal text, and a bool, a float or a coerced string (`+33`, ` 33`, `3_3`) is refused.
- Probe `probe-append.txt` confirms all of this. No epoch gives HB_EPOCH_NOT_SUPPLIED with all six fields. `'+33'`, `' 33'`, `'3_3'`, `'31'`, `31`, `True` and `'abc'` all give HB_EPOCH_INVALID.

**The gap #189 leaves.** `append` calls `supplied_epoch_failure(hb_epoch)` without passing a `reference`, so it never looks at the source receipt's `derived_from_clock`.

Several binders write the repository receipt first, through `emit.py`, and `emit.py` on main still falls back to the clock when no epoch is given (emit.py L105). Those binders then pass `repository_receipt["hb_reference"]["epoch"]` to the organization append.

The probe shows the result. The repository receipt is `HB:481438895` with `derived_from_clock: true`. The organization append admits it, and the organization receipt is stamped `derived_from_clock: false`. A clock-derived epoch passes as a supplied one.

## Runs

| Tree | Org suite (68 modules, per module) | C7/C8 against component e6ba9601 / f82c0324 / e29493af |
|---|---|---|
| org 0f9481af (before #189) | 948 tests; 3 modules fail, all environmental (reviewer_prompt 4F, sdk_manifest_crossing_fidelity 8F/5E, task_registry_schema 1E) | earlier baseline: 66 / 71 / 71, 0 failures, 2 findings |
| **org 40a5d235** | 957 tests; the same 3 modules fail with the same counts, so nothing new | **66 / 71 / 71, 0 failures, 2 findings**: C8 `--self-close` and C7 ingress with no `--hb-epoch` on InTr's own writers still exit 0 with ALLOW and append (the clock gap above) |
| 40a5d235 merged into #187 (scratch 41332b45) | 968 tests; nothing new (+11 tests OK) | **66 / 71 / 71, 0 failures, 0 findings** |
| 40a5d235 merged into #191 (bbf9e2d1), #190 (809e9948), #186 (6caec62f), #184 (8536b51d), #181 (106b763b), #192 (a158bd04) | nothing new in any of them | not applicable |
| 40a5d235 merged into #188 | **merge conflict** in resident-runtime/federation_cycle.py (3 hunks). After a scratch resolution (caa5d06f, described below): 962 tests, nothing new (+5 OK) | not applicable |
| Labs component at e6ba9601 / f82c0324 / e29493af | component suite 52 / 72 / 77 OK; manifest ALLOW (10 / 12 / 13 modules) | as above (C7/C8 at 40a5d235) |
| Labs p1/invariant-determination-001 @07cbae92 | 31 tests: 21 OK, 10 skipped (STEGCORE_SOURCE is not set, unrelated to the epoch) | not applicable (it cannot be merged with an org commit) |

`ledger_store.py` is unchanged by #189 (blob 3937db52 before and after). #3225's component `ledger_store.py` and Lane B's org#190 copy are still byte-identical (sha256 6bd217e0…). **Lane B does not need a flag.**

## Per-binder verdicts

| # | Binder (tree) | Always passes a valid supplied epoch? | Refusal handled or propagated? | Verdict |
|---|---|---|---|---|
| 1 | `org-kernel/kernel.py` `record_refusal` L768-779, `record_crossing` L832-843 (main) | **No.** L864 sets `epoch=None` on the `now_ns` path or when the frame has no epoch. emit then derives the epoch from the clock, and the org append (L776/L840) admits it (`probe-kernel.txt`: epoch None is appended with org `derived_from_clock: false`). An epoch below 32 raises `ValueError epoch_precedes_hb32_anchor`, which has no six fields | No | **FAIL_CLOSED** |
| 2 | `resident-runtime/intr_destination_ingress.py` `_append` L419-442 (main) | **No** on direct and CLI calls without `--hb-epoch` (C8 finding) | The CLI passes `.refusal` through (L825-838) | **FAIL_CLOSED** on main; **ALLOW** with #187 |
| 3 | `resident-runtime/organization_manifest_ingress.py` `_record_refusal` L560-584, `receive` L1172-1196 (main) | **No** (C7 finding) | Yes, through `_ledger_write` and `ledger_writer_refusal` | **FAIL_CLOSED** on main; **ALLOW** with #187 |
| 4 | `resident-runtime/organization_egress_boundary.py` `_record` L559-584 (main), `close` (#186) | Yes. `epoch_refusal` is checked first, so the repository receipt carries the supplied epoch | Yes | **ALLOW** |
| 5 | `resident-runtime/propagate_repository_receipts.py` `propagate`/`propagate_all` L185/L211 (main) | Passes the caller's epoch unchanged | Yes, it raises `OrgLedgerEpochRefused` | **ALLOW** |
| 5b | same file, CLI `main()` L232-249 (main; #191 L268-285) | **No.** `type=int` coerces `+33`, and the probe appended at epoch 33. #191 fixes this | **No.** With no epoch it exits 1, prints the code on stderr only and writes no six fields to stdout. This is still true with #191. The help text still says "derived from the host clock" | **FAIL_CLOSED** |
| 6 | `resident-runtime/aggregate_repo_transition.py` CLI `main()` L464/L478 (main) | **No.** `type=int` coerces: `+33`, ` 33` and `3_3` were each appended at epoch 33. No open PR covers this | Yes, six fields are printed (L479-481) | **FAIL_CLOSED** |
| 7 | `resident-runtime/federation_cycle.py` L147-152 (main) | Passes the raw CLI text | Yes, it catches `OrgLedgerEpochRefused` and records six fields | **ALLOW** |
| 8 | `resident-runtime/resident_executor.py` `cycle()` L46-48 (main) | **Never** passes `--hb-epoch`, so every cycle that has receipts to carry ends `repository_propagation` HB_EPOCH_NOT_SUPPLIED | Yes, `failed_transitions` reads it | **FAIL_CLOSED**; repaired by #188 |
| 9 | `observation_window.open_window`: observation-window-validation.yml L102/L153/L170 (main) | Yes: 5000, 6000 and 7000 | not reached | **ALLOW** |
| 10 | organization-repository-propagation-validation.yml L107/L125 (main) | Yes: `hb_epoch=32` | not reached | **ALLOW** |
| 11 | organization-ledger-transition.yml L316-325 (main; #184 rewords it) | The dispatch accepts any digits, then the ingress CLI (`cli_hb_epoch`) refuses a value below 32 with six fields | Yes | **ALLOW** |
| 12 | org#187 @4d04d805 | Yes. `direct_epoch_refusal` runs at `receive` and `closure` | Yes, six fields | **ALLOW** (repairs rows 2 and 3) |
| 13 | org#188 @ad10d55b | Yes once resolved: `cycle_heartbeat` plus executor `--hb-epoch` | **Conflict.** Taking #188's side drops 40a5d235's `except OrgLedgerEpochRefused` (federation_cycle L148-152), and the refusal would then escape the cycle | **FAIL_CLOSED** (needs a merge resolution) |
| 14 | org#191 @efc908ad | Yes, `type=str` and `cli_hb_epoch` (`+33` → HB_EPOCH_INVALID, exit 1) | Absent epoch: still no six fields on stdout (row 5b) | **FAIL_CLOSED** (residual) |
| 15 | org#181 @8a766fbd `intr_hop.py` (calls egress `_record`) | **No.** `require_epoch` L154-157 admits 0-31. The CLI L718/L724/L730 uses `type=int` | Epochs 0-31 raise `ValueError epoch_precedes_hb32_anchor` from `frame_for`/`hb_reference`, with no six fields | **FAIL_CLOSED** |
| 16 | org#190 @d0ccfca5 (byte copy of ledger_store.py), #192 @d760d04f (repository emitter only; its own `epoch_refusal` requires an int of at least 32), #183 @75e577d0 (readback) | no org append or open_window call sites | n/a | **ALLOW** |
| 17 | `submit_org_transition_to_master_records.py`, `receipt_disorder_measurement.py`, `receipt_lineage_projection.py` (main) | these load the module only to read; they never append | n/a | **ALLOW** (not binders) |
| 18 | Labs #3225 @e6ba9601. The component's own `append` (L331-341, `common.supplied_hb_reference`), component `propagate` L192, workflow C7 L287 and C8 L331 (`--hb-epoch "$HB_EPOCH"` every time, flat component writers) | Yes. The component's emit also refuses an absent epoch, so no clock epoch reaches its org append | Yes. `LedgerRefusal.refusal` has the same codes and predicate, and org's `ledger_writer_refusal` prints it as given | **ALLOW** |
| 19 | Labs #3226 @f82c0324: `propagate_after_append.py` L113 (`require_supplied_epoch` first), workflow L308/L376 | Yes | Yes, six fields | **ALLOW** |
| 20 | Labs #3234 @e29493af `readback_only.py` | no append | n/a | **ALLOW** (not a binder) |
| 21 | Labs `p1/invariant-determination-001` @07cbae92: `resident-runtime/governance_endpoint.py` `record` L168-212 | This binds **Labs' own** `resident-runtime/aggregate_repo_transition.py::aggregate_transition` (blob 7660d2bc). That file is not the org file (89be8754) and not the component, so the #189 contract does not reach it. INVARIANT_DETERMINATION refuses a missing epoch (L176-179, CLI L258-268) | Function-level refusal is a plain `SystemExit` string. The CLI prints six fields | **ALLOW** for #189 (not a binder). Separate note: other request kinds with no epoch still use Labs' clock-deriving writer, which is pre-existing P1-FC-4 scope and not caused by #189 |

## Six fields and draft repairs for each FAIL_CLOSED (not applied)

**Row 1: kernel crossing records**
- failure_code: `CLOCK_DERIVED_EPOCH_ADMITTED_BY_ORG_APPEND`
- failed_predicate: `SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH`
- required_evidence_or_repair: org-kernel/kernel.py, immediately before L768 (`record_refusal`) and L832 (`record_crossing`): `refused = organization_ledger.epoch_refusal(epoch)`, and `raise organization_ledger.OrgLedgerEpochRefused(refused)` when it is set. The custody org ledger is the kernel's own `aggregate_repo_transition` (L720). Also resident-runtime/federation_cycle.py L101: add an `except SystemExit` branch for an exception that carries `.refusal` (the kernel's `OrgLedgerEpochRefused`) next to `ValueError`, and record `consumption` as `exc.refusal`. Untested draft.
- retry_entrypoint: `org-kernel/kernel.py::consume_and_respond`
- owning_existing_goal: INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001 (InTr PR-1c follow-up). Tracked on StegVerse-org/.github#163 as P1-FC-8.
- next_attempt: re-run C7/C8 and test_kernel_crossing_organization_receipts with a frame that has no `heartbeat_reference.epoch`. Expected: HB_EPOCH_NOT_SUPPLIED and no ref change.

**Rows 2-3: InTr ingress and manifest ingress**
- failure_code: `CLOCK_DERIVED_EPOCH_ADMITTED_BY_ORG_APPEND`
- failed_predicate: `SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH`
- required_evidence_or_repair: merge org#187 (4d04d805). It merges cleanly with 40a5d235. Scratch suite shows nothing new, and C7/C8 has 0 findings.
- retry_entrypoint: `resident-runtime/intr_destination_ingress.py::receive|closure`, `resident-runtime/organization_manifest_ingress.py::receive`
- owning_existing_goal: INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001 (PR-1b). Tracked on #163 as P1-FC-8.
- next_attempt: C7/C8 against main once #187 is merged; expect 0 findings.

**Row 5b: propagate CLI**
- failure_code: `HB_EPOCH_REFUSAL_NOT_SIX_FIELD_AT_CLI`. Before #191 it is also `HB_EPOCH_CLI_COERCED`.
- failed_predicate: `EVERY_NON_ALLOW_CARRIES_SIX_FIELDS`
- required_evidence_or_repair: merge #191 (coercion). Then, in propagate_repository_receipts.py `main()` (40a5d235 L237-243; #191 L279-285), wrap `propagate`/`propagate_all` in `except organization_ledger.OrgLedgerEpochRefused as exc: print(json.dumps({"schema": RESULT_SCHEMA, **exc.refusal}, sort_keys=True)); return 1`. Fix the help text (L233; #191 L269-270), which says the epoch is "derived from the host clock".
- retry_entrypoint: `resident-runtime/propagate_repository_receipts.py (--hb-epoch)`
- owning_existing_goal: StegVerse-org/.github#163 (P1-FC-10)
- next_attempt: run the CLI with no `--hb-epoch`. Expected: six fields on stdout, exit 1, nothing appended.

**Row 6: aggregate CLI**
- failure_code: `HB_EPOCH_CLI_COERCED`
- failed_predicate: `SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH`
- required_evidence_or_repair: resident-runtime/aggregate_repo_transition.py L464, change `type=int` to `type=str`. `append` already applies the rule to the raw text, and L479-481 already prints six fields. Fix the help text on L465 to match. No open PR covers this; it is a candidate addition to #191.
- retry_entrypoint: `resident-runtime/aggregate_repo_transition.py (--hb-epoch)`
- owning_existing_goal: StegVerse-org/.github#163 (P1-FC-10)
- next_attempt: `--hb-epoch +33` should give HB_EPOCH_INVALID with exit 1.

**Row 8: resident executor**
- failure_code: `HB_EPOCH_NOT_SUPPLIED`. The binder supplies none.
- failed_predicate: `SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH`
- required_evidence_or_repair: org#188's resident_executor.py change: `cycle(mesh_root, node_state_root, hb_epoch)` passes `--hb-epoch` (main L46-48), plus the CLI argument. #188 needs the resolution in row 13 first.
- retry_entrypoint: `resident-runtime/resident_executor.py`
- owning_existing_goal: INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001 (org#188)
- next_attempt: run the executor with `--hb-epoch 4200`. Expected: `repository_propagation` ALLOW.

**Row 13: org#188 conflict**
- failure_code: `MERGE_CONFLICT_WITH_40a5d235`
- failed_predicate: `BINDER_KEEPS_THE_SIX_FIELD_EPOCH_REFUSAL`
- required_evidence_or_repair: resolve resident-runtime/federation_cycle.py on #188's branch. In hunks 1 and 3 (signature, `--hb-epoch type=str`), take #188's side. In hunk 2, take #188's `propagate_all(hb_epoch=heartbeat["epoch"] if heartbeat else None)` **and** keep 40a5d235's `except PR.organization_ledger.OrgLedgerEpochRefused` block (L148-152). Scratch resolution caa5d06f: suite shows nothing new.
- retry_entrypoint: `resident-runtime/federation_cycle.py::main`
- owning_existing_goal: INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001 (org#188)
- next_attempt: the #188 owner merges main into the branch with that resolution, then re-runs test_federation_cycle_supplied_epoch and test_federation_cycle_propagation_location.

**Row 15: org#181 intr_hop**
- failure_code: `HB_EPOCH_RULE_DIVERGES_FROM_SHARED_RULE`
- failed_predicate: `SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH`
- required_evidence_or_repair: resident-runtime/intr_hop.py L154-157. `require_epoch` should apply the shared `supplied_epoch_failure` (the egress boundary copy) and raise `HopRefused` with the HB_EPOCH_INVALID or HB_EPOCH_NOT_SUPPLIED detail. Change L718/L724/L730 from `type=int` to `type=str`.
- retry_entrypoint: `resident-runtime/intr_hop.py phase=send|receive|answer`
- owning_existing_goal: INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001 (org#181)
- next_attempt: `send(..., hb_epoch=5)` should return a six-field FAIL_CLOSED with `receipts_appended: false` instead of raising ValueError.

## Notes
- **Why the repair is per binder and not one change in `append`.** The single-point alternative would pass `reference=source_receipt.get("hb_reference")` into `supplied_epoch_failure` at aggregate L130/L391. That would close the clock gap for every binder at once. It would also refuse legitimate propagation of older repository receipts that are clock-derived, which propagate_repository_receipts re-stamps with a supplied epoch. So it is not proposed as the fix. It belongs on the joint-discovery list: the invariant to decide is whether an org receipt may consume a clock-derived source receipt under a supplied epoch.
- **Component pins.** The Labs component's `component-manifest.json` still pins the org source blob 3ed69e29 (0f9481af) for `aggregate_repo_transition.py`. Org main now has 89be8754. The component already enforces the stricter rule (it also refuses at the repository level), so no binder breaks. Only the derivation pin is stale. The reusable workflow's `intr_interface_ref` default is still 0f9481af; I tested a bump to 40a5d235 with C7/C8 and it passes.
- The Labs PRs cannot have 40a5d235 merged into them (a different repository). They were exercised by running C7/C8 with the 40a5d235 checkout as the InTr interface and each Labs head as the component.
