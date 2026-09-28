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
