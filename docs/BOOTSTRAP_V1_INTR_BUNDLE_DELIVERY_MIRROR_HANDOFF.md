# Bootstrap v1 Universal InTr Bundle Delivery Mirror Handoff

Updated: 2026-08-30
Repository: `StegVerse-Labs/.github`
Goal: `BOOTSTRAP-V1-INTR-BUNDLE-DELIVERY-001`

## Goal

Deliver the already-built canonical `stegverse.bootstrap.bundle/v1 @ 1.0.0-rc.1` from sovereign Bootstrap bound state to an already-established StegVerse browser node through the canonical Universal Interlock/InTr adjacent-boundary contract, without making GitHub, Site hosting, a package registry, or any provider the source or runtime authority.

This lane closes only the machine-delivery gap between:

```text
BOOTSTRAP_V1_DISTRIBUTABLE_BUNDLE_BUILT
  -> sovereign Bootstrap bundle custody
  -> Universal InTr delivery
  -> established browser-node bundle receiver
```

The existing Site materializer remains the sole browser-side source-byte verifier/materializer. This lane does not duplicate it.

## Canonical upstream

Required local bundle:

```text
~/.stegverse/state/bootstrap-v1-distributable-bundle/
  bundle/bootstrap-v1-1.0.0-rc.1.bundle.json
  receipts/latest.json
```

Required bundle receipt predicates:

```text
schema = stegverse.bootstrap.distributable-bundle-build-receipt/v1
state = COMPLETE
transition_id = BOOTSTRAP_V1_DISTRIBUTABLE_BUNDLE_BUILT
bundle_version = 1.0.0-rc.1
component_count = 4
github_platform_required = false
network_access_performed = false
credential_used = false
repository_writeback_performed = false
release_activated = false
publication_performed = false
execution_authority = NONE
```

The server recomputes `bundle_identity` from the exact local bundle before serving bytes. It never loads a bundle from a repository URL or remote package registry.

## Universal InTr topology

Bundle retrieval is a request/response double-Interlock exchange across the adjacent StegVerse boundaries:

```text
established browser node / DEVICE_SYSTEM
  -> device-facing Interlock request
  -> Universal InTr
  -> STEGOS_ECOSYSTEM receiving Interlock
  -> exact local bundle selection
  -> STEGOS_ECOSYSTEM egress Interlock
  -> Universal InTr
  -> DEVICE_SYSTEM receiving Interlock
  -> existing Site bundle verifier/materializer
```

Canonical policy:

```text
transport_profile: stegverse.universal-intr.adjacent-hop/v1
universal_intr_policy_id: STEGVERSE-UNIVERSAL-INTR-TRANSPORT-001
canonical_protocol_adopted: true
interlock_required_per_hop: true
receipt_hash_chain_required: true
runtime_activation_claimed: false
production_interlock_runtime_activated: false
authority_effect: NONE
```

Request intent:

```text
source_boundary = DEVICE_SYSTEM
source_subsystem = ESTABLISHED_BROWSER_NODE
destination_boundary = STEGOS_ECOSYSTEM
destination_subsystem = BOOTSTRAP_V1_BUNDLE_CUSTODY
```

Response intent:

```text
source_boundary = STEGOS_ECOSYSTEM
source_subsystem = BOOTSTRAP_V1_BUNDLE_CUSTODY
destination_boundary = DEVICE_SYSTEM
destination_subsystem = ESTABLISHED_BROWSER_NODE
prior_transport_receipt_hash = request ingress receipt hash
```

The response egress receipt therefore chains directly to the admitted request ingress receipt. Receipt objects contain hashes and boundary facts only; bundle plaintext is not copied into a transport receipt.

## Request contract

Schema:

`stegverse.bootstrap.bundle-delivery-request/v1`

Required request fields:

```text
schema
request_id
node_id
device_continuity_id
bundle_version = 1.0.0-rc.1
request_nonce
request_grants_execution_authority = false
credential_required = false
github_platform_required = false
authority_effect = NONE
```

The delivery runtime does not treat the supplied node/device IDs as proof of continuity. They bind the transport exchange only. The existing browser materializer remains responsible for validating the established node/device continuity journal before any source bytes are retained.

## Response contract

Schema:

`stegverse.bootstrap.bundle-delivery-response/v1`

Successful response:

```text
state = DELIVERED_UNADMITTED
bundle_version = 1.0.0-rc.1
bundle_identity = exact local bundle identity
bundle = exact canonical bundle object
transport_profile = stegverse.universal-intr.adjacent-hop/v1
universal_intr_policy_id = STEGVERSE-UNIVERSAL-INTR-TRANSPORT-001
canonical_protocol_adopted = true
request_ingress_receipt = canonical hop receipt
response_egress_receipt = canonical hop receipt
response_egress_receipt.prior_receipt_hash = request_ingress_receipt.receipt_hash
credential_required = false
execution_authority = NONE
release_activated = false
publication_performed = false
authority_effect = NONE_BUNDLE_DELIVERY_ONLY
```

The response object itself is not an execution or release receipt. It is bounded delivery evidence only.

## Endpoint

Canonical path:

`/intr/bootstrap-v1/bundle`

Readiness path:

`/intr/bootstrap-v1/readiness`

The service may bind loopback without TLS for local validation. Any non-loopback binding requires an already-materialized TLS certificate/key supplied through the sovereign route configuration. The browser receives no TLS key, GitHub token, provider token, or TV/TVC credential value.

The public origin is not part of bundle identity. The route configuration may therefore change without changing Bootstrap v1 source, candidate, package, or bundle identities.

## Browser discovery

The Site browser receiver first attempts the same-origin canonical path:

`/intr/bootstrap-v1/bundle`

This path is a logical StegVerse ingress projection, not a repository or hosting-provider identity. If the sovereign route is not currently projected at that origin, the receiver remains fail-closed and retains the existing local-file fallback. A missing route may not be interpreted as package absence or materialization success.

## Resident execution

Canonical worker:

`workers/bootstrap_v1_intr_bundle_delivery_worker.py`

Canonical server:

`scripts/serve_bootstrap_v1_intr_bundle_delivery.py`

The worker follows the existing sovereign resident-receiver pattern:
- requires a declared StegVerse node;
- requires an already-local route configuration;
- requires the canonical built bundle and receipt;
- starts or reuses the persistent bounded receiver;
- observes local readiness;
- remains ACTIVE until one authentic delivery receipt bundle is observed;
- transitions COMPLETE only after the exact request/response InTr receipt chain has been persisted.

## Route configuration

Default:

`~/.stegverse/config/bootstrap-v1-intr-bundle-delivery.json`

Required non-secret fields:

```text
stegos_root
runtime_root
bundle_state_root
host
port
allowed_origin
boundary_identity_ref
credential_authority = TV/TVC
github_token_runtime_authority = NONE
```

For non-loopback:

```text
tls_cert
tls_key
```

TLS private-key custody remains resident/TV-TVC governed. The route file may point to a key path; it must not contain private-key bytes.

## Durable runtime evidence

Readiness:

```text
<runtime_root>/receipts/sovereign-network/bootstrap-v1-intr/
  receiver.pid
  receiver.log
  receiver.latest.json
```

Each authentic delivery produces a write-once receipt bundle:

```text
<runtime_root>/receipts/sovereign-network/bootstrap-v1-intr/
  <request_id>.json
```

Required runtime transition after one authentic response:

`BOOTSTRAP_V1_INTR_BUNDLE_DELIVERY_OBSERVED`

## Authority boundary

```text
credential_authority: TV/TVC
browser_credential_required: false
github_token_required: false
github_token_runtime_authority: NONE
network_source_fetch_authority: false
repository_writeback_authority: false
package_execution_authority: false
sdk_admission_authority: false
release_activation_authority: false
publication_authority: false
transport_grants_execution_authority: false
second_machine_required: false
authority_effect: NONE_BUNDLE_DELIVERY_ONLY
```

The runtime may expose already-built distributable bytes over an admitted StegVerse route. It may not fetch or rebuild source, mutate the frozen candidate/bundle, admit execution, or publish a release.

## Completion and downstream

Completion means only:

```text
canonical bundle locally verified
+ sovereign InTr receiver READY
+ authentic established-browser request observed
+ request ingress hop receipt verified
+ exact bundle response emitted
+ response egress hop receipt chained to ingress
+ delivery receipt bundle retained
```

The next independent proof remains browser-side:

```text
existing Site verifier/materializer
-> stegverse.device-node-bootstrap-bundle-evidence/v1
-> BOOTSTRAP-V1-MATERIALIZATION-EVIDENCE-INTAKE-001
-> BOOTSTRAP-V1-RELEASE-GATE-001
```

Delivery does not imply materialization.

## Runtime truth

```text
canonical bundle builder: IMPLEMENTED / MERGED
Bootstrap release-prep resident chain: IMPLEMENTED / MERGED
Site four-component materializer: IMPLEMENTED / MERGED
Universal InTr bundle-delivery source: IMPLEMENTING
public sovereign bundle route: NOT YET OBSERVED
first authentic InTr bundle delivery: NOT YET OBSERVED
first authentic browser bundle materialization: NOT YET OBSERVED
Bootstrap v1 release authorization: NOT YET OBSERVED
```

Newer authentic runtime evidence overrides source merge, CI, request, and handoff claims.
