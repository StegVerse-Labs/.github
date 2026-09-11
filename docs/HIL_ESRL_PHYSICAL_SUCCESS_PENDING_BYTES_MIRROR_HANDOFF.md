# HIL ESRL Physical Success Pending Exact Bytes Mirror Handoff

Updated: 2026-09-11
Repository: `StegVerse-Labs/.github`
Parent goal: `SHWP-HIL-SOVEREIGN-RECEIVER-001`
Canonical parent handoff: `docs/HIL_RESIDENT_SESSION_MANIFOLD_ACTIVATION_MIRROR_HANDOFF.md`
Current COSV: `50000000103000`

## Authentic physical observation

The retained standalone-Safari current-iPhone G25 context has now physically reached the component-produced ESRL success surface.

Observed on the successful page:

```text
schema = stegverse.hil-browser-esrl-lease-open/v1
state = LEASE_OPEN
lease_state = LEASE_OPEN
lease_id = HIL-BROWSER-ESRL-7bafde4a280e847758da157e
hil_esrl_protocol = HIL_BROWSER_ESRL_V1
source_browser_protocol = HIL_BROWSER_EVIDENCE_V16
task_id = SHWP-HIL-SOVEREIGN-RECEIVER-001
resident_request_id = RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002
browser_context_id = ctx_d151139d2db1eeecb6512f5844058246
node_id = stegnode-web-f24e3bfb7f5343cb37323187a88e51f3
claim_id = SHWP-SHWP-HIL-SOVEREIGN-RECEIVER-001-G25
fencing_token = 25
source_execution_entry_sha256 = 8ddd8c6fc08038ce4111b349f47a5f44bd48a7bfbc551fae1bfb59a1a384da69
state_machine = REQUESTED -> ADMITTED -> PROVISIONING -> LOCAL_READY -> LEASE_OPEN
runtime_class = EVENT_EPHEMERAL
lease_profile = INTAKE
runtime_materialized = true
local_identity_verified = true
local_ready_source_observed = true
journal_replay_state = PASS
same_device_execution_required = true
execution_surface = CURRENT_USER_IPHONE
requires_other_machine = false
second_claim_minted = false
request_consumption_claimed = false
custody_observed = false
post_restart_exact_byte_proof_observed = false
tvc_lifecycle_receipt_observed = false
broader_hil_lifecycle_complete = false
credential_authority = TV/TVC
github_token_runtime_authority = NONE
heartbeat_granted_authority = false
authority_effect = NONE_RUNTIME_OBSERVATION_ONLY
```

The current public page also displayed enabled `Copy evidence JSON` and `Download evidence JSON` controls, proving the automatic retained-state continuation reached an exportable `LEASE_OPEN` artifact rather than remaining at the earlier opening state.

## Evidence boundary

This observation is sufficient to close the separate Site stale-navigation/public-convergence repair condition: current public page bytes, retained G25 context, automatic ESRL continuation, and component `LEASE_OPEN` are now physically observed together.

It is **not** sufficient to remove the canonical ESRL blocker because `scripts/intake_hil_browser_esrl_evidence.py` hashes the exact exported JSON bytes. Screenshots are visual corroboration, not a substitute for the exact artifact byte stream.

Therefore:

```text
AUTHENTIC PHYSICAL LEASE_OPEN = OBSERVED
EXACT EXPORTED ARTIFACT BYTES = PENDING INTAKE
AUTHENTIC_ESRL_HIL_LEASE_OPEN_NOT_YET_OBSERVED = remains canonical blocker until exact-byte intake ACCEPTED
current COSV = 50000000103000
```

No screenshot reconstruction, retyping, normalization, or regenerated JSON may be substituted for the exact downloaded file.

## Next transition

Once the exact unedited `hil-esrl-lease-open-*.json` file is available, run canonical intake against the existing G25 request-consumption receipt. If intake returns `ACCEPTED`, immediately use the already-merged reconciliation path to propose and review:

```text
50000000103000 -> 50000000102000
remove only AUTHENTIC_ESRL_HIL_LEASE_OPEN_NOT_YET_OBSERVED
retain POST_RESTART_EXACT_BYTE_PROOF_NOT_YET_PRESERVED
retain TVC_HIL_LIFECYCLE_HANDOFF_NOT_YET_PROVEN
next runtime stage = HIL_RECEIVER_READY_AND_CUSTODY
```

No G25 rerun, replacement claim/fence, Safari state reset, second machine, or source-level recreation is warranted.

## README review

README accuracy was re-reviewed. This handoff records a runtime observation/evidence boundary and does not change the documented public interface or architecture, so no README prose change is required.
