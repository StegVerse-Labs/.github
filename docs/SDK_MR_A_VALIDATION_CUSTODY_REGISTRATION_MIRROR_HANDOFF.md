# SDK-MR-A validation custody Registry reconciliation

Goal Task ID: `SDK-MR-A-VALIDATION-CUSTODY-001`
Canonical work Registry: `StegVerse-Labs/.github:data/canonical-task-registry.json`
Record projection: `data/canonical-task-records/SDK-MR-A-VALIDATION-CUSTODY-001.json`
Source issue: `StegVerse-org/StegVerse-SDK#452`
Coordination: ACTIVE; checkout: UNCLAIMED; COSV: `10100000100000`.
Evidence class: CI_VALIDATED source scope (no terminal class; partial evidence).

## Status

SOURCE/CI validation only. No runtime transition was attempted, no organization
ledger receipt exists, and runtime activation is not claimed. Master Records is
downstream evidence preservation and never gates.

## Evidence

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

## Continuation

The next transition is a runtime transition read back as ALLOW against an
authentic organization-ledger transition receipt
(`DEP-SDK-MR-A-ORGANIZATION-LEDGER-RUNTIME-TRANSITION-RECEIPT`). Until then the
record stays ACTIVE with CI_VALIDATED partial evidence. Manual work: None.

## 2026-10-11 successor evidence reconciliation (pending authenticated verification)

Claude's [SDK #452 report](https://github.com/StegVerse-org/StegVerse-SDK/issues/452#issuecomment-6105086142) reports a distinct `SDK-MR-A-ORGANIZATION-LEDGER-RECEIPT-002` ALLOW in [run 38108737432](https://github.com/StegVerse-org/.github/actions/runs/38108737432), organization ledger tip `4e20f265fbfb727f766fc62ebafef3dfcca8ce71`, ingress `sha256:a7f67a3ee47a017ef9df4ed6b9a50ecd44ea718bdfc4f66e4563fe1b06db5ab8`, emission `sha256:d0657cacbe4cd46f8805ddd7ff565bf4edca4764cbe2c3b735741cbcbfde2b55`, and federation mesh tip `18b3ef3f38d10e798458aed495c77568cbe9fa76`. Claude reports independent readback and PRs #127/#128 merged. This entry records **reported evidence**, not a fresh authenticated readback by this reconciliation. Do not overwrite the historical source-only evidence or mark a terminal COSV state until the sovereign refs, exact manifest binding, and chain are independently verified and Registry authority allows promotion. No runtime transition was attempted by this reconciliation. Master Records remains downstream and non-gating.
