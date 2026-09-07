# Authority × Time Governance Coordinate Mirror Handoff

## Source of truth

```text
organization: StegVerse-Labs / Admissible-Existence
primary_task_registry_identifier: AUTHORITY-TIME-GOVERNANCE-COORDINATE-001
coordinator_issue: StegVerse-Labs/.github#1154
coordination_pr: StegVerse-Labs/.github#1155
state: SOURCE_CORRECTION_AND_VALIDATION_IN_PROGRESS
canonical_governance_coordinate: Authority × Time
```

## Primitive

```text
Governance = Authority × Time
G = (A, T)
```

Authority and Time are the coordinates of governance.

State, identity, delegation, policy, evidence, verification, consent, context, boundary, capability, recoverability, uncertainty, continuity, manifold structure, and transition geometry are evaluated at a governance coordinate. They do not replace either coordinate.

## Non-causality safeguard

```text
Time != Authority
Delta-time -/-> Delta-authority
wall-clock observation != Authority
heartbeat cadence != Authority
verification != Authority
state != governance coordinate
```

These safeguards do not demote Time from governance. Time locates governance; clocks/timestamps/durations are observations or policy inputs associated with that coordinate.

## Collision / supersession rule

Any ecosystem text stating or implying any of the following must be reconciled:

- Time is merely evidence unless explicitly governing;
- governance is state-relative instead of Authority × Time;
- Authority is only a derived state/relation and not a governance coordinate;
- state, verification, evidence, autonomy, identity, consensus, capability, or runtime execution constitutes an additional governance coordinate;
- non-authorizing wall-clock/HB language means Time is outside governance.

Preserve useful state-manifold, RTG, AE, TT, STCM, GTG, ET, StegGate, Continuity, and receipt semantics by treating them as transition/context/evidence/admissibility/continuity structures evaluated at `(Authority, Time)`.

## Active correction repositories

```text
Admissible-Existence/AE#28 / PR #29
  branch: fix/authority-time-governance-coordinate
  anchor: docs/AUTHORITY_TIME_GOVERNANCE_COORDINATE.md
  direct source corrections:
    docs/STATE_MANIFOLD_RELATIONAL_GOVERNANCE_MATHEMATICS.md
    docs/protocols/GTG/VOLUME_01_GOVERNANCE_PRIMITIVES_AND_DECISION_ALGEBRA.md
    README.md

Admissible-Existence/RTG#7 / PR #8
  branch: fix/authority-time-governance-coordinate
  anchor: docs/AUTHORITY_TIME_GOVERNANCE_COORDINATE.md
  direct machine correction:
    coordination/state-manifold-governance-binding.json

Admissible-Existence/STCM#5 / PR #6
  branch: fix/authority-time-governance-coordinate
  direct machine correction:
    integration/state-manifold-governance-binding.json

Admissible-Existence/GTG#26 / PR #27
  branch: fix/authority-time-governance-coordinate
  direct corrections:
    docs/GTG_GOVERNED_STATE_RECONCILIATION.md
    docs/GTG_GOVERNED_STATE_INCOMPATIBILITY_REPORT.md
    formalism/governed-state-reconciliation.json
    formalism/triform-governed-state-manifest.json
    formal/governed_state.py
    tests/test_governed_state.py

Admissible-Existence/ET#8 / PR #9
  branch: fix/authority-time-governance-coordinate
  direct correction:
    docs/ET_GOVERNED_STATE_RECONCILIATION.md

StegVerse-Labs/ara-admissibility-interop#137 / PR #138
  branch: fix/authority-time-governance-coordinate
  anchor: docs/AUTHORITY_TIME_GOVERNANCE_COORDINATE.md
  direct source correction:
    docs/state-relative-authority-applicability.md

StegVerse-Labs/admissibility-wiki#134 / PR #135
  branch: fix/authority-time-governance-coordinate
  public anchor: docs/governance/authority-time-governance-coordinate.md
  remaining: direct cross-links/wording reconciliation

StegVerse-Labs/StegCore#188 / PR #189
  branch: fix/authority-time-governance-coordinate
  runtime anchor: docs/AUTHORITY_TIME_GOVERNANCE_COORDINATE.md
  remaining: direct manifold/runtime wording reconciliation and tests where applicable
```

## README completeness predicate

README impact is REQUIRED where a repository README defines governance primitives or presents state/time/authority relationships to consumers. Where README is only navigational and does not state those semantics, an explicit no-change determination must be recorded in the repository PR.

Current state:

```text
AE: README UPDATED
RTG: README REVIEW REQUIRED
STCM: README REVIEW REQUIRED
GTG: README REVIEW REQUIRED
ET: README REVIEW REQUIRED
ARA: README REVIEW REQUIRED
admissibility-wiki: README REVIEW / PUBLIC NAVIGATION LINK REQUIRED
StegCore: README REVIEW REQUIRED
```

## Required propagation

After source PRs merge, verify and update as applicable:

```text
StegVerse-Labs/Site
GCAT-BCAT-Engine/Publisher
StegVerse-Labs/admissibility-wiki
StegVerse-Labs/stegguardian-wiki
StegIndex / repository indexes
Master Records / canonical task registry
```

Post-merge propagation verification issue: `StegVerse-Labs/.github#1156`.

## Completed in current correction branch set

1. AE state-manifold primitive no longer demotes Time or Authority.
2. AE GTG protocol now separates governance coordinate from evaluation inputs.
3. RTG machine binding no longer contains `time_is_evidence_unless_explicitly_governing`.
4. ARA state-relative document now treats State as evaluated context at `(Authority, Time)`.
5. STCM machine binding now preserves Authority × Time and receipt evidence-only semantics.
6. GTG prose, formal JSON, executable reference code, manifest, and tests now require an explicit Authority × Time coordinate instead of state-only governance inference.
7. ET governed-state reconciliation now preserves Authority × Time while retaining evidence reconstruction and temporal non-causality.
8. Public admissibility-wiki and StegCore anchor documents are present on draft branches.

## Remaining machine work

1. reconcile StegCore manifold/runtime source wording directly;
2. update admissibility-wiki cross-links/glossary and any conflicting public pages;
3. review/update remaining affected READMEs and task-specific mirror handoffs;
4. inspect GTG/ET/STCM dependent fixtures/validators for stale exact-string/schema assumptions;
5. run repository CI/validation on exact PR heads and repair failures;
6. register/refresh the canonical task-registry entry and indexes;
7. merge/release only after validation passes and review gates permit;
8. verify downstream Site/Publisher/admissibility-wiki/stegguardian-wiki/StegIndex propagation;
9. run the established manual email monitor during final completion routine if still applicable.

## Archive rule

This handoff is the continuation source of truth for this semantic correction. Sessions must read it before creating additional Authority/Time governance work and must reuse the active branches/issues above rather than duplicate them. Once all remaining items are transferred to durable task/PR/issue ownership, the originating chat thread is not required for continuation.
