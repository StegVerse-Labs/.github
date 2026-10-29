# Interlock/InTr runtime-independent protocol mirror handoff

Updated: 2026-10-29
Goal Task ID: `INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001`
Issue: #2897
COSV ID: `50000000102000`
Status: `ACTIVE`

## 2026-10-29 session 12 integration handoff (latest)

Canonical main shard remains ACTIVE (blob a6cd7003ff8088749337d2e2c970c728c6757670),
with null claim/fence. This documentary update confers no authority.
Session Prompt Count: 12. Cumulative recovery lower bound: 32/20;
exact Goal Prompt Count remains unverified and must not reset.

### Completed verification and source reconciliation

- Org #258 at 9f21aa837852ed7bd341598e545eb8fd29cfa9b3 was independently
  tested: 10 ingress tests pass, including undeclared successor rejection,
  refusal propagation and already-observed predecessor rejection.
  All 46 hosted checks succeeded at that head; it remained draft/unmerged.
- Strict replay at that head over the retained 13 public-ledger snapshots:
  156 ALLOW / 0 DENY / 0 FAIL_CLOSED, byte-identical to this PR's retained
  pg_replay.json (SHA256 fdca42b36ddff4775656de3e14db63bb836abaf76e9d7960e06ccd3e7a61b3f2).
  This is historical public verification, not a fresh private crossing.
- H36 phase patch dbedb702e7180071f7d6434c2463325139562e4374ed50d63dcf63cca7b5b012
  independently passed 20 combined hop tests on Org 0b50df09. Claude/Muse's
  broader 48/48 vector result is attributed to those lanes.
- Labs #3404 d8a2efaa delta is reviewed: documentary additions only, six checks
  successful. Earlier d141afef wording below is historical.
- Labs #3212, Org #184/#185 and SDK #537 are merged. Their old pending labels
  below are historical. Labs #3207/#3213 need remaining-delta review;
  #3206 retains joint source-successor/hygiene disposition.
- The older 56-hop 12 FAIL / 44 UNREACHABLE inventory must be reconciled by
  source, scope and ledger pins against the later 156-path evidence; it is
  not a current failure count and the two inventories are not interchangeable.

### Existing-owner actions, independently actionable

| Owner | Concrete next action |
|---|---|
| Org #162 | Ratify declared-successor option (ii), integrate #258 through protected expected-head authority, and integrate H36 tests with combined-head CI. Preserve historical receipts. |
| Labs source owners | Integrate #3404 and this #3405 documentary update; reconcile shared README changes on the actual base and verify resulting head. Prior-head CI does not validate a new commit. |
| Registry #3195 | Use exact requests in comments 6504255468/6504255852. Native read-only plans refused InTr's missing explicit task_registry_mints_execution_authority=false and KV's IN_PROGRESS/null-claim inconsistency. Governed record/state repair precedes regenerated row==shard requests, current-generation plan/apply/verify and count disposition. First refusals only; later predicates unproven. |
| Registry #3195 / Org #167 | Authenticate intr-destination and hygiene registration scopes/identity inputs; no proposed ID or COSV is admission. Serialize Registry mutations. |
| TVC owner | Review/integrate #562 and adjudicate #561 versus #533 as PUBLIC-ledger-reader work. |
| TVC/SDK/runtime owners | D1/D2 decision, broker/issuer/nonce/receiver preparation and separately admitted private execution; public historical verification does not require private warrants. |
| KV custody owner | Labs #2810 remains a distinct custody goal, not an InTr documentary prerequisite. |

Current evidence: [Org #162](https://github.com/StegVerse-org/.github/issues/162#issuecomment-6504333517),
[Labs #2897](https://github.com/StegVerse-Labs/.github/issues/2897#issuecomment-6504334009),
[TVC #488](https://github.com/StegVerse-Labs/TVC/issues/488#issuecomment-6504334518).
Drive coordination file 1zTyY4o7CDp2xPldMjDQim6uVijUIJgcj retains the approved
session-6 revision; session-8 replacement requires the requested exact-payload
approval. Later issue evidence is not yet mirrored there. No new upload attempted.

## 2026-10-29 independent strict replay reconciliation (retained evidence)

This is a documentary evidence update under the existing task, with authority
effect NONE. Earlier sections are retained as history; their blanket
`UNKNOWN_NOT_AUTHENTICALLY_OBSERVED` and public-route warrant prerequisites are
superseded for the 156 declared paths at the source and ledger commits below.
This does not establish a new execution, admission, external conformance,
private-ledger warrant, release, or task closure.

### Registry and counters

Read at Labs main `6b13c3a749b2940d6142644196a8302823c1f45a`:
the canonical task shard and vector retain ACTIVE / COSV `50000000102000`.
The complete aggregate Registry, generation 322 (120 rows), contains no row
for this task. The shard is DOCUMENTARY_NON_AUTHORIZING, with
`projection_only=true`, null claim/fence, and only
`PROTOCOL_SCHEMA_AND_CONFORMANCE_VECTORS_VALIDATED` as an allowed next
transition. ACTIVE is the shard's coordination state; CHECKED OUT and native
execution admission are not established. This update changes none of those
records.

Session Prompt Count: 2 in the fresh continuation. Exact cumulative Goal Prompt
Count remains unverified and is not reset. The prior session's prompt-20
handoff is retained at [#2897 comment 6500157092](https://github.com/StegVerse-Labs/.github/issues/2897#issuecomment-6500157092).
Together with these two continuation prompts it gives a recovery lower bound of 22, already
beyond the 20-prompt budget. Registry/Coordination must reconcile the cumulative
count and dispose the documentary validation milestone; this is not permission
to extend this task into distinct runtime work or mint substitute task IDs.

### Independently executed evidence

- The protocol-vector verifier passes on Labs main `6b13c3a7`: ALLOW, DENY,
  FAIL_CLOSED, MasterRecordsCheckpoint profile and all six negative vectors.
- On clean Org main `0b50df09f620304319f99de58af081aa8902c37e`,
  `scripts/intr_post_genesis_replay.py check` verifies all 156 committed records,
  all class DESTINATION_RECEIPT_LEDGERED, with no problems.
- Independently fetched the organization-ledger refs anonymously for precisely
  the 13 organizations returned by the native `orgs` command. Executed native
  `replay --require-ledgered-allow`: exit 0, **156 ALLOW / 0 DENY / 0 FAIL_CLOSED**,
  `e0_terminal=true`, `authority_effect=NONE`. All 156 complete per-path results
  equal Claude's published results at TVC evidence commit
  `e2ebde781f8e8cb77dd827519fc0db65bd2aa3ab`.
- The independent raw output SHA-256 is
  `fdca42b36ddff4775656de3e14db63bb836abaf76e9d7960e06ccd3e7a61b3f2`;
  its native record seal is
  `sha256:870f318b9a9ad2bc830f447038ac6793e21db5fa0c7e4041815a21bb61868b9d`.
  It is not byte-identical to Claude's file: that file inventories a fourteenth,
  unused `master-records` ledger copy. Its 13 declared-path ledger tips and all
  per-path results match. Only that extra inventory entry and the resulting
  record seal differ. No receipt or result was changed to force a digest match.
- The separately executed Labs↔Org pair replay remains retained in
  [#2897 comment 6499684394](https://github.com/StegVerse-Labs/.github/issues/2897#issuecomment-6499684394)
  and PR #3404: eight byte hashes matched in that worker's run. This session's
  independent execution is the full 156-path strict replay, not a new claim to
  have rerun that eight-output script.

Evidence class: independently executed read-only verification of historical
public-ledger receipts, using the native verifier. These receipts were already
ledgered; no transition or receipt was replayed or appended. Public ledger reads
need no TV/TVC credential. Private-ledger warrant hardening remains separate.
Raw output, exact pins, comparison and reproduction details:
[retained evidence](evidence/intr-readback-20261029/README.md).

### Integration and owner transitions

PR [#3404](https://github.com/StegVerse-Labs/.github/pull/3404) remains draft,
open and unmerged at `d141afefd8791f841e4f0bca25787014d3f45a0c`. All three
returned exact-head workflow runs succeed: 40893614980, 40893615124 and
40893615034. No approving review or native merge-admission evidence was
observed. Its source owner retains ratification and protected expected-head
merge. This handoff update is independently reviewable and does not modify
that owner's branch.

| Remaining action | Existing owner / evidence surface | Concrete next step |
|---|---|---|
| Documentary validation and cumulative-count disposition | Registry / Coordination, Labs #3195 and Org #167 | Reconcile omitted aggregate row with the ACTIVE shard; authenticate the allowed validation transition and closure or a genuinely separate successor through native registration. Do not equate source evidence with claim/fence. |
| Source integration | Labs #2897 / PR #3404 owners | Review current exact heads and retained evidence, ratify, and use the protected expected-head path. |
| Duplicate destination-receipt policy | Org #162 | Retain both b122500a and e4e9d2e3; decide successor selection/idempotency semantics without rewriting or reissuing historical receipts. Strict replay is now independently complete. |
| Private-ledger warrant hardening | TVC #488, #533 / #561 owner | Bind to an authenticated existing or genuinely distinct successor task before issuer/nonce mutation. It is not a prerequisite for the verified public routes. |

Adjacent sealed-source custody reader work remains with Labs #2810's existing
owner; it is not part of this documentary protocol goal. No successor Goal ID,
COSV, WorkerCoordinator claim, sovereign KV write, or release is assigned here.

## 2026-10-17 conformance reconciliation (historical)

Read at `StegVerse-Labs/.github` main `5b3fc476`, Registry generation 317. Coordination: StegVerse-org/.github#162 (P0), [#2897](https://github.com/StegVerse-Labs/.github/issues/2897). Evidence class: source reading and a local verifier run. This section changes no record, Registry row, claim or ledger.

- **Status line correction.** The line above says `ACTIVE / CHECKED OUT`. The task record is `ACTIVE`. It has no `checkout_state`, and its `worker_claim` is `projection_only: true` with null `claim_ref` and `fence_ref`, so "CHECKED OUT" is not supported. The task is also absent from `data/canonical-task-registry.json` at generation 317.
- **Next action above is done.** The #2915 artifacts are on main: the test vectors, the source mapping and `scripts/verify_interlock_intr_runtime_independent_protocol.py`. Run on main `5b3fc476`, the verifier returned `status: PASS` across ALLOW, DENY, FAIL_CLOSED, the MasterRecordsCheckpoint profile and six negative vectors. That is CI-class evidence for the one allowed transition, `PROTOCOL_SCHEMA_AND_CONFORMANCE_VECTORS_VALIDATED`. It is not runtime execution or external conformance.
- **Runtime state needs the six fields.** The sentence "runtime state remains `UNKNOWN_NOT_AUTHENTICALLY_OBSERVED`" is not a finding under conformance item 5. The six-field form, matching Lane B's F-1/F-2 on #162:
  - `failure_code`: `TVC_HOP_WARRANT_ISSUANCE_PATH_ABSENT`
  - `failed_predicate`: `CROSS_ORG_HOP_CREDENTIAL_IS_TV_TVC_WARRANTED` and `DESTINATION_RECEIVE_NOT_MANIFEST_AND_WARRANT_BOUND`
  - `required_evidence_or_repair`: a TV/TVC broker operation for the hop (StegVerse-Labs/TVC#488), then a receive that checks the warrant and manifest digest before any ledger append
  - `retry_entrypoint`: TVC#488, then the hop branches (Labs #3206 and twins) and StegVerse-SDK#537
  - `owning_existing_goal`: this task
  - `next_attempt`: the owner's choice of credential form (#162)
- **Standing rules for this protocol** (from the standard and the invariants):
  - Destination existence is sufficient; liveness is not a predicate.
  - An unavailable receiver is answered by `DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION`.
  - `FEDERATION_HOP_TOKEN` is not installed: credentials are TV/TVC-issued.
  - The 56-hop readback (0 PASS / 12 FAIL / 44 UNREACHABLE) is an evidence state. The 44 UNREACHABLE results are not a blocker; the 12 FAIL results need per-hop root cause.

### Open draft PRs in this lane (all draft; merge is the owner's)

- Labs: #3206 (one-way hop), #3207 (ledger-transition six fields), #3212 (governance six fields, carrier epoch), #3213 (D6/D7 crossing refusals, twin of org#185)
- StegVerse-org/.github: #181, #183, #184, #185
- StegVerse-org/StegVerse-SDK#537
- Hop twins: SV-011/.github#11, GCAT-BCAT-Engine/.github#13, Admissible-Existence/.github#95, StegGhost/.github#21, StegVerse-002/.github#47, SV-LLM/.github#41

### Work that can run in parallel now

| Work | Owner | Depends on |
|---|---|---|
| TVC broker operation `DISPATCH_INTR_DESTINATION_PHASE` (fixture tests only, no real tokens) | TV/TVC owner, Lane B | nothing |
| Six fields on refusals: #3207, #3212, #3213 and org #184, #185 | Lane B | nothing |
| Independent negative and consumer tests (H36) | Claude | nothing |
| Exact-head and ledger readback audit (H37) | ChatGPT | nothing |
| Per-hop root cause for the 12 FAIL hops | Lane B | nothing |
| Aggregate Registry row for this task; Task ID for `intr-destination` | Registry owner | nothing |
| Receive-side warrant and manifest binding | Lane B | TVC broker operation |

## Goal

Define a runtime-independent, machine-readable Interlock/InTr interoperability protocol in which registered nodes exchange manifested, payload-bound communications while each receiving framework independently determines the admissible state transition in its own runtime.

## Protocol boundary

The protocol standardizes the observable inter-system boundary, not participating runtimes. A conforming external framework is not required to adopt StegVerse internal runtime code, governance implementation, state representation, database, credential implementation, Master Records, or SDK.

Communication using Interlock/InTr requires registered-node identity and manifested intent. The protocol binds the communication to source, destination, payload commitment, applicable predecessor/state context, requested capability, disposition, receipt, resulting-state commitment where applicable, and evidence references.

The receiving framework remains authoritative for its own state machine. Incoming external data is not presumed to be governed by the originating framework. StegVerse governs its own output automatically; that property does not transfer StegVerse governance authority to the external framework.

## Disposition

Every attempted state-transition-dependent communication MUST terminate with an evidentiary disposition:

- `ALLOW`
- `DENY`
- `FAIL_CLOSED`

A transport success alone MUST NOT be represented as an allowed state transition.

## Initial interoperability profile

`MasterRecordsCheckpoint/v1` is the first bounded profile of this protocol.

Master Records remains sole checkpoint-construction authority for organization records; custody remains with the Organization. For external checkpoint communication:
1. Master Records establishes canonical checkpoint C.
2. An egress manifest declares intent, checkpoint reference/commitment, registered destination node and requested checkpoint capability.
3. The receiving StegVerse boundary resolves applicable state and governs the permitted output projection.
4. Interlock/InTr transfers the permitted data and retains a transfer receipt.
5. External witness evidence may return through manifested registered-node ingress bound to digest(C).
6. The return is verified and receipted before any applicable resulting state/evidence is retained.

The manifest is provenance for communicating the checkpoint; it is not the checkpoint.

## Adoption/conformance boundary

No external adoption, external conformance, production interoperability, network participation, or runtime execution is claimed by this documentary task. Such claims require independently retained evidence.

## Parent

Decomposed from `MASTER-RECORDS-REPORTABLE-CHECKPOINT-001` / issue #2895.

## Reviewed implementation plan and vectors

The accepted machine-readable implementation plan is `docs/INTERLOCK_INTR_RUNTIME_INDEPENDENT_PROTOCOL_IMPLEMENTATION_PLAN_v1.json`. Synthetic non-authorizing conformance fixtures are in `test-vectors/interlock-intr-runtime-independent-protocol-v1.json` and cover ALLOW, DENY, FAIL_CLOSED, node identity, payload, predecessor/state, manifest intent, requested capability, receipt binding, and the first bounded `MasterRecordsCheckpoint/v1` profile.

Exact-head workflow evidence on the prior PR head demonstrated a missing `execution_substrate_resolution` for this documentary task. The task record now declares all runtime substrates NOT_APPLICABLE with no selected substrate. The prior test-suite ratchet also reported an unrelated/new registry-gate failure and one newly passing baseline test; fresh exact-head CI is required before attributing or repairing further defects.

No external adoption, external conformance, production interoperability, runtime execution, deployment, or merge is claimed.

## Replacement PR and exact-head validation

PR #2898 remained unavailable through authoritative connector search. The preserved branch was therefore used to create replacement PR #2909 with explicit replacement evidence. At creation, #2909 targeted `master-records-reportable-checkpoint-2895` from exact head `5ec4bdf4b9244f19051048434df9380375532692`. All five observed workflows for that exact head completed SUCCESS, including Cross-Task Coordination Validation and Test suite ratchet. The branch remains diverged from its base (10 ahead / 2 behind), so mergeability is not inferred from CI success.

## Initial source-level surface trace

Default-branch source evidence identifies these existing seams:

- Public SDK `run-manifest` exists and prior canonical evidence binds successful public results to the exact canonical ingress manifest and deterministic generic execution request.
- Current SDK source at `StegVerse-org/StegVerse-SDK@bafb093797f75e4d1fc94f8b45eb278dda3809f9` traces public `run-manifest` through `stegverse/manifest_execution.py` to route-selected runtime bindings including `stegverse.manifest_state_transition_runtime.execute_manifest`.
- The current manifest-state-transition runtime no longer uses `STEGVERSE_UNIVERSAL_INTR_INGRESS_URL` or `STEGVERSE_TVC_RELAY_AUTHORIZATION_ID`. It resolves the destination only from `completion.egress`, opens no connection, supplies no transport credential, and returns an SDK-bound handoff to the receiving Interlock runtime. That handoff is explicitly not admission and must not be promoted into an authentic far-side disposition.
- The shared canonical ingress profile is `SDK:ManifestStateTransition` at `/intr/materialization`; repository source includes `workers/manifest_state_transition_intr_ingress.py` and tests for the shared profile.
- Repository evidence also states that GitHub is validation/evidence transport, not authentic Universal InTr runtime authority, and that the active ChatGPT execution surface did not expose a non-caller-editable authenticated Universal InTr/TVC invocation primitive in the cited observations.

These are source-level findings only. An authentic current production invocation boundary has not been established in this task and remains `UNKNOWN_NOT_AUTHENTICALLY_OBSERVED`.

## Parent reconciliation, verifier and field mapping

The two parent-only changes were reconciled into this branch by carrying forward the current parent versions of the Master Records checkpoint task record and handoff; no successor artifact was discarded. A deterministic verifier now exists at `scripts/verify_interlock_intr_runtime_independent_protocol.py` for the synthetic fixture package. Its fixture semantics were independently exercised during this task and produced the expected ALLOW, DENY, FAIL_CLOSED and negative FAIL_CLOSED classifications; repository exact-head CI remains the required admission evidence for the committed verifier.

Machine-readable source mapping is retained at `docs/INTERLOCK_INTR_RUNTIME_INDEPENDENT_PROTOCOL_SOURCE_MAPPING_v1.json`. It maps registered identity, manifest intent, source/destination, payload commitment, state/predecessor context, capability, disposition, transfer receipt, resulting-state commitment and evidence references to current SDK seams and explicitly records partial/profile-dependent gaps.

Authentic Interlock/InTr execution remains `UNKNOWN_NOT_AUTHENTICALLY_OBSERVED`.

## Existing-owner seam resolution

Current source makes the smallest ownership boundary explicit rather than requiring another SDK transport path:

1. SDK/Manifest Builder owns canonical manifest validation, route resolution, state-graph derivation, destination binding and handoff commitment.
2. TV/TVC remains credential authority; `derive_execution_request` declares `credential_authority = TV/TVC` without making the SDK a credential issuer.
3. The receiving Interlock/InTr runtime is the existing owner that must authenticate registered-node identity, consume the manifested handoff, evaluate the receiving state/predecessor and produce the terminal ALLOW, DENY or FAIL_CLOSED.
4. That same receiving boundary must produce the authentic transfer/admission receipt and resulting-state commitment where applicable.
5. Master Records remains limited to organization records and reconstruction for applicable retained closure evidence.

Therefore the smallest unresolved seam is not a new SDK feature: it is exposure/observation of the existing receiving Interlock/InTr admission operation with authenticated node/TVC context and receipt/result return. Until that owner seam is authentically callable, the runtime state remains `UNKNOWN_NOT_AUTHENTICALLY_OBSERVED`.

## Exact-head validation

PR #2915 ultimately merged into its checkpoint parent as `03e043f4680612bcbaf14601bd799b71b662877d` from exact head `f00400f2fd35bad2aacff368f8de9db4a5cbbd86`. All six observed exact-head workflows succeeded, including the dedicated non-authorizing protocol-vector verifier and Test suite ratchet. This merge is parent-branch source evidence only; it does not establish runtime execution, external conformance, or canonical-main ancestry.

## Next action

Use the current evidence and owner-transition table above. The #2915 artifacts
are already on main and their verifier passes. Complete protected documentary
integration and the original Registry owner's validation/count disposition;
route distinct remaining work to its authenticated existing owner. Preserve
runtime independence, external_conformance_claimed=false, all historical
receipts, and the separation between evidence verification and execution
authority. Repository merge is source integration only.

Combined integration check: H36 patch applied cleanly to Org #258 at 9f21aa83;
`python -m unittest discover -s tests -p 'test_intr_*py'` passed 314 tests
in 27.031s. Local fabricated-fixture/source verification only; hosted CI on
an owner-created combined commit remains required.
