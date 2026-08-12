# VACC Longitudinal Continuity Mirror Handoff

## Authority

This is the canonical provisional continuation record for the VACC longitudinal continuity-risk / care-relationship capability recovered from the 2026-08-12 session until a dedicated VACC repository is designated. Organization-wide authority remains `docs/ORG_MIRROR_HANDOFF.md`; repository-local implementation evidence in a future VACC repository will supersede this provisional implementation location after explicit transfer.

## Active goal and goal ID

```text
goal_id: VACC-LONGITUDINAL-CONTINUITY-001
originating_session_goal: extend VACC from claim-record review into governed longitudinal care-continuity analysis that can surface evidence-based potential care gaps, disengagement signals, and alternative engagement pathways without overclaiming causation or fault
repository: StegVerse-Labs/.github
branch: main
canonical_issue: StegVerse-Labs/.github#87
claim_state: CLAIMED_FOR_INTEGRATION_AND_REQUIREMENTS_TRANSFER
canonical_owner: StegVerse-Labs/.github#87 until dedicated VACC repo designation
active_implementation_claim: none in a dedicated VACC repo; no connected repository named VACC was found
active_validation_claim: this session owns de-identified reference-fixture definition and requirements reconciliation
claim_created_at: 2026-08-12T11:56:05-05:00
claim_release_condition: dedicated VACC repo designated; repo handoff installed; requirements transferred; executable implementation + tests evidenced
thread_archive_ready: false
```

## Originating and adjacent goals preserved

1. Longitudinal record sufficiency gate before care-quality/continuity conclusions.
2. Potential deficiency / unresolved-care detection across substantial VA records.
3. Concise provider-facing pre-encounter summary with traceable evidence and confidence.
4. Adverse characterization context review for labels such as non-compliant, aggressive, hostile, disruptive, or similar terms.
5. Preserve Veteran-originating concern separately from provider interpretation; detect semantic/interpretation mismatch.
6. Characterization provenance, age, temporal validity, and contradictory evidence.
7. Multi-signal care-disengagement trajectory detection without deterministic suicide/homelessness prediction.
8. Alternative engagement pathway identification when the current care relationship may itself be contributing to disengagement; human review required.
9. Prescription-state provenance: expiration/refill exhaustion != clinical ineligibility or contraindication.
10. Request -> portal transaction -> routing -> prescriber authority -> pharmacy release -> replacement-Rx lineage reconstruction.
11. Treat refill/renewal portal events as evidentiary transactions even when outside secure messaging or omitted from Blue Button narrative exports.
12. Prior-evaluation sufficiency check using recent ED/inpatient/provider vitals, labs, medication reconciliation, treatment response, and record acknowledgement before describing a request as medication requested without evaluation.
13. Preserve medication scope in disputed encounters; the recovered reference scenario concerns longstanding BP + GERD therapy, not new medication, narcotics, controlled substances, or dose escalation.
14. Longitudinal quality metric may be initiated when the uploaded record reaches a governed sufficiency threshold and should be available as a care-continuity summary at encounters.
15. Milestone/publication obligation: once implemented/released, propagate pertinent status to Site, Publisher, admissibility-wiki, stegguardian-wiki and applicable master-records surfaces.

## Governance contract

The system must preserve these distinct states:

```text
OBSERVATION
INFERENCE
POTENTIAL_DEFICIENCY
CLINICIAN_DETERMINATION
ACTION
NOT_EVALUABLE
INSUFFICIENT_EVIDENCE
CONTRADICTORY_EVIDENCE
```

It must not silently collapse one state into another. Missing coverage must fail closed to `NOT_EVALUABLE` or bounded uncertainty. The system must not autonomously diagnose malpractice/negligence, remove safety flags, change treatment, transfer care, or make deterministic suicide/homelessness predictions. Legitimate safety concerns remain visible and attributable.

## De-identified reference fixture

The first validation fixture shall model this chronology without retaining personal identifiers:

1. longstanding chronic antihypertensive and GERD treatment predating the disputed PCP relationship;
2. antihypertensive prescription authored in 2022, final 90-day fill in June 2023, no refills remaining, nominal expiration in September 2023;
3. August 2023 provider instruction that PACT visit/labs are required for further medication refills;
4. later 2023 VA encounters containing vitals, laboratory data, medication reconciliation, examinations, and provider assessments;
5. January 2024 hypertensive-urgency episode after antihypertensive exhaustion and documented difficulty obtaining PCP refill; medication restarted with clinical improvement;
6. February 2024 encounter where a medication-continuity concern and provider interpretation diverge;
7. later 90-day pharmacy release under a distinct prescription lineage;
8. portal refill-request provenance is unavailable in the narrative export even though the normal patient workflow can occur outside secure messaging;
9. every derived finding records proven / inferred / unavailable / contradictory status.

## Required implementation components

A dedicated VACC repository or canonical VACC application repository must contain at minimum:

```text
contracts/longitudinal_record_sufficiency.schema.json
src/.../longitudinal_sufficiency evaluator
src/.../care_continuity_signal extractor
src/.../characterization_provenance evaluator
src/.../interpretation_mismatch evaluator
src/.../prescription_provenance reconciler
src/.../prior_evaluation_sufficiency evaluator
src/.../continuity_risk_summary generator
tests/fixtures/deidentified_medication_continuity_case.*
tests for NOT_EVALUABLE / contradictory evidence / provenance / no-overclaim behavior
provider-facing summary contract with evidence pointers
```

Exact language/runtime paths may adapt to the canonical VACC repository after designation, but the functional requirements above are mandatory unless explicitly superseded with evidence.

## Automation / task ownership

Machine-readable task: `handoffs/VACC-LONGITUDINAL-CONTINUITY-001.json`.

Canonical durable owner: `.github#87`. The task is not classified as an unspecified external task. Until repository designation, #87 owns repository-resolution, handoff transfer, implementation claim creation, validation claim creation, and cross-repository integration. After transfer, the future VACC handoff must name the implementation worker and machine-observable release conditions.

## Collision check

Connected GitHub search on 2026-08-12 found no repository named VACC and no indexed StegVerse-Labs code matching the VACC longitudinal-continuity requirement. Therefore this session is not duplicating an observed active implementation claim. If a later canonical repo is discovered, #87 and this handoff must be updated to `MERGED_INTO_CANONICAL_WORKSTREAM` rather than creating competing implementations.

## Local-model/runtime convergence

The originating session also inherited the local-model/runtime task. That work is not owned here and must not be duplicated:

```text
formal local model: COMPLETE_RELEASED
local runtime discovery/launch/inference/proof: COMPLETE_RELEASED
GitHub-token production/control authority: NONE
credential/route semantics: TV/TVC
canonical source handoff: StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md
runtime activation owner: StegVerse-Labs/.github#59 + #65 + resident sovereign heartbeat
Ecosystem Chat inference owner: StegVerse-Labs/.github#60 + resident sovereign heartbeat
```

The unresolved local-runtime activation lane is machine-owned and physical-carrier dependent; hosted GitHub/Render/Vercel/Cloudflare execution is not an authorized substitute.

## Validation commands / acceptance criteria

Until the VACC repo is designated, validation is requirements-level only. The eventual implementation must provide executable commands that prove:

- insufficient record -> NOT_EVALUABLE;
- adequate longitudinal record -> deterministic sufficiency result;
- adverse characterization is context-reviewed, not treated as proof of patient fault;
- originating concern and provider interpretation remain separately attributable;
- prescription expiration and refill exhaustion remain distinct from clinical ineligibility;
- portal request absence from a narrative export does not become proof that no request occurred;
- prior ED/inpatient/provider evaluations are considered when assessing later `without evaluation` characterizations;
- summary output is concise, evidence-linked, non-deterministic, and does not autonomously change care.

## Cross-repository dependencies / propagation

Upon implementation/release, verify and record pertinent propagation to:

```text
StegVerse-Labs/Site
GCAT-BCAT-Engine/Publisher
admissibility-wiki
stegguardian-wiki
master-records as required by live contracts
```

No propagation is claimed complete by this handoff.

## Session consolidation state

```text
local-runtime discovery/launch/proof requirement: MERGED INTO CANONICAL WORKSTREAM / source complete
formal local-model requirement: MERGED INTO CANONICAL WORKSTREAM / source complete
no-GitHub-token runtime authority requirement: COMPLETE_RELEASED / TV/TVC authoritative
VACC longitudinal continuity requirement: DURABLY TRANSFERRED TO .github#87 + this handoff, implementation not complete
session-specific chat-only VACC requirements after this commit: 0 expected
archive dependency: VACC requirements are preserved, but this session still holds a distinct integration/requirements-transfer role until machine-readable task is installed and direct repository evidence is verified
```

## Incomplete work

1. Designate or discover canonical VACC implementation repository.
2. Read/create its applicable `*_MIRROR_HANDOFF.md` before mutation.
3. Transfer #87 + this handoff requirements.
4. Install executable longitudinal sufficiency, continuity, characterization, prescription-provenance, and summary logic.
5. Install de-identified fixtures and tests.
6. Validate strongest available local/CI path.
7. Record implementation commit/PR/workflow evidence.
8. Propagate release/status obligations when criteria are met.

## Completeness

```text
developed_files: 1/9 required implementation/handoff deliverable groups at provisional owner
scaffolding_or_stubs: 0
missing_required_files: 8 implementation groups pending canonical repo designation
validation: 1/8 requirements-transfer validations complete
integration: 1/6 provisional integration steps complete
propagation: 0/4 minimum named public propagation surfaces verified
session_consolidation: 4/5 session goal groups durably transferred-or-complete; VACC implementation continuation remains active
VACC goal_activation: 15%
```
