# Federal Health / PII Exceedance Hardening Mirror Handoff

Updated: 2026-09-10

```text
goal_id: FEDERAL-HEALTH-PII-EXCEEDANCE-HARDENING-001
parent_goal: STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001
state: ACTIVE
canonical_owner: StegVerse-Labs/.github
implementation_repository: StegVerse-Labs/StegOS
credential_authority: TV/TVC
github_runtime_authority: NONE
heartbeat_execution_authority: false
model_output_authority: false
```

## Goal

Engineer StegVerse sensitive-data handling so the technical enforcement surface is intentionally stricter than the current federal baseline for health information and PII. This work does not itself assert HIPAA compliance, FedRAMP authorization, FISMA authorization, or legal certification.

Current external design references verified 2026-09-10: current HIPAA Security Rule; HHS 2025 Security Rule NPRM direction; NIST SP 800-53 Rev.5 Release 5.2.0 and SP 800-53A 5.2.0; NIST SP 800-122; OMB A-130/RMF principles.

## Child 1 — minimum-necessary sensitive-data admission

```text
task_id: STEGOS-SENSITIVE-DATA-MINIMUM-NECESSARY-001
cosv_profile: task.v1
cosv: 71000000100100
state: COMPLETE_VALIDATED_MERGED_SOURCE_CONTROL
StegOS PR: #320
merge: 3b0440c6c23b56c7d1b3076cb964cacc74b45edb
CI: 34489989173 SUCCESS
```

Implemented `stegos/sensitive_data_minimum_necessary.py` and negative/positive regression coverage. Sensitive PII/ePHI processing fails closed unless an explicit manifest binds purpose, exact allowed fields, approved sinks, mandatory encryption at rest and in transit, audit receipt requirement, ephemeral or <=24h retention with automatic disposition, hashed subject identity, no raw subject identifier, and explicit prohibitions on secondary use, training use, advertising use, and data sale. TV/TVC remains the only credential authority; GitHub, Heartbeat, and model output remain non-authorizing.

The child COSV is task.v1: lifecycle COMPLETE (7), archive readiness true (1), no unassigned work/counts, canonical owner installed (1), evidence complete true (1), activation/propagation false because this is a source control and not yet bound into live InTr processing.

## Next hardening child

```text
task_id: INTR-SENSITIVE-DATA-MANIFEST-PAYLOAD-BINDING-001
state: NEXT
```

Bind the admitted sensitive-data manifest cryptographically to exact payload bytes and require the binding at the Interlock/InTr materialization boundary. A sensitive payload must not be transportable merely because an adjacent manifest exists; the manifest, payload digest, purpose, field set, sink, retention policy, and transition request must be one fail-closed evidence object.

## Planned exceedance sequence

1. Exact manifest-to-payload cryptographic binding at InTr ingress/egress.
2. Raw-PHI-free write-once audit receipts with subject pseudonymization.
3. Automatic disposition proof and bounded transient-state verification.
4. Object/field-level authorization plus purpose-of-use enforcement independent of network identity.
5. Break-glass emergency access with explicit dual receipt, strict timeout, no silent persistence, mandatory post-event review.
6. Availability/reconstruction controls preserving authorized clinical availability without restoring stale authority.
7. Continuous machine-readable control assessment mapped to NIST SP 800-53A, not annual-only review.
8. Incident detection, containment, disclosure-impact lineage, and deterministic remediation evidence.
9. Supply-chain/component provenance checks for any code handling PII/ePHI.
10. Machine-readable federal control crosswalk with exact evidence refs and explicit SATISFIED/PARTIAL/UNMET/NA states.

## Invariants

```text
no sensitive-data operation without explicit admission
minimum necessary enforced before execution
TV/TVC credential authority only
Interlock/InTr transition admission remains canonical
no GitHub runtime authority
no Heartbeat execution authority
no model-output authority
no hosted execution fallback
no Render
no second user-operated machine requirement
```
