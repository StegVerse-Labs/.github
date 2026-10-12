# SDK-MR-A validation custody Registry reconciliation

Goal Task ID: `SDK-MR-A-VALIDATION-CUSTODY-001`
Canonical work Registry: `StegVerse-Labs/.github:data/canonical-task-registry.json`
Record projection: `data/canonical-task-records/SDK-MR-A-VALIDATION-CUSTODY-001.json`
Source issue: `StegVerse-org/StegVerse-SDK#452`
Coordination: ACTIVE; checkout: HANDOFF_READY; COSV: `60000000102010`.
Evidence class: EXTERNAL_PROVIDER_OBSERVED (source, runtime organization-ledger
readback and an attempted governance decision return; terminal class END_TO_END
not met; partial evidence). Two owner-held predicates remain.

The current state is set by the
[2026-10-11 decision-return reconciliation](#2026-10-11-decision-return-reconciliation)
at the end of this document. The
[2026-10-11 runtime reconciliation](#2026-10-11-runtime-reconciliation) and the
2026-10-10 `Status`, `Evidence` and `Continuation` sections are kept as history.

## Status (2026-10-10, superseded by the 2026-10-11 runtime reconciliation)

Superseded: as registered on 2026-10-10 (COSV `10100000100000`, ACTIVE/UNCLAIMED,
CI_VALIDATED). SOURCE/CI validation only. No runtime transition was attempted, no organization
ledger receipt exists, and runtime activation is not claimed. Master Records is
downstream evidence preservation and never gates.

## Evidence (2026-10-10 registration)

All SDK merges used expected-head protection with every check green at the head:

| PR | Validated head | Merge |
| --- | --- | --- |
| #453 | `daf78200a8b9b9a5daea05cdbd1046b58f85e9bb` | `1923a513da77cfed573e2f6594704b8508a508d2` |
| #455 | `199a53af476c435d1ad620cba0673931ec21bde0` | `aa25095396e9d1e88a3c21c8a380c272b5c5312d` |
| #456 | `b86e04fc2a9ea15a7d5fe662972d715ea3cbfb04` | `3259843d23c85dfa21fae024f2fce9beb7ea2b77` |
| #457 | `bd28589204902ed4fc7a7719ebfb2835801138b8` | `8c4d373451e9c3c5f6fa927b03b145584308f157` |
| #458 | `636136ab8b7dfdfb61d47b568dd7a531eb801224` | `8559c4700a076a733de048910344f99bedaae4ca` |

- #453: `organization_ledger_evidence.verify_organization_ledger_readback` returns
  ALLOW or a six-field FAIL_CLOSED.
- #457: the `stegverse-master-records` dependency is removed;
  `stegverse/local_run_record.py` (stdlib, non-authoritative, `authority_effect`
  NONE) replaces `services.manifest_receipt_custody`; the production release-set
  schema v2 uses role `downstream_run_evidence`; v1 is frozen and still verifiable.
- #458: docs sweep.
- SDK `data/master-records-role-audit.json` at `8559c470`: 44/44 REMEDIATED, 0 BLOCKED.
- Receiver compatibility: `StegVerse-Labs/.github#3082` merge
  `adf312bb4f9c2f071e8f65653fb80405e8b75218` accepts ORGANIZATION_LEDGER as
  canonical and MASTER_RECORDS as legacy-compat with `grants_authority` false.

## Continuation (2026-10-10, superseded by the 2026-10-11 runtime reconciliation)

Superseded: the runtime transition below has since been recorded. The next transition is a runtime transition read back as ALLOW against an
authentic organization-ledger transition receipt
(`DEP-SDK-MR-A-ORGANIZATION-LEDGER-RUNTIME-TRANSITION-RECEIPT`). Until then the
record stays ACTIVE with CI_VALIDATED partial evidence. Manual work: None.

## 2026-10-11 runtime reconciliation

This section supersedes the 2026-10-10 source-only status and continuation above.
An authentic organization-ledger transition for this task has been recorded and
read back as ALLOW. The record, the Registry entry (generation 307), the COSV task
vector and its index row now carry that evidence.

### Evidence checked for this reconciliation

Fetched anonymously from `https://github.com/StegVerse-org/.github` on 2026-10-11:

- `refs/stegverse/organization-ledger` tip
  `4e20f265fbfb727f766fc62ebafef3dfcca8ce71` (moved from `c1de41e9`). The
  organization chain, walked from `HEAD.json` through `previous_receipt_sha256`,
  has length 6.
  - Ingress receipt
    `sha256:a7f67a3ee47a017ef9df4ed6b9a50ecd44ea718bdfc4f66e4563fe1b06db5ab8`
    for `ORGANIZATION-SDK-MANIFEST-INGRESS-0d3494183d1c8a62`, the transition request
    `.stegverse/transition-requests/SDK-MR-A-ORGANIZATION-LEDGER-RECEIPT-002.json`
    (predecessor `-001`, recorded FAIL_CLOSED). Its candidate is
    `decide_terminal_custody_authority` targeting
    `SDK-MR-A-VALIDATION-CUSTODY-001`. Disposition ALLOW; the crossing is recorded
    as consumed and completed.
  - Emission head receipt
    `sha256:d0657cacbe4cd46f8805ddd7ff565bf4edca4764cbe2c3b735741cbcbfde2b55`
    (`ORGANIZATION_EGRESS_EMITTED:pkt-5efe4b0372bbffa4d2a356fe`, disposition ALLOW):
    a governance request emitted to StegVerse-Labs with decision state
    `REQUESTED_OF_DECIDING_ORGANIZATION`.
- Repository chain `repository-ledger/StegVerse-org/.github` in the same ref has
  length 4 (head
  `sha256:0bb938817895181434c8ffac68fd1bf1ab6bf31fc13f86ad357214bcfbb6623d`).
- `refs/stegverse/federation-mesh` tip
  `18b3ef3f38d10e798458aed495c77568cbe9fa76` holds one frame to StegVerse-Labs
  (`stegverse-labs.governance`): packet `pkt-5efe4b0372bbffa4d2a356fe`, frame
  `sha256:909bb21e89c7bf6d37caf19acdbf5bcdaee455f0efaec059134fef9d0b247ae1`.
- Source merges on StegVerse-org/.github `main`: #124 `6a7c2e4e`, #125 `df4086bf`,
  #126 `ca0751ee`, #127 `12ae5952`, #128 `4a59a8b3`. SDK: StegVerse-org/StegVerse-SDK#462
  `012bf2ee`.
- GitHub Actions runs in StegVerse-org/.github, workflow
  `organization-ledger-transition.yml`:
  - [38108737432](https://github.com/StegVerse-org/.github/actions/runs/38108737432):
    `workflow_dispatch` on `3278c76`; ingress ALLOW, emission ALLOW; both chains and
    the mesh read back from a fresh fetch.
  - [38108928361](https://github.com/StegVerse-org/.github/actions/runs/38108928361):
    push on `4a59a8b`; answered ALREADY_RECORDED, appended nothing, readback ALLOW.
- Issue comments: StegVerse-org/StegVerse-SDK#452 comment `6105086142`,
  StegVerse-org/.github#118 comment `6105087837`.

The ledger and mesh refs, every receipt above and the merge commits were checked by
git fetch. The Actions run pages and the issue comments could not be fetched
anonymously from the session that made this reconciliation (the API was refused
there). They are recorded as references. The receipts' own `receipt_path`
(`/home/runner/work/...`) records a GitHub-hosted runner workspace, which is
consistent with them.

### State changes

| Field | Before (2026-10-10) | After (2026-10-11) |
| --- | --- | --- |
| coordination_state | ACTIVE | ACTIVE |
| checkout_state | UNCLAIMED | HANDOFF_READY |
| COSV | `10100000100000` (UNCLAIMED, unassigned 1, not activated) | `50000000100010` (MACHINE_OWNED, unassigned 0, activated) |
| evidence_class | CI_VALIDATED | EXTERNAL_PROVIDER_OBSERVED |
| scope | SOURCE_CI_VALIDATION_ONLY | SOURCE_CI_VALIDATION_PLUS_RUNTIME_ORGANIZATION_LEDGER_READBACK |
| runtime_transition_attempted | false | true |
| organization_ledger_receipt_ref | null | ingress receipt `sha256:a7f67a3e…` |
| DEP-SDK-MR-A-ORGANIZATION-LEDGER-RUNTIME-TRANSITION-RECEIPT | UNRESOLVED | SATISFIED |
| allowed_next_transitions | RUNTIME_TRANSITION_WITH_ORGANIZATION_LEDGER_RECEIPT | STEGVERSE_LABS_GOVERNANCE_DECISION_RETURN |

Unchanged: `terminal_evidence_class` null (END_TO_END is the terminal class),
`end_to_end_complete` false, `authority_effect` NONE_COORDINATION_ONLY,
`release_authorized` false, `master_records_gates` false, `propagation_claimed`
false. `runtime_activation_claimed` is now true, scoped to
`ORGANIZATION_LEDGER_TRANSITION_AND_READBACK_ONLY` to match COSV `activated`.
The prior values are kept in the record's `reconciliation_history`.

### Evidence class

The class is `EXTERNAL_PROVIDER_OBSERVED`. The transition ran on GitHub-hosted
Actions against the real sovereign ledger ref. The result can be seen on that
provider in the run logs and in the ledger and mesh refs. It is higher than
`SANDBOX_RUNTIME_OBSERVED` because the ref is the organization's own ledger, not
a sandbox copy. It is not `MASTER_RECORDS_RECONSTRUCTED` because nothing was
reconstructed by Master Records. It is not `END_TO_END` because the deciding
organization has not returned a decision. The repository's order
(`data/task-registry-global-invariants.json`,
`scripts/validate_completion_evidence_v1.py`) puts this class directly above
`SANDBOX_RUNTIME_OBSERVED`, and no repository definition contradicts this reading.

### COSV

`50000000100010` was encoded by `scripts/cosv.py` (`encode_task`) from these
exact metrics, which are identical in the record, the Registry entry and the task
vector (`observed_at` 2026-10-11): lifecycle MACHINE_OWNED; unassigned_work 0;
blocker_count 0; canonical_owner_installed true; thread_required false; every
chat_owned_* 0; activated true; evidence_complete false; propagated false;
archive_ready false.

The checkout state is HANDOFF_READY with coordination ACTIVE. The
validators do not constrain this pairing. The Registry already pairs
ACTIVE/HANDOFF_READY with a MACHINE_OWNED vector
(`CANONICAL-MASTER-RECORDS-STATE-TRANSITION-CUSTODY-001`). UNCLAIMED would
contradict `unassigned_work` 0, and CHECKED_OUT would need an authentic current
claim.

### Remaining work (superseded by the decision-return reconciliation)

Superseded: the decision return was attempted and two owner-held predicates now
block END_TO_END (see below). As recorded at the runtime reconciliation:


The next transition is `STEGVERSE_LABS_GOVERNANCE_DECISION_RETURN`: StegVerse-Labs
returns its governance decision for frame
`sha256:909bb21e…` (packet `pkt-5efe4b0372bbffa4d2a356fe`). The receiving
organization's machine path over the federation mesh owns this step. It is not
chat work. It is recorded as remaining work with `is_blocker` false, and
`blocker_count` stays 0. Under the prohibition
`NO_DESTINATION_LIVENESS_OR_ALWAYS_ON_RECEIVER_AS_TRANSITION_PREDICATE`,
destination liveness is not a transition predicate. Master Records stays
downstream and never gates. Manual work: None.

## 2026-10-11 decision-return reconciliation

This section supersedes the remaining-work statement of the runtime
reconciliation above. The governance decision return for packet
`pkt-5efe4b0372bbffa4d2a356fe` was attempted on 2026-10-11. StegVerse-Labs
decided the request and published its answer. StegVerse-org took the answer in,
consumed it and closed the crossing. The decision itself is FAIL_CLOSED
`GOVERNANCE_RUNTIME_STEGCORE_UNAVAILABLE`, so END_TO_END is not met. Two
predicates that only the owner can satisfy remain. The record, the Registry entry
(generation 308), the COSV task vector and its index row carry this.

### Evidence checked for this reconciliation

Fetched anonymously on 2026-10-11:

- **StegVerse-Labs decision.** Run
  [38155820321](https://github.com/StegVerse-Labs/.github/actions/runs/38155820321),
  workflow `organization-governance-decision.yml` on `8ca1db37` (#3104
  `f3ee5047`, #3105 `8ca1db37`), concluded success.
  - The answer was read back from `refs/stegverse/federation-mesh` of
    `https://github.com/StegVerse-Labs/.github`, tip
    `77bbe5f855d1c96417f46ff311b1b709175193ac`.
  - Frame key:
    `frames.d/4cafedc4844d4139f17d914036b3686e1d9f0ab1b237e42d2df8e7884e450006.json`.
    The key recomputes from the frame.
  - frame_sha256:
    `sha256:1ee814a89a04e7dc2102c9446f62098dd3f1ffc6686b33163246b5765d5b0ee2`.
  - packet_id:
    `governance:0d3494183d1c8a62ff5ab3408b34302e82a92a7fb75e48587edfedbc51013763:response:stegverse-labs`.
  - It recovers with `org-kernel/kernel.py::recover_packet`. It is an
    `ecosystem.work.ack` to StegVerse-org, with `body.request_packet_id`
    `pkt-5efe4b0372bbffa4d2a356fe`.
  - The decision is FAIL_CLOSED `GOVERNANCE_RUNTIME_STEGCORE_UNAVAILABLE`.
  - Labs repository receipt
    `sha256:0e654f7a4fa00377e32f8bd027ce6a6c3ae662984db70f0d4b6625f40053b526`.
    Labs organization receipt
    `sha256:33d13cd8e9605000613e73b2a899ad0c0523012c263a157bb3f2bece953c5ef5`.
    These are the same digests the run's evidence artifact reports.
  - The run's report states `ledger_persistence:
    EXECUTION_SCOPED_PROPAGATE_TARGET_NULL`. These are real appends to run-scoped
    ledgers, and by the approved declaration they are published nowhere.
- **StegVerse-org return**, read from `https://github.com/StegVerse-org/.github`:
  - `refs/stegverse/organization-ledger` moved from `4e20f265` to
    `3e16f5a807e33c1e91639712aaf68a0de99e5f2b`, a fast-forward. The organization
    chain has length 8. Its `HEAD.json` is the closure receipt
    `sha256:ccefb8f885f29c22c18b4b51895ee30561199f907f22547241d4560108c202c0`,
    with `repo_transition_id`
    `ORGANIZATION_EGRESS_CLOSED:pkt-5efe4b0372bbffa4d2a356fe` and boundary
    disposition ALLOW.
  - The repository chain has length 6, head
    `sha256:b97f168bd62d507a10e68816478187f2709b254a61cac71ef3e1019a447c80c7`.
    Its last three classes are `ORGANIZATION_EGRESS_EMITTED`,
    `ORGANIZATION_FEDERATION_CROSSING_CONSUMED` and `ORGANIZATION_EGRESS_CLOSED`.
  - `refs/stegverse/federation-mesh` moved from `18b3ef3f` to
    `7a093db9070ebf5b74c3654cf4a6d97d651b81a1`, a fast-forward. It holds the
    request frame and an answer frame byte-identical to the StegVerse-Labs one.
  - `main` is `a1b2ebe5`, the merge of StegVerse-org/.github#129, which added
    `organization-governance-return.yml`.
- **SDK acceptance verifier.** StegVerse-org/StegVerse-SDK `main` is
  `e8a34b6d`, the merge of #466, and carries
  `stegverse/governance_return_evidence.py`. It checks
  `GOVERNANCE_DECISION_IS_A_DECISION` (ALLOW or DENY only) before
  `DECIDING_ORGANIZATION_RECEIPT_READ_BACK`, so it fails at the first of these on
  a FAIL_CLOSED decision.

Recorded as references, not fetched here: the StegVerse-org run
[38155889110](https://github.com/StegVerse-org/.github/actions/runs/38155889110)
and its return readback (return ALLOW, `decision_returned` true). The verifier's
result on that readback is also a reference (FAIL_CLOSED, `failed_predicate`
`GOVERNANCE_DECISION_IS_A_DECISION`). The GitHub API for StegVerse-org
repositories was refused from this session. The ledger evidence above matches
them: the closure receipt is ALLOW and it is at the head of the sender's chain.

### In-progress source repair (not evidence)

A local rehearsal by the parent session is non-authoritative and is not recorded
as evidence. It used StegCore 0.3.0 (StegVerse-Labs/StegCore `9882851b`).
- The emitted governance request fails `AdmissibilityRequest` validation:
  `signal.uncertainty_state` is `"known"`, and StegCore accepts only `bounded`,
  `material` or `unknown`.
- With `"bounded"`, StegCore decides DENY `signal.inputs_incomplete`.
- The request is being repaired as `SDK-MR-A-ORGANIZATION-LEDGER-RECEIPT-003` in
  StegVerse-org/.github. The record carries it under
  `completion.in_progress_source_repairs`.

### Outstanding end-to-end predicates (owner-held)

Both predicates are recorded as six-field FAIL_CLOSED blockers with
`decision_owner: REGISTRY_OWNER`. Each points at a `HUMAN_ACTION` dependency in
state `UNRESOLVED_OWNER_DECISION`.

| Field | a. Governance decision | b. Deciding-organization receipt |
| --- | --- | --- |
| failure_code | `END_TO_END_REQUIRES_A_VERIFIED_GOVERNANCE_DECISION_RETURN` | `END_TO_END_REQUIRES_A_VERIFIED_GOVERNANCE_DECISION_RETURN` |
| failed_predicate | `GOVERNANCE_DECISION_IS_A_DECISION` | `DECIDING_ORGANIZATION_RECEIPT_READ_BACK` |
| required_evidence_or_repair | An ALLOW or DENY from StegCore. The owner decides how the Labs decision run gets read access to the private StegVerse-Labs/StegCore: a read-only credential for the decision workflow, or StegCore readability. The request repair `-003` is also needed. | The Labs organization receipt read back from an independent fresh fetch. The owner designates a private-custody `propagate_target` for the Labs organization ledger. It is null by the TVC#488 approval and is never invented. |
| retry_entrypoint | `StegVerse-Labs/.github:.github/workflows/organization-governance-decision.yml`, then `StegVerse-org/.github:.github/workflows/organization-governance-return.yml` | `stegverse/governance_return_evidence.py::verify_governance_decision_return` |
| owning_existing_goal | `SDK-MR-A-VALIDATION-CUSTODY-001` | `SDK-MR-A-VALIDATION-CUSTODY-001` |
| next_attempt | `STEGVERSE_LABS_GOVERNANCE_DECISION_RETURN` retry once StegCore is importable by the decision run and `-003` is emitted | `STEGVERSE_LABS_GOVERNANCE_DECISION_RETURN` retry once the owner designates the `propagate_target` |

### State changes

| Field | Before (runtime reconciliation) | After (decision-return reconciliation) |
| --- | --- | --- |
| coordination_state | ACTIVE | ACTIVE |
| checkout_state | HANDOFF_READY | HANDOFF_READY |
| COSV | `50000000100010` (MACHINE_OWNED, 0 blockers) | `60000000102010` (BLOCKED, 2 blockers) |
| evidence_class | EXTERNAL_PROVIDER_OBSERVED | EXTERNAL_PROVIDER_OBSERVED |
| scope | SOURCE_CI_VALIDATION_PLUS_RUNTIME_ORGANIZATION_LEDGER_READBACK | SOURCE_CI_VALIDATION_PLUS_RUNTIME_ORGANIZATION_LEDGER_READBACK_PLUS_DECISION_RETURN_ATTEMPT |
| blockers | none | the two owner-held predicates above |
| DEP-SDK-MR-A-STEGVERSE-LABS-GOVERNANCE-DECISION-RETURN | (absent) | ATTEMPTED_DISPOSITION_FAIL_CLOSED |
| DEP-SDK-MR-A-LABS-DECISION-STEGCORE-READ-ACCESS | (absent) | UNRESOLVED_OWNER_DECISION |
| DEP-SDK-MR-A-LABS-ORGANIZATION-LEDGER-PROPAGATE-TARGET | (absent) | UNRESOLVED_OWNER_DECISION |
| Earlier dependencies | SATISFIED_MERGED_VALIDATED; SATISFIED | unchanged |
| remaining_work.is_blocker | false | true (held by the owner) |
| allowed_next_transitions | STEGVERSE_LABS_GOVERNANCE_DECISION_RETURN, REOPENED_DUE_TO_NEW_EVIDENCE | unchanged; the decision return is now a retry |

Unchanged:
- `terminal_evidence_class` null (END_TO_END is the terminal class).
- `end_to_end_complete` false.
- `authority_effect` NONE_COORDINATION_ONLY.
- `release_authorized` false.
- `master_records_gates` false.
- `propagation_claimed` false.

The prior values are kept in the record's `reconciliation_history`.

### Lifecycle and checkout choice

The COSV lifecycle digit is BLOCKED (6), with `blocker_count` 2:
- The next transition cannot proceed on the machine path until the owner acts.
  MACHINE_OWNED would claim that it can.
- `unassigned_work` stays 0 and every `chat_owned_*` stays 0. The held work is
  the owner's decision, not unassigned or chat-owned work.
- `activated` stays true, and `evidence_complete` and `propagated` stay false.
- The vector was encoded by `scripts/cosv.py` (`encode_task`) from exact metrics
  that are identical in the record, the Registry entry and the task vector.

`coordination_state` stays ACTIVE and is not BLOCKED:
- `tests/test_canonical_task_active_state_policy.py` forbids a BLOCKED
  coordination state.
- `control/active-worker-state-policy.json` requires a held constraint to name
  its successor or escalation. Here those are the decision-return retry and the
  owner decision.

`checkout_state` stays HANDOFF_READY:
- No worker holds a claim. CHECKED_OUT would need an authentic WorkerCoordinator
  claim and fence.
- UNCLAIMED would contradict `unassigned_work` 0.
- The Registry has no owner-held checkout value. The owner-held condition is
  carried by the blockers' `decision_owner` instead, following the
  `REGISTRY_OWNER` blockers of `STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001`.
- The other BLOCKED-digit tasks in the Registry are CHECKED_OUT because they have
  live claims, which this task does not.

### Next transition

`STEGVERSE_LABS_GOVERNANCE_DECISION_RETURN`, retried once predicates a and b
hold:
1. Emit the repaired request (`-003`).
2. Dispatch the StegVerse-Labs decision workflow with the StegVerse-org mesh
   locator.
3. Return the answer through `organization-governance-return.yml`.
4. Verify it with `verify_governance_decision_return` against a fresh readback
   of both organizations' ledgers.

Destination liveness is still not a transition predicate, and Master Records
stays downstream and never gates.

### Update: request repair done, decision run can install StegCore

- 2026-10-11: the request repair is done. `SDK-MR-A-ORGANIZATION-LEDGER-RECEIPT-004`
  was received under the post-migration StegVerse-SDK `e8a34b6d`, so the custody
  authority is ORGANIZATION_LEDGER (StegVerse-org/.github#132, merge `cdfeb65e`).
  Dispatch run
  [38161387492](https://github.com/StegVerse-org/.github/actions/runs/38161387492)
  recorded ingress `sha256:ddef834bbf3bee2b94802cbdfe0c2443c6bf8ced4b6972283059673aa6ab142e`
  (bound to canonical manifest `df97554a8eec79a2110885100082f0ab201011fda87d07e75b9ca8551428ba98`)
  and emission `sha256:7470eaf423cb427612c702c04f5ceacf78bfb7407a0520e82d2997116befa001`.
  Packet `pkt-c64077b3c2b188aabf176050` is durably queued on StegVerse-org
  `refs/stegverse/federation-mesh` `91b88b5fa6bb338756d203046f38d493f9bda91c`;
  the ledger is `refs/stegverse/organization-ledger`
  `ff5ae361769e8f3451c425edac5ef3953fd04cca`. Both refs were read back by an
  anonymous fetch. StegVerse-Labs/.github#3114 (merge `aeb3fad4`) makes
  `organization-governance-decision.yml` install StegCore at the pinned `9882851b`
  when the `STEGCORE_READ_TOKEN` secret exists. The only remaining owner action
  for `GOVERNANCE_DECISION_IS_A_DECISION` is that secret (read-only, Contents:
  read on StegVerse-Labs/StegCore). Step 1 of the next transition is done; the
  decision workflow answers the queued `-004` frame. Both owner-held blockers and
  `end_to_end_complete` false are kept. Registry generation 310; COSV unchanged.

## 2026-10-12 verified decision return

`end_to_end_complete` is true. Registry generation 313; COSV `60000000102010` ->
`71000000100110` (COMPLETE, archive-ready, 0 blockers, evidence complete,
activated, not propagated), encoded by `scripts/cosv.py` (`encode_task`) from
exact metrics identical in the record, the Registry entry and the task vector.
`coordination_state` RETIRED, `checkout_state` COMPLETED_VALIDATED; the only
next transition is `REOPENED_DUE_TO_NEW_EVIDENCE`.

Both owner-held predicates were decided by the owner and implemented:

- `DEP-SDK-MR-A-LABS-DECISION-STEGCORE-READ-ACCESS`: StegCore is public; the
  decision run fetches `9882851b` anonymously and installs it only from that
  checkout (#3150 merge `468340ba`, #3151 merge `b1a63a04`).
- `DEP-SDK-MR-A-LABS-ORGANIZATION-LEDGER-PROPAGATE-TARGET`: this repository's
  `refs/stegverse/organization-ledger`, in StegVerse-org's location structure
  (#3142 merge `e3b93be4`).

Runtime evidence:

1. StegVerse-Labs decision run [38196127077](https://github.com/StegVerse-Labs/.github/actions/runs/38196127077) (success, 14/14 steps) on `b1a63a04`:
   StegCore 0.3.0 at `9882851b` decided `-004` `pkt-c64077b3c2b188aabf176050`
   and `-003` `pkt-e409e211d3bbab312bee4ad8`, both DENY
   `signal.inputs_incomplete`. Ledger `9f0a53e5` (4 receipts; `-004` decision
   receipt `sha256:273ffa70d766e003d7c649d4b7b5fd83c95a532f58c0c79fd13bf5617ca094da`)
   and mesh `f1b23e5e` (2 answer frames) were published and read back ALLOW from
   an independent fresh fetch.
2. StegVerse-org return run
   [38196229848](https://github.com/StegVerse-org/.github/actions/runs/38196229848)
   (default SDK, `deciding_ledger` set): `-004` returned and closed
   (`ORGANIZATION_EGRESS_CLOSED` `sha256:f3156e28ee4aa4fdcd4af475dbd21aaea56d5f0c1d151187583f5ca97ba85c4b`,
   ledger `6312057c`, readback ALLOW chain 15); `acceptance.json`:
   `end_to_end_acceptance` `["pkt-c64077b3c2b188aabf176050"]`, verifier
   `stegverse/governance_return_evidence.py` from the pinned SDK checkout. The
   run concludes failure only because `-003` does not reproduce under this SDK;
   that refusal appends nothing.
3. StegVerse-org return run
   [38196303110](https://github.com/StegVerse-org/.github/actions/runs/38196303110)
   (`sdk_ref` `657576e6`): `-003` returned and closed
   (`sha256:abddfbd65d2bc434d2dd284f44aac211ae96219b4bcf053d5f8326b21161ceb7`,
   ledger `ab3cbc14`, readback ALLOW chain 16) and accepted end to end. No
   closure is duplicated: the ledger holds exactly one `ORGANIZATION_EGRESS_CLOSED`
   each for `-002`, `-003` and `-004`.

The governance outcome is DENY. END_TO_END means the request was decided by
the receiving organization's authority and that decision was returned and
verified; it does not mean the requested action was approved. `-002`'s
write-once FAIL_CLOSED answer is kept and not reopened. Master Records stays
downstream and never gates; destination liveness was never a predicate.
