# Publisher Universal InTr Artifact Transfer Runtime Handoff

Updated: 2026-08-31
Issue: StegVerse-Labs/.github#583

```text
state: FORWARD_SOURCE_MERGED_VALIDATED / RETURN_SOURCE_IMPLEMENTED_PENDING_VALIDATION
canonical_profile: publisher-artifact-transfer
destination: STEGOS_ECOSYSTEM / Publisher:Ingress
response: Publisher:Export -> KV / KnowledgeVault:DocumentImport
credential_authority: TV/TVC
github_token_runtime_authority: NONE
authority_effect: NONE
```

## Purpose

Bind the already-merged Publisher exact-byte application adapter to the canonical
Universal InTr event-materialization plane without making an always-running
Publisher receiver a prerequisite.

The shared profiled ingress may accept a bounded
`stegverse.publisher-intr-materialization-trigger/v1` containing:

- the canonical non-authorizing materialization request;
- the exact transfer payload bytes as base64;
- the already-produced canonical forward hop-receipt chain.

Ingress verifies the exact payload hash and persists the request, payload, and
receipt-chain sidecars write-once before dispatching the consumer.

The consumer then independently requires:

1. canonical `publisher-artifact-transfer` profile from already-local StegOS;
2. exact payload hash match;
3. reconstructed canonical transport intent matching the materialization request;
4. complete canonical forward receipt-chain validation;
5. already-local Publisher source;
6. Publisher's own exact-byte transfer admission and document rendering validation.

Only after all forward predicates pass may Publisher render.

## Return boundary

Publisher output is converted with the same canonical connector into a response
packet:

```text
Publisher:Export
  -> KV / KnowledgeVault:DocumentImport
```

The consumer persists the exact response bytes and response intent but records:

```text
return_transport_observed=false
state=RENDERED_RETURN_PACKET_PREPARED_NOT_TRANSPORTED
```

until a separate authentic reverse InTr receipt chain exists.

## Non-claims

```text
materialization request != transport completion
ingress receipt != complete forward receipt chain
Publisher render != return transport
return packet prepared != KV import
KV import != publication
publication != release
```

No GitHub token, NON-TV/TVC credential, publication authority, release authority,
claim/fence, or runtime activation fact is created by this source.


## Merge and retry reconciliation

```text
source PR: #587
validated head: c351db843994b189d6fd0f3b2d0722918d05567e
merge: 0c9781d3de7a0b12b07ef136607ea69bb578f7a3
Cross-Framework Current-Basis Resident Request Validation: 33352019009 SUCCESS
Validate organization control plane: 33352018988 SUCCESS
Heartbeat Worker Project: 33352018992 SUCCESS
```

Exact-packet retry is permitted while the transfer has not reached
`RENDERED_RETURN_PACKET_PREPARED_NOT_TRANSPORTED`. Once that exact request hash
has produced the staged return packet, ingress and consumer replay are
idempotent and do not repeat Publisher rendering.

The materialization `payload_ref` must bind exactly to the runtime-local
write-once payload sidecar:

```text
runtime://intr-payloads/publisher-artifact-transfer/<materialization_id>.bin
```

This hardening changes neither publication/release authority nor the remaining
reverse-transport requirement.


## Reverse Publisher -> KV event-materialization — issue #592

Publisher now queues a non-authorizing Universal InTr materialization request for
`Publisher:Export -> DEVICE_SYSTEM -> KV/KnowledgeVault:DocumentImport`.
The return payload and intent are retained locally; `return_transport_observed`
remains false until a complete reverse hop-receipt chain exists.

The far-side shared ingress accepts a bounded return trigger containing the exact
return bytes, exact return intent, and reverse receipts. The KV consumer validates
that complete chain and then requires the original owner-authorized export bundle
from private KV-local state (`private-kv-document-exports/<export_id>.json` or
`STEGVERSE_KV_DOCUMENT_EXPORT_BUNDLE_ROOT`) before invoking CVK's merged
`runtime/document_intr_transfer.py`.

Success is only `VALIDATED_IMPORT_CANDIDATE_NOT_COMMITTED`; canonical KV mutation,
publication, release, and execution authority remain false.
