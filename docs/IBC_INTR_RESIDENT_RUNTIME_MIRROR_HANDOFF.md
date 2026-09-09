# IBC InTr Resident Runtime Mirror Handoff

Updated: 2026-09-09
Organization: `StegVerse-Labs`
Repository: `StegVerse-Labs/.github`
Goal: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
State: `RESIDENT_CONSUMER_SOURCE_IN_PROGRESS / AUTHENTIC_RESIDENT_CONSUMPTION_PENDING`

## Purpose

Carry the already-retained, independently verified Cosmos Hub -> Osmosis acknowledgement evidence through the existing canonical sovereign resident WorkerCoordinator/dispatcher substrate without creating a second runtime, scheduler, credential lane, transition path, or custody path.

## Canonical parents

- `docs/CANONICAL_WORK_COORDINATION_SYSTEM_MIRROR_HANDOFF.md`
- `docs/CANONICAL_RESIDENT_CARRIER_MIRROR_HANDOFF.md`
- `StegVerse-Labs/StegOS/docs/IBC_INTR_INTEROPERABILITY_MIRROR_HANDOFF.md`

The canonical Task Registry remains generation 17 with `STEGVERSE-CANONICAL-WORK-COORDINATION-001` in `PROPOSED` state. No dedicated IBC task is registered. This resident experiment is therefore a bounded continuation under that task identity.

## Already-established evidence

StegOS has already retained and merged:

- authentic public Cosmos Hub acknowledgement proof material for `transfer/channel-141`, sequence `999999`;
- independent ICS-23 membership verification;
- accepted StegOS verification record;
- verified classic-IBC evidence projection;
- workflow-executed canonical `heterogeneous-interop` `ACKNOWLEDGE` receipt.

The workflow receipt is transport-conformance evidence only. It is not resident runtime evidence.

## Resident experiment contract

The resident consumer must:

1. execute only through the existing `scripts/dispatch_resident_execution_requests.py` substrate;
2. require a locally materialized StegOS source root via `STEGVERSE_STEGOS_ROOT`;
3. perform no GitHub/source/network fetch during resident dispatch;
4. verify the exact merged StegOS evidence and ACK-ingress source are present locally;
5. execute the merged StegOS verified-ACK materializer locally;
6. retain a task-specific resident consumption receipt under `receipts/sovereign-host/`;
7. preserve `TV/TVC` credential authority and `NONE` GitHub-token runtime authority;
8. never claim original Cosmos/Osmosis packet relay, transition admission, application execution, WorkerCoordinator claim/fence minting, credentials, or Master Records custody unless separately observed.

## Evidence classes

A successful resident consumption receipt may establish that a sovereign resident process consumed the verified external evidence through the merged canonical InTr ACK materializer. It does not by itself establish live original IBC relay or downstream governed transition/custody.

## Next work

- create the resident request and fail-closed consumer;
- register the consumer in the canonical dispatcher;
- add deterministic tests and repository documentation;
- merge only after organization-control / deterministic validation passes;
- then wait for authentic sovereign resident dispatch to produce the task-specific receipt.

## Human action

None currently required.
