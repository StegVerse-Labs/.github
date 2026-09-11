# Ecosystem Continuity Healer Intake Contract

StegVerse-Healer may consume ECE findings as repair-dispatch input. ECE findings never grant execution authority.

Accepted finding fields: deterministic finding ID, evaluation ID, component/predicate, observation state, severity, continuity-critical flag, evidence references, evidence age, canonical authority owner, remediation class, and diagnostic detail safe for the Healer boundary.

Healer may acknowledge, queue, dispatch, retry within its existing bounded scheduler semantics, or mark an authority/human boundary. It must not rewrite the underlying ECE observation state.

A repair receipt or Healer state of DISPATCHED / REMEDIATION_IN_PROGRESS / RECOVERY_PENDING_VERIFICATION does not close a finding. VERIFIED_RECOVERED requires a later independent ECE evaluation that observes the required predicate satisfied with acceptable freshness and evidence.

ECE must not create a second scheduler. Periodic ECE invocation belongs to the existing StegVerse-Healer sovereign scheduler path when runtime scheduling is introduced.
