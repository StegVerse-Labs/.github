# StegBrowser Manifest Interlock/InTr Ingress Execution Mirror Handoff

Updated: 2026-09-16
Repository: `StegVerse-Labs/.github`

## Task pointer

- Goal Task ID: `STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001`
- Parent Goal: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / SINGLE CANONICAL UNIVERSAL-INTR BINDING MERGED+VALIDATED / SV002 SITE BASELINE+ADAPTATION MERGED+VALIDATED / CURRENT-IPHONE BINDING MERGED+VALIDATED / AUTHENTIC A1-A4 EXECUTION PENDING`
- Current exact condition: `AUTHENTIC_CURRENT_IPHONE_STEGBROWSER_A1_A4_EXECUTION_PENDING`

## Immutable one-shot request

```text
canonical request commit = 19935454cd8c68000b3a0fd70478b0d89d5cd622
invocation_request_nonce = STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z
requested_test_scope = A0_A4_SINGLE_INVOCATION
requested_invocation_count = 1
```

No second request may be emitted or substituted.

## Canonical representation

The only retained StegBrowser-specific Universal InTr representation remains PR `#1955` destination/profile `StegBrowser:ManifestInvocation`.

PR `#1960`'s overlapping alternate `StegBrowser:ManifestIngress` representation was retired by corrective convergence PR `#1964` and must not be reintroduced.

No control-plane source-package relay, resident-request sweep, external runtime/device/host discovery, second listener, second scheduler, second dispatcher, second materializer, second WorkerCoordinator, or second user-operated device is a runtime prerequisite.

## Validated reusable baseline

The validated StegVerse-002 Site browser lane remains the reusable execution baseline:

```text
registered StegVerse Node
-> Interlock
-> Universal InTr materialization
-> bounded lease
-> EVENT_EPHEMERAL browser runtime
-> execution-time runtime identity
-> existing WorkerCoordinator claim/fence
-> exact governed ingress
```

Key baseline evidence:

- `.github` PR `#1966` exact validated head `6edba060692e275361f9d8be8d17b5ad21158711`; Organization Control `35092566189`, Deterministic Suite `35092566222`, Heartbeat `35092566216` all SUCCESS; merge `94b8804687baed9251b4e6ecbb640f14c7259dc6`.
- Site PR `#1354` validated the unchanged SV002 lane; merge `a8846026bc80b9890c07ad72dda1350ce7f3c0d4`.
- Site PR `#1358` adapted only current StegBrowser Goal/COSV/manifest/payload/owned-mirror bindings while preserving the validated runtime mechanics; merge `64dcbb8803dae67d96d33849d92f45fb1206d57e`.

Source/CI has runtime authority `NONE`.

## First observed current-iPhone transition defect and repair

The existing current-iPhone same-device execution surface already owned the correct runtime mechanics:

- registered Node IndexedDB `stegos-node-v1`;
- write-once `intr_outbox`;
- existing root `/intr-service-worker.js`;
- `CURRENT_USER_IPHONE_SERVICE_WORKER` runtime surface;
- fail-closed local InTr admission.

The first observed transition defect was narrower: the existing current-iPhone launcher/extension still bound retired lineage task `STEG-BROWSER-RUNTIME-CONSUMPTION-001` to destination `CanonicalWork:Ingress` instead of the active immutable StegBrowser manifest invocation.

Site PR `#1360` repaired only that invocation-specific edge. It reused the same root worker, Node outbox, runtime, and authority boundaries and rebound them to:

```text
Goal = STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001
Parent = STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001
COSV = 40000100100000
nonce = STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z
destination = StegBrowser:ManifestInvocation
downstream owner = StegVerse-Labs/.github#1952
manifest sha256 = fcde63451bf612df8f3b2b62fa6766670dc880f2fcb66605680a2af6f2096f74
```

The materialization ID is deterministic from the unchanged nonce, so repeated page activation targets the same write-once Node-outbox identity instead of silently minting another invocation.

Site PR `#1360` evidence:

- exact validated source head `d031a1c560814a1c1cd275656925258cee11f323`;
- Session Work Claims PASS;
- Site Handoff Orchestration PASS;
- Ecosystem Heartbeat contract PASS;
- Site validation / Node-continuity / IndexedDB-alignment PASS;
- Cloudflare Workers build SUCCESS, version `4d24d113-f37e-4b59-8c94-c49b60cd559b`;
- merge `76af62f2befdfa7034d3dd00891bfe60a0990abb`.

Site handoff reconciliation PR `#1361` subsequently merged as `7c483335f259d5eacf9a55dde923c0c4fefd660e` after exact-head Site Bootstrap, orchestration, heartbeat, and Cloudflare build validation passed.

Attempted claim-only terminalization PR `#1362` was closed without merge because Site orchestration correctly requires the claim to remain active while authentic same-device A1-A4 execution is unfinished. That is coordination truth, not a runtime failure.

## Existing authorized same-device execution surface

The existing Site execution page is:

```text
https://stegverse.org/stegos-bootstrap/canonical-work-runtime-consumption.html?autostart=1
```

It loads the existing Node bootstrap, root-profile bridge, and current-iPhone launcher. In the same Safari site-data context that owns the registered StegVerse Node, it reads Receipt #1 from the existing Node IndexedDB and submits the deterministic unchanged-nonce trigger through the existing root `/intr-service-worker.js`.

The page may promote only authentic current-device `INGRESS_ADMITTED` evidence. It explicitly leaves EVENT_EPHEMERAL runtime identity, WorkerCoordinator claim/fence, A4, and Round Trip 1 pending unless those authority-owned receipts are actually observed.

## Required authentic chain

```text
registered Node Receipt #1
-> deterministic unchanged-nonce Node outbox entry
-> StegBrowser:ManifestInvocation Universal InTr materialization
-> write-once INGRESS_ADMITTED
-> bounded invocation lease
-> EVENT_EPHEMERAL runtime identity
-> WorkerCoordinator claim/fence
-> exact governed StegBrowser A4 ingress
```

Exact Goal/COSV/nonce/manifest/node/interlock/registration/materialization/lease/runtime/claim/fence correlation is required across the retained evidence.

## Current authentic predicates

Source validation, merge, deployment, public reachability, service-worker installation, and page load are not runtime proof. No authority-owned same-invocation A1-A4 receipt set has yet been observed in this chat, so:

```text
MANIFEST_BOUND_TO_INVOCATION runtime confirmation = false
STEGVERSE_NODE_BOUND_TO_INVOCATION = false
INTERLOCK_BOUND_TO_NODE_AND_MANIFEST = false
INTR_MATERIALIZATION_ADMITTED = false
INVOCATION_SCOPED_LEASE_ESTABLISHED = false
EVENT_EPHEMERAL_STEGOS_RUNTIME_MATERIALIZED = false
EXECUTION_TIME_RUNTIME_IDENTITY_BOUND = false
CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED = false
ORGANIZATION_LOCAL_INTR_INGRESS_RECEIPT_VERIFIED = false
AUTHENTIC_INTR_INGRESS_OBSERVED = false
ROUND_TRIP_1_STARTED = false
```

## Authority boundaries

- StegVerse Node: continuity/admission anchor only.
- Universal materialization request: execution authority `NONE`.
- Shared InTr ingress: transition/admission only; does not mint claim/fence.
- EVENT_EPHEMERAL runtime: bounded compute/materialization only.
- WorkerCoordinator: sole claim/fence authority.
- Interlock/InTr: governed transition authority.
- TV/TVC: credential authority.
- GitHub/CI: source validation/evidence transport only; runtime authority `NONE`.

## Immediate continuation

Do not emit another request, revive PR `#1960`, restore `CanonicalWork:Ingress` as the active StegBrowser binding, or add any second runtime/listener/scheduler/dispatcher/materializer/WorkerCoordinator/device/authority path.

Execute or observe only the unchanged nonce from the same registered iPhone/Safari context through the merged Site current-iPhone surface. Retain the page JSON exactly. Promote only predicates directly proven by authority-owned receipts. If A1-A4 all verify, enter Round Trip 1 immediately; otherwise repair only the first authentic transition failure exposed by the retained runtime evidence.

## README review

README reviewed after Site PRs `#1360` and `#1361`. No byte change required because public runtime/authority topology is unchanged; the repair changes only the active invocation binding and evidence correlation on the already-existing same-device surface.

## Manual work

Open the existing same-device execution page on the same iPhone/Safari site-data context that owns the registered StegVerse Node; do not use Private Browsing or clear site data. Preserve and return the complete page JSON or exact `FAIL_CLOSED` reason unchanged.
