# Workflow surface reclassification proposal (#3039 H6)

Updated: 2026-10-09
Repository: `StegVerse-Labs/.github`
Registry: `control/workflow-surface-registry.json`
Validator: `scripts/validate_workflow_surface_hygiene.py`
Status: `APPLIED` in #3039 H6b (see "Applied" below); the tables are the original proposal

PR #3042 registered 28 workflow files as `REVIEW_REQUIRED`. This document proposes a target classification for each one. The goal is fewer surfaces and fewer dependencies on external machines and frameworks, without weakening any check. Applying it is a separate change. That change edits the registry and removes or merges workflow files, and it must first confirm that none of the removed files is a branch-protection required check. This session cannot read branch protection.

## Basis

- `test-suite-ratchet.yml` runs the whole `tests/` suite with pytest on every pull request, with no path filter. It fails when a test fails that the baseline does not already list. Every test file named by the pure-test workflows below exists under `tests/` and is absent from `data/test-suite-baseline.json` `known_failing` (checked 2026-10-09). The ratchet therefore already fails any pull request that breaks one of those tests. A dedicated workflow that only re-runs them adds no coverage.
- Validation scripts, inline checks and tests outside `tests/` are not covered by the ratchet. They keep their gate by moving into the existing stable dispatcher `org-control-plane-validate.yml`.
- Under "GitHub Actions: no runtime authority", a workflow must not be an execution path. One that invokes a task is eliminated, not consolidated.
- External dependencies observed: network download of another repository's source archive, `pip install` from PyPI, and anonymous `git fetch` of this or other public repositories.

## Priority 1: external machine, hosted execution or external source dependency

| Workflow | Dependency observed | Proposed | Note |
| --- | --- | --- | --- |
| `canonical-work-exact-ephemeral-invocation.yml` | GitHub-hosted runner used as the **execution** surface (`trigger_reusable_task.py` on push to `invoke/canonical-work-coordination-*`) | `ELIMINATE` | Conflicts with "GitHub Actions: no runtime authority". The invocation belongs to a manifest-bound state transition run by an executor. |
| `validate-purpose-bound-worker-derived-lifetime.yml` | `curl` of the `StegVerse-org/StegVerse-SDK` archive at a pinned SHA, then `pip install` of it | `CONSOLIDATE_INTO_STABLE_DISPATCHER` after removing the fetch | Replace the network fetch with a pinned in-repository source snapshot (the pattern `validate-deepseek-resident.yml` uses for StegIndex), or hand the cross-owner wire test to the SDK owner. Its `tests/` files are already covered by the ratchet. |
| `repository-hygiene-ecosystem-bulk-census.yml` | Anonymous clone of a matrix of other repositories | `CONSOLIDATE_INTO_STABLE_DISPATCHER` (into the existing `repository-hygiene-reusable.yml` exception) | One hygiene surface instead of two. The census is evidence collection, not a gate. |

## Priority 2: pure re-runs of `tests/` already covered by the ratchet

| Workflow | Tests | Proposed |
| --- | --- | --- |
| `aex-stcm-chf-native-capability-audit.yml` | `test_aex_stcm_chf_native_capability_review` | `ELIMINATE` |
| `stcm-chf-witness-registration-validation.yml` | `test_stcm_chf_witness_registration` | `ELIMINATE` |
| `transition-disposition-source-validation.yml` | `test_transition_disposition_invariant` | `ELIMINATE` |
| `validate-immutable-resident-dispatch-receipt.yml` | `test_immutable_resident_dispatch_receipt` | `ELIMINATE` |
| `validate-master-records-source-proof.yml` | `test_bootstrap_v1_source_package_production_worker`, `test_sovereign_worker_source_refresh` | `ELIMINATE` |
| `validate-sdk-review-publisher-intr-forward.yml` | `test_publisher_intr_materialization` | `ELIMINATE` |
| `generic-sdk-manifest-resident.yml` | `test_sdk_generic_manifest_execution_resident` | `ELIMINATE` |
| `organization-control-plane-parity.yml` | `test_organization_control_plane_parity` | `ELIMINATE` |
| `validate-ecosystem-receipt-hb-successor.yml` | `test_receipt_hb_creation_reference` and related | `ELIMINATE` |
| `validate-healer-first-consumption.yml` | `test_healer_resident_request` | `ELIMINATE` |
| `validate-rtc008-carriage.yml` | `test_rtc008_mir_southbound_intr_admission`, `test_sdk_publisher_return_intr_materialization` | `ELIMINATE` |
| `validate-rtc008-custody.yml` | `test_rtc008_mir_southbound_intr_admission` (push only, subset of the above) | `ELIMINATE` |
| `validate-organization-transition-ledger.yml` | `test_organization_transition_ledger`, `test_organization_batch_custody`, `test_org_batch_exact_source_replay` | `ELIMINATE` |

Each of these also runs `pip install pytest` on its own. Eliminating them leaves one pytest install, the ratchet's, instead of 13 or more.

## Priority 3: non-test validation, merged into the stable dispatcher

| Workflow | Uncovered step to keep | Proposed |
| --- | --- | --- |
| `governance-endpoint-validation.yml` | `python org-kernel/tests/test_kernel.py` (outside `tests/`) | `CONSOLIDATE_INTO_STABLE_DISPATCHER` |
| `component010-checkout-audit.yml` | `scripts/audit_component010_checkout.py` | `CONSOLIDATE_INTO_STABLE_DISPATCHER` |
| `task-work-correlation-validation.yml` | `scripts/resolve_task_work_correlation.py --task-id ...` | `CONSOLIDATE_INTO_STABLE_DISPATCHER` |
| `test3-richard-seam-acceptance.yml` | `scripts/run_sdk_tt_richard_seam_test3.py` | `CONSOLIDATE_INTO_STABLE_DISPATCHER` |
| `validate-interlock-intr-protocol-vectors.yml` | `scripts/verify_interlock_intr_runtime_independent_protocol.py` | `CONSOLIDATE_INTO_STABLE_DISPATCHER` |
| `validate-master-records-checkpoint.yml` | `scripts/verify_master_records_checkpoint.py` | `CONSOLIDATE_INTO_STABLE_DISPATCHER` |
| `validate-organization-role-deployment-packet.yml` | `scripts/verify_organization_role_deployment.py --org-root .` | `CONSOLIDATE_INTO_STABLE_DISPATCHER` |
| `validate-organization-role-runtime-reality.yml` | `scripts/validate_task_registry_global_invariants.py` | `CONSOLIDATE_INTO_STABLE_DISPATCHER` |
| `validate-conversation-evidence-ingestion.yml` | inline Python check | `CONSOLIDATE_INTO_STABLE_DISPATCHER` |
| `validate-stegbrowser-intr-retention.yml` | inline Python check over an anonymous fetch of this repository's own ref | `CONSOLIDATE_INTO_STABLE_DISPATCHER` (use the checkout instead of a second fetch) |
| `validate-task-registry-kv-event-projection.yml` | fetch of the PR merge ref plus pinned `pytest==8.3.5` | `CONSOLIDATE_INTO_STABLE_DISPATCHER` (tests already covered by the ratchet; the merge-ref replay step moves) |

## Keep

| Workflow | Proposed | Reason |
| --- | --- | --- |
| `test-suite-ratchet.yml` | `KEEP_STABLE_DISPATCHER` | It is the coverage backstop that makes the Priority 2 eliminations safe. |

## Result if applied

28 `REVIEW_REQUIRED` surfaces become 14 `ELIMINATE` (1 in Priority 1, 13 in Priority 2), 13 `CONSOLIDATE_INTO_STABLE_DISPATCHER` (2 in Priority 1, 11 in Priority 3) and 1 `KEEP_STABLE_DISPATCHER`; at most 1 workflow file (the ratchet) remains of the 28. The repository goes from 42 workflow files toward the registry's `preferred_repository_workflow_count_max`. No check is weakened, because each removed gate is either already enforced by the ratchet or moved into `org-control-plane-validate.yml`.

## Separate observation (report only)

`validate-deepseek-resident.yml` (`KEEP_STANDALONE_EXCEPTION`) runs on a GitHub-hosted `ubuntu-24.04` runner. It does an anonymous `git fetch` of this repository and a `pip install --user pytest`. It does **not** require an external machine or resident host to pass. It validates source records that describe a resident path (`control/resident-execution-request.d/deepseek-intr-runtime-001.json`, `scripts/dispatch_resident_execution_requests.py`), and it asserts `second_machine_required: false` and `another_physical_machine_required: false` from a pinned StegIndex snapshot that needs no network at validation time. Its framework dependency is pytest from PyPI.

## Applied (#3039 H6b)

Applied 2026-10-09. Branch protection was read back before applying: `repos/StegVerse-Labs/.github/branches/main` reports `protected: false`, `required_status_checks.contexts: []`, `enforcement_level: off`; `/rulesets` and `/rules/branches/main` return `[]`; the classic `/protection` endpoint returns 403 to the integration. No workflow job is a required context, and branch protection is unchanged.

Two findings changed the proposal:

- `org-control-plane-validate.yml` and `heartbeat-worker-project.yml` run on `workflow_dispatch` only. Moving a pull-request gate into either would have removed the gate. The non-`tests/` validators therefore moved into a new `consolidated-source-validators` job of `test-suite-ratchet.yml` (now `KEEP_STABLE_DISPATCHER`), which runs on every pull request and, newly, every push to `main`, with no path filter.
- Some workflows proposed for `ELIMINATE` also ran a `py_compile` or a JSON parse. Those steps moved too, so those workflows are recorded as `CONSOLIDATE_INTO_STABLE_DISPATCHER`.

Result: 10 `ELIMINATE`, 16 `CONSOLIDATE_INTO_STABLE_DISPATCHER` (26 files removed), 1 `KEEP_STABLE_DISPATCHER` (`test-suite-ratchet.yml`), 1 `KEEP_STANDALONE_EXCEPTION` (`repository-hygiene-ecosystem-bulk-census.yml`, reduced to its census job because it clones other repositories). The SDK fetch in `validate-purpose-bound-worker-derived-lifetime.yml` is gone: its Experiment 3 wire test runs in `org-runtime-boundary.yml`, which already installs the same pinned SDK. Per-file coverage is recorded in `control/workflow-surface-registry.json` under `retired_in_h6b_3039`, and the hygiene validator fails if a retired file reappears.
