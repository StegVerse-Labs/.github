# Authority × Time Governance Coordinate Mirror Handoff

## Source of truth

```text
organization: StegVerse-Labs / Admissible-Existence
coordinator_issue: StegVerse-Labs/.github#1154
state: SOURCE_CORRECTION_IN_PROGRESS
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

Preserve useful state-manifold, RTG, AE, TT, STCM, GTG, StegGate, Continuity, and receipt semantics by treating them as transition/context/evidence/admissibility/continuity structures evaluated at `(Authority, Time)`.

## Active correction repositories

```text
Admissible-Existence/AE#28
  branch: fix/authority-time-governance-coordinate
  anchor: docs/AUTHORITY_TIME_GOVERNANCE_COORDINATE.md

Admissible-Existence/RTG#7
  branch: fix/authority-time-governance-coordinate
  anchor: docs/AUTHORITY_TIME_GOVERNANCE_COORDINATE.md

StegVerse-Labs/ara-admissibility-interop#137
  branch: fix/authority-time-governance-coordinate
  anchor: docs/AUTHORITY_TIME_GOVERNANCE_COORDINATE.md

StegVerse-Labs/admissibility-wiki#134
  branch: fix/authority-time-governance-coordinate
  public anchor: docs/governance/authority-time-governance-coordinate.md

StegVerse-Labs/StegCore#188
  branch: fix/authority-time-governance-coordinate
  runtime anchor: docs/AUTHORITY_TIME_GOVERNANCE_COORDINATE.md
```

## README completeness predicate

README impact is REQUIRED where a repository README defines governance primitives or presents state/time/authority relationships to consumers. Where README is only navigational and does not state those semantics, an explicit no-change determination may be recorded in the repository PR.

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

## Remaining machine work

1. replace contradictory primitive statements in existing AE state-manifold mathematics;
2. replace RTG machine invariant `time_is_evidence_unless_explicitly_governing`;
3. rewrite ARA state-relative document so State is evaluated context, not governance coordinate;
4. clarify StegCore manifold/runtime language;
5. update public wiki cross-links and glossary;
6. add deterministic fixtures proving both `Governance = Authority × Time` and `Delta-time -/-> Delta-authority`;
7. run repository validation and README impact checks;
8. merge/release only after validation;
9. verify downstream publication/index propagation.

## Archive rule

This handoff is the continuation source of truth for this semantic correction. Sessions should read it before creating additional Authority/Time governance work and should reuse the active branches/issues above rather than duplicate them.
