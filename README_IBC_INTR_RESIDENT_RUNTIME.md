# IBC InTr Resident Runtime Consumer

Updated: 2026-09-09

Goal Task ID: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
Handoff: `docs/IBC_INTR_RESIDENT_RUNTIME_MIRROR_HANDOFF.md`

This repository slice integrates the already-merged StegOS verified Cosmos Hub → Osmosis ACK ingress with the existing canonical sovereign resident WorkerCoordinator/dispatcher substrate.

## Source

```text
control/resident-execution-request.d/ibc-verified-intr-ack-resident-001.json
scripts/consume_ibc_intr_resident_request.py
scripts/dispatch_resident_execution_requests.py
tests/test_ibc_intr_resident_consumer.py
```

The consumer requires:

```text
STEGVERSE_SOVEREIGN_NODE
STEGVERSE_STEGOS_ROOT
```

`STEGVERSE_STEGOS_ROOT` must point to a locally materialized StegOS source tree that already contains the merged verified ACK evidence chain and resident-capable `scripts/materialize_verified_ibc_intr_ack.py`. Resident dispatch performs no GitHub or network source fetch.

Without `STEGVERSE_SOVEREIGN_NODE`, the consumer returns `SOVEREIGN_NODE_MARKER_REQUIRED` and does not invoke the StegOS materializer. This prevents CI/source validation from manufacturing resident-runtime evidence.

When all predicates are satisfied, the consumer invokes the StegOS materializer with:

```text
--observation-class SOVEREIGN_RESIDENT_EXECUTED_CANONICAL_INTR_TRANSPORT_RECEIPT
--output <resident-runtime>/receipts/sovereign-host/ibc-verified-intr-ack-transport.latest.json
```

A successful resident consumption receipt may establish only that the sovereign resident process consumed the retained verified external ACK evidence through the canonical `heterogeneous-interop` `ACKNOWLEDGE` transport source.

It does not establish or mint:

```text
original IBC packet relay
transition admission
application execution
WorkerCoordinator claim/fence
credentials
Master Records custody/reconstruction
```

Those predicates remain separate and must be observed independently.

## Runtime receipt

The task-specific resident consumption receipt path is:

```text
receipts/sovereign-host/ibc-verified-intr-ack-request-consumption.latest.json
```

The inner canonical InTr transport artifact is retained at:

```text
receipts/sovereign-host/ibc-verified-intr-ack-transport.latest.json
```

Source, tests, CI, PR merge, or request registration do not satisfy the resident execution predicate. Only actual sovereign dispatcher consumption can produce the authentic runtime receipt.
