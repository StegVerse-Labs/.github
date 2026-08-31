# SV-DN-1 Browser Evidence Universal InTr Ingress Mirror Handoff

Updated: 2026-08-30
Repository: `StegVerse-Labs/.github`
Goal: `SV-DN1-BROWSER-EVIDENCE-INTR-INGRESS-001`

## Goal

Provide the missing machine-owned transport from an already-authentic established StegVerse web-bootstrap SV-DN-1 observation bundle into the sovereign runtime path consumed by the existing SDK browser-evidence adapter.

This lane does not create an observation and does not execute the SDK. It transports one exact already-observed bundle through the canonical Universal InTr profiled ingress and persists it as local sovereign evidence.

Canonical path:

```text
established stegverse.org web-bootstrap node
  existing stegverse.sv-dn1.browser-resident-observation-bundle/v3
        ↓
source-side Interlock egress receipt
        ↓
Universal InTr adjacent hop
  DEVICE_SYSTEM -> STEGOS_ECOSYSTEM
        ↓
shared profiled sovereign ingress /intr/materialization
        ↓
independent bundle/journal/receipt validation
        ↓
write-once local bundle materialization
        ↓
control/sv-dn1-browser-observation-locator.json
        ↓
existing sv_dn1 resident consumer
        ↓
existing workers/sv_dn1_sdk_browser_evidence_adapter.py
        ↓
existing sovereign first-round chain
```

## Why this lane is required

The existing SDK adapter can consume an authentic browser bundle through `STEGVERSE_SV_DN1_BROWSER_OBSERVATION_BUNDLE` or the persisted local locator. The resident portable bridge can persist a locator only when the bundle is already visible as a sovereign-local filesystem object. The authentic bundle currently originates on the established browser node; requiring manual file movement would violate the no-second-machine and machine-execution goals.

The shared `workers/universal_intr_profiled_ingress.py` already provides the canonical event-ephemeral sovereign ingress for HIL and SV002. SV-DN-1 must extend that same ingress rather than introduce another transport server.

## Transport profile

Profile name:

`SV-DN1:BrowserObservation`

Transport header origin:

`STEGOS_WEB_BOOTSTRAP_EGRESS`

Required transport contract:

```text
X-StegVerse-Transport: InTr
X-StegVerse-Transport-Origin: STEGOS_WEB_BOOTSTRAP_EGRESS
X-StegVerse-Payload-SHA256: <exact request-body sha256 hex>
Content-Type: application/json
```

No authorization header or credential is permitted for this browser-origin profile.

The body schema is:

`stegverse.sv-dn1.browser-observation-transport/v1`

The request contains:
- `profile_id=SV-DN-1`
- the complete authentic `stegverse.sv-dn1.browser-resident-observation-bundle/v3`
- canonical `bundle_sha256`
- established `node_id` and `device_continuity_id`
- Universal InTr policy/profile fields
- `boundary_from=DEVICE_SYSTEM`
- `boundary_to=STEGOS_ECOSYSTEM`
- a source-side Interlock receipt whose `receipt_hash` is recomputed and verified
- explicit zero-authority flags.

The source Interlock receipt is chained from the established web-bootstrap journal tail and binds the exact bundle hash. The transport request's `previous_receipt_hash` must equal that source receipt hash.

## Ingress validation

The sovereign ingress MUST independently verify:

1. request schema/profile/policy/boundaries;
2. no credential, execution, SDK, governance, publication, repository, or certification authority is claimed;
3. bundle schema/state/observation class;
4. exact established node and device-continuity identity binding;
5. full web-bootstrap journal replay and every receipt/entry hash;
6. resident receipt COMPLETE and raw source digest continuity;
7. Hugging Face semantic exchange identity continuity;
8. existing Universal InTr EXTERNAL_SYSTEM -> STEGOS_ECOSYSTEM receipt COMPLETE, destination validation PASS, and lineage verified;
9. source Interlock receipt hash, bundle hash, and prior journal-tail binding;
10. write-once local persistence.

The validator must not trust the browser's `journal_replay=PASS` assertion without replaying the journal itself.

## Sovereign local materialization

Successful ingress writes the exact validated JSON object once under mutable resident state:

```text
<runtime-root>/evidence/sv-dn1-browser-observation/<materialization-id>/bundle.json
```

It then writes/updates only the non-secret locator:

```text
<runtime-root>/control/sv-dn1-browser-observation-locator.json
```

using the existing schema:

`stegverse.sv-dn1.browser-observation-locator/v1`

The locator grants no authority. It only names the already-local exact bundle path for `workers/sv_dn1_sdk_browser_evidence_adapter.py`.

## Ingress receipt

Successful admission emits:

`stegverse.sv-dn1.browser-observation-ingress-receipt/v1`

with terminal ingress state:

`INGRESS_ADMITTED`

and must prove:

```text
exact_bundle_validated=true
journal_replay_validated=true
source_interlock_validated=true
destination_validation=PASS
lineage_verified=true
write_once_persisted=true
locator_persisted=true
consumer_dispatch_attempted=<bool>
request_grants_execution_authority=false
claim_or_fence_minted=false
sdk_admitted=false
governance_decision_made=false
repository_writeback_performed=false
deployment_performed=false
publication_decision_made=false
credential_used=false
authority_effect=NONE_INGRESS_ONLY
```

Ingress admission is not SDK admission and is not first-round completion.

## Consumer dispatch

After successful write-once admission, the ingress may launch the already-existing `sv_dn1` resident consumer using a credential-scrubbed environment.

The ingress does not mint a WorkerCoordinator claim/fence and does not grant execution authority. The consumer and each downstream task remain subject to their existing independent-task-control contracts.

The current resident request is:

`RESIDENT-EXEC-SV-DN1-FIRST-ROUND-007`

A successful ingress may therefore immediately give the existing request a locally resolvable authentic browser bundle without another manual file handoff.

## Size boundary

The authentic known bundle is approximately 70 KiB. The shared ingress's existing 512 KiB hard request ceiling remains in force. Oversize bundles fail closed; the limit is not increased merely for SV-DN-1.

## Explicit prohibitions

The ingress MUST NOT:
- fetch Hugging Face;
- fetch GitHub or any source repository;
- accept GitHub/HF/provider credentials;
- manufacture or modify the browser observation bundle;
- mint a second node identity;
- execute SDK evaluation in the HTTP handler;
- grant claim/fence authority;
- make StegCore/StegGate decisions;
- perform Master Records custody/reconstruction itself;
- commit/push/merge repository content;
- deploy the public dashboard;
- certify or endorse the external model.

## Runtime truth at handoff creation

```text
authentic established-node Hugging Face observation: OBSERVED
authentic EXTERNAL_SYSTEM -> STEGOS_ECOSYSTEM InTr receipt: OBSERVED
browser bundle available in sovereign-local filesystem: NOT PROVEN
browser -> sovereign evidence ingress profile: MERGED / VALIDATED (PR #565 / 5626800bdd542b77ce169964231b66b9513edc95)
resident request 007: MERGED / REQUESTED
production-source-prep v2 receipt: NOT YET OBSERVED
SDK first production round ANALYZED: NOT YET OBSERVED
public governed first-round result: WITHHELD
public shared-Gateway SV-DN-1 ingress admission: NOT YET OBSERVED
```

Newer authentic runtime evidence overrides this handoff.


## 2026-08-31 downstream request refresh

The existing ingress continues to dispatch only the existing `sv_dn1` resident consumer. Its current request is now `RESIDENT-EXEC-SV-DN1-FIRST-ROUND-007`, reissued solely because downstream InTr terminal validation now requires the exact shared HB signal proof. Ingress admission itself remains non-authorizing and does not manufacture that proof.
