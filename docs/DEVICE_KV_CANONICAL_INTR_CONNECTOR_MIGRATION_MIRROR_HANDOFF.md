# DEVICE_KV Canonical InTr Connector Migration Mirror Handoff

Updated: 2026-09-02
Repository: `StegVerse-Labs/.github`
Issue: `#567`
State: HANDOFF_ESTABLISHED / SOURCE_IMPLEMENTATION_PENDING
Credential authority: TV/TVC
GitHub token runtime authority: NONE
Authority effect: NONE

## Goal

Migrate the sovereign `SHWP-DEVICE-KV-INTR-OBSERVATION-001` worker away from worker-local DEVICE↔KV transport-intent/receipt construction and consume the already-merged canonical StegOS `device-kv` profile through `stegos.intr_backbone.CanonicalInTrConnector`.

## Canonical source

Already-local StegOS source only:

```text
stegos/intr_backbone.py
specs/universal-intr-connector-profiles.v1.json
profile_id=device-kv
payload_schema=kv.interlock.request.v1
source=DEVICE_SYSTEM
destination=KV
response=KV -> DEVICE_SYSTEM
credential_authority=TV/TVC
authority_effect=NONE
```

No network clone/fetch or package acquisition is admitted by this migration.

## Required behavior

For the authentic request lane:

```text
controlled kv.interlock.request.v1
-> CanonicalInTrConnector(device-kv).prepare(...)
-> canonical transport intent
-> connector.accept_hop(...)
-> connector.validate_complete(...)
-> existing HB-derived exact-byte carrier
-> KV endpoint compatibility projection
```

For the response lane:

```text
KV endpoint result
-> connector.prepare_response(...)
-> canonical response transport intent
-> connector.accept_hop(...)
-> connector.validate_complete(...)
-> existing HB-derived exact-byte carrier
-> DEVICE receiver
```

The existing `stegverse.kv-interlock.intr-envelope/v1` may remain only as a compatibility projection consumed by the current continuity-vault-kit endpoint. Its packet/payload identity must be derived from the canonical connector packet, not independently invented.

## Governing invariants

- Authentic Node-KV continuity/event-materialization predecessor remains mandatory.
- WorkerCoordinator remains the sole local task claim/fence admission mechanism.
- Transport intent/receipt construction grants no execution authority.
- HB/HB-derived carrier grants no admission, execution, credential, routing, receiving, transition, publication, custody, claim/fence, or consequence authority.
- TV/TVC remains credential authority.
- GitHub/GitHub Actions remain validation/evidence transport only.
- No canonical KV mutation is authorized.
- No provider operation is authorized.
- No second user machine is required.
- No PyPI/CDN/runtime package authority is introduced.
- Source/CI completion must not be reported as authentic DEVICE_KV runtime observation.

## Source implementation requirements

1. Load the canonical already-local StegOS connector registry.
2. Require exact profile `device-kv`.
3. Prepare request packet through the canonical connector.
4. Derive compatibility envelope identity from the canonical packet.
5. Issue/validate canonical request-hop receipt through the connector.
6. Prepare response through `prepare_response`.
7. Issue/validate canonical response-hop receipt through the connector.
8. Bind durable DEVICE_KV evidence to:
   - connector profile id;
   - request intent hash/result;
   - response intent hash/result;
   - request and response canonical receipt hashes;
   - existing HB-derived carrier evidence.
9. Preserve all current exact-byte/shared-HB signal terminal predicates.
10. Add focused regression tests.
11. Pass current organization-control and Heartbeat validation.
12. Merge to current main.

## Completion boundary

Source completion is reached only when the worker no longer uses its local transport-intent/receipt builders as the canonical DEVICE↔KV transport authority and both directions are validated through `CanonicalInTrConnector(device-kv)`.

Authentic completion remains deployment-local:

```text
receipts/device-kv-intr/SHWP-DEVICE-KV-INTR-OBSERVATION-001.json
state=OBSERVED
transition_id=DEVICE_KV_INTR_OBSERVED
canonical_connector_profile=device-kv
request canonical transport complete=true
response canonical transport complete=true
HB exact-byte/shared-signal predicates=true
```

Current authentic runtime evidence: NOT OBSERVED.

## Next authorized machine action

Implement the connector migration against current main without changing the existing WorkerCoordinator, HB carrier, KV endpoint authority boundary, or terminal runtime-evidence requirements.
