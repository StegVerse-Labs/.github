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
- `StegVerse-Labs/Governance` README and `GOVERNANCE_MIRROR_HANDOFF.md`: policy-version semantics, immutable GDRs. Governance #16 already owns G0–G6 / A0–A8 taxonomy and failure schema; #30 connector profiles. SVG must extend or map under native owner, not duplicate.
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
