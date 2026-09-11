## Ecosystem Continuity Evaluator (ECE)

ECE is the non-authorizing continuity-evaluation layer for the StegVerse ecosystem. It derives categorical continuity state from registered component predicates and evidence while preserving FAIL, DEGRADED, UNKNOWN, NOT_OBSERVED, STALE, UNREACHABLE, and PROBE_REQUIRED as distinct observations. ECE findings may be projected safely to Site and consumed by StegVerse-Healer for repair dispatch, but ECE grants no repair/execution authority and Healer dispatch never proves recovery. A later independent ECE observation is required to verify recovery.

Canonical docs:
- `docs/ECOSYSTEM_CONTINUITY_EVALUATOR_MIRROR_HANDOFF.md`
- `docs/ECOSYSTEM_CONTINUITY_EVALUATOR_DESIGN.md`
- `docs/ECOSYSTEM_CONTINUITY_SITE_PROJECTION_CONTRACT.md`
- `docs/ECOSYSTEM_CONTINUITY_HEALER_INTAKE_CONTRACT.md`
