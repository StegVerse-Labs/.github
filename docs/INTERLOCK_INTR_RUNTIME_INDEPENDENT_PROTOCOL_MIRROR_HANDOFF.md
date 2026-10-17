# Interlock/InTr runtime-independent protocol mirror handoff

Updated: 2026-10-01
Goal Task ID: `INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001`
Issue: #2897
COSV ID: `50000000102000`
Status: `ACTIVE / CHECKED OUT / CONFORMANCE VECTOR PREPARATION`

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

Reconcile the completed parent-branch #2915 artifacts onto current canonical main through the repository's existing latest-main reconstruction pattern. Preserve synthetic/non-authorizing fixtures, runtime independence, external_conformance_claimed=false, and UNKNOWN_NOT_AUTHENTICALLY_OBSERVED for authentic Interlock/InTr execution. Repository merge is source integration only.

## 2026-10-17 — executable D6 / destination-mesh remediation handoff (coordination, not authority)

**Workstream:** existing Labs PR #3206 on `intr/one-way-hop`; coordinated org PR #181, SDK PR #537 and the seven other open destination PRs. **Goal:** `INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001`, COSV `50000000102000`. Keep the existing PR lanes; do not open duplicate PRs or require any external/resident machine, second device, or hosted service. Every action is manifest-directed under the canonical Task Registry, with expected-head protection. The task shard currently reports ACTIVE, no WorkerCoordinator claim/fence, and no validated completion; do not infer authority from this handoff.

**Immediate implementable repair — D6 (Grok, with Claude independent verification):**
1. In both `StegVerse-Labs/.github/resident-runtime/sdk_manifest_crossing.py` (observed blob `79718ec867f9d6d2b5df5bc582b88a1a03f1b345`) and `StegVerse-org/.github/resident-runtime/sdk_manifest_crossing.py` (blob `359a4abaa0735f83b4ed222d20b7d1785dae319d`), repair the branch `if completed.returncode != 0 or not execution.is_file()`. This is a source path name, **not** a prerequisite to provision a resident machine.
2. Preserve `crossing_completed: false` and `authority_effect: NONE_CROSSING_ATTEMPT_ONLY`. Return a deterministic `FAIL_CLOSED` or authenticated `DENY` disposition as supported by evidence; never promote free-form stderr, missing output, transport success, or a timeout to `ALLOW`. Add all six required actionable non-ALLOW fields: `failure_code`, `failed_predicate`, `required_evidence_or_repair`, `next_attempt`, `retryable`, `owner`. Bind each field to the actual refusal/unreachable/missing-output condition and name the existing owner; preserve manifest hash, packet ID, service/destination and evidence references. No invented far-side receipt.
3. Add deterministic negative tests in **each** repository for subprocess nonzero exit, missing output file with zero exit, unreachable receiver and malformed/absent response; assert schema, six fields, correct non-ALLOW classification, no crossing or authority effect, and no fabricated egress/sovereign readback. Test both the mirror implementations and require identical contract semantics.
4. Commit on the **existing** corresponding branches only after refreshing their exact heads; run repository unit tests and required CI on the new head. Record full head SHA, run URLs, result counts, changed-file blobs and any failed predicates in this handoff and governing issues #2897 / StegVerse-org #162. Claude independently reruns negative cases and publishes a pass/fail matrix to `CLAUDE_STATUS.md`; Grok publishes implementation details to `GROK_STATUS.md`. ChatGPT verifies rather than withholding source remediation.

**Credential/dispatch continuation (TVC owner and Grok):**
5. The proposed `StegVerse-Labs/TVC/.github/workflows/github-repository-operation-broker-dispatch.yml` was NOT_FOUND on default branch at this checkpoint. Trace the actual authorized TV/TVC issuer and capability-scoped credential contract from canonical sources. If not implemented, make the smallest owner-routed implementation proposal/patch through the existing TVC issue and manifest workflow; do not substitute `FEDERATION_HOP_TOKEN`, a classic PAT, an SDK-issued token, or a locally forged warrant. State the precise missing issuer interface and evidence requirements rather than awaiting a machine.
6. Bind issuer identity, destination, requested capability, scope, expiry/revocation, manifest and correlation ID to the hop request. Test denial, expiration, revocation, wrong destination, replay, missing token and receipt absence as FAIL_CLOSED; require real TV/TVC issuance evidence before any authenticated dispatch. Preserve durable queue/event-ephemeral processing without polling/sleep loops.
7. Once authorized and observable, run one bounded manifest-directed hop through the existing GitHub Actions/substrate lane. Require actual receiving-side disposition, ingress/egress commitments and sovereign organization-ledger readback with predecessor, receipt locator/digest and Master Records evidence where applicable. If no authenticated ingress/ledger interface is exposed, report `UNKNOWN_NOT_AUTHENTICALLY_OBSERVED` for runtime and a specific actionable FAIL_CLOSED attempt receipt if an attempted transition failed; do not claim ALLOW.

**Promotion and coordination:** Exact-head green CI proves only source checks. Do not merge or claim production conformance on that basis. Use owner-authorized expected-head merges only after D6, independent tests, TVC issuance and applicable receipt predicates are evidenced. For blocked operations publish `Goal Task ID / COSV / attempted operation / head / failed predicate / evidence reference / non-ALLOW disposition / named owner / next authorized attempt` in the **existing** issue and KnowledgeVault monitor; do not create duplicate comments or files. Grok alone updates `INDEX.md` and `GROK_STATUS.md`, Claude updates `CLAUDE_STATUS.md`, ChatGPT updates its existing monitor. If a write is unavailable, leave the exact patch or instruction in this native handoff and use the other coordination surface.

**Checkpoint evidence (not a runtime decision):** Nine existing PRs were open with passing PR-triggered CI at SDK #537 `57beffa`, org #181 `5e8e01c`, Labs #3206 `894a10c`, SV-LLM #41 `c32c1a7`, SV-011 #11 `6c0b281`, GCAT #13 `1d27ab9`, Admissible-Existence #95 `101fad0`, StegGhost #21 `7728427`, StegVerse-002 #47 `692bfb4`. Recheck after any commit. No D6 fix, independent Claude regression, TVC-issued hop credential or authentic sovereign readback was established by that checkpoint.


## 2026-10-17 — owner-requested exact-head merge inventory and repair assignments

Owner instruction: merge PRs that satisfy all existing ecosystem invariants and exact-head checks; write precise remediation for the remainder. **Scope actually inspected:** nine coordinated InTr destination/SDK PRs plus patent-registry PR #5; this is not a claim that every open PR in every ecosystem repository was inventoried. No merge was attempted on a nonconforming head. `mergeable=true` and successful source CI do not establish permission to bypass TV/TVC, missing D6 evidence, draft state or sovereign custody.

| Existing PR | Verified exact head | Source CI / merge state | Required next action before merge |
| --- | --- | --- | --- |
| `StegVerse-org/StegVerse-SDK#537` | `57beffa4ebf5ec4243f6ab219cfbbf2009956d3d` | 8/8 success; open, non-draft, mergeable | Replace/authorize TV/TVC credential path; complete seven route installers or register an evidence-backed exemption; independently verify no live ALLOW claim. |
| `StegVerse-org/.github#181` | `5e8e01cadde072b5f7bd9e7addead8c5c83f7f41` | 1/1 success; open, non-draft, mergeable | Replace `FEDERATION_HOP_TOKEN` with approved TV/TVC-issued capability-scoped credential; repair D6 in org crossing source and add negative tests. |
| `StegVerse-Labs/.github#3206` | `d79c37772c7a7a343c4b57e91eca609b3da62eeb` | InTr Destination Hop success; **Test suite ratchet IN_PROGRESS** at inspected head; open, non-draft, mergeable | Wait for exact-head ratchet result, fix any failures on same branch; repair Labs D6 with tests; replace unapproved token; retain this remediation handoff. |
| `SV-LLM/.github#41` | `c32c1a729f6d49e097132036a7eece21f316fe85` | 2/2 success; open, non-draft, mergeable | Coordinate same TV/TVC issuance and cross-org ingress contract; validate no uncredentialed dispatch. |
| `SV-011/.github#11` | `6c0b281f6d764c1800a389d9ec062278c3e9e33e` | 2/2 success; open, non-draft, mergeable | Coordinate same TV/TVC issuance and authenticated destination evidence. |
| `GCAT-BCAT-Engine/.github#13` | `1d27ab9677398effb3acc79d94edb29dd3ec1ef4` | 1/1 success; open, non-draft, mergeable | Coordinate same TV/TVC issuance and authenticated destination evidence. |
| `Admissible-Existence/.github#95` | `101fad0b1a079eb99016b5eb8bccbba3c3c71de6` | 1/1 success; open, non-draft, mergeable | Coordinate same TV/TVC issuance and authenticated destination evidence. |
| `StegGhost/.github#21` | `7728427fafde6c239f707b99d0e8755b0e81f92c` | 1/1 success; open, non-draft, mergeable | Coordinate same TV/TVC issuance and authenticated destination evidence. |
| `StegVerse-002/.github#47` | `692bfb4dedd9c94c207ef91dda281b9e7d3340b5` | 1/1 success; open, non-draft, mergeable | Coordinate same TV/TVC issuance and authenticated destination evidence. |
| `StegVerse-Labs/patent-registry#5` (separate PAT-003 lane) | `3d4b1a4367cc6c80d33a46fb6c262de19ba2638b` | 1/1 Registry validation success; **DRAFT**; open, mergeable | PAT-003 owner must resolve approved mirror snapshot and crash-consistency/concurrency behavior; Claude independently test torn writes and recovery; do not merge a draft. Update PAT-003 native handoff and #16. |

**Concrete work sequencing:** (1) Grok fixes both D6 branches and corresponding negative tests on existing PR branches; (2) TV/TVC owner supplies an authorized credential issuance contract and evidence, replacing all `FEDERATION_HOP_TOKEN` references in coordinated hop workflows; (3) SDK owner completes or explicitly exempts route installers; (4) Claude independently tests the exact new heads and posts the negative-case matrix; (5) rerun required checks on **each** final head, inspect runtime evidence predicates and receive authenticated sovereign ledger readback for any transition actually attempted; (6) owner-authorized merges use `expected_head_sha` and are verified by re-reading merged state. For non-runtime documentary work, do not invent runtime prerequisites beyond the registered task contract; however these particular hop PRs contain dispatch capability and currently advertise an unapproved credential path.

**Disposition for this inventory:** `NO_PR_VERIFIED_MERGE_READY` in the examined set, for the specific reasons above. This is a source-level coordination conclusion, **not** a sovereign DENY/FAIL_CLOSED event. No merge or runtime transition was attempted. Each repair belongs to its named existing PR/issue; do not create replacement PRs, duplicate issues, new sessions or a second device.


## 2026-10-17 — session-wide 21-PR correction, four completed merges

**Scope correction:** prior ten-PR count was incomplete. Fresh `search_prs(state=open)` across `StegVerse-Labs`, `StegVerse-org`, `SV-LLM`, `SV-011`, `GCAT-BCAT-Engine`, `Admissible-Existence`, `StegGhost`, and `StegVerse-002` found **21 open PRs before merges**. This session-wide instruction applies to **every** active work lane in the coordination KnowledgeVault, not only InTr: execute direct ecosystem remediation wherever authorized; otherwise update the lane's existing canonical GitHub handoff with file-level fixes, owner, tests, evidence and next executable action; synchronize the **existing** KnowledgeVault stream and Grok-owned INDEX (no duplicate files). A source audit cannot veto authorized development. Never make up runtime receipts or replace owner approval.

**Four exact-head-protected merges succeeded** (GitHub reported `merged=true`):
- Labs `StegVerse-Labs/.github#3205`, original head `b50fb13ce65bdd745977015ce404ed2956afeac6`, merge commit `fc14e216f0ca2e038f5f9964add6baa3b6a3f2e7`: `hb_epoch` dispatch input.
- Org `StegVerse-org/.github#182`, original head `4165649b6cbcf2b5efadf6db05e34b3a20fd897a`, merge commit `10d141041fd0fa3b8bd696f6c6236bef199845b8`: ledger self-closure mode.
- SV-LLM `SV-LLM/.github#40`, original head `fe5fa9b1dd1e46716139584253f43f318ea5ccaf`, merge commit `78a5296a3c7bdc7c46c1f1cd35909e799a87c3fd`: `hb_epoch` dispatch input.
- StegVerse-002 `StegVerse-002/.github#46`, original head `c40cdf9444062d795b2e81b21eb1056ee7edb234`, merge commit `b122dfe4654630620cbf650661290da4518f45ba`: `hb_epoch` dispatch input.

**Additional seven PRs omitted from the earlier ten-PR inventory, still needing attention:**
- `StegVerse-Labs/.github#3203` draft, head `abc8f855faee7d6b599b6f540f0a5b719b31c46b`, both Cross-Task Coordination Validation and Test suite ratchet **FAILURE**. Repair external-machine rejection validation on existing branch; run negative flag-bypass tests; obtain owner ready-for-review decision and exact-head green CI.
- `StegVerse-Labs/Executive_Rhetoric_Ledger#226` head `a1148e1a367b858d8cadbadbbd50f26bc7faf979`, Validate Ledger Schemas `action_required` (not success). Investigate check permissions/approval or failing workflow and revalidate. Candidate evidence must not be promoted without governed review. Existing ERL handoff/issue #30 owns follow-up.
- `StegVerse-org/StegVerse-SDK#536` draft, head `b3e934375bc4ecdad71497636df3761f4df1edc3`, 25 successful PR-triggered workflows. Owner review STEGHEALER classifier and OWNER_TASK_ID compatibility, route hash preservation and non-ALLOW remediation semantics; ready-for-review and expected-head merge only when approved.
- `StegVerse-org/StegVerse-SDK#535` non-draft, head `d2a02443d2a2dd64511c655fc68ee866c8ccca2d`, seven successful workflows. Owner resolve governance-gate release-note identity/version and relationship to pending #534; documentation-only integration may proceed independently if it does not assert a release or grant.
- `StegVerse-org/StegVerse-SDK#534` draft, head `d56f45c652ba44cefe609af5b9e6610b95522143`, 22 successful workflows. Owner must authorize version/pin and confirm no release/tag before ready/merge; preserve rollback discipline.
- `StegVerse-org/StegVerse-SDK#533` draft, head `7abe6f3ac65471497fb3452c9d632032df4a6c88`, eight successful workflows. Diagnostic owner to approve source-only MPDV tests and non-authorizing boundaries, then ready/merge.
- `SV-011/.github#9` draft, head `a2ed38a6fcd7a96fc65d18b6496ff979212ca5cd`, three successful workflows. Resolve issue #12 premerge observation semantics and constraint_set grant alignment; no ledger ALLOW inference; owner ready/merge only after evidence.

**Remaining earlier inventory:** the nine hop/SDK PRs `#537/#181/#3206/#41/#11/#13/#95/#21/#47` plus patent-registry draft `#5` are still in the preceding table and require the previously stated repairs. `#3206` head advanced through handoff commits; refresh checks after this documentation commit. Thus **17 of the 21 remain open immediately after four merges** subject to fresh GitHub readback. Do not use the old nine-PR exact heads as current once another commit lands.

**Every work lane's ongoing execution protocol:** (1) discover all currently open PRs in its owning repositories; (2) identify Task ID/COSV and exact head; (3) repair source directly on the **existing** branch if authorized; (4) independently test and rerun exact-head CI; (5) merge with `expected_head_sha` if owner authority and applicable invariants permit; (6) re-read merge and ledger evidence separately; (7) for anything not executable, write precise remediation in that lane's native handoff and the existing KnowledgeVault coordination stream, with a named next actor. Never block source-only work on fictional external devices or an unexposed runtime; never claim runtime ALLOW from a merge.
