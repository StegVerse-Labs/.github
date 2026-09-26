# SVG Governance-Cycle Capability Versioning — Admission Mirror Handoff

**Coordination state:** ADMISSION_REQUESTED / NOT_CANONICALLY_REGISTERED  
**Central intake:** [StegVerse-Labs/.github#2757](https://github.com/StegVerse-Labs/.github/issues/2757)  
**Candidate Goal Task ID (NOT ISSUED):** `SVG-GOVERNANCE-CAPABILITY-VERSIONING-001`  
**COSV:** UNASSIGNED — must derive from authentic existing Task Registry admission  
**Last read:** central generation 251, 92 tasks, Registry blob `1eb23ccd55fa42299e37a95c0851b8e9b1bd1aa7`  
**Source effect:** proposal only; no credential, policy, runtime, execution, hardware, product-release or publication authority.

## Why this proposed goal is separate
StegVerse Governance (SVG) capability versioning concerns the **observable properties of a correctly governed transition cycle**, not the version of any AI entity or the authority it holds. SV-011 is an independent AI entity. Distinguish (a) policy/contract versions, (b) implementation/conformance profile versions, (c) observation/evidence resolution and measured physical capability and (d) AI entity identity and legitimately delegated authority. A more capable entity cannot self-promote authority merely by upgrading hardware.

## Proposed core cycle
Authenticated constraints/observations -> admissibility disposition -> authorized consequence (if ALLOW) -> original organization evidence and independent custody reconstruction -> updated constraints. DENY, FAIL_CLOSED and other non-ALLOW transitions retain explicit attempted-transition evidence; unobserved evidence is never misreported as an authentic runtime DENY.

## Canonical ownership and collision map to adjudicate
- `StegVerse-Labs/Governance` README and `GOVERNANCE_MIRROR_HANDOFF.md`: policy-version semantics, immutable GDRs. Governance #16 (CLOSED 2026-09-24) owns the G0–G6 / A0–A8 taxonomy and failure schema; #30 connector profiles. SVG must extend or map under native owner, not duplicate.
- `StegVerse-Labs/repo-standards` [ST-020 versioned capability propagation](https://github.com/StegVerse-Labs/repo-standards/blob/main/standards/ST-020_VERSIONED_CAPABILITY_PROPAGATION.standard.md), issues #52/#55: reusable compatibility/migration/consumer-binding and released/distributed/installed/activated/runtime-observed separation. Do not reissue ST-020. Distinguish unrelated branch-lifecycle naming collision by exact file path.
- `StegVerse-Labs/StegCore` existing AdmittedCode performance policy/benchmark: native owner chooses bounded reference adapter and measures against current work. The proposed SVG benchmark does not claim those results.
- Existing SDK/InTr/Interlock, StegOS, StegID, TV/TVC, organization event history and Master Records retain their native authorities/evidence. Benchmark has authority_effect=NONE. Do not create another runtime or require any second user-operated machine.
- Hardware/Infra ownership must be discovered and approved separately before hardware-specific implementation. Existing single-host CPU path is the portability baseline; accelerators are optional profiles.

## Proposed measurable hardware-independent capability contract (non-normative until admitted)
Each sample declares `governance_contract_version`, `policy_hash`, `constraint_state_hash`, `input_manifest_hash`, `entity_id`, `authority_context_ref`, `hardware_profile`, `workload_profile`, `evidence_assurance`, `measurement_class` (`synthetic` / `source-test` / `authentic-runtime`), `original_receipt_refs`, and when authentically present `independent_reconstruction_ref`. None of these fields grants authority.

Measurements: stage and full-cycle p50/p95/p99 latency; admitted throughput; correctly refused throughput (DENY/FAIL_CLOSED separately); error and false-admission rates from labeled tests; observation resolution and uncertainty; custody/reconstruction success; energy/joules per verified transition only where directly metered. Define measurement-window boundaries, workload and confounders before comparison. Incomplete custody is a distinct status, not a completed verified transition.

Deterministic conformance candidates: ALLOW, DENY, FAIL_CLOSED, stale constraint, revoked permission, missing/ambiguous evidence, replay, interrupted recording/restart, concurrent entities, and partitioned/disconnected operation. Tests prove schema behavior only. Real claims require original sovereign execution and independent Master Records reconstruction.

## Immediate admission transition
1. Read the latest canonical Registry and exact associated task shards/handoffs; obtain real AI_SESSION_GATE collision result on [#2757](https://github.com/StegVerse-Labs/.github/issues/2757).
2. Reuse an existing Goal Task ID if the native owner establishes a collision, otherwise register the approved new identity and genuine canonical COSV through existing admission, with source/task index projections.
3. Record exact owner assignments for Governance contract, repo-standards compatibility, StegCore benchmark and optional native Infra research. No ownership reassignment by this proposal.
4. On ALLOW, advance only approved owner-specific source through independently reviewed exact-head CI and expected-head-protected merges. On DENY, record and fix specified predicates. On unavailable gate, preserve UNKNOWN_NOT_AUTHENTICALLY_OBSERVED without inventing disposition.
5. After true conformance and authentic live evidence, separately request release and downstream propagation verification.

## Latest session evidence
- 2026-09-25: central Registry generation 251 / 92 rows read through GitHub; relevant existing Governance, repo-standards and StegCore sources read.
- 2026-09-25: central admission request #2757 created; branch holds this proposal and a README pointer only.
- No Task Registry admission, COSV allocation, authentic InTr invocation, hardware benchmark, independently verified receipt, release or propagation yet.

## Gate-source reconciliation — 2026-09-25 follow-up

Original source `scripts/evaluate_task_registry_ai_session_checkin.py` on current central main was inspected. For `CHATGPT_SESSION`, the existing public CLI returns `STOP_AUTHENTIC_ORIGIN_UNAVAILABLE` before the canonical evaluator or event-ledger write because no authenticated host-to-resident session origin is supplied by that CLI. A caller-crafted `session_id`, `actor_kind`, or attestation object cannot repair that boundary. This session cannot produce an authentic `AI_SESSION_GATE` disposition by calling that public source through GitHub; no surrogate or forged event is permitted. Component-010 issue #1620 retains native ownership of the trusted ingress interface. Proposed SVG registration remains a **source-admission proposal**, not a runtime check-in.

GitHub readback of intake #2757 and PR #2758 found no admission response, comments or independent approval; current default Registry remains generation 251 / 92 rows. Draft PR original exact head `0a8515bfdcb4cedbea1839a2ec976872d43a6748` had two successful PR workflow runs (`36215827716`, `36215827722`), but no complete required-check or independent-owner clearance was established. The draft branch was ahead of main by two commits and not behind at that read. Any later source mutation invalidates those exact-head results.

**Actionable alternative while component-010 ingress is unavailable:** ask the existing Task Registry source owner to adjudicate the candidate as an explicitly coordination-only source registration, following current exact-shard/aggregate/index rules and current-main reconciliation; this would still **not** create a genuine runtime session check-in. Assign the source owner and native Governance/StegCore/repo-standards signoffs first. If owner policy requires the authentic component-010 event before source registration, record a precise DENY with the trusted-interface requirement, not a synthetic ALLOW or perpetual unspecified wait. A genuine admitted COSV must come only from canonical owner-approved registration.

**Benchmark implementation boundary:** The metrics listed above are *review inputs*, not a published conformance standard. After canonical source admission, produce versioned schemas/fixtures/reference runner under the actual named native owners. Distinguish exact provenance of deterministic simulated durations from wall-clock values; calibrate monotonic timing, warm-up/sample count, workload complexity and input-size distribution. Track correctly admitted, correctly refused, falsely admitted, falsely refused, UNKNOWN and incomplete-custody events separately. The final denominator for `verified_transitions_per_second` must require original execution evidence plus the independent reconstruction required by that transition; a synthetic baseline cannot count. No mandatory GPU, hardware enclave, remote resident, second device, or newly minted authority.

## Native source-owner collision refinement

Governance issue [#16](https://github.com/StegVerse-Labs/Governance/issues/16) was independently read back as CLOSED (2026-09-24): the G0–G6/A0–A8 specification already has an established owner. Do not reopen or fork that taxonomy for SVG. The SVG proposal concerns cross-stage observations and versioned benchmark profile *only*. Repo-standards [#52](https://github.com/StegVerse-Labs/repo-standards/issues/52) remains OPEN for ST-020 advisory propagation; issue #55 covers consumer-binding refinements. Current StegCore [AdmittedCode performance contract](https://github.com/StegVerse-Labs/StegCore/blob/main/docs/ADMITTEDCODE_PERFORMANCE.md) already implements bounded core-evaluation latency, concurrency 1/10/50, resource measures and correctness/fail-closed acceptance. SVG's only prospective new benchmark scope is end-to-end original-observation → native admissibility → **real consequence** → original receipt → independently reconstructed evidence → next-constraint feedback, with explicit per-stage latency and version binding. Reuse StegCore performance receipt and runner where the native owner approves; do not duplicate existing core timing or claim full-cycle proof from that benchmark. No new hardware code until an actual eligible owner is identified.

## Registry / branch reconciliation — 2026-09-26

Latest independently reread canonical main Registry: generation **259**, **92** tasks, blob `a473b9a6da80512cb071abd34799f6ac3c02024e`; exact SVG candidate is still absent. No native decision, authentic AI_SESSION_GATE event or allocated COSV appears on issue #2757 or PR #2758. The original draft diverged 106 commits behind current main; this branch reconciliation merges current main ancestry and keeps all concurrent main contents. A previous exact-head success belongs only to previous head `d6590f2e5236e20009f5e474164d50f23de9fcbe`, not this new head. Review fresh exact-head CI and current-main ancestry before any merge. The original public AI_SESSION_GATE cannot authenticate a ChatGPT session; await an authentic existing owner disposition rather than forging one.
