# Universal User-Facing Explanation Contract Mirror Handoff (scaled-up HIL experiment)

Status: ACTIVE (source merged; experiment preregistered, NOT_MEASURED)
Updated: 2026-10-11
Repository: `StegVerse-Labs/.github`
Issue: `StegVerse-Labs/.github#3106` (coordinates with `StegVerse-Labs/Site#1509`, `StegVerse-Labs/crypto-bot#23`)
Contract: `stegverse.user-facing-explanation/v1` (`schemas/user-facing-explanation.v1.schema.json`)
Experiment: `HIL-SCALED-EXPLANATION-001` (candidate id; `schemas/hil-explanation-trial-record.v1.schema.json`)
Registry state: PROPOSED / NOT YET REGISTRY-ADMITTED. This handoff records source and a preregistered protocol; it is not task admission, approval, or evidence of measurement.

## Research origin (owner-reported attribution; preserve verbatim)

This scaled-up HIL experiment originated entirely from the conversation between Rigel Randolph and Sara Katpar.

Reference supplied by the owner: https://www.linkedin.com/in/sara-katpar-8b13b0348. The participant's name spelling is taken from that URL as supplied by the owner and is to be confirmed with the participant before any further biographical claim is published. This document records the owner's attribution; it is not an independently verified account of that conversation. Future derivatives of this contract or experiment must carry this statement unchanged; it must not be erased, diluted, or replaced.

## Connection to the original HIL experiment

The original Human-in-the-Loop (HIL) experiment placed a person in an ordinary browser context as the producer of request-bound evidence that the sovereign receiver validates (`SHWP-HIL-SOVEREIGN-RECEIVER-001`, `docs/HIL_BROWSER_EVIDENCE_INTAKE_MIRROR_HANDOFF.md`, `docs/HIL_RUNTIME_OBSERVATION_20260907_MIRROR_HANDOFF.md`). Its lesson was that a human and a governed system can exchange exact, verifiable artifacts without either side holding privileged access to the other.

The scaled-up experiment turns that exchange outward: every public-facing outcome in the ecosystem is explained to the person in prose and, optionally, as one self-contained JSON artifact that the person can hand to any independent LLM. The human stays in the loop as the interpreter and decider; the ecosystem stays governed because the artifact can describe but never authorize.

## The contract

One versioned artifact across WorkSpace, MyKV, StegTalk, CryptoBot, Developer surfaces and every other public StegVerse surface. Builder: `scripts/user_facing_explanation.py` (`build_explanation`, `render_prose`, `validate_explanation`). Site mirror: `assets/workspace-explanation.js` in `StegVerse-Labs/Site`.

Every artifact carries:

- `outcome`: `disposition` (ALLOW | DENY | FAIL_CLOSED | UNKNOWN), `observation_state`, `outcome_class` (SUCCESS_VERIFIED | AUTHORIZED_NOT_VERIFIED | DENIED | FAILED_CLOSED | UNOBSERVED), the exact canonical `predicate` and `predicates`, and the canonical record locator.
- `authorization` and `execution` as separate facts: `authorized`, `requested_action`, `authority_source`; `executed`, `execution_state` (VERIFIED | NOT_EXECUTED | NOT_VERIFIED), `consequence_observation`. ALLOW never implies execution; execution is VERIFIED only with receipt-class evidence and an OBSERVED consequence.
- `prose` (displayed by default): what happened, why, outcome summary, what was authorized, what was executed, what evidence exists, what the person can safely do next, limitations. Prose never shows raw JSON, unexplained variables or predicates as the primary experience.
- `terminology`: every technical term with a definition (ALLOW, DENY, FAIL_CLOSED, UNKNOWN / NOT_AUTHENTICALLY_OBSERVED, predicate, manifest / ACTION BY MANIFEST, KV projection, receipt, Task Registry / COSV, Interlock / InTr, authorization versus execution) plus surface-supplied terms.
- `evidence`: sanitized locators with descriptions only (RECEIPT_REF | PROVENANCE_REF | SOURCE_REF | PUBLIC_URL | DIGEST | NONE); never contents, never invented.
- `remediation_draft` (optional): an unsubmitted, non-authorizing manifest draft (`submitted: false`, `manifest_admitted: false`, `authority_effect: NONE_REQUEST_ONLY`, `non_authorizing: true`). Submission is a separate governed decision through the existing Task Registry / COSV, manifest, SDK and Interlock/InTr paths.
- `llm_interpretation`: instructions, prohibited assumptions, `self_contained: true`.
- `authority`: `authority_effect: NONE`, `explanation_is_non_authoritative: true`, `canonical_record_mutation: false`, `alternate_governance_path: false`.
- `sanitization`: `secrets_present: false`, `personal_data_minimized: true`, `invented_evidence: false`. The builder refuses any record or surface descriptor carrying secret-shaped keys or values and copies only whitelisted fields.
- `recognition_probe`: `STEGVERSE_ECOSYSTEM_KNOWLEDGE_PROBE_V1`, status CANDIDATE_NOT_CANONICAL.

## Five distinctions every surface must keep

| Layer | What it is | What it can do |
| --- | --- | --- |
| Explanation | the prose and JSON artifact | describe a canonical outcome |
| Interpretation | what a person or an independent LLM concludes from the artifact | inform a decision |
| Proposed action | an unsubmitted remediation draft | be submitted through the governed path |
| Governance authorization | a Task Registry / COSV, manifest, Interlock/InTr decision (ALLOW / DENY / FAIL_CLOSED) | admit or refuse a transition |
| Verified state transition | the performing component's receipt and observed consequence | prove that something happened |

No layer above may stand in for a layer below it. An explanation that claims an authorization or a transition it cannot locate by receipt is invalid (`validate_explanation` refuses it).

## Fixtures and published examples

`data/user-facing-explanation/fixtures.d/` holds five SYNTHETIC_TEST outcome records (success verified, denied with draft, fail-closed, authorized-not-verified / missing evidence, unobserved runtime). `data/user-facing-explanation/examples.d/` holds the generated artifact and prose for each; `scripts/render_user_facing_explanation_examples.py --check` proves they have not drifted. Tests: `tests/test_user_facing_explanation.py`.

## Scaled-up HIL experiment

Protocol: `docs/HIL_SCALED_EXPLANATION_EXPERIMENT_PROTOCOL.md`. Preregistration: `data/hil-explanation-experiment/preregistration.json`. Source: `scripts/hil_explanation_experiment.py` (stimuli for conditions A/B/C from the same fixture, HIL-3 probes, deterministic rubric, trial validation, summary). Results: `data/hil-explanation-experiment/results.json`, currently `NOT_MEASURED` with zero trials. Tests: `tests/test_hil_explanation_experiment.py`.

Dimensions: HIL-1 human effectiveness; HIL-2 ecosystem interpretability across independent LLM providers and models; HIL-3 ecosystem knowledge acquisition and persistence. Recognition-literal protocol and its limitations are in the protocol document: echoing the literal is scored LITERAL_ECHO_ONLY and never counts as knowledge; blind probes carry neither the literal nor JSON; cross-session training may be claimed only in a fresh, unexposed session with holdout recognition and written evidence ruling out public retrieval, account memory, session carryover and pre-existing model knowledge.

## Surface implementation and compatibility requirements

1. Produce the artifact only from a canonical disposition record the surface already holds; never from narration.
2. Show prose by default; offer the complete JSON behind an explicit control with accessible copy or export.
3. Pass the artifact through `validate_explanation` (or the Site mirror's equivalent) before display; refuse to display an artifact that fails.
4. Keep the canonical disposition visible alongside the explanation; the explanation never replaces it.
5. Never submit, execute or record from the explanation surface; a remediation draft is a proposal the person carries into the governed path.
6. Version: `explanation_version` 1.0.0; additive changes bump the minor version and keep every required key; a removed or renamed key is a new major schema id.

## Owner work not executable from this lane

- Canonical Task Registry / COSV admission of the explanation contract and of `HIL-SCALED-EXPLANATION-001` through the owner-approved workflow (ChatGPT reconciliation on #3106: `CANONICAL_TASK_ADMISSION_AND_WORKERCOORDINATOR_CLAIM_NOT_VERIFIED`).
- Canonical approval of the recognition literal.
- Running trials: human participants (opt-in), independent LLM providers and models, fresh signed-out and ordinary signed-in sessions, holdout questions and control identifiers kept outside every repository.
- Confirming the participant's preferred name spelling.
