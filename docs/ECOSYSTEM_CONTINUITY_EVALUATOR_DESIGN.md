# Ecosystem Continuity Evaluator (ECE)

ECE is a trustworthy, non-authorizing continuity-evaluation layer for the StegVerse ecosystem.

## Processing model

```text
registered ecosystem components
-> bounded observations/evidence
-> deterministic predicate evaluation
-> categorical continuity derivation
-> retained evaluation + stable findings
-> Site read-only projection
-> StegVerse-Healer finding intake
-> canonical-owner remediation
-> later ECE re-observation
-> verified recovery
```

## Trust properties

- Diagnostic output never grants repair or execution authority.
- Missing, stale, unknown, unreachable, failed, and probe-required states remain distinct.
- Critical-path continuity derives from predicate criticality and dependency semantics, not a health percentage.
- Finding IDs are deterministic for identical component/predicate/state/evidence input.
- Every run exposes evaluator version, registry hash, completeness, and evaluation errors.
- Invalid observation vocabulary makes the run INDETERMINATE rather than coercing it into a favorable state.
- Repair dispatch never proves recovery.
- A later independent PASS observation is required to establish recovery.
- Site is a projection only; retained evaluation truth exists independently of Site availability.
- Scheduled execution must reuse StegVerse-Healer; ECE owns no scheduler.

## v1 implementation boundary

The initial implementation is source-only and fixture-testable. Live probes, Master Records custody, scheduled Healer execution, and Site rendering are separate evidence-bearing integration steps and must not be inferred from this source implementation.
