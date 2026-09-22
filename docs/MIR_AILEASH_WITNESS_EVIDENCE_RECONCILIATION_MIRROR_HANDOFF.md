# MIR / AILeash witness evidence reconciliation mirror handoff

Updated: 2026-09-19
Goal Task ID: `MIR-AILEASH-WITNESS-EVIDENCE-RECONCILIATION-001`
Parent Task ID: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV ID: `50000000100000`
Status: `ACTIVE / APPENDIX A R4 BEHAVIOR INDEPENDENTLY REPRODUCED / V0.7 USER-SUPPLIED SHARED ARTIFACT REVIEWED / V0.8 COUNTERPART RUN REPORT OBSERVED / SUBMITTER-REMOVED RUN CLAIMED COMPLETE BUT ARTIFACT NOT YET INDEPENDENTLY RETRIEVED / PER-ROW EVIDENCE CLASS PRESENT / A.2 R10 BASIS NARROWED / A.1 R2 LIMITATION EXPLICIT / SEBBI R10 PORTABILITY GAP SOURCE-INSPECTED / HISTORICAL V1.1 VOCABULARY AND SCHEME SOURCE RECOVERED / BLOB-COMMIT MISCLASSIFICATION CORRECTED / OTS PROOF RETAINED PENDING`

## Goal

Reconcile prior AILeash/sebbi.pro observations with the current Evidence Custody Seam Appendix A claims and Justin Dobson witness-topology contribution while preserving strict evidence-status boundaries.

## Current truth

The canonical prior observations remain unchanged:

- exact unauthenticated witness-attest behavior for one `flavorflowstrategy.uk` peer/tip is independently reproduced;
- the retained pending OTS artifact is byte/hash consistent but not Bitcoin-confirmed;
- identity, current liveness, control/failure-domain independence, and complete topology remain unpromoted beyond the evidence actually retained.

## v0.7 joint-review state

The user supplied the complete Evidence Custody Seam v0.7 joint-review text. The artifact repaired the v0.6 presentation defect by carrying an evidence class on every Appendix A row: `Operator-disclosed`, `Demonstrated`, or `Third-party checkable`.

For A.2 R10, v0.7 correctly narrows the independently supported mechanism to the artifact condition: historical sealed records do not self-carry the field-meaning statement, while the full `NOT MET` remains operator-disclosed pending the historical R6-linked publication question.

For A.1 R2, v0.7 explicitly marks the row `Operator-disclosed` because the prior Section 5 run joined external time to the same sequence tip but did not walk the chain end to end; an outside attempt was indeterminate because of pagination.

The open questions after v0.7 were:

1. whether a durable vocabulary publication tied to the R6 scheme covered the historical commitments before the rename;
2. whether `custodian` collides with a privacy-regime term in a way the document's definition/non-claims do not already resolve;
3. whether an authentic submitter-removed rerun of the Section 5 test exists.

## Evidence Custody Seam v0.8 — user-retained counterpart report observed

The user supplied review-thread screenshots in which Richard Whitney states that v0.8 is published and that the previously intended submitter-removed run now exists.

Richard reports that the run used a live production export and produced these results:

- one artifact containing 1,534 events and 50 checkpoints;
- 48 checkpoints reported as Bitcoin-anchored;
- 1,406 events reported as falling under an anchored checkpoint;
- an OpenTimestamps proof for checkpoint 4714 reported as committing, when read offline, to the exact sequence tip carried inside the bundle;
- two independently operated explorers reported as confirming the block Merkle root;
- all 1,534 leaf hashes reported as recomputed and all 1,534 inclusion proofs reported as reaching their roots;
- chain links reported unbroken;
- the verification key reported fetched from a different endpoint than the bundle and pinned before use;
- zero socket-family syscalls reported across three runs;
- a maximum observed gap of 233 ms between a production submitter's claimed `occurredAt` and the custodian receipt, while claimed ordering still differed from proof-derived ordering;
- an adversarial local case with two submitters, one adversarial, claims displaced by 2,453 days and asserted in the exact reverse of sealing order, with proof-derived order returning the reverse of the claimed order;
- negative controls reported fail-closed when editing the submitter's claim, editing a weight, or substituting a valid but unpinned key;
- ordering reported as derived from checkpoint-chain position plus each leaf's index inside its own tree, not from any party-provided date field.

Richard also records three corrections to his own analysis:

1. an initial within-checkpoint sort by `createdAt` was wrong because that substituted the custodian's receipt time for proof-derived position; he reports correcting the analysis to derive position from the proof path before counted runs;
2. syscall traces were miscounted twice by treating signal lines as syscalls; he reports the corrected socket-family count as zero for every run;
3. R5 was understated in the appendix, because refusing a bundle-carried key is an artifact construction property rather than merely a runtime check.

### Evidence classification for v0.8

These v0.8 statements are presently classified as `USER_RETAINED_COUNTERPART_COMMUNICATION`.

The screenshots materially supersede the earlier `rerun intended` statement as a counterpart claim: Richard now says the submitter-removed rerun exists. However, no matching public run artifact, bundle, proof package, or repository-bound result containing the reported 1,534-event / 50-checkpoint / checkpoint-4714 evidence was independently located in the inspected public GitHub source.

Therefore:

- do not continue to describe the rerun as merely intended;
- do describe it as `COUNTERPART_REPORTED_COMPLETE`;
- do not promote the reported run statistics, Bitcoin-anchor checks, offline OTS binding, chain walk, syscall trace, negative controls, or order reconstruction to independently verified until the underlying artifacts are retrievable and checked;
- preserve Richard's explicit self-corrections as part of the run record rather than smoothing them away.

## R6-linked historical publication inspection — corrected 2026-09-19

Current-main recovery originally used `dccf6638510fe5907cef614a45a9ac33f6ae6eab`, Task Registry generation 67. This continuation re-read canonical main at `67d082eb648a65f4b1a3dc61b639354de7c3b933`, Task Registry generation 70, and the canonical child record, which remains ACTIVE with COSV `50000000100000`. This is documentary/source reconciliation; no runtime, custody receipt, or conformance completion is asserted.

### Corrected object identity

The earlier inspection treated `f824ac83c5843053bdeca7eba53b77afa99465f5` as a commit ref and described the historical source as unavailable. That conclusion was incorrect: it is the Git **blob SHA** of witness v1.4, retrievable through the [Git blob endpoint](https://api.github.com/repos/justrightdecorators-ops/aileash/git/blobs/f824ac83c5843053bdeca7eba53b77afa99465f5) and through [modules/witness.py at commit 4c78cdff](https://github.com/justrightdecorators-ops/aileash/blob/4c78cdff5695d5f1ff8b141f2f3befc45dce1bbe/modules/witness.py). Failure to resolve a blob as a commit is not publication loss.

### Recovered historical source

| Source revision | Witness version / blob | Independently inspected fact |
|---|---|---|
| `2d6715868bb2812b98d874ab17890ff89ece30d5` | v1.1 / `e6093a954837a418ceef99e6e474bcd61c59704f` | Docstring defines `confirmed` as endpoint/submitted-tip equality; `_check_liveness` implements that check; `_peers` emits its meaning in a legend. |
| `2cac24a11ceeef32e9d347b8915922dbe696b204` | v1.2 / `9b4c26efa7566288969c562c35ade937e3162310` | Source explains the rename to `self-consistent`, preserves the legacy `confirmed` value, and reconciles both meanings. |
| `4c78cdff5695d5f1ff8b141f2f3befc45dce1bbe` | v1.4 / `f824ac83c5843053bdeca7eba53b77afa99465f5` | Later vocabulary attachment and witness-specific spec route remain inspectable. |

The [v1.1 vocabulary source](https://github.com/justrightdecorators-ops/aileash/blob/2d6715868bb2812b98d874ab17890ff89ece30d5/modules/witness.py) is retained in the same Git revision as [server.py](https://github.com/justrightdecorators-ops/aileash/blob/2d6715868bb2812b98d874ab17890ff89ece30d5/server.py), blob `99718aa051dc09448ade1a6700abc738ebc38a13`. The latter publishes the chain hash shape and implements `sha`, `seal`, and `verify_chain`: SHA-256 over sorted-key JSON containing `prev_hash`, `ts`, `event`, and `result`. The witness payload passes its version, liveness and name-status values to the supplied seal function, without embedding the vocabulary definitions.

The same revision's [modules/spec.py](https://github.com/justrightdecorators-ops/aileash/blob/2d6715868bb2812b98d874ab17890ff89ece30d5/modules/spec.py), blob `982e37b001dcdcad48ed12d9e78804f2ea88e0a1`, contains an existing generic spec/discovery surface and describes all modules sealing into one chain. Its discovery routine extracts summaries, endpoint lines and versions; it does not export the complete vocabulary docstring.

### Bound conclusion

Historical vocabulary and commitment-scheme implementation are now independently retrievable together at a pre-rename source revision. The witness-specific `/x/witness/spec` route arriving in v1.3 therefore cannot establish that vocabulary publication began in v1.3. This corrects the earlier inference of a historical publication gap; it does not erase the source-inspected artifact-portability gap.

Appendix A.2 R10 `NOT MET` remains **operator-disclosed**, with the recovered v1.1 source as material evidence requiring reconciliation before any independent MUST-failure verdict. Do not promote either blanket failure or blanket compliance: the exact disputed commitments, their sealing/version interval, and their binding to this retained scheme/vocabulary revision have not been established. Git commit metadata alone is not an external-time proof of when a source revision was publicly available.

Next R6 action: bind the actual disputed historical commitment(s) to the applicable v1.1 scheme/vocabulary source and inspect any operator answer against that concrete publication path. Do not reopen normative R1–R10 or custodian naming.

## Naming resolution

Canonical StegVerse usage supports `custodian`. Existing architecture uses `historical custodian` and `personal-record custodian` while keeping custody separate from governance, admission, transition, credential, and interpretation authority. No specific privacy-regime collision has been established in the supplied materials.

## Evidence map

Canonical evidence map: `docs/mir-reference-architecture/AILEASH_SEBBI_WITNESS_EVIDENCE_MAP.md`.

## Next action

Retrieve the authentic v0.8 submitter-removed run artifacts if Richard/MIRegistry publishes or shares them: the production export bundle, checkpoint-chain material, checkpoint 4714 OpenTimestamps proof, inclusion proofs, pinned key record, explorer evidence, syscall traces, adversarial fixtures, and negative-control results. Recompute the run claims independently before promoting any row from counterpart-reported/demonstrated to third-party-checkable or independently established.

Separately, preserve the unresolved historical A.2 R10 publication question until Justin's answer or an independently retrievable historical publication record resolves it.

## Session continuation record — 2026-09-19

Session Prompt Count: 1. Goal Prompt Count: 5/20 from the supplied recovery count of 4/20; no later cumulative counter was present in the inspected child record or handoff. PR #2119 already contains a counterpart report of a 1,534-event / 50-checkpoint rerun; this session preserves that existing PR provenance without claiming to have independently inspected its underlying screenshots or run artifacts. No matching authentic rerun bundle was retrieved, and no rerun was executed. The 784-record / 30-commitment run remains historical only. No message was sent to a counterpart.

## Targeted artifact acquisition — 2026-09-19, Session Prompt 2 / Goal Prompt 6

The child remains ACTIVE. Registry generation 67 was re-read before inspection; main subsequently advanced from the prior merge to `0470412d1745391c42cd9904ec323424d4df0606`, whose registry was re-read and verified at generation 68 before the documentation update. No historical commitment was substituted with a current witness tip, and no run was synthesized or executed.

### Retrieval observations

- The public [sebbi.pro witness roster](https://sebbi.pro/x/witness/peers) was independently readable and exposes MIR's bound URL as `https://mir.events/v1/transparency/tip`. This establishes a retrieval locator, not historical commitment coverage or rerun verification.
- The ordinary web reader did not retrieve MIR's home/tip or sebbi.pro's requested historical peer route. Browser navigation to MIR's home and `/x/witness/history?peer=red-flag-ai-pro` returned `net::ERR_BLOCKED_BY_CLIENT`. This is a retrieval limitation in this environment; no service-down, bot-block, missing-evidence, or failed-runtime conclusion follows.
- Published AILeash source at `b119e2d91cd37a4929d2c69367fcba51cb7a292f` explicitly marks [full audit block reads](https://github.com/justrightdecorators-ops/aileash/blob/b119e2d91cd37a4929d2c69367fcba51cb7a292f/modules/blocks.py) as keyed with an empty PUBLIC set. [Evidence-pack preview](https://github.com/justrightdecorators-ops/aileash/blob/b119e2d91cd37a4929d2c69367fcba51cb7a292f/modules/pack.py) is also keyed; only its spec is public. No credentials were requested or access controls bypassed.
- Focused public GitHub searches under `MIR-2025` for `1534`, `4714`, and `clean-room` returned no matches. The inspected `MIR-2025/mirprotocol` tree `d8bd04d1e7cd956ef1f7fdf294adad78dc39893e` contains protocol/SDK conformance fixtures, not the reported production export package. Search absence does not establish that the package does not exist.

### Exact inputs that make the next verification executable

| Lane | Authentic artifact needed | Check to perform after acquisition |
|---|---|---|
| Historical A.2 R10 | Operator-selected disputed pre-rename sealed block(s), preserving original event, result, timestamp, previous hash and audit hash; block/sequence identity, witness version and source/export provenance; the applicable historical vocabulary/scheme publication reference and any retained timing evidence | Recompute the original seal using the recovered scheme; inspect the sealed version/term; bind that exact record to revision `2d6715868bb2812b98d874ab17890ff89ece30d5` or the actually applicable historical revision. Separate semantic agreement from evidence of publication coverage at sealing. |
| Reported v0.8 rerun | Original 1,534-event / 50-checkpoint export bundle, bundle digest, checkpoint chain and inclusion paths, checkpoint 4714 raw OTS proof, independently obtained/pinned public-key record, verifier source/version and invocation, raw traces for all three runs, adversarial fixtures and negative-control outputs, and retained Bitcoin/explorer references | Check artifact identity before counting; recompute leaves, inclusion, chain continuity, proof-derived order and key pinning; independently check the OTS/Bitcoin path and negative controls. Reproduce offline verification only from these authentic inputs. |

User action if those artifacts are not publicly retrievable: attach the operator-provided historical block export and the original v0.8 verification package, or supply their exact downloadable links and separately obtained public-key fingerprint/provenance. Do not provide passwords, API keys or private signing keys. Sending a request to Richard/Justin has not been authorized or performed.

R10 remains operator-disclosed NOT MET; no independent failure or compliance verdict is promoted. The 784-record / 30-commitment run remains historical only; the newer rerun remains COUNTERPART_REPORTED_COMPLETE. Normative R1–R10 and custodian naming remain settled. The next step is artifact acquisition at the recorded locators or from the operator, followed by the table's exact checks; repeating broad searches or re-reading the same source does not advance either predicate.


## Generation 70 commitment-binding / rerun artifact reconciliation — 2026-09-19

Canonical main was re-read at `67d082eb648a65f4b1a3dc61b639354de7c3b933`; Task Registry generation is `70`, and `MIR-AILEASH-WITNESS-EVIDENCE-RECONCILIATION-001` remains `ACTIVE` with COSV `50000000100000`.

The recovered v1.1 source tree at `2d6715868bb2812b98d874ab17890ff89ece30d5` was inspected as a complete Git tree. It contains the witness vocabulary/legend source (`modules/witness.py`, blob `e6093a954837a418ceef99e6e474bcd61c59704f`), the chain hash/seal/verification implementation (`server.py`, blob `99718aa051dc09448ade1a6700abc738ebc38a13`), and generic spec/discovery source, but no retained historical sealed-block/export corpus from which a disputed commitment can be authenticated and tied to that revision. Therefore the recovered source revision is a valid semantic/scheme publication candidate, not by itself proof that any specific disputed historical commitment was covered by that publication when sealed.

A fresh public GitHub search for the reported v0.8 identifiers and statistics (`1534`, `50 checkpoints`, checkpoint `4714`, `1406`, the `2453-day` adversarial displacement, plus the reported historical-run counts) did not retrieve an authentic production export bundle, checkpoint-chain package, raw OTS proof, inclusion-proof set, pinned-key record, syscall traces, adversarial fixtures, or negative-control outputs. Broad search collisions with unrelated repositories were discarded. Search absence is not evidence that the run package does not exist.

Evidence dispositions are unchanged:

- A.2 R10 remains operator-disclosed `NOT MET`; neither blanket independent failure nor blanket compliance is promoted until an authentic disputed commitment is bound to the actually applicable historical publication path and its publication timing/provenance is evidenced.
- The reported 1,534-event / 50-checkpoint submitter-removed rerun remains `COUNTERPART_REPORTED_COMPLETE`, not independently verified.
- The 784-record / 30-commitment run remains historical and settled under its prior R1-R10/custodian-naming treatment; it is not replaced or reinterpreted by the newer counterpart report.

Next executable step: acquire one authentic disputed pre-rename sealed record/export with immutable block/sequence identity and provenance, then recompute its seal and bind its witness version/term to `2d6715868bb2812b98d874ab17890ff89ece30d5` or the actually applicable revision. In parallel, only an authentic v0.8 package should be used to verify the 1,534/50 claims. Do not repeat broad GitHub absence searches unless a new locator or artifact identifier is supplied.


## Generation 86 newly published public-walk/reset-disclosure source — 2026-09-19

Canonical Task Registry generation 86 was re-read before this continuation. The child task remains `ACTIVE` with COSV `50000000100000`.

A new exact AILeash source locator was discovered without repeating the prior broad searches. Upstream main `8edfe2b97e489c3d1f1a576505f95bfbe6c1b7d7` contains `modules/walk.py` v1.1.0 (blob `4d221287de5356d42d9fff83ecd7373b7da60a24`) and `modules/disclosure.py` v1.0.0 (introduced by `7de6e4d09944533bbc0548af27820a7aef7d4eac`).

### Source-inspected effect

`walk.py` publishes a public current-chain traversal contract at `/x/walk/*` and gives the exact seal formula and preimage-recomputation procedure for public blocks. However, it explicitly states that the audit chain restarted from `GENESIS` on 2026-09-07 and that a block index quoted before that date belongs to the earlier chain.

`disclosure.py` makes that reset boundary explicit and seals a fixed statement into the current chain. Its source states that pre-reset blocks are not part of the current chain and cannot be verified against it. The source also leaves `PREVIOUS_CHAIN_FINAL_TIP` and `PREVIOUS_CHAIN_FINAL_HEIGHT` empty; the resulting disclosure text therefore records those values as `not recorded in this disclosure` unless the source is changed before deployment. The statement further acknowledges that some records kept outside the chain, including completeness-period commitments, still quote block indexes from the earlier chain.

This is material evidence because it establishes a concrete historical-chain discontinuity in the operator's current source. It does **not** itself establish the identity, contents, final tip, height, or v1.1 vocabulary binding of any disputed pre-reset commitment.

### Evidence disposition

- Current-chain public-walk capability: `SOURCE_INSPECTED_NEW_PUBLIC_VERIFICATION_SURFACE`.
- 2026-09-07 reset and pre-reset/current-chain separation: `SOURCE_INSPECTED_OPERATOR_DISCLOSURE_CONTRACT`.
- Previous-chain final tip/height: `NOT_RETAINED_IN_DISCLOSURE_SOURCE`.
- Historical disputed commitment binding to `2d6715868bb2812b98d874ab17890ff89ece30d5`: still `NOT_ESTABLISHED`.
- A.2 R10 remains operator-disclosed `NOT MET`; neither independent blanket failure nor compliance is promoted.
- The 1,534-event / 50-checkpoint v0.8 rerun remains `COUNTERPART_REPORTED_COMPLETE`; no authentic package was surfaced by this new locator.
- The 784-record / 30-commitment run remains historical and settled without reinterpretation.

The public runtime endpoints named by the source (`https://sebbi.pro/x/walk/*` and `https://sebbi.pro/x/disclosure/*`) were not retrievable through the available web reader in this continuation, so no runtime response, sealed reset block, current-chain arithmetic, or live deployment is claimed. The source evidence alone is retained with that limitation.

Next executable historical action: obtain an authentic pre-reset sealed block/export or an operator-retained prior-chain tip/height plus the exact block/sequence provenance needed to bridge the old chain. Only then recompute the historical seal and test whether its witness version/term binds to `2d6715868bb2812b98d874ab17890ff89ece30d5` or another applicable revision. Do not substitute current `/x/walk` blocks for pre-reset evidence.


## Generation 111 retained pre-reset completeness and Bitcoin anchoring verification — 2026-09-19

Canonical Task Registry generation 111 was re-read before documentation reconciliation. The child task remains `ACTIVE` with COSV `50000000100000`.

### Retained pre-reset commitments independently retrieved

The public `/x/complete/periods` and `/x/complete/root` surfaces were retrieved through a one-shot GitHub Actions evidence-transport run, preserving exact response bytes. The August 2026 deployment-wide commitments are:

- receipts: block index `1894`, 1,844 leaves, root `040fc1b82362da2449f453b5de3bfef95a7c054e8df8911bcc4168c885ded1f1`, chain seal `65d63926b6a32f69244607d6953a427b0a01bd9df4dc32a6ae3fbbfe0aa4a3e3`;
- subjects: block index `1895`, 30 leaves, root `5a34b9af7ab85de4d2b9b3d18c238c4aaa632333f4fedeb4c5fe1d5c6953abff`, chain seal `4a99a3b5fa83d79a8baba0c8cd4415bab37b0435ee5dff14d50900e7b0acf260`.

Both pre-date the disclosed 2026-09-07 chain reset. Current-chain inclusion and consistency endpoints report those exact historical seals as not members of the chain currently served, which is consistent with the disclosed reset and independently confirms that current-chain traversal cannot reconstruct these historical blocks.

The public completeness proof for `wit:flavorflowstrategy.uk` recomputed independently to the exact August subjects root at index 26. The same independent recomputation succeeded for `wit:praesidium` at index 27 and `wit:red-flag-ai-pro` at index 28. A query for `wit:shango` returned a valid absence proof bounded by independently verified adjacent leaves `wit:red-flag-ai-pro` and `wit:shango.in`; this is a spelling/identity distinction and is not promoted as evidence that Shango was absent.

### Historical subjects commitment OpenTimestamps verification

The exact public OTS artifact for historical subjects seal `4a99a3b5fa83d79a8baba0c8cd4415bab37b0435ee5dff14d50900e7b0acf260` was retrieved with original proof SHA-256 `275186cb44c66ef366181d10f26daa9df0afec6a44e996a491061e352604d38f`, stamp ID `1788293244`, stamped at `2026-09-01T20:07:24Z`. The retained server copy was still reported as pending.

A copy of that exact proof was upgraded using the standard OpenTimestamps client. The corrected verification run is GitHub Actions run `35463311073` at commit `66fa946fb9441ee8f5df06a65bdf60b8a3da27ef`. It verified that the proof starts from SHA-256 digest `4a99a3b5...` and yielded Bitcoin block attestations:

- height `965082`, proof-derived Bitcoin block Merkle root `f2bd1ec41da3c464a39074b6e1d8db35f1ab489dfa36a8e228ddcf8068f7d25a`;
- height `965103`, proof-derived Bitcoin block Merkle root `b3a444da6e952ba00431ad67770ade15b70672c714571d0c35e9b37d4868e7ec`.

For both heights, Blockstream and mempool.space independently returned the same block hash, height, and Merkle root as the proof-derived values. The corrected run completed `success` with `all_two_explorer_matches=true`.

A prior verification attempt, run `35449567326` at commit `46752f34ad6ad8cbd093fb0ec6e00befa6f9529e`, failed because the verifier incorrectly compared the internal timestamp message immediately before the Bitcoin attestation with the block header Merkle root. That verifier defect was corrected rather than interpreted as failed evidence.

Evidence classification for the historical subjects commitment is therefore advanced narrowly to:

`INDEPENDENTLY_RETRIEVED_PRE_RESET_COMPLETENESS_COMMITMENT / INDEPENDENT_MERKLE_MEMBERSHIP_VERIFIED / OTS_PROOF_COPY_UPGRADED / BITCOIN_BLOCK_ATTESTATIONS_MATCHED_BY_TWO_INDEPENDENT_EXPLORERS`.

This proves that the retained August subjects commitment hash was incorporated into an OpenTimestamps proof that resolves to independently confirmed Bitcoin blocks. It does **not** by itself reconstruct block 1895's original chain preimage, prove the complete old-chain predecessor path, or reveal the exact historical witness record's sealed `witness_version` / liveness term.

### R10 and rerun disposition

A.2 R10 remains operator-disclosed `NOT MET`. The stronger commitment/anchoring evidence does not yet bind a disputed historical witness record to `2d6715868bb2812b98d874ab17890ff89ece30d5` or another exact historical revision because the necessary original sealed-record preimage and per-record historical version/term remain unavailable.

The reported v0.8 1,534-event / 50-checkpoint run remains `COUNTERPART_REPORTED_COMPLETE`; no authentic run package surfaced during this exact-locator continuation. The prior 784-record / 30-commitment run remains historical and settled, including its existing R1-R10 treatment and `custodian` naming.

The temporary GitHub evidence-fetch workflow was removed by resetting the evidence branch back to current canonical main before this documentation update. No new runtime, scheduler, credential path, custody store, or device dependency was retained.

## Canonical state-dependent test contract — 2026-09-19

This goal is a **strict state-dependent test**, not an evidence checklist. Every accepted state MUST transition to the next state in order. No state may be satisfied independently, in parallel, out of order, or by evidence that bypasses the immediately preceding closure.

Every transition edge requires the predecessor to exist in canonical Master Records with all four predicates satisfied simultaneously:

- `state=RECORDED`;
- `reconstruction_status=PASS`;
- `required_evidence_validation_status=PASS`;
- exact receipt/reconstruction digest equality.

The ordered state graph is:

1. `PRE_RESET_COMPLETENESS_COMMITMENT_CLOSED`
   - retains the independently retrieved August subjects commitment at old-chain block 1895, root `5a34b9af...`, chain seal `4a99a3b5...`, verified subject-membership proofs, and independently upgraded-copy Bitcoin anchoring.
   - this state is the sole predecessor for state 2.

2. `HISTORICAL_WITNESS_RECORD_RECONSTRUCTED`
   - may be admitted only by consuming state 1's exact Master Records closure.
   - requires one authentic individual pre-reset witness record with immutable identity/provenance and the original `event`, `result`, `timestamp`, and `prev_hash` material needed by the historical seal contract.
   - this state is the sole predecessor for state 3.

3. `HISTORICAL_WITNESS_SEAL_RECOMPUTED`
   - may be admitted only by consuming state 2's exact Master Records closure.
   - recomputes the historical audit seal from the retained preimage and requires exact equality with the historical retained seal.
   - this state is the sole predecessor for state 4.

4. `HISTORICAL_WITNESS_VERSION_TERM_BOUND`
   - may be admitted only by consuming state 3's exact Master Records closure.
   - requires the sealed historical witness version and liveness term and binds that exact record to revision `2d6715868bb2812b98d874ab17890ff89ece30d5` or the actually applicable immutable revision.
   - this state is the sole predecessor for state 5.

5. `R10_DISPOSITION_RECONCILED`
   - may be admitted only by consuming state 4's exact Master Records closure.
   - R10 disposition is derived here and nowhere earlier.

Current chain position: `PRE_RESET_COMPLETENESS_COMMITMENT_CLOSED`.

Current successor pending: `HISTORICAL_WITNESS_RECORD_RECONSTRUCTED`.

R10 remains operator-disclosed `NOT MET` until the entire predecessor chain closes through state 4 and admits state 5. The independently verified `4a99a3b5...` commitment is therefore not a parallel proof that can independently modify R10; it is predecessor state 1 and must be consumed by state 2.

The v0.8 1,534-event / 50-checkpoint rerun remains `COUNTERPART_REPORTED_COMPLETE` and does not form an alternate path around this state graph. The historical 784-record / 30-commitment run remains settled and historical.

## Goal prompt 17: StegBrowser supersession reconciliation — 2026-09-21

The copied continuation that requested repair of the StegBrowser A1 observer/composition seam was reconciled against current canonical authority before mutation.

Current source has advanced beyond that continuation:

- `STEG-BROWSER-RUNTIME-CONNECTION-INGRESS-001` is retired/decomposed at its prompt limit; its later source history records the SV002-derived browser execution path, Node-journal retention, evidence export, Master Records ingress/custody bindings, and successor decomposition.
- Site PR `#1436` is merged as `c9af43f7fd70a2fbd6ce45351e5538acdc14fa01`; it repairs the existing browser-to-sovereign Universal InTr compatibility seam by carrying the unchanged canonical materialization request and browser binding through the same deterministic Node outbox entry without a second invocation, listener, scheduler, dispatcher, materializer, WorkerCoordinator, authority plane, credential path, or device requirement.
- The older `.github` A1 observer still contains a host-side `STEGVERSE_NODE_GENESIS_RECEIPT` filesystem projection, but current authority no longer permits treating that projection as the canonical execution gate or as evidence that the registered Node is absent. The validated browser lane reads the existing registered Node continuity directly and the later merged compatibility path carries that binding into sovereign InTr. No new repair was applied to the retired observer.

The reusable-task registry was then searched for an already-existing manifest-compatible arbitrary external GET/navigation StegBrowser invocation. None was found.

Two adjacent reusable identities were inspected and rejected as substitutes:

- `RT-EXTERNAL-ENDPOINT-MONITOR-001` is a generic observation contract with no executable runner templates; it requires an existing adapter/governed path and is not an arbitrary StegBrowser GET/navigation invocation.
- `RT-EXTERNAL-FRAMEWORK-ROUNDTRIP-ROLLOUT-001` is bounded to canonical external-framework registry entries and manifested operations; its registry-sweep contract explicitly performs no external calls and it is not a generic URL-fetch task.

Therefore no sebbi.pro request was issued through either identity, no new StegBrowser task/manifest/request was minted, and the immutable owned-mirror nonce was not altered or reused for external navigation.

Most importantly, the current canonical task record for `MIR-AILEASH-WITNESS-EVIDENCE-RECONCILIATION-001` now marks all StegBrowser execution substrates `NOT_APPLICABLE` for this documentary/public-verification goal. Its strict state-dependent contract permits exactly one next transition: `HISTORICAL_WITNESS_RECORD_RECONSTRUCTED`, consuming the immediate `PRE_RESET_COMPLETENESS_COMMITMENT_CLOSED` Master Records predecessor. The stale StegBrowser continuation is therefore `SUPERSEDED_BY_CURRENT_AUTHORITY` and cannot be used to bypass, parallelize, or leapfrog the ordered evidence chain.

No runtime execution, external GET, A1/A2/A3/A4 promotion, or new authority path is claimed from this reconciliation.

## Goal prompt 18: predecessor Master Records closure verification — 2026-09-21

The strict state-dependent contract was re-read before attempting state 2. The canonical task remains ACTIVE and permits only `HISTORICAL_WITNESS_RECORD_RECONSTRUCTED` after the immediate predecessor `PRE_RESET_COMPLETENESS_COMMITMENT_CLOSED` is consumed from canonical Master Records.

The predecessor evidence identity remains:

```text
subjects_block_index = 1895
subjects_root = 5a34b9af7ab85de4d2b9b3d18c238c4aaa632333f4fedeb4c5fe1d5c6953abff
subjects_chain_seal = 4a99a3b5fa83d79a8baba0c8cd4415bab37b0435ee5dff14d50900e7b0acf260
```

Exact closure verification was attempted against current authority before acquiring any state-2 evidence.

Findings:

1. Searches across `StegVerse-Labs/.github` found the state declaration and closure requirements, but no retained receipt carrying `PRE_RESET_COMPLETENESS_COMMITMENT_CLOSED` with an exact `receipt_sha256` / `reconstructed_receipt_sha256` pair.
2. The private authoritative repository `master-records/orchestration` was inspected directly. Its complete main tree contains no path or indexed object matching the MIR task ID, predecessor state ID, block 1895, subjects root, or subjects chain seal. The repository-backed `receipts/` and `reconstructions/` trees likewise expose no matching retained artifact.
3. The canonical Master Records implementation does expose the non-authorizing query contract:
   `GET /api/master-records/state-transitions/query?subject_or_correlation_id=<id>`, optionally filtered by `transition_id`.
4. No TV/TVC-authorized live Master Records endpoint/token binding is exposed to this conversation. The previously observed public same-origin path `https://stegverse.org/api/master-records/state-transitions` returned HTTP 404 and is not evidence that the durable store is empty.

Therefore the required predecessor closure is currently `UNKNOWN_NOT_AUTHENTICALLY_OBSERVED` from this execution context. The task record's `current_chain_position` is coordination state and is not substituted for the required Master Records closure.

Because the predecessor closure has not been authenticated with all four required predicates simultaneously—

```text
state = RECORDED
reconstruction_status = PASS
required_evidence_validation_status = PASS
receipt_sha256 == reconstructed_receipt_sha256
```

—state 2 was not entered. No pre-reset individual witness record was acquired for admission, no `HISTORICAL_WITNESS_RECORD_RECONSTRUCTED` transition was submitted, and no parallel evidence was allowed to satisfy or bypass the missing predecessor closure.

Next execution boundary: query the existing TV/TVC-authorized canonical Master Records service for subject/correlation identity `MIR-AILEASH-WITNESS-EVIDENCE-RECONCILIATION-001` and the exact predecessor transition identity. Only if one returned record proves the four closure predicates and binds block 1895/root/seal exactly may the task acquire and retain one authentic pre-reset witness record and propose state 2.

## Goal prompt 19: canonical-work Master Records binding carriage repair — 2026-09-21

Canonical Task Registry generation 191 was re-read before mutation. The predecessor `PRE_RESET_COMPLETENESS_COMMITMENT_CLOSED` remains `UNKNOWN_NOT_AUTHENTICALLY_OBSERVED`; no state-2 acquisition or admission is permitted until the exact canonical Master Records closure is returned and reconstructed.

The first concrete existing service-binding defect was isolated in the already-registered Canonical Work resident path:

```text
scripts/dispatch_resident_execution_requests.py
  -> clean_exec_env(...)
     preserves existing Master Records endpoint/token and durable-local DB/key bindings
  -> canonical_work_coordination
  -> control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py
  -> legacy clean_env(...)
     previously stripped every Master Records binding before the Canonical Work child
```

This meant the existing TV/TVC-authorized query capability could be present on the resident carrier and still become invisible at the exact Canonical Work child boundary, producing a query/custody-surface-unavailable condition without proving the durable store absent.

The bounded repair changes only `consume-canonical-work-coordination-bootstrap.legacy.py`:

- preserve the already-carried `STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT` / `STEGVERSE_MASTER_RECORDS_SOURCE_ROOT`;
- preserve the already-carried HTTP binding `STEGVERSE_MASTER_RECORDS_ENDPOINT`, `STEGVERSE_MASTER_RECORDS_TOKEN`, and timeout;
- preserve the already-carried durable-local binding `MASTER_RECORDS_DB`, `MASTER_RECORDS_RECEIPT_KEY`, and durability flag;
- preserve `STEGVERSE_REPO_ROOTS_JSON` only as the existing source locator;
- continue stripping GitHub credentials and all pre-existing forbidden credential names;
- report only a boolean `credential_material_present` plus the bounded scope `EXISTING_TV_TVC_MASTER_RECORDS_BINDING_ONLY`; no credential value is written to receipts.

Focused regression coverage asserts that every canonical Master Records binding survives `clean_env(...)`, while `GITHUB_TOKEN` and `GH_TOKEN` do not.

This creates no new custody service, query API, credential route, runtime, transport, dispatcher, scheduler, WorkerCoordinator, evidence store, or user/device prerequisite. It only restores carriage of the already-authorized Master Records binding through an existing consumer boundary.

Source repair does not prove that the predecessor exists. After merge and authentic resident refresh/dispatch, the same existing canonical `query_state_receipts(...)` path must query:

```text
subject_or_correlation_id = MIR-AILEASH-WITNESS-EVIDENCE-RECONCILIATION-001
transition_id = PRE_RESET_COMPLETENESS_COMMITMENT_CLOSED
```

and accept progression only if one returned reconstruction binds block 1895, root `5a34b9af7ab85de4d2b9b3d18c238c4aaa632333f4fedeb4c5fe1d5c6953abff`, seal `4a99a3b5fa83d79a8baba0c8cd4415bab37b0435ee5dff14d50900e7b0acf260`, and simultaneously proves `RECORDED + reconstruction_status=PASS + required_evidence_validation_status=PASS + receipt_sha256==reconstructed_receipt_sha256`.

No predecessor, state-2, runtime, or completion predicate is promoted by this source change.

