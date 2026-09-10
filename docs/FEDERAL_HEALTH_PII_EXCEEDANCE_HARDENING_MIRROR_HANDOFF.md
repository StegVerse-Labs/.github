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

## Child 4 — exact manifest/posture/payload/InTr binding

```text
task_id: INTR-SENSITIVE-DATA-MANIFEST-PAYLOAD-BINDING-001
state: COMPLETE_VALIDATED_MERGED_SOURCE_CONTROL
SDK PR: #170
SDK merge: 4601a6537270167edf72d7eecec28aad8de3fe76
SDK validation: 34506885779 SUCCESS
StegOS PR: #322
StegOS merge: 05848191ea2715aa9bdf37d63e22622744128a9d
StegOS validation: 34506947325 SUCCESS
```

SDK #170 adds an exact task-posture projection only after the ephemeral instance passes task and lifetime validation. The projection binds the complete posture-instance SHA-256, posture ID, posture-definition version/digest, effective tier, issuance/expiry, and explicit non-transferability/non-reuse state. It remains admission evidence only.

StegOS #322 adds the fail-closed `stegos.intr-sensitive-data-payload-binding.v1` boundary evidence object. Before sensitive Universal InTr materialization it re-runs minimum-necessary manifest admission, requires exact payload bytes, binds the canonical manifest digest, binds the exact SDK posture instance and projection, verifies task/lifetime and mandatory security floors, verifies the exact Universal InTr request hash, requires the request payload hash to equal the exact payload bytes, and binds task identity, purpose, requested field set, sink, retention policy, posture identity/version/digest, and transition request in one deterministic evidence object. Raw sensitive payload is explicitly absent from evidence.

The companion boundary verifier recomputes the full evidence object from exact inputs. Detached or mutated payloads, manifests, posture instances, transition requests, expired/cross-task posture instances, or mutated binding evidence fail closed. The evidence does not commit a transition or grant execution, transport, claim/fence, credential, GitHub, Heartbeat, or model-output authority. Interlock/InTr remains transition-admission authority and TV/TVC remains credential authority.

## Next hardening child

```text
task_id: INTR-SENSITIVE-DATA-RAW-PHI-FREE-AUDIT-RECEIPT-002
state: NEXT
```

Add write-once sensitive-data audit receipts that preserve binding/provenance and subject pseudonymization while prohibiting raw PHI/PII values and raw subject identifiers from the receipt layer. Receipts must bind the exact Child 4 evidence identity, purpose, field names (not sensitive field values), sink, posture identity, transition identity, disposition obligation, timestamp, prior receipt hash where applicable, and TV/TVC credential semantics without turning audit custody into transition authority.

## Planned exceedance sequence

1. Raw-PHI-free write-once audit receipts with subject pseudonymization.
2. Automatic disposition proof and bounded transient-state verification.
3. Object/field-level authorization plus purpose-of-use enforcement independent of network identity.
4. Break-glass emergency access with explicit dual receipt, strict timeout, no silent persistence, mandatory post-event review.
5. Availability/reconstruction controls preserving authorized clinical availability without restoring stale authority.
6. Continuous machine-readable control assessment mapped to NIST SP 800-53A, not annual-only review.
7. Incident detection, containment, disclosure-impact lineage, and deterministic remediation evidence.
8. Supply-chain/component provenance checks for any code handling PII/ePHI.
9. Machine-readable federal control crosswalk with exact evidence refs and explicit SATISFIED/PARTIAL/UNMET/NA states.

## Invariants

```text
no sensitive-data operation without explicit admission
minimum necessary enforced before execution
posture definition durable; posture instance task-ephemeral
organization/data/channel security floors cannot be downgraded
KV-SKAP and SKAP-KV always require HIGHEST current posture
exact payload bytes must be bound to manifest + posture + transition request before sensitive InTr materialization
raw sensitive payload must not appear in binding evidence
TV/TVC credential authority only
Interlock/InTr transition admission remains canonical
no GitHub runtime authority
no Heartbeat execution authority
no model-output authority
no hosted execution fallback
no Render
no second user-operated machine requirement
```
