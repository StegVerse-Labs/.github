# Substrate-Neutral Decision Predicate Mirror Handoff

Updated: 2026-10-05
Repository: `StegVerse-Labs/.github`
Goal Task ID: `SUBSTRATE-NEUTRAL-DECISION-PREDICATE-001`
COSV: `10100000110000`
Native owner: issue #2955
Registration lifecycle: #2956 CLOSED/unmerged -> #2958 MERGED (`8dd7dca9afed1f7d8ae512c4820b85faafbdd093`)
Status: `PROPOSED / UNCLAIMED`

## Purpose
Define and experimentally validate a substrate-neutral operational decision predicate. The experiment asks whether controlled evidence perturbation produces relevant, counterfactually discriminating, traceable selection behavior. It does not presuppose or establish consciousness, sentience, personhood, free will, human equivalence, moral/legal agency, execution authority, or governance authority.

## Canonical sources
- `experiments/substrate-neutral-decision-predicate.v1.json`
- `schemas/substrate-neutral-decision-receipt.v1.schema.json`
- `data/canonical-task-records/SUBSTRATE-NEUTRAL-DECISION-PREDICATE-001.json`
- `control/task-vectors/SUBSTRATE-NEUTRAL-DECISION-PREDICATE-001.json`
- `control/task-vector-index.d/SUBSTRATE-NEUTRAL-DECISION-PREDICATE-001.json`
- `data/canonical-task-registry.json`

## Required experimental predicates
P1 alternative availability; P2 evidence sensitivity; P3 relevance discrimination; P4 counterfactual differentiation; P5 selection commitment; P6 traceable consequence.

Each predicate returns exactly one experimental result: `PASS`, `FAIL`, or `INDETERMINATE`.

## Semantic firewall
`DECISION_OBSERVATION::{PASS,FAIL,INDETERMINATE}` is an experimental namespace.
`GOVERNANCE_DISPOSITION::{ALLOW,DENY,FAIL_CLOSED}` remains the governed-transition namespace.

No mapping between those namespaces grants authority. In particular, experimental PASS is not ALLOW, FAIL is not DENY, and INDETERMINATE is not FAIL_CLOSED.

The experimental terminal state is `DECISION_EVENT_OBSERVED`. Any later proposed transition remains independently subject to the existing authority/admissibility/execution/receipt pipeline.

## Current work
Source registration and schemas are merged on canonical main through replacement PR #2958. Experiment activation now uses the minimum LLM fixture `experiments/substrate-neutral-decision-llm-minimal.v1.json`; no experimental result is claimed until authentic trial outputs and retained evidence exist. The repository-required execution substrate review is present: the five same-device/ephemeral candidates remain PENDING_EVIDENCE / EVIDENCE_REACHABILITY, the external-device last resort is NOT_APPLICABLE, no substrate is selected, and no external or second user-operated device is required. This is registration validation only. No experiment has been run. No participant result exists. No WorkerCoordinator claim/fence, Interlock/InTr admission, runtime execution, Master Records experimental organization records, deployment, or propagation is claimed.

## Completion
Completion requires controlled trial families across eligible subject classes, adversarial controls, retained receipts satisfying the receipt schema, reproducible predicate evaluation, and evidence sufficient to distinguish PASS, FAIL, or INDETERMINATE without substrate-specific assumptions.

## Human action
None currently required.
