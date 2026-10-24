# Six-field entries: P1 component-reuse lane (#163), drafted 2026-10-17
Nothing below is posted. Each entry gives all six fields and the conforming resolution. Since the 2026-10-18 04:08Z directive there are no owner items: each item is classified A/B/C/D in the reclassification section below, and that section supersedes any "owner" wording left in the history.

## A. InTr's two entries assigned to us (copied verbatim from #163 issuecomment-6234609427 §9)

**FC-1. Template not published** (IN PROGRESS 2026-10-18: DRAFT PRs StegVerse-Labs/.github#3225, head `afa2e10c`, and #3226, head `8a0aa8b9` and stacked, are open. All checks that ran pass. It stays OPEN until merge admission (class B, ST-019 `merge_admission`) puts the component at a pinned commit on main.)
- **failure_code:** SHARED_LEDGER_COMPONENT_NOT_PUBLISHED
- **failed_predicate:** H28_COMPONENT_AVAILABLE_AT_PINNED_COMMIT
- **required_evidence_or_repair:** P1 Ecosystem AI Lane publishes the shared ledger component (workflow + resident-runtime modules + tests) at a pinned commit and posts its parameter list on StegVerse-org/.github#163; reconcile §2.2 against it
- **retry_entrypoint:** this plan §3 step 2 (formalism-tests parameter file draft PR)
- **owning_existing_goal:** StegVerse-org/.github#163 (INDEX H28)
- **next_attempt:** on the #163 comment that names the component commit; no polling — the next lane turn reads #163 once

*What our drafts already provide:*
- The component's full source map at 10d14104: `evidence/source-inventory.json`.
- Eleven profile rows plus the RTC-004 extension row: `rows/`.
- Contracts C1–C11: `contracts/CONTRACTS.md`.
- The reusable workflow and per-org caller: `workflow/`.
- The digest verifier and a source-blob manifest, self-tested: `component-tools/`.
- The contract generator, which reproduces StegVerse-org's contracts byte-identically: `params/generate_ledger_contracts.py`.
- The request schema, 9/9 requests pass: `schemas/`.

*Remaining (reclassified 04:08Z):*
- D1: resolved by invariant (D, KM canonical_source).
- D2: resolved by invariant (D, RTCM).
- Making the extraction repairs to C3, C4 and C10, which is a branch/PR on the home repo.
- Publishing the pinned commit.
- Posting the #163 comment that names it.

*Status:* repaired in a local-only commit, `build/labs-local` fd7aeca (component) + 43f9308 (CONF-1). Patches are in `build/patches/`. Remains FAIL_CLOSED until merge admission of #3225 (class B) and publication of the commit SHA on #163.

**FC-2. Parameter list not posted**
- **failure_code:** TEMPLATE_PARAMETER_LIST_NOT_POSTED
- **failed_predicate:** ISSUE_163_DECLARES_PARAMETER_SET
- **required_evidence_or_repair:** #163 comment with the parameter list; until then §2.2 is the derived, PROPOSED set
- **retry_entrypoint:** this plan §2.2
- **owning_existing_goal:** StegVerse-org/.github#163
- **next_attempt:** same event as FC-1

*What our drafts provide:*
- `params/stegverse.organization-ledger-parameters.v1.schema.json` adopts InTr's names #1–#21 **unchanged**. Derived fields (#2, #4, #7, #8, #13, #14) are refused if typed. Dispatch inputs (#15–#17) are never stored.
- Worked examples: `params/StegVerse-org.parameters.json` (regenerates IDENTICAL) and `params/formalism-tests.parameters.json` (the H29 pilot; output is in `params/generated/formalism-tests/`).
- Three additions beyond InTr's list:
  - optional `repository_ledger_designation_source` and `repository_ledger_rule`, both needed to reproduce existing orgs byte-for-byte;
  - an optional `hb_epoch` on committed requests (C9), because a push has no dispatch input.

*Remaining:* posting the parameter-list comment on #163 (class D, G-1). The draft text is in `consumer-interface-spec.md`.

*Status:* the ready-to-post comment is `build/drafts/163-parameter-list-comment.md`. Remains FAIL_CLOSED until it is posted on #163 under G-1.

## B. Our own entries

**CONF-1. RTC-EVIDENCE-CUSTODY-004 names Master Records as owner (conformance violation)**
- **failure_code:** RTC_CANONICAL_OWNER_MASTER_RECORDS_NONCONFORMING
- **failed_predicate:** CUSTODY_COMPONENT_OWNER_IS_ORGANIZATION_AND_MASTER_RECORDS_IS_DOWNSTREAM_NON_GATING_RECORDER
- **required_evidence_or_repair:**
  - Change `StegVerse-Labs/.github@fc14e216:data/reusable-transport-component-contract.json` (blob f81a4734):
    - L33 `"canonical_owner":"Master Records"` becomes `"Organization"`, adding `downstream_recorder: Master Records`, `downstream_recorder_gates: false` and `component_ref`.
    - L45 `invariants.observed_reality_reconstruction_authority: "Master Records"` becomes `observed_reality_custody_authority: Organization` plus `observed_reality_reconstruction_recorder: Master Records (downstream, non-gating)`.
    - Exact patch: `conformance/RTC-EVIDENCE-CUSTODY-004.proposed.diff`, which validates as JSON.
  - Related wording to reconcile in the same change:
    - `data/reusable-task-registry.json` (d2c454e8) L10 `authority.observed_reality_and_reconstruction: "MASTER_RECORDS"`.
    - `source-bundles/reusable-task-registry.d/RT-CANONICAL-MASTER-RECORDS-STATE-TRANSITION-CUSTODY-001.json` (fbbe9647) L4 purpose: "require exact validation and reconstruction … before machine-owned progression continues". That makes Master Records a progression gate, contrary to `propagation_gates_organization_runtime_reality: false` and SDK #452/#466.
  - Model file `data/reusable-task-component-model.json` already says `observed_reality_custody: Organization`, so the transport contract is the outlier.
- **retry_entrypoint:** StegVerse-Labs/.github data/reusable-transport-component-contract.json (existing canonical file; no new registry)
- **owning_existing_goal:** StegVerse-org/.github#163 (with #160 invariant: Master Records is a downstream recorder only)
- **next_attempt:** applied in #3225 (`4e336f8`); merge admission (B), then admit `rows/RTC-EVIDENCE-CUSTODY-004.json` and profiles C1–C6, C9–C11

*Class:* D (GI/ORRD decide it); residual Registry-surface wording is C (JD-1).

**P1-FC-3. Component home and distribution undecided**
- **failure_code:** ORGANIZATION_LEDGER_COMPONENT_HOME_UNDECIDED
- **failed_predicate:** ORG_KERNEL_DECLARES_AN_ORGANIZATION_LEDGER_MODULE_AT_A_PINNED_COMMIT
- **required_evidence_or_repair:**
  - org-kernel (`canonical_source: StegVerse-Labs/.github/org-kernel`, Labs 1.3.2) has no ledger module.
  - Kernel copies have drifted: StegVerse-org runs 1.3.1, and federation.json requires 1.3.0.
  - There is no sync workflow; vendoring is by hand-copy.
  - D1 and D2 are resolved by invariant (KM, RTCM). Add `organization ledger` to kernel-manifest `modules`, place C3–C6 and C11 under `org-kernel/organization-ledger/` with `component-manifest.json` blob digests, and add the reusable workflow.
- **retry_entrypoint:** StegVerse-Labs/.github org-kernel/kernel-manifest.json
- **owning_existing_goal:** StegVerse-org/.github#163
- **next_attempt:** D1/D2 resolved by invariant (reclassification 04:08Z); landing via FC-1
- **Status (local build, 2026-10-17):** D1/D2/D4 defaults applied locally only, in `build/labs-local` commit fd7aeca (not pushed). The tree is `org-kernel/organization-ledger/`, the kernel-manifest module entry is added, and the 1.4.0 bump is held at 1.3.2 pending JD-2 (no declared version rule). This stays open until merge admission of #3225.

**P1-FC-4. Clock fallback in the extraction source (InTr FC-8 root cause)**
- **failure_code:** REPO_RECEIPT_HB_REFERENCE_CLOCK_FALLBACK
- **failed_predicate:** EVERY_APPEND_USES_A_SUPPLIED_HB_EPOCH
- **required_evidence_or_repair:**
  - Remove the `kernel.hb_reference()` fallback in `emit.py:105`, `aggregate_repo_transition.py:311` and the propagation path, and refuse `HB_EPOCH_NOT_SUPPLIED` with six fields.
  - Add test `test_repo_receipt_refuses_without_supplied_epoch`.
  - GCAT-BCAT-Engine repo receipt `ed4fe98d` (`sampled_unix_ns`, `phase_offset_ns: 2494976`) shows the effect; its workflow says "empty derives one from the clock".
- **retry_entrypoint:** component test suite (C3/C4)
- **owning_existing_goal:** StegVerse-org/.github#163
- **next_attempt:** in the extraction commit (part of FC-1). GCAT's existing receipt stays as history, never re-minted; GCAT remediation is a separate item.
- **Status:** REPAIRED in the local build (fd7aeca).
  - Shared rule, agreed with InTr and matched by TVC#488 `validate_warrant`:
    - absent epoch: `HB_EPOCH_NOT_SUPPLIED` (failed_predicate `HB_EPOCH_IS_SUPPLIED_BY_THE_MANIFEST_OR_DISPATCH`);
    - malformed epoch: `HB_EPOCH_INVALID` (`HB_EPOCH_IS_AN_INTEGER_AT_OR_AFTER_THE_HB32_ANCHOR`);
    - six fields, retry by re-dispatch, nothing written, no clock read.
  - `test_repo_receipt_refuses_without_supplied_epoch` passes, along with the org and propagation equivalents.
  - Also found: StegVerse-org's own repository chain holds 7 clock-derived receipts out of 20, and SV-LLM holds 21 of 30. They stay as history.
  - **Interface delta for InTr (not ours to change):** two clock-path tests in StegVerse-org now hit `HB_EPOCH_NOT_SUPPLIED` through InTr-owned callers. They are `test_organization_egress_boundary::test_an_emission_without_a_supplied_epoch_is_recorded_each_time` and `test_intr_destination_capability::test_a_peer_frame_at_the_address_is_received_and_grants_nothing` (kernel `ingest_frame` → capability ingress with no epoch). Under the shared rule they become refusal tests on the InTr side.

**P1-FC-5. Aggregator refusals lack six fields**
- **failure_code:** ORG_LEDGER_REFUSAL_MISSING_SIX_FIELDS
- **failed_predicate:** EVERY_NON_ALLOW_CARRIES_SIX_FIELDS
- **required_evidence_or_repair:**
  - 25 `raise SystemExit("<code>")` sites in `aggregate_repo_transition.py` emit a bare string. Convert them to `stegverse.organization-ledger-append-refusal/v1`, with `owning_existing_goal` as a parameter.
  - Same for the workflow's `DISPATCH_HB_EPOCH_INVALID` (L318, 3 of 6 fields) and the hardcoded goals at L357, L369 and L398. The draft workflow already does this.
- **retry_entrypoint:** resident-runtime/aggregate_repo_transition.py::append
- **owning_existing_goal:** StegVerse-org/.github#163
- **next_attempt:** in the extraction commit
- **Status:** REPAIRED in the local build (fd7aeca). The sites converted are 24 aggregator `raise SystemExit("...")` (the 25th is the CLI `SystemExit(1)` exit code), 5 propagation sites, emit contention, and the workflow's epoch refusal, now `HB_EPOCH_NOT_SUPPLIED`/`HB_EPOCH_INVALID` with six fields. `owning_existing_goal` is read from the consumer's committed parameter file, and the dispatch input must equal it. No new environment variable is read, so the governed-ingress census holds.

**P1-FC-6. Candidates 7 and 8 are InTr-owned interfaces, not yet published at a pin** (RESOLVED LOCALLY at 0f9481af, PENDING PUBLICATION via FC-1)
- **failure_code:** CONSUMED_INTR_INTERFACE_NOT_PINNED
- **failed_predicate:** INTR_MESH_PUBLISHES_INGRESS_AND_SELF_CLOSURE_INTERFACE_AT_A_COMMIT
- **required_evidence_or_repair:**
  - **Merged:** StegVerse-org/.github#185 merged 2026-10-17T16:22:58Z as merge commit **0f9481af324fc0cf8e46c2446ad69de07f9a8a9d** (PR head 78ae1f8e625f1c577feaaeb858915c94c8866d78, same tree 4b5c0ba8). Org `main` is at 0f9481af. The Labs twins #3212/#3213 are still open.
  - **Pin:** `intr_interface_ref` now defaults to the main merge commit 0f9481af (reachable from main; InTr confirmed it). The PR head 78ae1f8e is also reachable (it is the merge's second parent) and has the same tree, but it was never main's tip, so there is no reason to fall back to it.
  - **Flat layout accepted on main:** the `$RUNNER_TEMP` staging step is removed. C7/C8 get the digest-verified component directory itself as `--ledger-component "$COMPONENT"`, plus `--consumer-root "$GITHUB_WORKSPACE"`.
  - **Readback context:** at 0f9481af, `--verify-self-closure` takes `--org-contract` and `--repository-namespace` and hands them to the bound component's readback. The workflow now passes `--org-contract "$GITHUB_WORKSPACE/.stegverse/transition-ledger/org-contract.json"`. That is the same file as the default, made explicit. The intake has the row `ORGANIZATION_LEDGER_HEAD_ABSENT` / `ORGANIZATION_LEDGER_HEAD_PRESENT` -> FAIL_CLOSED. This closes the earlier gap where InTr's verify path called the readback without the org contract.
  - **Verified locally** (`build/evidence/intr-0f9481af/c7c8.{py,json}`; 0f9481af worktree with SDK 74d9b473): **66/66 checks OK**, across InTr's own writers, the flat component and the nested-staged component:
    - C8 self-close at HB4200 gives the same org receipt sha256:85142d00… and identical ledger trees.
    - C7 ingress at 32 gives the same org receipt under all three writer sets.
    - Verify returns ALLOW with and without `--org-contract`.
    - Redelivery leaves the ref unchanged.
    - `0033` is accepted as 33.
    - `''`, `+33`, ` 33`, `3_3`, `abc` and `31` are refused with six fields and nothing is appended.
    - The component's `LedgerRefusal` HB_EPOCH_NOT_SUPPLIED is printed as given: the writer's own predicate and `emit.py::append` entrypoint.
    - An empty ledger gives ORGANIZATION_LEDGER_HEAD_ABSENT on ORGANIZATION_LEDGER_HEAD_PRESENT.
    - A segment declared through `--org-contract` reaches the G4 rule, and a wrong namespace gives REPOSITORY_NAMESPACE_MATCHES_THE_CONTRACT.
- **retry_entrypoint:** workflow input `intr_interface_ref`
- **owning_existing_goal:** StegVerse-org/.github#162 (InTr & Mesh)
- **next_attempt:** publication of the component (FC-1: merge admission of #3225, class B). Nothing else is outstanding on the pin.

**P1-FC-7. Reconciliation instruction not on Labs main**
- **failure_code:** COMPONENT_RECONCILIATION_INSTRUCTION_NOT_CANONICAL
- **failed_predicate:** INSTRUCTION_8E67CE42_INTEGRATED_ON_MAIN
- **required_evidence_or_repair:**
  - Integrate Labs `intr/one-way-hop@8e67ce42` (docs/INTERLOCK_INTR_RUNTIME_INDEPENDENT_PROTOCOL_MIRROR_HANDOFF.md, blob c4c57175) on main.
  - This lane already applies it: evaluator run, negative search, per-task matrix in README.
- **class:** B (merge admission, ST-019); never an LLM merge
- **retry_entrypoint:** existing Labs branch intr/one-way-hop
- **owning_existing_goal:** INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001 (#162 mesh audit 6234657929)
- **next_attempt:** when the merge gate admits `intr/one-way-hop@8e67ce42`

**P1-FC-8. Direct InTr receive/closure calls with no epoch fall back to the ledger default** (OPEN, residual, InTr-owned)
- **Status at 0f9481af (org main):**
  - **Partly repaired.** The CLI now prints the component's `LedgerRefusal` as given, as six-field FAIL_CLOSED. Coerced epochs are refused HB_EPOCH_INVALID on both sides.
  - **Still open on InTr's own default writers.** `--self-close` (C8) and the C7 ingress with **no** `--hb-epoch` still exit 0 ALLOW and append. The appended epoch is oscillator-derived (`HB:474289663`, `derived_from_clock: false`).
  - The component path is unaffected: the component writers refuse HB_EPOCH_NOT_SUPPLIED, and the workflow always passes the epoch.
- **failure_code:** INTR_DIRECT_CALL_EPOCH_FALLBACK
- **failed_predicate:** DIRECT_RECEIVE_AND_CLOSURE_CALLS_REQUIRE_A_SUPPLIED_EPOCH
- **required_evidence_or_repair:**
  - At e0e132d7 the kernel path refuses a missing epoch, through capability_ingress. Direct receive/closure calls with no epoch still fall back to the ledger default. This was observed with InTr's own writers: a no-epoch self-close gave a clock-derived ALLOW.
  - When the same call is pointed at the component writers, the result is `HB_EPOCH_NOT_SUPPLIED` and nothing is written. But InTr's CLI does not catch the component's `LedgerRefusal`, so it exits 1 with no six-field `--out` JSON.
  - Repair: InTr PR-1b. Direct calls require a supplied epoch (ASCII digits, >= 32, TVC#517 `require_hb_epoch`), and the CLI passes ledger refusals through as six-field FAIL_CLOSED.
  - **Not reachable from the component path.** The reusable workflow validates `hb_epoch` in its first step: it must be non-empty, ASCII digits only, and >= 32, otherwise six-field FAIL_CLOSED. It passes `--hb-epoch "$HB_EPOCH"` on both appending InTr calls (C7 ingress and C8 `--self-close`). The verify and readback calls only read. So the fallback is never hit.
- **retry_entrypoint:** InTr receive/closure (`intr_destination_ingress.py`, kernel receive) at org#185 successor
- **repair lane:** 03dd62b7's PR-1b (org#187), routed by InTr; admission class B
- **owning_existing_goal:** INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001 (StegVerse-org/.github#162)
- **next_attempt:** PR-1b (03dd62b7), as listed open on #163 issuecomment-6236719594

**P1-FC-9. SV-011's legacy-segment declaration lacks the G4 members** (OPEN, owned by the SV-011 lane)
- **failure_code:** LEGACY_SEGMENT_DECLARATION_INCOMPLETE
- **failed_predicate:** LEGACY_SEGMENT_DECLARES_EVERY_REQUIRED_MEMBER
- **required_evidence_or_repair:**
  - SV-011/.github PR #9 @20186d0 `org-contract.json` `source_receipt_retention.legacy_pre_retention_segment` needs three more members:
    - `waived_predicate: "SOURCE_RECEIPT_RETAINED_AND_VERIFIES"`;
    - `six_fields` (the H45 six fields);
    - `declaration_sha256`.
  - The exact JSON is in `build/evidence/g4-legacy-segment/sv011-org-contract.pr9-plus-g4-members.json`, and its digest is `sha256:36c43b78e2c820d5448d7edb7f4bf7222d22faf9a91925ad18e3e50a54267375`.
  - With them, the readback at 2cc58cec is `FAIL_CLOSED DECLARED_LEGACY_SEGMENT_NOT_SOURCE_RETAINED`, naming only 3db9008d. It is never ALLOW.
- **retry_entrypoint:** SV-011/.github PR #9 branch cursor/sv011-org-ledger-17f9 `.stegverse/transition-ledger/org-contract.json`
- **owning_existing_goal:** SV011-TT-CAPABILITY-MAP-OBSERVATION-001 (#167 lane B, #68)
- **next_attempt:** the SV-011 lane adds the members on PR #9, then reads back with the component at its published commit.
- **Resolved by invariant (D, ORRD §5 and GI NO_STRONGER_COMPLETION_CLASS_WITHOUT_NATIVE_EVIDENCE): option (i).** A ledger with a declared segment never reads back as ALLOW, so workflow runs on SV-011 end with the readback `FAIL_CLOSED`. Options: (i) accept this (the default); (ii) gate the step on `ingress_receipt_in_fully_verified_suffix` (not implemented); (iii) amend the standard to add a fourth outcome. See `build/G4-legacy-segment-rule.md`.

**Epoch rule, CLI parity (TVC#517):**
- The `--hb-epoch` flag in `emit.py`, `aggregate_repo_transition.py` and `propagate_repository_receipts.py` is now `type=str`. `ledger_common.require_supplied_epoch` enforces `re.fullmatch("[0-9]+", value, re.ASCII)` and then >= 32. So `+33`, ` 33`, `33 `, `3_3`, `31` and non-ASCII digits are refused with `HB_EPOCH_INVALID`, and `32`/`33` are accepted.
- The workflow's shell check uses the explicit class `[!0123456789]`, so it does not depend on the locale.
- Leading zeros (`0033`) are ASCII digits and are accepted as 33 by both the CLI and the workflow. Confirm this matches TVC#517.

Entries owned elsewhere and referenced only: InTr FC-3 (StegVerse-org self-closure dispatch), FC-5 (SV-011/entity), FC-6 (master-records role) and FC-7 (manifest-ingress correlation). Our C9 `hb_epoch` field closes the epoch half of FC-7.


**P1-FC-10. org main's propagate_repository_receipts.py coerces --hb-epoch with int()** (OPEN; repair lane Lane B / #189 author per #162 issuecomment-6245048098; goal INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001. Resolved by invariant (D, EPOCH): `type=str`; the earlier "no change" default is retired by the 04:08Z directive)
- **failure_code:** HB_EPOCH_INVALID_COERCED
- **failed_predicate:** SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH
- **required_evidence_or_repair:**
  - At StegVerse-org/.github@0f9481af, `resident-runtime/propagate_repository_receipts.py` L232 declares `--hb-epoch type=int`. This is one of the four int CLIs. With `--hb-epoch=+33` and `--hb-epoch=3_3` it exits 0, coerced to 33 (`build/evidence/ecosystem-readback/upstream-propagate-int-coercion.txt`).
  - Repair: `type=str` plus the shared validator (`require_hb_epoch` / `supplied_epoch_failure`).
  - The component path is unaffected:
    - The component's copy takes `type=str` through `ledger_common.require_supplied_epoch`.
    - The workflow never calls the CLI. It calls `propagate_after_append.py`, which validates the run's epoch text first, refusing `+33` before propagation is loaded (test `test_plus_33_is_refused_before_propagation_is_reached`), and then hands over the int in-process.
- **retry_entrypoint:** StegVerse-org/.github `resident-runtime/propagate_repository_receipts.py::main`
- **owning_existing_goal:** INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001 (StegVerse-org/.github#162)
- **next_attempt:** #189 repair (b)/(d) on its next head, then merge admission (B). It is never reached from the component.

**P1-FC-11. No ecosystem capability fetches and reads back the federation ledgers as a sweep** (OPEN, P1; class B, built locally at `e29493a`, not pushed)
- **failure_code:** ECOSYSTEM_CAPABILITY_ABSENT
- **failed_predicate:** ECOSYSTEM_CAPABILITY_PERFORMS_STEP
- **required_evidence_or_repair:**
  - Item (1) used the existing readback (StegVerse-org/.github@0f9481af `resident-runtime/organization_ledger_readback.py`, blob e3cd9d1e) unchanged. Fetching each ref into a local clone, invoking the readback per ledger, and recording command, ref SHA and output sha256 is done by the lane's `build/evidence/ecosystem-readback/run.sh`, not by an ecosystem capability, and no Actions run id exists for these invocations.
  - Extend the existing component: the reusable workflow `organization-ledger-transition-reusable.yml`, in a readback-only dispatch mode that fetches the designated ref fresh and runs the readback (offload map item 1, "optional readback-only dispatch mode"). The JSON is then emitted under a run id.
- **retry_entrypoint:** org-kernel/organization-ledger (reusable workflow `organization-ledger-transition-reusable.yml`, readback step)
- **owning_existing_goal:** StegVerse-org/.github#163
- **next_attempt:** readback-only mode is built locally (`p1/readback-only-mode` @`e29493a`, 77/77); it goes out as a draft PR stacked on #3226. Until it lands, the sweep counts as LLM work.

**P1-FC-12. A remote locator is read as an empty ledger, not refused as a locator** (component part REPAIRED LOCALLY at `1ad75d6`, not published, publication via FC-1; org part: Lane B draft org#190 @`d0ccfca5`, a byte copy (blob `9c50cd20`); admission class B)
- **Component repair (local, `1ad75d6`, patch 0009):**
  - `ledger_store.parse_locator` and `open_store` refuse a URL (`https://`, `http://`, `ssh://`, `git://`, `file://`) or an scp-style `user@host:path` / `host:path` location, bare or as the `git+` repository. The refusal is FAIL_CLOSED `LEDGER_LOCATOR_INVALID` / `LEDGER_LOCATOR_NAMES_A_STORE_ON_THIS_NODE`, owned by StegVerse-org/.github#163, before any read. The readback reports it; emit and aggregate re-raise it as a LedgerRefusal.
  - Evidence: `build/evidence/ecosystem-readback/remote-https-locator.component-fc12.txt`.
  - No component refusal now carries an empty or `None` `required_evidence_or_repair`. SOURCE_RECEIPT_RETAINED_AND_VERIFIES names the receipt and the repair. In the 8-ledger replay, only SV-011's value changed, from `None` to that repair; every other field and the exit code are unchanged.
  - Tests: `RemoteLocatorRefused`, `RequiredRepairIsNeverEmpty`. Suite 54/54.
- **Remaining (org `resident-runtime/` at 0f9481af):**
  - **failure_code:** LEDGER_LOCATOR_INVALID
  - **failed_predicate:** LEDGER_LOCATOR_NAMES_A_STORE_ON_THIS_NODE (org readback still reads `git+https://…` as `ORGANIZATION_LEDGER_HEAD_PRESENT` "no HEAD", see `build/evidence/ecosystem-readback/remote-https-locator.json`)
  - **required_evidence_or_repair:** the same `parse_locator` refusal in org `resident-runtime/ledger_store.py`, and a non-`None` repair for SOURCE_RECEIPT_RETAINED_AND_VERIFIES in org `organization_ledger_readback.py`. Patch 0009 is the reference.
  - **retry_entrypoint:** org `resident-runtime/ledger_store.py::parse_locator`
  - **owning_existing_goal:** StegVerse-org/.github#163 (routed by InTr on #162)
  - **next_attempt:** merge admission of org#190 (B). Any change to #3225's `ledger_store.py` must be flagged to Lane B.


**Lane B review #162 issuecomment-6245048098: findings on #3225 and #3226 (REPAIRED on the branches, 2026-10-18)**
- W1 PROPAGATION_REFUSAL_NOT_RECORDED: fixed in `5f96829`. The wrapper catch-all always writes `--out`, and the workflow records `propagation.exit` (no `|| true`).
- G1/G2 PROPAGATION_GATE_TREATS_ABSENCE_AS_PASS: fixed in `5f96829` with `propagation_gate.py`. Absence and non-ALLOW records fail closed in six fields, and success records carry `disposition: ALLOW`.
- N1: fixed in `5f96829`. A refusal lists `propagated_before_refusal`, and `consequence_committed` reflects it.
- N2: aligned in `3518275`. The rule decides case for case like `org-kernel/kernel.py::supplied_epoch_failure`, uses predicate SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH and sets `derived_from_clock: false`. A parity test covers 25 inputs. The one behaviour change is that `""` is now HB_EPOCH_INVALID instead of NOT_SUPPLIED; both refuse.
- `parse_locator` retry_entrypoint is now worked out from `__file__` (`3518275`), so an org `resident-runtime/` byte copy is possible. The org port itself (LEDGER_LOCATOR_INVALID_NOT_REFUSED_IN_ORG_COPY) stays with Lane B on #162; see P1-FC-12.

**Lane B re-review #162 issuecomment-6245224202 (REPAIRED on the branches, 2026-10-18)**
- BC1 ORG_BYTE_COPY_BREAKS_LEDGER_LOCATION_GUARD (blocking, #3225): fixed in `e6ba960`. The locator refusal's `next_attempt` reads `+<ledger ref>:<ledger ref>`. `ledger_store.py` contains none of `refs/stegverse`, `refs/heads/`, `refs/ledger`, `DEFAULT_REF` or `DEFAULT_LOCATOR`, and a test mirrors org's guard. Blob `9c50cd200db1496c6820616262bbc1ae4b23879a`, sha256 `6bd217e0df6de9fee072933bf2251f24ea4bf4ca5d1eb18b4bebe226e86534cf`. Merged into wiring by the merge commit `e783042`.
- G3 (#3226): fixed in `f82c032`. A missing `propagation.exit` is FAIL_CLOSED `PROPAGATION_EXIT_STATUS_ABSENT` in six fields.
- N3 (#3226): fixed in `f82c032`.
  - The request loop writes `results/NO_REQUESTS.json` when it received no request.
  - Only then does the gate return ALLOW (`applicability: NO_REQUEST_RECEIVED`, nothing appended, so nothing to propagate).
  - An empty `results/` without the marker is `PROPAGATION_NO_REQUEST_RECORDED`.
  - An invalid or contradicted marker is `PROPAGATION_NO_REQUESTS_MARKER_INVALID`.
- N1 partial (#3226): fixed in `f82c032`. `propagated_before_refusal` is recorded for any exception raised part-way, not only `SystemExit`.

## Reclassification 2026-10-18 (no owner items; supersedes owner wording above)

**P1 reclassification: no owner items (Rigel directive 04:08Z; invariant-first rule 04:09Z). Aligned with Coordination 6245552272.**

Classes follow Coordination 6245552272:
- **A**: an existing transition or workflow performs the step, and its receipt is the observation.
- **B**: a capability to build.
- **C**: joint discovery (INDEX JOINT DISCOVERY QUEUE).
- **D**: resolved by a declared invariant.

Nothing below waits on Rigel. Every item that isn't ALLOW keeps its fail-closed default, and the never-grantable actions (merge, tag, release, ledger dispatch, Registry edits, settings, deletion) stay out of every LLM lane.

**Invariant refs** (Labs main `bfcf0318`, org main `0f9481af`):
- **ORRD:** org `docs/ORGANIZATION_ROLE_RUNTIME_REALITY_DEPLOYMENT.md` cd56b2d0, §Conformance 1-5.
- **GI:** Labs `data/task-registry-global-invariants.json` 208177e0.
- **WBF:** `docs/WORKER_BLOCKER_FALLBACK_INVARIANT.md` 553a079e.
- **REG:** `data/canonical-task-registry.json` gen 319, `human_actions: []`.
- **FENCE:** `data/task-coordination-policy.json#session_mutation_generation_fence`.
- **KM:** `org-kernel/kernel-manifest.json` 1fdf59a9.
- **RTCM:** `data/reusable-task-component-model.json` 87688679.
- **EPOCH:** `org-kernel/kernel.py::supplied_epoch_failure` (L236); TVC#517.
- **NG:** INDEX "Never grantable".
- **ST-019:** repo-standards#78 9b662862, `config/repository-protection-policy.json#merge_admission`.
- **GOV (A route):** decisions go through the existing governance decision path.
  - The request is org `.stegverse/transition-requests/*.json` (`stegverse.organization-transition-request/v1`, `process: governance`).
  - It runs through `organization-ledger-transition.yml`, which records the receipt `stegverse.organization-transition-receipt/v1`.
  - Labs `organization-governance-decision.yml` decides it with StegCore `steggate.evaluate_admissibility` @9882851b and records `stegverse.org-governance-decision/v1`.
  - Org `organization-governance-return.yml` returns it as `stegverse.organization-governance-decision-return-result/v1`.
  - Precedent: SDK-MR-A-ORGANIZATION-LEDGER-RECEIPT-001..004.

| Item | Class | Resolved by invariant | Six fields (failure_code / failed_predicate / required_evidence_or_repair / retry_entrypoint / owning_existing_goal / next_attempt) |
|---|---|---|---|
| FC-1: admit Labs#3225, then #3226 | **B** (merge admission, #162), order **D** | ST-019 P2: #3225 goes first. Then #3226 retargets to `main`, and it is admitted only on `validate-organization-ledger-component` ALLOW. Lane B PASS on both heads (#162 6245397227). | SHARED_LEDGER_COMPONENT_NOT_PUBLISHED / H28_COMPONENT_AVAILABLE_AT_PINNED_COMMIT / merge-admission receipt for #3225 at `e6ba9601`, then #3226 at `f82c0324` after the retarget / ST-019 `merge_admission` on Labs#3225 / #163 / when the merge gate admits #3225, P1 retargets #3226 (update_pull_request) and reports its check |
| FC-2: parameter list | **D** | INDEX G-1 (own Goal issue, COMMENT ALLOW). The names are InTr H29 §2.2 (#163 6234609427), adopted unchanged. | TEMPLATE_PARAMETER_LIST_NOT_POSTED / ISSUE_163_DECLARES_PARAMETER_SET / post `build/drafts/163-parameter-list-comment.md` on #163 / #163 comment / #163 / posted with this checkpoint |
| D1: component home | **D** (done) | KM `canonical_source: StegVerse-Labs/.github/org-kernel`, so the home is `org-kernel/organization-ledger/` (#3225) | landing rides FC-1 |
| D2: identity | **D** (done) | RTCM (no reimplementation of an existing component): extend RTC-EVIDENCE-CUSTODY-004 with profiles, with no new RTC id (#3225) | landing rides FC-1 |
| D3 / CONF-1 | **D** (done in #3225 `4e336f8`); residual **C** (JD-1) | GI `runtime_reality_authority: Organization`, `master_records_may_gate_organization_runtime_reality: false`, `master_records_role: ORGANIZATION_RECORDS_AND_RECONSTRUCTION_ONLY`; ORRD | RTC_CANONICAL_OWNER_MASTER_RECORDS_NONCONFORMING / CUSTODY_COMPONENT_OWNER_IS_ORGANIZATION_AND_MASTER_RECORDS_IS_DOWNSTREAM_NON_GATING_RECORDER / transport contract repaired in #3225. Residual: the same wording in `data/reusable-task-registry.json` L10 and the RT-CANONICAL-MASTER-RECORDS-…-001 source bundle, which is a Registry-surface edit / those files / #163 / JD-1 answer |
| D4: genesis_mode | **D** (closed) | Not a global decision. It is a per-consumer committed parameter (`stegverse.organization-ledger-parameters/v1`, H29 #3, default SELF_CLOSURE_OPENS_CHAIN). ORRD §1 requires an explicit predecessor. | none |
| D5: Task ID/COSV for ORG-LEDGER-REUSABLE-COMPONENTS-163 | **C** (JD-1) | FENCE decides how a Registry mutation is fenced, not who performs it. NG excludes LLM lanes. REG `human_actions: []`. | REGISTRY_TASK_ABSENT / GOAL_TASK_IS_REGISTERED_WITH_COSV / a canonical record plus COSV (repo-standards `derive_task_registry_cosv.py`) / `data/canonical-task-records/` under FENCE / #163 / JD-1 answer; default: COSV UNASSIGNED, the goal issue is the reference |
| D6: convergence of the 8 forks | **D** | GI `organization_role_deployment_scope: PER_ORGANIZATION_IN_ITS_OWN_DOT_GITHUB`; org-contract `append_only_receipts` (never re-mint). Each fork commits its own caller and parameter file after FC-1, and its history is kept. | FORK_NOT_ON_SHARED_COMPONENT / FORK_CONSUMES_COMPONENT_BY_PINNED_SHA / per-org caller draft (each org's lane) / that org's caller / #163 / after FC-1 |
| G4: option (i)/(ii)/(iii) | **D**: option (i) | ORRD §5: a non-ALLOW with six fields is actionable and is not a blocker, and the outcomes are ALLOW/DENY/FAIL_CLOSED, which excludes a 4th outcome (iii). GI `NO_STRONGER_COMPLETION_CLASS_WITHOUT_NATIVE_EVIDENCE` excludes (ii), passing on a partly verified suffix. | none: a declared segment reads back FAIL_CLOSED `DECLARED_LEGACY_SEGMENT_NOT_SOURCE_RETAINED` (as built) |
| B3 / SV-011#12 item 1 | **D**; residual **A** (SV-011 lane, PR #9) | ORRD §5 and the three outcomes: a successful readback with no disposition is not ALLOW. Item 1 is rescinded for the readback outcome only (C6 `readback/v1`, top-level ALLOW). The rest of item 1 stands. | READBACK_SUCCESS_SHAPE_NONCONFORMING / READBACK_SUCCESS_CARRIES_ALLOW / SV-011 converges on C6's success form / SV-011/.github PR #9 / SV011-TT-CAPABILITY-MAP-OBSERVATION-001 / SV-011 lane's next turn |
| kernel 1.4.0 | **C** (JD-2) | KM schema `stegverse.org-resident-kernel-manifest/v1` declares no version rule. `control/organization-federation.json` and `control/organization-task-registry.json` pin `kernel_version` per org. | KERNEL_VERSION_RULE_UNDECLARED / KERNEL_MANIFEST_DECLARES_ITS_VERSION_RULE / a declared rule / KM / #163 / JD-2 answer; default: stays 1.3.2, module entry added (#3225) |
| P1-FC-7: 8e67ce42 on Labs main | **B** (merge admission; same gate as FC-1) | ST-019 | COMPONENT_RECONCILIATION_INSTRUCTION_NOT_CANONICAL / INSTRUCTION_8E67CE42_INTEGRATED_ON_MAIN / merge-admission receipt for `intr/one-way-hop@8e67ce42`, with the merge-step conflict resolved (Claude Q6) / ST-019 on that branch's PR / INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001 / when the gate admits it |
| P1-FC-8: direct calls with no epoch | **D** (rule); residual **B** (merge admission of org#187, then #189) | EPOCH: a direct receive or closure must refuse an unsupplied epoch. The repair is org#187 (`4d04d805`) plus #189 for the binders. | INTR_DIRECT_CALL_EPOCH_FALLBACK / DIRECT_RECEIVE_AND_CLOSURE_CALLS_REQUIRE_A_SUPPLIED_EPOCH / admit #187, then #189 at a head with 0 C7/C8 findings / ST-019 on org#187 / INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001 / proposed order #188 > #187 > #189 > #186 |
| P1-FC-10: `--hb-epoch type=int` | **D**: switch to `type=str` (the "no change" default is retired, INDEX 04:08Z) | EPOCH: `+33`/`3_3` coerced to 33 fails SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH | HB_EPOCH_INVALID_COERCED / SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH / `type=str` plus `supplied_epoch_failure` in the 4 org CLIs (= #189 repair (b)/(d)) / org `resident-runtime/propagate_repository_receipts.py::main` / INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001 / the #189 author's next head, then ST-019 |
| P1-FC-11: readback sweep | **B**, ours. Built locally at `e29493a`, not pushed. | none needed (component extension) | ECOSYSTEM_CAPABILITY_ABSENT / ECOSYSTEM_CAPABILITY_PERFORMS_STEP / `mode: readback` plus `readback_only.py` (77/77) / reusable workflow `mode: readback` / #163 / a draft PR stacked on #3226 under G-8 |
| P1-FC-12: org copy | **A**: Lane B org#190 (`d0ccfca5`); admission **B** | Byte-copy rule: org#190 `resident-runtime/ledger_store.py` is blob `9c50cd20`, identical to #3225 (sha256 `6bd217e0…`). Any change to #3225's `ledger_store.py` is flagged to Lane B. | LEDGER_LOCATOR_INVALID / LEDGER_LOCATOR_NAMES_A_STORE_ON_THIS_NODE / admit org#190 / ST-019 on org#190 / #163 (Lane B, #162) / when the gate admits it |
| #189 sign-off | **A** (P1 re-runs its own sign-off) | WBF: the blocker is preserved as durable work state. INDEX Q-O1 03:30Z: #189 reaches 0 C7/C8 findings only on top of #187. | CLOCK_DERIVED_EPOCH_ADMITTED_BY_ORG_APPEND / SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH / repairs (a)-(d) (#163 6245039352) on a #189 head containing #187 / `aggregate_repo_transition.py::append` / sign-off #163; repair INTERLOCK-…-001 / P1 re-runs the suite, C7/C8 and CI on the next #189 head |
| SV-LLM#30 note | **C** (JD-3) | INDEX G-1..G-8 do not cover SV-LLM/.github#30 (`SURFACE_GRANT_ABSENT`) | SURFACE_GRANT_ABSENT / ACTION_SURFACE_IS_GRANTED_BY_THE_OWNER / hand-off to Claude (W4 session) / JOINT DISCOVERY QUEUE / SVORG-LLM-ORG-FOUNDATION-001-W04 / Claude's next #30 turn |
| F1 (#120 Sandbox scope) | **A** (GOV route) | GI `actions_by_manifest_required`; ORRD §1 | OWNER_AUTHORIZATION_PENDING becomes SANDBOX_SCOPE_NOT_DECIDED / SANDBOX_SCOPE_DECIDED_BY_GOVERNANCE_TRANSITION / a `process: governance` request / `.stegverse/transition-requests/` / SVORG-LLM-ORG-FOUNDATION-001 / its decision receipt; default: hold |
| F2 (Labs#2901 gates) | **D**; residual **A** (#2901 author applies) | GI `destination_liveness_is_transition_predicate: false`, `external_machine_awaiting_allowed: false`, `master_records_may_gate…: false` | ORGANIZATION_ROLE_CONFORMANCE_NOT_DECLARED / (unchanged) / apply the drafted rewording or register an exemption / Labs#2901 / SDK-GENERIC-MANIFEST-ECOSYSTEM-INVARIANT-005 / #2901's next head |
| F3 / #151 Q1 (SV-LLM path) | **D**: option (a) | RTCM (reuse an existing component). A pinned existing dependency is not a new one. | none: reuse the pinned SDK |
| F4 / LLM-adapter#368 | Q1/Q2 **D**; Q5 **C** (JD-4) | GI `completion_claim_requires_evidence_refs` and NO_STRONGER_COMPLETION_CLASS → Q1(b), a fresh real DENY. ORRD "evidence travels as bytes" → Q2(a), digests in the payload. Deleting a file is NG. | SDK_RUNTIME_RESULT_NOT_ADMISSIBLE / (unchanged) / Q1(b), Q2(a) / LLM-adapter#368 / LLMA-DECLARED-PATH-CONFORMANCE-368 / its lane's next head |
| F5 (#152 copies) | **D** | GI `evidence_reachability_may_establish_substrate_unsuitable: false`, NO_EVIDENCE_REACHABILITY_GAP_AS_EXTERNAL_DEVICE_REQUIREMENT: it is an evidence-state value, not a blocker or completion check | TERMS_PAGE_COPY_NOT_BOUND / (unchanged) / the W03 lane binds copies through its own fetch / #152 / SVORG-LLM-W03-TERMS-PAGE-COPIES-001 / that lane's next turn |
| F6 (HCB#39) / F7 (X1) / #150 | F7 and #150 **D**; F6 **C** (JD-1) | FENCE `canonical_generation_ref` names the canonical registry, Labs `data/canonical-task-registry.json` (F7). #150 reuses the existing repo-standards `derive_task_registry_cosv.py` (RTCM). | F6: REGISTRY_TASK_ABSENT / JD-1 |
| N1 / #161 (`ecosystem_ai_reuse.py`) | **D**; residual: P1 draft PR (G-8) | RTCM L56/L59 (no reimplementation) | REUSABLE_COMPONENT_DUPLICATED / (unchanged) / a supersession draft PR in StegVerse-org/.github / `orchestration/ecosystem_ai_reuse.py` / #163 / next P1 turn |
| N2 (ref branch) | **D**: add a `commit` field to the ref schema | NG excludes settings, so the default-branch option is unavailable | CAPABILITY_DECLARATION_REF_BRANCH_UNBOUND / (unchanged) / a `commit` field (SV-LLM/schemas) / `org-runtime/sandbox_registration.py` / …-W06 / that lane |
| N3 (build backend) | **D**: `--no-build-isolation` | The no-new-dependency rule: no third-party package enters the ledger path | (advisory) / … / `organization-ledger-transition.yml` L100-101 / …-W04 / that lane |
| N4 (StegVerse_AI declaration) / HCB#38 closure / #167 predicate 3 | **C** (JD-5) | No declared invariant says whether an ECOSYSTEM_ENTITY must be Sandbox-registrable, or which transition closes an issue | defaults: unregistered; HCB#38 recorded as SOURCE_IMPLEMENTED (GI forbids an unqualified "complete"); the issue stays open |

**(B) under #163:** INVARIANT-DETERMINATION-001, as defined by Coordination 6245552272. Another worker is building it, so P1 does not. P1's own (B) build is P1-FC-11's readback-only mode: local `p1/readback-only-mode` @`e29493a`, 77/77, `ledger_store.py` unchanged. It goes out as a draft PR stacked on #3226 next.

**(C) hand-offs:** JD-1 to JD-5 in the INDEX JOINT DISCOVERY QUEUE. Each entry gives INVARIANT CHECKED, QUESTION and FEEDBACK OUTPUT, and each FEEDBACK OUTPUT is an invariant amendment or an input to INVARIANT-DETERMINATION-001, so the ecosystem answers the item itself next time.

**#3225/#3226 currency:** Labs main is still `bfcf0318`, so no merge was needed. #3225 is not merged, so #3226 stays on the core base. `ledger_store.py` is unchanged (blob `9c50cd20`, the same blob as Lane B's org#190).
