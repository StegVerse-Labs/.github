# GADI Resident Execution Mirror Handoff

Updated: 2026-09-11
Repository: `StegVerse-Labs/.github`
Goal ID: `GADI-001`
Task ID: `GADI-RESIDENT-EXECUTION-001`
Parent task: `GADI-001`
Umbrella goal: `GOVERNED-MULTILANE-MANIFOLD-ACTIVATION-001`
COSV ID: `10100000100000`
Canonical issue: `StegVerse-Labs/.github#1239`
Status: `ACTIVE / NONCLAIM_READINESS_MERGED / RUNTIME_SUBJECT_BINDING_MERGED / NATIVE_PLAN_MATERIALIZER_MERGED / EXTERNAL_EVIDENCE_FACT_PROJECTOR_MERGED / VERIFIED_EXTERNAL_EVIDENCE_BINDING_MERGED / ED25519_VERIFIER_PLUGIN_MERGED / PENDING_GOVERNANCE_CANDIDATE_MATERIALIZER_MERGED / LOCAL_GOVERNANCE_INTR_ADMISSION_MATERIALIZER_MERGED / NATIVE_COMMAND_LOCAL_CALLER_MERGED / AUTHENTIC_RESIDENT_EXECUTION_PENDING`

## Current canonical state

`GADI-001` remains ACTIVE / CLAIMED_INTEGRATION and is not superseded.

The source/runtime-adapter chain now contains, without introducing parallel authority planes:

- canonical runtime evidence source resolution/materialization/preflight/consumption;
- current subject-bound GADI runtime-binding observation;
- native StegOS boundary planning and exact current-plan materialization from local evidence;
- a GADI external-evidence facts projector that requires an independent exact-envelope verification binding;
- a trusted-key StegOS Ed25519 public-key verifier plugin over the canonical SHA-256 signing digest;
- StegCore local threat correlation / least-destructive capability selection / PENDING intervention request materialization;
- exact hash binding of the PENDING request into the GADI Governance candidate;
- Governance-owned GADI connector profile;
- StegCore local InTr + Governance admission materialization and decision -> GADI Admission projection;
- exact native-command bridge plus production local CLI from plan + ADMITTED request + current runtime binding;
- controlled StegOS actuator-output receipt seam;
- WorkerCoordinator claim/fence normalization and targeted worker bridge;
- non-claim readiness gating and stale-consumption replay protection.

Authentic current runtime execution remains unobserved. Source, CI, profile declarations, examples, simulation evidence, verifier source, and merged adapters do not satisfy runtime predicates.

## Relevant merged trajectory

- `.github` PR #1388 -> `261b1636db05baa3d34072236557618e9607b5e7`: targeted WorkerCoordinator registration repair.
- `.github` PR #1395 -> `b1b613452406b26d8fe17a9fbb98b57054a4f046`: post-claim ProcessWorkerAdapter/GADI dispatcher bridge.
- `.github` PR #1405 -> `1fe63d76ffd2d499daaeab9a942af5dfef50b4d9`: non-claim readiness convergence and stale-consumption replay protection.
- `Governance` PR #40 -> `2765854132872078bcd15a4432a65095831b432e`: authoritative `gadi.defensive-intervention.v1` profile.
- `StegCore` PR #202 -> `282f30e9e46efc3a8d0d867f48e08c3aa6534e22`: Governance-decision -> GADI Admission projector.
- `.github` PR #1413 -> `71338d71c7122e7be9d4a1015e2bde353a3ff0e6`: current runtime-root/node subject binding and readiness enforcement.
- `StegOS` PR #331 -> `84302fc96502eceb074ce2920b8816eb491b9d83`: controlled actuator-output receipt seam.
- `StegOS` PR #337 -> `0409aadbc894c9d0976e41a946b588ef93c34b8d`: native command artifact bridge.
- `StegOS` PR #342 -> `918bc7d78f47bc775736ce85e5026f9fead03555`: native plan materializer and canonical safe-state vocabulary repair.
- `StegCore` PR #204 -> `44f4240c72ae1e64cefd829e469e64a40b5034a3`: local GADI InTr/Governance admission materializer.
- `StegOS` PR #344 -> `0199d36afa3e3a327c3815edbb22dc82b03704d3`: production local native-command materializer CLI.
- `StegCore` PR #205 -> `43f61a9feda8944a5551cfbc39b302f8c65ef69c`: PENDING-request + hash-bound Governance-candidate materializer.
- `.github` PR #1479 -> `5f375ff28bf011744d3823c77c2c9cc4c1a74378`: canonical pre-claim artifact-chain reconciliation.
- `StegCore` PR #206 -> `ed94d900c58c59e316a1591d27404cf372edaeb1`: external-evidence -> exact three-layer Governance-facts projector.
- `.github` PR #1480 -> `4f2c20af71a6e3e56573b4bfde9fa950d67ac8ce`: canonical external-evidence runtime-boundary reconciliation.
- `StegCore` PR #207 -> `3019b31b3c9bc826c96829eb9296c0c4445275a7`: independent verified-external-evidence binding required before GADI fact projection; exact head `6c14012c537f9eb97e9918162853b62fe86f4b95` passed the observed task-specific GADI validation before merge.
- `StegOS` PR #345 -> `b5e27cf0cb920e43395fbd81aa869d47dce0c8c0`: trusted-key Ed25519 verifier plugin plus explicit `cryptography>=42.0.0` dependency and corrected package discovery/CI dependency installation. Initial head exposed pre-existing flat-layout packaging ambiguity; repaired exact head `f968d1dc6b3bb3acec77ac4263126f97bfca5683` passed StegOS CI plus all five observed GADI validation lanes before merge.

## Canonical execution chain

```text
CURRENT RESIDENT-PRESENCE SUBJECT BINDING
-> CURRENT THREAT / BOUNDARY OBSERVATIONS
-> CURRENT GADI-SCOPED EXTERNAL-EVIDENCE ENVELOPE
-> CURRENT INDEPENDENT VERIFIED-EXTERNAL-EVIDENCE BINDING
-> CURRENT PRE-ADMISSION NATIVE DEFENSE PLAN
-> PROJECTED CURRENT THREE-LAYER GOVERNANCE FACTS
-> CURRENT PENDING INTERVENTION REQUEST + HASH-BOUND GOVERNANCE CANDIDATE
-> LOCAL CANONICAL INTR TRANSPORT + GOVERNANCE EVALUATION
-> CURRENT ADMITTED GADI REQUEST
-> NATIVE STEGOS COMMAND BOUND TO EXACT RUNTIME SUBJECT
-> CONTROLLED PREAUTHORIZED OUTPUT OBSERVATION
-> NON-CLAIM READINESS
-> TARGETED WORKERCOORDINATOR CLAIM/FENCE
-> SOURCE RESOLUTION WITH CLAIM DEFERRED
-> FRESH CLAIM PROJECTION
-> MATERIALIZATION
-> PREFLIGHT
-> RESIDENT CONSUMPTION
-> REASSESSMENT / TERMINATION
-> CONTINUITY / MASTER RECORDS RECONSTRUCTION
```

WorkerCoordinator remains sole claim/fence authority. HB/runtime-presence remains observation only. TV/TVC remains credential authority. Governance/InTr remains transition/admission authority. GitHub validation does not become runtime authority.

## Verified external-evidence boundary — merged

StegCore PR #207 hardens `scripts/materialize_gadi_governance_facts_from_external_evidence.py` so an external-evidence envelope cannot establish its own authenticity merely by carrying favorable fields.

The projector now requires a separate `stegcore.gadi-verified-external-evidence-binding/v1` artifact bound to the exact canonical envelope hash and exact provider/key/content-digest/authorization identity. It requires independent evidence that:

```text
signature_verified = true
chain_verified = true
provider_authorized = true
scope_match = true
freshness_verified = true
verification_receipt_ref = <non-empty>
verifier_authority_ref = <non-empty>
execution_authority_granted = false
authority_effect = NONE_EVIDENCE_VERIFICATION_ONLY
```

The projector itself does not perform cryptographic verification or create this binding.

## StegOS cryptographic verifier — merged

StegOS PR #345 extends the existing verifier-plugin registry with:

```text
plugin_id = ed25519-public-key
verification_method = ed25519-sha256-digest
```

The plugin:

- recomputes the canonical payload SHA-256 digest;
- requires envelope digest equality;
- requires `signature_algorithm=ed25519`;
- requires the signed key reference to match the requested trusted key reference;
- obtains the raw Ed25519 public key only from a separately supplied trusted-key registry mapping;
- verifies the signature over the raw 32-byte SHA-256 digest;
- fails closed for unknown keys, wrong keys, tampered payloads, algorithm/key-reference drift, malformed signatures, or invalid signatures.

No trusted keys are embedded in source. The signed payload cannot supply the trusted public key used for verification. The plugin exposes no signing/private-key path and grants no execution, credential, provider-authorization, Governance, or InTr authority.

StegOS now explicitly declares `cryptography>=42.0.0`. PR #345 also corrected setuptools package discovery to `stegos*` and changed StegOS CI to install the package itself before tests, ensuring declared dependencies are exercised.

## Remaining provider-verification authority gap

Repository-wide searches after #345 did not surface a canonical current provider-authorization registry or verification receipt producer that already combines all remaining predicates required by StegCore #207:

```text
trusted provider/key identity
signature verification
chain continuity verification
provider authorization
scope match
freshness verification
exact envelope hash binding
```

The StegOS Ed25519 plugin supplies only the cryptographic signature component. It must not be treated as provider authorization, freshness, chain continuity, or GADI admissibility.

The retained `SHWP-HOST-SELF-ATTEST-001` receipt is not eligible for reuse as this binding. It contains historical claim/fence/worker completion evidence but lacks provider public key, signature, chain-validity, freshness, subject/candidate state hashes, and the required current provider-verification semantics. Its bounded worker authorization likewise does not constitute evidence-provider authorization.

No role is assigned to TV/TVC, HB, GitHub Actions, or WorkerCoordinator by inference. A lawful provider-verification receipt must come from an existing or explicitly implemented evidence-verification authority surface, with its authority boundary independently defined.

## Other merged pre-claim adapters

- StegOS PR #342: current local boundary observation + TV/TVC capability evidence -> pre-admission native plan.
- StegCore PR #206/#207: current envelope + independent verified binding -> exact three-layer Governance facts.
- StegCore PR #205: current threat observations + capability records + projected facts -> PENDING request + exact hash-bound Governance candidate.
- StegCore PR #204: exact PENDING request/candidate -> local canonical InTr transport + Governance decision -> ADMITTED/DENIED request.
- StegOS PR #344: exact plan + current ADMITTED request + current subject-bound runtime binding -> native resident command.

Each adapter performs only its declared projection and grants no execution authority.

## Runtime-local source reuse

The existing sovereign resident environment permits non-secret local roots including:

```text
STEGVERSE_STEGOS_ROOT
STEGVERSE_STEGCORE_SOURCE_ROOT
STEGVERSE_TVC_ROOT
STEGVERSE_TV_ROOT
```

GADI must reuse those existing local materialized source surfaces. No hosted fallback or second runtime/source-discovery plane is authorized.

## Current authentic evidence boundary

The following remain unobserved until produced on the actual sovereign resident runtime:

```text
CURRENT_GADI_RUNTIME_PRESENCE_SUBJECT_NOT_OBSERVED
CURRENT_GADI_RUNTIME_BINDING_NOT_OBSERVED
CURRENT_GADI_BOUNDARY_INTERACTION_NOT_OBSERVED
CURRENT_GADI_THREAT_OBSERVATION_NOT_OBSERVED
CURRENT_GADI_EXTERNAL_EVIDENCE_ENVELOPE_NOT_OBSERVED
CURRENT_GADI_VERIFIED_EXTERNAL_EVIDENCE_BINDING_NOT_OBSERVED
CURRENT_GADI_PRE_ADMISSION_PLAN_NOT_OBSERVED
CURRENT_GADI_RESOLVED_GOVERNANCE_FACTS_NOT_OBSERVED
CURRENT_GADI_PENDING_INTERVENTION_REQUEST_NOT_OBSERVED
CURRENT_GADI_INTR_ADMISSION_NOT_OBSERVED
CURRENT_GADI_NATIVE_COMMAND_NOT_OBSERVED
CONTROLLED_PREAUTHORIZED_ACTUATOR_RESULT_NOT_OBSERVED
CURRENT_GADI_WORKERCOORDINATOR_CLAIM_FENCE_NOT_OBSERVED
CURRENT_GADI_RESIDENT_CONSUMPTION_NOT_OBSERVED
```

The last authorized resident-device inspection returned no connected device. That observation must not be replaced with CI, source examples, retained historical receipts, or controlled simulation.

## Immediate continuation

1. Inspect existing StegVerse evidence/identity/attestation services for a lawful current provider-verification authority capable of producing the full #207 binding; reuse it if present and do not synthesize one from envelope fields.
2. If no existing authority exists, define the narrow provider-verification receipt/registry boundary separately from GADI, preserving evidence-only semantics and trusted-key custody outside the payload.
3. When an authorized sovereign resident/device is reachable, obtain current runtime presence/binding, current boundary/threat observations, and a current GADI-scoped external-evidence envelope.
4. Obtain the independent verified-external-evidence binding, then project facts through StegCore #207.
5. Continue merged #205 -> #204 -> StegOS #344 only from those authentic current artifacts.
6. Observe the controlled pre-authorized software test-surface effect and receipt it through the merged StegOS actuator seam.
7. Let `run_gadi_targeted_runtime_if_ready.py` verify all non-claim artifacts; only then visit canonical targeted WorkerCoordinator for a fresh claim/fence.
8. Require zero-blocker materialization/preflight and a newly changed resident-consumption receipt.
9. Complete adaptive reassessment/termination, Continuity custody, Master Records reconciliation, and exact confrontation reconstruction.

## Collision boundary

No second heartbeat, runtime-presence projector, WorkerCoordinator, scheduler, resident service, runtime lease plane, claim/fence plane, InTr authority, Governance evaluator, evidence-provider authority, provider transport, credential route, actuator implementation, or Master Records custody path is introduced.

## README impact

No root README mutation is required. Existing documentation already defines runtime-presence subject binding, local sovereign source reuse, Governance/InTr authority separation, external-evidence interoperability, WorkerCoordinator authority separation, runtime convergence, and non-authorizing HB semantics.

## Release rule

None of the merged source/runtime-adapter or verifier work above is GADI activation or release evidence. Release/tag propagation remains deferred until authentic current resident execution, adaptive reassessment/termination, complete receipt chain, exact reconstruction, and canonical activation predicates are observed.
