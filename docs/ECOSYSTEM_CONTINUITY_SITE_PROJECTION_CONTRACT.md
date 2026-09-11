# Ecosystem Continuity Site Projection Contract

Site is a read-only projection consumer of ECE output. Site is not continuity authority and must not infer health beyond the retained evaluation.

Public/private-safe projected fields may include: evaluation ID, evaluated-at time, evaluator version, overall continuity state, component/predicate identifier, observation state, evidence age, severity, continuity-critical flag, safe evidence locators, authority owner, and remediation state.

The projection must exclude secrets, credentials, private KV paths, sensitive infrastructure identifiers, callback query material, private keys, tokens, and exploit-relevant diagnostic detail.

If the latest retained evaluation is unavailable, invalid, stale under Site policy, or fails schema validation, Site must display continuity as INDETERMINATE/UNAVAILABLE rather than reuse an older green state without an explicit stale marker.

Site presentation must preserve the distinction between FAIL, NOT_OBSERVED, STALE, UNKNOWN, UNREACHABLE, and PROBE_REQUIRED. A numeric score must not replace the categorical continuity determination.
