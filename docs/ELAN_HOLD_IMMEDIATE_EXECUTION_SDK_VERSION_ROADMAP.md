# HOLD delivery and capability roadmap — 2026-09-25

Goal: ELAN-PAPER-COAUTHOR-PUBLICATION-001; COSV 71000000100100. This plan reuses current SDK, Manifest Builder and Publisher owners. It establishes immediate HOLD delivery without waiting for future general-purpose releases.

## Parallel execution

**Native ÉLAN lane (start now):** Send Élisabeth the exact ordered HOLD protocol for joint approval. After approval she can run actual API requests, preserve raw responses, timestamps, request/session metadata where available, errors and the separate no-request control, then deliver immutable result blocks. Collection does not await new SDK releases. No absence-of-prompt interval is model output.

**SDK lane (start now):** Complete SDK PR #340's generic source-observation guard via current public Manifest Builder and installed diagnostic/governance processors. Its fixtures are synthetic and cannot stand in for ÉLAN. Once real results arrive, validate attribution, build the unchanged manifest, execute through the installed route and preserve the next real disposition. Correctable DENY receives a distinct successor attempt; FAIL_CLOSED terminates that attempt. Do not declare a live runtime from source tests.

**Evidence/Publisher lane:** Freeze original ÉLAN result bytes before SDK evaluation. Reuse the existing Publisher reviewer evidence package when a manifest declares it, including original attachments only with authorization. Distinguish locally generated review documents from authenticated publisher and external-delivery transitions.

**Publication lane:** The corrected historical Test 2 and existing FAccT draft remain available for coauthor review. Include new HOLD findings only once real execution evidence exists; writing continues independently of SDK upgrades. FAccT target dates: October 27 abstract and November 3 full paper, with internal evidence checkpoint October 10–15.

## Current source-backed capabilities

| Surface | Confirmed source contract | Proof still needed for HOLD |
| --- | --- | --- |
| SDK | Generic source-native manifests, hashes, caller-selected projection, published evaluator declarations, existing governance and diagnostic processor bindings, worker processors, replay/reconstruction entrypoints. | Actual new HOLD run through the evaluator-visible public route, exact runtime disposition and retained original custody. |
| Manifest Builder (SDK-owned) | Constructs stegverse.ingress-manifest.v1 from arbitrary native data, explicit processor request, chosen installed route and return depth; supports declared Publisher and SOUTH stages. | Optional generic source-observation profile from PR #340, malformed attribution rejection and a real ÉLAN payload test. |
| Read-only SDK diagnostic | Returns NOT_OBSERVED / PROBE_REQUIRED from supplied evidence; no mutation or authority. | Diagnostic cannot itself query ÉLAN or authenticate self-declared native output. Real source and independent verification remain distinct. |
| Publisher | Static paper metadata; owner-authorized KV document conversion; generic SDK reviewer package v1 with original evaluator_assets byte/hash retention and transfer/return contract. | Original ÉLAN attachments and result bindings under actual approved use. Generated output alone does not prove publication or external delivery. |
| Interlock/InTr and Master Records | Existing governed ingress/egress and canonical custody contracts. | Authentic request-bound runtime, predecessor, custody and far-side evidence for this exact HOLD run, when those stages are claimed. |

The historical SDK cross-evaluation script still embeds the superseded human-authored native-presence claim and uses a simulated InTr resolver. Retain it as historical evidence; never run it as corrected ÉLAN science.

## Proposed release and contract gates

**Existing SDK 1.3.0 release candidate:** VERSION.json says RELEASE_CANDIDATE, not tagged GA; TV/TVC publication remains separately required. Moving main declares 1.4.0.dev0, which must not be passed off as frozen 1.3. Manifest Builder is SDK-owned, not an independently verified release. Publisher component release number was not verified; its report package profile is v1.

**SDK 1.4.0 / Manifest Builder v1 HOLD-compatible extension — immediate milestone:** Provider-neutral source-observation preflight, optional attribution guards on generic manifests, no-request and actual invocation controls, precise distinct outcome classes and tamper tests. Reuse installed route; do not create an ÉLAN-only processor. Run authentic HOLD input through the same evaluator public API, preserve actual disposition/custody/replay or the first exact failure receipt. Source tests passed and PR #340 merged on Sept 25; actual HOLD processing as soon as joint-approved source arrives, target by October 10. An exact run and released package are separate gates.

**Publisher report package v1 HOLD binding — same milestone:** Owner-authorized original native source, exact SDK evidence, separate human/client/model provenance, report artifacts and an exact manifest; retain explicit GENERATED_NOT_PUBLISHED until genuinely authorized delivery. No independent Publisher component semver is assumed.

**SDK 1.5.0 — proposed next milestone:** General evaluator-defined multi-condition test composition, explicit installed-capability diagnostic, evidence-by-requirement qualification and reusable independent-verification packet. Acceptance: two unrelated external-framework test fixtures through the same public interface with observable unsupported/denied cases and full source/custody boundaries. Reserve scope for unexpected evaluator needs. Not a HOLD prerequisite.

**SDK 1.6.0 — proposed later milestone:** Extensible governed processor/plugin registration, external-framework interoperability, complete Publisher return and far-side evidence where supported, and reproducible portable evaluator setup. Acceptance: independent evaluator verifies supported end-to-end experiment without privileged internal commands or a second user-controlled device. Not a HOLD prerequisite.

## Change admission

A new requirement directly needed for HOLD enters the 1.4 vertical slice as a reusable guard, adapter or public interface extension. Missing source-native provider evidence is collected by the external operator, not synthesized by SDK. Broad optional enhancements go to 1.5; genuinely new processors or integrations require authorized Task Registry ownership and a separately demonstrated route. Every requested capability receives a documented supported, source-only, unknown, unsupported or authentic-denial disposition instead of one unsupported global PASS.

## Completion definition

HOLD is not complete merely because the generic validator and CI pass. Completion requires a real, jointly agreed ÉLAN invocation and exact native output/nonresult, no-request attribution controls, a genuine public SDK manifest submission, authentic applicable transition disposition, original custody and verifiable replay/reconstruction at the level actually observed. For review-facing full-cycle manifests, Publisher and external delivery must also be verified or expressly marked not observed. Coauthor approval remains separate for exact scientific protocol and final FAccT submission.
