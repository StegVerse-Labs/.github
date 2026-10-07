# Master Records bulk semantic remediation 002 mirror handoff

Updated: 2026-10-07
Goal Task ID: `MASTER-RECORDS-BULK-SEMANTIC-REMEDIATION-002`
Parent Goal Task ID: `CANONICAL-MASTER-RECORDS-STATE-TRANSITION-CUSTODY-001`
COSV ID: `50000000100000`
Status: `ACTIVE / CHECKED_OUT / INVENTORY-DRIVEN BULK REMEDIATION`

## Owner rule
Master Records relates to organization records; the only other permitted reference is reconstruction. Organization owns runtime/observed reality. Interlock/InTr owns governed transition admission. Master Records does not provide generic transition custody, evidence custody, runtime truth, admission, closure, propagation gating, or transition prerequisites.

## Inventory baseline
Full semantic repair manifest: 3,815 prohibited references across 1,212 files; 2,064 ambiguous references require contextual resolution.
StegVerse-Labs/.github share: **2,329 prohibited references across 614 files**.

The persisted classifier on this branch is the current class-count authority:
- RUNTIME_OBSERVED_REALITY: 95 references / 63 files
- GENERIC_CUSTODY: 689 references / 289 files
- TRANSITION_GATE_CLOSURE: 230 references / 114 files
- GENERIC_TRANSITION_API: 201 references / 86 files
- CONTEXT_SPECIFIC: 1,114 references / 408 files

The older 581/565/492/169/522 partition is superseded and MUST NOT be used for burn-down.

## Reproducibility defect and repair path
`data/master-records-prohibited-reference-classifier-2026-10-07.json` currently persists ordered rules, aggregate counts, and entry-identity fields, but not the 2,329 entry assignments themselves. Its declared source `master_records_semantic_repair_set_2026-10-07.json` is not present at the recorded repository path on the current PR head. Therefore aggregate counts MUST NOT be represented as completed per-entry disposition.

Repair this on this same PR lane by materializing a self-contained per-entry classifier/disposition artifact from the canonical semantic repair source before claiming class completion. Each row must retain path, source line, kind, reconstruction flag, negation/prohibition flag, text SHA-256, primary class, current disposition, and replacement/evidence reference. Historical/test/supersession evidence is preserved explicitly.

## Current semantic repairs
Current-branch contextual inspection found active prohibited semantics still present despite earlier bulk wording replacement. Repairs now include:
- `data/goal-task-component-profiles/PA-001-ECOSYSTEM-RUNTIME-ENFORCEMENT-001.json`: replaced generic evidence-custody/runtime-reality semantics with Organization runtime authority plus Master Records organization-record/reconstruction semantics.
- `data/canonical-task-records/SV002-REQUEST-BOUND-EVIDENCE-RETENTION-001.json`: replaced request-bound Master Records custody semantics with organization-record retention plus Master Records reconstruction semantics.

These repairs are evidence of progress only; neither the 95-record runtime class nor the 689-record custody class is yet claimed fully dispositioned.

## Execution method
Consume the persisted classifier and materialize its missing per-entry assignments from the canonical source; process deterministic mutation classes repository-wide; preserve organization-record/reconstruction semantics and explicitly historical evidence; context-resolve ambiguous references before mutation; persist exact reference/file burn-down; repair CI on the same PR lane.

## Current continuation
Continue PR #2988 only from its current exact head. First repair the classifier persistence defect without returning to a fresh keyword inventory. Then complete all RUNTIME_OBSERVED_REALITY per-entry dispositions and mutations, followed by all GENERIC_CUSTODY entries. Update this handoff and README, validate the exact head, repair every failure on this branch, and merge with expected-head protection only when required checks are green.
