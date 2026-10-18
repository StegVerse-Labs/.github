# Organization ledger component

This is the reusable form of StegVerse-org/.github@10d141041fd0fa3b8bd696f6c6236bef199845b8's organization-ledger path (StegVerse-org/.github#163). It is registered as the organization-ledger profiles of **RTC-EVIDENCE-CUSTODY-004** (`data/reusable-task-components/RTC-EVIDENCE-CUSTODY-004.json`). It adds no new RTC id, no new registry and no new dependency. It is stdlib only.

The organization owns the ledger. Master Records is a downstream recorder only: it never gates and never owns gating. A ledger writer is not subordinate to Registry coordination.

Registration and CI never stand for runtime. Runtime counts only when a manifest-directed transition appends a receipt to `refs/stegverse/organization-ledger`.

## Layout

| File | Role (source at 10d14104) |
|---|---|
| `emit.py` | repository receipt emitter (`.stegverse/transition-ledger/emit.py`, blob f30c02e8) |
| `aggregate_repo_transition.py` | organization aggregator: CAS append, GENESIS/FROM_HEAD, `consumes` gate (blob 3ed69e29) |
| `ledger_store.py` | posix and git-ref store, verbatim (blob 3937db52) |
| `organization_ledger_readback.py` | readback from a fresh fetch (blob e3cd9d1e) |
| `propagate_repository_receipts.py` | intra-org repository→organization propagation (blob 2369d68e) |
| `ledger_common.py` | new; holds the three shared rules below |
| `generate_ledger_contracts.py` | `contract.json` / `org-contract.json` from one parameter file; `--check` |
| `verify_component_manifest.py`, `component-manifest.json` | git blob digests of every module and schema |
| `schemas/` | transition-request v1 (optional `hb_epoch`), parameter file v1 (InTr #163 names) |
| `../../.github/workflows/organization-ledger-transition-reusable.yml` | `workflow_call`; callers pin it by 40-hex SHA |

## The three rules (ledger_common.py)

1. **Supplied epoch.** `hb_epoch` must be digits only and at least 32. It is carried in the committed transition request or the dispatch.
   - Absent: FAIL_CLOSED `HB_EPOCH_NOT_SUPPLIED`.
   - Malformed: FAIL_CLOSED `HB_EPOCH_INVALID`.
   - In both cases nothing is written, the retry is a re-dispatch with the epoch, and no clock is read anywhere.
   - This is the same rule as InTr's TVC `validate_warrant` (TVC#488). It decides case for case like `org-kernel/kernel.py::supplied_epoch_failure`, with the same codes and predicate `SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH`, and carries `derived_from_clock: false`. Only `None` is absent; `""` is invalid. The test `SharedSuppliedEpochRule` pins the two together (Lane B #162 N2).
   - Test: `test_repo_receipt_refuses_without_supplied_epoch`.
2. **Six fields.** Every non-ALLOW carries `failure_code`, `failed_predicate`, `required_evidence_or_repair`, `retry_entrypoint`, `owning_existing_goal` and `next_attempt`.
   - `owning_existing_goal` comes from the consumer's committed parameter file.
   - The SystemExit message is unchanged, so existing callers behave as before. `.refusal` is the record.
   - `required_evidence_or_repair` is never empty or `None`. For example, an unretained source receipt names the receipt and the repair (retain it, or declare a legacy segment) instead of `None`.
   - **Local locators only (P1-FC-12).** `ledger_store.parse_locator` refuses a remote location (a URL such as `https://`, `ssh://`, `git://`, `file://`, or scp-style `user@host:path`), bare or as the repository of `git+`. The refusal is FAIL_CLOSED `LEDGER_LOCATOR_INVALID` in six fields, owned by StegVerse-org/.github#163. Before the fix such a location read as an empty ledger. The readback reports it, and the writers re-raise it as a LedgerRefusal with their own retry entrypoint. Nothing is opened, read or written. Its `retry_entrypoint` is worked out from `__file__` (the path from the repository root, plus `::parse_locator`), so an organization's `resident-runtime/` byte copy names its own path. Test classes: `RemoteLocatorRefused`, `RequiredRepairIsNeverEmpty` and `LocatorRetryEntrypointFromFile`.
3. **Component-relative loading.**
   - Siblings load from this directory, and the kernel is `../kernel.py`.
   - The consumer's contracts are read from the working directory, which is the consumer checkout.
   - No new environment variable is read. The only names read stay `STEGVERSE_REPO_LEDGER_ROOT`, `STEGVERSE_ORG_LEDGER_ROOT` and `STEGVERSE_REPO_LEDGER_HOME`.

A legacy-layout fallback (`resident-runtime/`, `.stegverse/transition-ledger/`) exists only so that an existing fork can converge in place.

## Consumer

Commit these two things:
- `.stegverse/transition-ledger/organization-ledger.parameters.json`;
- the contracts generated from it, unedited.

Then call the reusable workflow with:
- `component_ref` pinned to this repository's commit;
- `intr_interface_ref` defaults to `0f9481af324fc0cf8e46c2446ad69de07f9a8a9d`, the StegVerse-org/.github main merge commit of #185 (PR head `78ae1f8e`, identical tree; C7/C8 signatures: #163 issuecomment-6235428412). The workflow passes the digest-verified component directory itself as the flat `--ledger-component` (no staging), `--consumer-root "$GITHUB_WORKSPACE"`, and on `--verify-self-closure` also `--repository-namespace` and `--org-contract`, so the interface reads back with the component's readback and the consumer's org contract. P1-FC-6 is resolved locally at this pin, pending publication (FC-1).
- `hb_epoch` must be ASCII digits only and >= 32, the same rule as TVC#517 `require_hb_epoch`. Every CLI takes `--hb-epoch` as a string and `ledger_common.require_supplied_epoch` validates it, so `+33`, ` 33` and `3_3` are refused with `HB_EPOCH_INVALID`.

A fresh org opens its chain through the InTr self-closure (`genesis_mode: SELF_CLOSURE_OPENS_CHAIN`). The `communication_id` default is `intr-selfclose-<org>-HB<hb_epoch>`. The 7 existing closures keep `intr-selfclose-<Org>-20261017`, and both forms read back.

## Version

The kernel-manifest gains a module entry. The proposed `kernel_version` bump to 1.4.0 is left to the owner, because `kernel.py` and `kernel-manifest.json` move together.

## Legacy segments (G4/H45)
A ledger can declare the receipts it wrote before source retention began in `org-contract.json`, under `source_receipt_retention.legacy_pre_retention_segment`. The declaration has these members:
- `receipts`
- `waived_predicate` = `SOURCE_RECEIPT_RETAINED_AND_VERIFIES`
- `six_fields`
- `ledger_tip_commit`
- `re_minted: false`
- `reported_as_source_retained: false`
- `declaration_sha256`

The readback still self-hashes and chain-links every receipt, and it verifies every receipt after the segment in full. It waives only source retention, and only for the declared contiguous prefix from genesis. The whole-ledger result is still `FAIL_CLOSED` `DECLARED_LEGACY_SEGMENT_NOT_SOURCE_RETAINED`, never ALLOW, with one six-field finding per declared receipt. Nothing is re-minted. Undeclared failures, declarations that waive integrity checks, segments that are not a prefix, segments that overlap retention, and edited declarations are each refused six-field. Component consumers put the declaration in the parameter file. The generator carries it into `org-contract.json` and validates it.

## Propagation after each append (item 5, INDEX H51)

Right after each C7 ingress and each C8 self-close, the reusable workflow does two things:

1. Materializes the repository subtree of the appended ref with `git archive`.
2. Runs `propagate_after_append.py`.

That module is wiring only. It calls the existing `propagate_repository_receipts.propagate()` in-process; that script is digest-pinned in `component-manifest.json` like every other module.

- **Epoch:** the run's `--hb-epoch` text goes through `ledger_common.require_supplied_epoch` before propagation is loaded, so `+33` is refused there. The validated int is handed over and never re-coerced.
- **Refusals:**
  - A `LedgerRefusal` is printed as `json.dumps(exc.refusal)`, unchanged.
  - A plain `SystemExit(str)` or `LedgerLocationRequired` gets the six fields (`REPOSITORY_RECEIPTS_PROPAGATE_AFTER_THE_APPEND`).
  - Any other exception (`RuntimeError`, `FileNotFoundError`, `KeyError`, a non-str `SystemExit`, ...) is six-field FAIL_CLOSED `PROPAGATION_REFUSAL_NOT_RECORDED`. `--out` is always written (Lane B #162 W1).
  - If an append refuses part-way through, the refusal lists `propagated_before_refusal`, and `consequence_committed` is true when any receipt was carried (N1).
  - A success carries `disposition: ALLOW`.
- **No rollback, no block:** this follows the existing contract. Each organization append is its own committed receipt under the ledger lock, and a refused propagation writes nothing.
  - The appended receipt is published and read back as usual.
  - The workflow records the wrapper's exit status in `propagation.exit` (no `|| true`).
  - The final step "Fail on a recorded propagation refusal" runs `propagation_gate.py`. Every request that appended must have a `propagation.json` with `disposition: ALLOW` under the result schema and exit 0. Absence (no `results/`, no request directory, no record) is FAIL_CLOSED `PROPAGATION_GATE_TREATS_ABSENCE_AS_PASS`. DENY, PENDING, a missing disposition or an unreadable record fail too, all in six fields (G1/G2).
- **Normal result:** after a normal append the repository receipt is already carried, so propagation is a no-op (`skipped`). It appends `REPO_STATE_PROPAGATION` receipts only for repository receipts the organization chain does not yet carry. A rerun skips them.

