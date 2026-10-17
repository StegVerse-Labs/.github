# StegVerse WorkSpace Any-Device KV Surface Mirror Handoff

Updated: 2026-10-17

Goal Task ID: `STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001`  
Handoff: `docs/STEGVERSE_WORKSPACE_ANY_DEVICE_KV_SURFACE_MIRROR_HANDOFF.md`  
Repository: `StegVerse-Labs/.github`  
COSV (task.v1, B=0): `10500000110000`. It is identical on the aggregate registry row, the canonical record, the task vector and the vector index (#3193, exact-head CI-validated).  
Coordination state: `PROPOSED`  
Checkout state: `UNCLAIMED`  
Authority effect: `NONE_COORDINATION_REGISTRATION_ONLY`

## Current canonical truth

PR #2819 is merged as design-session capture only. This handoff applies only the owner decision that is sufficiently explicit and leaves unresolved items unresolved.

### BLK1 resolved — WorkSpace is the shell, KV pages remain canonical KV entry points

The canonical browser model is composition, not replacement:

- `workspace.html` is the persistent WorkSpace shell/chrome and tab host.
- `my-kv.html` remains the standalone MyKV entry point.
- OrgKV and Company-Employee-KV remain standalone KV entry points.
- A KV tab is a UI over admitted KV state, not a second browser-local authority.
- Cross-KV movement is a governed state transition, not shell-local copying.
- Capabilities common across KV switches belong to shell/chrome; KV-specific capabilities belong to the admitted tab projection.

This resolves `BLK1-CANONICAL-WORKSPACE-SURFACE-OWNER`.

## Registry-owner decisions recorded (2026-10-10)

Owner-approved decisions: [Registry #2796 comment 6094254732](https://github.com/StegVerse-Labs/.github/issues/2796#issuecomment-6094254732).

- **COSV:** `10500000110000`. Computed-vector consistency and exact-head validation passed in #3193 (`ee32d7c8`), which reconciled the stale aggregate row to the canonical record. The former values `10500000113000` (B=3) and `10500000114000` (B=4) were stale state vectors; the current value has B=0. COSV is not a unique identity.
- **BLK2:** retain existing governed SKAP ingress paths; WorkSpace is a unified non-authoritative UI.
- **BLK3:** retain existing authorized KnowledgeVault writer; do not create another authoritative writer.
- **BLK4:** distinguish StegVerse WorkSpace and Google Workspace by canonical task identity and non-overlapping write ownership.

These are **owner decisions**, not a successful governed task admission, WorkerCoordinator claim/fence, or runtime observation. Task remains `PROPOSED / UNCLAIMED` until canonical predicates pass.

## Previously unresolved decisions

PR #2819 did not resolve the following decisions; the owner subsequently approved all three in Registry #2796:

1. `BLK2-SKAP-INGRESS-CONSOLIDATION` — whether all sensitive ingress consolidates behind WorkSpace while preserving any required independent SKAP ingress.
2. `BLK3-WORKSPACE-KV-STORE-WRITER` — whether the WorkSpace KV store retains the current Google Drive writer path or gains a StegVerse-native writer.
3. `BLK4-WORKSPACE-NAME-COLLISION` — how the StegVerse WorkSpace surface is namespaced against Google Workspace external-collaboration work.

The goal remains `PROPOSED / UNCLAIMED` until Registry COSV/generation validation, authenticated admission and WorkerCoordinator ownership requirements are satisfied.

## Current-work reconciliation

PR #2819 predates or omits several live canonical facts that must govern continuation:

- No second user-operated device or continuously connected external machine is a prerequisite.
- Runtime evidence is produced by the original manifest-bound state transition and its authentic organization/Master Records evidence, not by device inventory.
- `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001` remains the active Device/KV/SKAP runtime owner for the sovereign single-device lane.
- `SV-KV-AI-WORKERCOORDINATOR-ADMISSION-001` is adjacent to this goal because WorkSpace admitted write capabilities must not outrun the canonical KV/AI admission path.
- Task Registry state is coordination-only; WorkerCoordinator owns claim/fence, Interlock/InTr owns transition authority, KV/SKAP Vault owns user verification, TV/TVC owns credentials, and Master Records is limited to organization records and reconstruction.
- A failed or unavailable authenticated transition interface is not an indefinite blocker. An actually attempted transition must return ALLOW, DENY, or FAIL_CLOSED; when no authenticated attempt can be made, preserve UNKNOWN_NOT_AUTHENTICALLY_OBSERVED without inventing a transition.

## PR #2819 findings retained as source-gap evidence

The following remain useful source findings, but are not themselves runtime proof:

- transition receipts need sufficient manifest/handoff correlation to reconstruct endpoint-to-endpoint journeys;
- ingress-manifest attestation/freshness shapes remain a source-hardening concern unless superseded by later SDK source;
- KV/SKAP/Node endpoint receipt chains are a different axis from repository/organization/master-records ledger scope;
- the WorkSpace goal must depend on the canonical KV/AI admission chain rather than assuming writes are already admitted.

## Reconciliation and conformance (2026-10-14 to 2026-10-17)

- **Registry projections (#3193, `ee32d7c8`):** the aggregate row equals the canonical record, `source_state_vector_ref` is bound, and the vector-index `registry_ref` names `data/canonical-task-registry.json`. `audit_canonical_task_projections.py` reports no drift for this task.
- **Next transition (#3209, `3da74c74`):** every BLK2–BLK4 blocker carries a recorded owner decision. The allowed transition is now `PROPOSED_TO_ACTIVE_ON_AUTHENTICATED_ADMISSION_AND_WORKERCOORDINATOR_CLAIM_AND_FENCE`, replacing the stale `…_DECISION_OF_REMAINING_THREE_BLOCKERS`.
- **WU1-NO-BROWSER-LOCAL-ROOT-OF-TRUTH (#3209, Site#1604):**
  - The Organizational path reads no browser storage (Site W2). Its locked gate carries the six actionable fields.
  - The Personal path binds its KV query only to a device-local StegOS node registration or an admitted device-continuity recovery result. That precondition holds a registered exemption in `data/organization-role-exemption-register.json` (FAIL_CLOSED `DEVICE_INDEPENDENT_VERIFIED_USER_QUERY_PATH_NOT_SUPPLIED`, review 2026-11-17). The repair is a device-independent verified-user query path from continuity-vault-kit.
- **WorkSpace source conformance (Site#1581, #1586, #1587, #1589, #1592, #1602, #1603, #1604):**
  - receipt invariant: no ALLOW without a receipt;
  - destination existence, not liveness: single KV lookups, no polling;
  - every non-ALLOW outcome carries the six Organization Role item 5 fields.
- **Evidence class:** `SOURCE_IMPLEMENTED`, `MERGED`, `CI_VALIDATED` only. Nothing is runtime-observed.

## Canonical next actions

1. **Authenticated admission and the WorkerCoordinator claim and fence** move PROPOSED to ACTIVE (Site#1509 B2). Only the WorkerCoordinator issues `claim_ref` / `fence_ref`; this record is `projection_only`.
2. **WU1–WU5 assignment** after admission. WU1's Personal path follows the continuity-vault-kit device-independent query path named in its exemption.
3. **Keep the dependencies explicit:** `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001`, `KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001`, `SS-KV-SKAP-SOCIAL-RELEASE-001`, `MYKV-PERSONAL-DATA-BACKUP-001`, `TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001`, `SV-KV-AI-PERSISTENCE-001` and `SV-KV-AI-WORKERCOORDINATOR-ADMISSION-001`.
4. **Execute WorkSpace mutations** only through admitted manifest-directed transitions, and retain original organization/Master Records evidence.

Open items and their owners are recorded on Site#1509 (comments 6168883346 and 6234931876) and StegVerse-Labs/.github#3183.

## Non-claims

This handoff does not claim runtime execution, provider execution, WorkSpace deployment, InTr admission, a WorkerCoordinator claim, or completion of any WorkSpace evidence predicate. It does not claim a Master Records organization record either.
