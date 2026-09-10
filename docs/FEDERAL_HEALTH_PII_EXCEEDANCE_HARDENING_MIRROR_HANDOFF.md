# Federal Health / PII Exceedance Hardening Mirror Handoff

Updated: 2026-09-10

```text
goal_id: FEDERAL-HEALTH-PII-EXCEEDANCE-HARDENING-001
parent_goal: STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001
state: ACTIVE
canonical_owner: StegVerse-Labs/.github
implementation_repositories: StegVerse-Labs/StegOS; StegVerse-org/StegVerse-SDK
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

## Child 2 — SDK versioned posture package

```text
task_id: SDK-SECURITY-POSTURE-PACKAGE-001
state: COMPLETE_VALIDATED_MERGED_SOURCE_CONTROL
SDK PR: #167
merge: ce10a41d84c0ef7fa16d356c89a4650aa69a834a
```

Introduced immutable versioned SDK security-posture profiles and fail-closed runtime-attestation validation without placing control lists into source-native test data or evaluator declarations.

## Child 3 — task-scoped ephemeral posture selection

```text
task_id: SDK-TASK-SCOPED-EPHEMERAL-POSTURE-002
state: COMPLETE_VALIDATED_MERGED_SOURCE_CONTROL
SDK PR: #168
merge: 388ae329872d1846b458a24257bf6e58bf4db673
SDK validation: 34504652433 SUCCESS
```

Posture definitions are durable and immutable; posture instances are ephemeral, task-scoped, non-transferable, non-reusable across tasks, and time bounded. The SDK selects the strongest applicable floor across evaluator-requested tier, evaluator-organization minimum, data-class minimum, and channel minimum.

Current tiers:

```text
SECURE  -> stegverse.security.secure.v1
HIGH    -> stegverse.security.high.v1
HIGHEST -> stegverse.security.health-pii-high.v1
```

Mandatory elevation rules currently include:

```text
PII -> at least HIGH
ePHI / sensitive-health-data -> HIGHEST
KV-SKAP / SKAP-KV -> HIGHEST regardless of evaluator request
```

This permits SDK evaluators to request the security level appropriate to their organization while preventing them from weakening mandatory StegVerse, data-class, or channel floors. KV/SKAP always instantiates the strongest current posture. Future stronger posture versions can raise these floors without rewriting historical task evidence.

## Next hardening child

```text
task_id: INTR-SENSITIVE-DATA-MANIFEST-PAYLOAD-BINDING-001
state: NEXT
```

Bind the admitted sensitive-data manifest and ephemeral task-posture instance cryptographically to exact payload bytes and require that binding at the Interlock/InTr materialization boundary. A sensitive payload must not be transportable merely because an adjacent manifest/posture exists; payload digest, manifest digest, posture ID/version/digest, task identity, purpose, field set, sink, retention policy, and transition request must be one fail-closed evidence object.

## Planned exceedance sequence

1. Exact manifest/posture-to-payload cryptographic binding at InTr ingress/egress.
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
posture definition durable; posture instance task-ephemeral
organization/data/channel security floors cannot be downgraded
KV-SKAP and SKAP-KV always require HIGHEST current posture
TV/TVC credential authority only
Interlock/InTr transition admission remains canonical
no GitHub runtime authority
no Heartbeat execution authority
no model-output authority
no hosted execution fallback
no Render
no second user-operated machine requirement
```
