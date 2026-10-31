# Independent InTr strict replay — 2026-10-29

Goal: `INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001`.
Evidence class: independently executed read-only verification of historical
public-ledger receipts. Authority effect: NONE.

On Org source `0b50df09f620304319f99de58af081aa8902c37e`, the committed kit
check exits 0: 156 records verified, all DESTINATION_RECEIPT_LEDGERED, no
problems. Native strict replay exits 0: **156 ALLOW, 0 DENY, 0 FAIL_CLOSED**,
with `e0_terminal=true`. Source files were not changed before execution.

- [Raw replay output](pg_replay.json) includes the 13 exact public ledger
  commits, each path's linked receipt identities, and native record seal.
- [Kit check](pg_check.json) retains the native check output.
- [Comparison](verification.json) retains source pins and output hashes.
- Comparison source: [TVC's committed replay](https://github.com/StegVerse-Labs/TVC/blob/e2ebde781f8e8cb77dd827519fc0db65bd2aa3ab/evidence/intr-readback-2026-10-29/post-genesis-replay/pg_replay.json).

All 156 complete per-path objects, counts and other result fields match the
published output. The two raw files do **not** have the same hash. The published
output inventories an additional `master-records` public ledger, outside the
13 organizations and 156 paths declared by this kit. This independent run
fetched precisely the native `orgs` list. The sole differences are that extra
tip and the resulting record seal. Removing that unused tip from a comparison
copy and recomputing the native canonical seal reproduces this run's seal.
Neither retained output has been edited to hide the difference.

Reproduction, from the pinned Org checkout, with git and Python only:

```sh
python3 scripts/intr_post_genesis_replay.py orgs
python3 scripts/intr_post_genesis_replay.py check
# Anonymously fetch refs/stegverse/organization-ledger from each listed
# organization's public .github into <public-ledgers>/<Organization>.git.
# Use bare repositories, credential.helper= and no GitHub extraheader.
python3 scripts/intr_post_genesis_replay.py replay \
  --public-ledgers <public-ledgers> --require-ledgered-allow --out pg_replay.json
```

The fetched refs were read-only local copies. No new receipt, transition,
Registry admission, WorkerCoordinator claim/fence, private warrant, sovereign
KV write, external conformance or release was created. Duplicate-receipt
selection policy remains with Org #162. Integration and canonical task
disposition remain with the existing owners named in the
[handoff](../../INTERLOCK_INTR_RUNTIME_INDEPENDENT_PROTOCOL_MIRROR_HANDOFF.md).
