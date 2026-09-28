# KV AI End-to-End Runtime Evidence Mirror Handoff

Status: ACTIVE / BLOCKED-BY-WORKERCOORDINATOR-OBSERVATION / RUNTIME-EVIDENCE-PENDING
Goal Task ID: `SV-KV-AI-END-TO-END-RUNTIME-EVIDENCE-001`
Parent Goal Task ID: `SV-KV-AI-PERSISTENCE-001`
Upstream Goal Task ID: `SV-KV-AI-WORKERCOORDINATOR-RUNTIME-OBSERVATION-001`
COSV task.v1: `20111110110002`
Repository: `StegVerse-Labs/.github`
Owner issue: `StegVerse-Labs/.github#1883`

## Purpose

This handoff owns the downstream KV AI memory runtime chain after an authentic same-execution WorkerCoordinator claim/fence has been observed and bound.

## Required runtime chain

```text
real Personal-KV root + real _System/AI/Memory/Inputs files
-> autonomous fenced resident staging
-> shared Universal InTr exact-packet ALLOW
-> memory-packet-admission.json
-> fresh WorkerCoordinator claim/fence
-> KV_AI_MEMORY_PROVIDER_REQUEST_MATERIALIZED
-> governed TV/TVC provider/model ingress-response-egress chain
-> evidence-gated Personal-KV writeback/readback
-> Master Records reconstruction binding
```

## Entry condition

`SV-KV-AI-WORKERCOORDINATOR-RUNTIME-OBSERVATION-001` must first classify an authentic claim_id, worker_instance_id, lease, fencing_token, assignment timer, and Master Records worker-assignment binding. Source-only observer output, GitHub Actions validation, fixtures, or handoff prose cannot satisfy this entry condition.

## Authorized next action after entry

Continue only through the existing WorkerCoordinator and Interlock/InTr authority path. Use real owner-custodied Personal-KV inputs. Do not synthesize private memory/provider settings and do not export private content to GitHub.

## Nonclaims

This handoff does not authorize provider use, does not create credentials, does not mint claim/fence authority, does not claim Personal-KV inputs, does not claim live InTr admission, does not claim ProviderRequest materialization, does not claim provider/model execution, does not claim KV writeback/readback, and does not complete until the same execution chain binds every required predicate.


## Manifested one-way transport and receipt custody rule — owner decision 2026-09-28

Interlock/InTr is a one-way manifested transport. A round trip is two manifested one-way legs. Each endpoint boundary is itself a state transition and must be receipt-correlated:

1. origin endpoint EGRESS;
2. destination endpoint INGRESS;
3. destination endpoint EGRESS for the separately manifested return leg;
4. origin endpoint INGRESS.

All four endpoint receipts for one out-and-return journey carry the same `journey_id`, plus `leg`, `direction`, `endpoint`, `counterparty`, and the manifest digest for that one-way leg. Each leg's EGRESS/INGRESS pair carries the same `manifest_sha256`; the separately manifested return leg carries `predecessor_manifest_sha256` pointing to the outbound manifest. This evidence convention is additive inside the existing free-form receipt `evidence`; it does not change `.stegverse/transition-ledger/contract.json` or `emit.py`.

For an ephemeral StegOS/Node, ephemeral means non-durable custody, not passive transport. An admitted ephemeral node SHOULD be capable of reading the manifest, validating and acting on the capabilities/routes assigned to it, directing the manifested packet to the next manifest-selected Interlock/InTr destination, and updating/appending its own endpoint transition receipts as the packet crosses ingress and egress. Where a return or onward leg is required, the node uses the received manifest plus admitted return/next-hop instructions to construct or select the separately manifested next leg and predecessor-link it to the received leg. Its endpoint receipts use `custody: RETURN_WITH_MANIFEST`: they travel with the onward/return manifested packet to durable organization custody. No durable node-local receipt store is required after successful handoff, and lack of such storage must not become an external-device prerequisite. Organization receipt custody remains durable and Master Records reconstructs the governed communication from the organization chain.

For StegVerse-organization to StegVerse-organization transfer, each organization records its side of the manifested handoff and Master Records records/reconstructs the organization-to-organization communication. For an external framework, the admitted manifest must provide enough route/return shape for that framework to construct the separately manifested return leg; the external framework does not gain StegVerse transition authority by doing so.

### Source validator

`scripts/validate_transition_receipt_journey.py` validates the minimal two-leg/four-endpoint receipt journey and returns `ALLOW` only when correlation, manifest continuity, endpoint reversal, counterparty closure, returned ephemeral evidence, and custody semantics all agree. Missing or mismatched evidence returns an actionable `FAIL_CLOSED` from the CLI. Synthetic tests prove the validator contract only; they do not claim live InTr transport.

This validator is independent source work that can proceed while the authentic WorkerCoordinator claim/fence observation remains pending. It does not bypass that runtime entry condition.


## Source-interface reconciliation after PR #2824

The receipt-journey contract is now mapped onto existing implementation owners rather than a new transport plane:

- **Manifest / InTr request ingress:** `workers/manifest_state_transition_intr_ingress.py` already validates canonical manifest hash/projection, graph, capability, route, canonical task, and predecessor closure before using the existing WorkerCoordinator path.
- **KV exact-packet InTr ingress:** `workers/kv_ai_memory_intr_transport.py` validates exact resident-local InTr bytes and `workers/kv_ai_memory_intr_profile.py` emits the existing `INGRESS_ADMITTED / ALLOW` admission receipt. This is the current KV ingress seam to extend with journey evidence; it is not a second listener.
- **KV event bootstrap:** `workers/kv_ai_memory_intr_event_bootstrap.py` starts the existing shared Universal InTr listener for one request and continues only from real owner-custodied KV inputs.
- **Ephemeral StegOS/Node packet surface:** `StegVerse-Labs/Site:stegos-node/stegos-node-impl.js` already maintains an InTr outbox and exact materialization/payload continuity, but its current entries remain `LOCAL_OUTBOX_PENDING_NETWORK_DELIVERY` and explicitly report `network_delivery_observed=false`, `runtime_materialization_observed=false`, and `receiver_receipt_observed=false`. That source therefore does **not** yet satisfy the four-receipt journey.
- **Manifest-bound browser ingress owner:** `STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001` / `docs/STEGBROWSER_MANIFEST_INTR_INGRESS_EXECUTION_MIRROR_HANDOFF.md` already owns the manifest-defined Node -> Interlock -> InTr -> ephemeral StegOS runtime path.
- **Resident receipt transport owner:** `STEG-BROWSER-RESIDENT-RECEIPT-TRANSPORT-001` / `docs/STEGBROWSER_RESIDENT_RECEIPT_TRANSPORT_MIRROR_HANDOFF.md` already owns authentic receipt reachability/transport. The KV journey must consume that owner rather than create a parallel receipt transporter.
- **Durable custody:** `workers/canonical_state_transition_custody.py` already records organization custody before Master Records submission and verifies reconstruction/evidence closure. `resident-runtime/aggregate_repo_transition.py` and `.stegverse/transition-ledger/org-contract.json` remain the organization ledger seam.

### First real round-trip integration boundary

The first authentic journey is not gated on another device or a new listener. The missing source integration is narrower:

1. origin InTr EGRESS must append a packet-carried endpoint receipt with `journey_id`, leg 1, origin/counterparty, and outbound manifest digest;
2. the admitted ephemeral node must read the manifest, append leg-1 INGRESS, act/route only as manifested, construct/select the predecessor-linked return manifest, append leg-2 EGRESS, and place both ephemeral receipts in the onward packet;
3. origin leg-2 INGRESS must append its receipt and retain the returned endpoint receipts;
4. the existing organization custody path must record the endpoint handoff evidence and Master Records must reconstruct the same journey;
5. `scripts/validate_transition_receipt_journey.py` evaluates the retained four-receipt set. Until those authentic source calls exist and run, the runtime predicate remains pending.

The source changes for browser/ephemeral receipt transport belong to the two existing StegBrowser owners above. This KV task consumes their result and must not duplicate their checked-out authority. The KV-specific ingress/profile may add the journey fields when those owner interfaces expose them.

No source inspection here changes the authentic WorkerCoordinator claim/fence entry condition or claims a live round trip.
