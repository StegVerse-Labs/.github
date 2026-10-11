# SDK-MR-A validation custody Registry reconciliation

Goal Task ID: `SDK-MR-A-VALIDATION-CUSTODY-001`
Canonical work Registry: `StegVerse-Labs/.github:data/canonical-task-registry.json`
Record projection: `data/canonical-task-records/SDK-MR-A-VALIDATION-CUSTODY-001.json`
Source issue: `StegVerse-org/StegVerse-SDK#452`
Coordination: ACTIVE; checkout: HANDOFF_READY; COSV: `50000000100010`.
Evidence class: EXTERNAL_PROVIDER_OBSERVED (source plus runtime organization-ledger
readback; terminal class END_TO_END not met; partial evidence).

The current state is set by the
[2026-10-11 runtime reconciliation](#2026-10-11-runtime-reconciliation) below.
The `Status`, `Evidence` and `Continuation` sections that follow it are the
2026-10-10 source-only registration, kept as history.

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

### Remaining work (not a blocker)

The next transition is `STEGVERSE_LABS_GOVERNANCE_DECISION_RETURN`: StegVerse-Labs
returns its governance decision for frame
`sha256:909bb21e…` (packet `pkt-5efe4b0372bbffa4d2a356fe`). The receiving
organization's machine path over the federation mesh owns this step. It is not
chat work. It is recorded as remaining work with `is_blocker` false, and
`blocker_count` stays 0. Under the prohibition
`NO_DESTINATION_LIVENESS_OR_ALWAYS_ON_RECEIVER_AS_TRANSITION_PREDICATE`,
destination liveness is not a transition predicate. Master Records stays
downstream and never gates. Manual work: None.
