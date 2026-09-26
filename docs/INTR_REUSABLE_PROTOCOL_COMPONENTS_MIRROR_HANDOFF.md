# Interlock/InTr Reusable Protocol Components Mirror Handoff

Updated: 2026-09-15
Status: ACTIVE_SOURCE_DEFINED
Experiment basis: `STEGVERSE-002-SELF-CHARACTERIZATION-001` / frozen v0.3
Existing protocol definition task: `RT-INTR-PROTOCOL-ESTABLISH-001`

## Purpose

Project the smallest reusable Interlock/InTr work identities needed across StegVerse without cloning provider-, framework-, repository-, or application-specific governance planes.

The frozen StegVerse-002 self-characterization contract preserves the distinctions that drive this decomposition: evidence availability is not identity constitution; inference is not admission; admission is not authority transfer; successful execution is not standing; transport success is not application success; custody/reconstruction is not transition authority.

## Frozen-contract experimental result used for decomposition

The released deterministic principal policy `stegverse-sv002-native-evidence-principal-v1` was applied to the frozen v0.3 evidence surface with the subject identity manifest excluded as required. The evidence set included the frozen organization capability snapshot and pinned formal-resource material from AE, GTG, and RTG.

Observed policy result:

```text
entity_id: StegVerse-002
organization capability entries observed: 9
active capability ids observed:
  - stegverse-002.micro-node-runtime
  - stegverse-002.org-boundary
formal resource evidence observed: true
subject identity manifest observed: false
repository topology alone defines entity: false
capability availability alone defines entity: false
authority transfer assumed: false
proposed external interactions: none
```

This result is used only as the decomposition basis for reusable protocol work. It does not promote repository evidence, model output, or this handoff into runtime, standing, credential, or transition authority.

## Reusable InTr task set

### `RT-INTR-PROTOCOL-ESTABLISH-001`
Resolve or establish the applicable normalized Interlock/InTr protocol contract. This already existed and remains the protocol-definition root.

### `RT-INTR-BOUNDARY-ADMISSION-001`
Validate exact ingress boundary identity, normalized envelope/manifest, payload integrity, destination profile, and applicable standing. Emit an explicit allow/deny admission result and receipt.

### `RT-INTR-GOVERNED-TRANSITION-001`
Evaluate one admitted proposed transition through the applicable Transition Elements and resolve allow/deny plus authority effect separately. Successful execution or model/provider output cannot self-authorize.

### `RT-INTR-ROUNDTRIP-CORRELATION-001`
Preserve exact request/response correlation, destination profile, exactly-once semantics, response-loop prevention, and transport-versus-application disposition across governed return traffic.

### `RT-INTR-EVIDENCE-CUSTODY-001`
Bind exact receipt/artifact hashes and hand them to Master Records or the applicable canonical custody/reconstruction owner. Recording and reconstruction never inherit transition authority.

## Composition rule

```text
protocol needed but unresolved
  -> RT-INTR-PROTOCOL-ESTABLISH-001

governed ingress
  -> RT-INTR-BOUNDARY-ADMISSION-001

externally consequential state change
  -> RT-INTR-GOVERNED-TRANSITION-001

request/result exchange
  -> RT-INTR-ROUNDTRIP-CORRELATION-001

durable evidence required
  -> RT-INTR-EVIDENCE-CUSTODY-001
```

A Goal Task selects only the pieces it requires. These task identities may compose existing reusable transport components including `RTC-MANIFEST-001`, `RTC-GOVERNED-PROCESSING-002`, `RTC-ROUNDTRIP-003`, `RTC-EVIDENCE-CUSTODY-004`, `RTC-STEGVERSE-EGRESS-007`, `RTC-INTERLOCK-INTR-TRANSPORT-008`, and `RTC-FARSIDE-FINAL-009`; they do not duplicate those implementations.

## Authority invariants

- Task Registry / reusable registry: coordination and discovery only.
- WorkerCoordinator: execution claim/fence authority.
- Interlock/InTr: admission, governed transition, and packet-movement authority.
- TV/TVC: credential/provider authority.
- Master Records: observed reality, custody, and reconstruction authority.
- Provider/framework adapters: translation only unless separately authorized for provider operation.
- Model output: no self-granted authority.
- GitHub: no runtime authority.

## README determination

`NO_README_CHANGE_REQUIRED` for this source addition. The root README already documents the reusable-task component model and the Interlock/InTr transport family. This handoff and the registry shards add reusable task identities without changing runtime behavior or authority ownership.

## Next use

New Goal Tasks should resolve these reusable identities before deriving new Interlock/InTr implementation work. A new protocol/adapter implementation is warranted only when the existing protocol and reusable tasks cannot represent the required boundary semantics without mutation or ambiguity.

## Bounded participation clarification — 2026-09-25

The relevant canonical coordination goal is `STEGVERSE-CANONICAL-WORK-COORDINATION-001`; this handoff is a reusable-protocol definition, not a new canonical goal or independent authority. At the observed main Task Registry generation 251, preserve the existing goal and reuse the five `RT-INTR-*` identities above.

Every **presented** transition at a participating governed ingress/egress must be evaluated before its protected effect. An authenticated, scoped ALLOW admits only that attempt; DENY or FAIL_CLOSED terminates its attempted protected transition according to the native policy, while REVIEW/ESCALATE/REFUSE and other non-ALLOW dispositions remain distinct and non-authorizing. A correction is a new governed attempt, never silent continuation of the denied one.

Interlock/InTr does not claim to observe all AI, all traffic or every possible bypass, and a missing observation does not constitute a DENY or evidence of nonoccurrence. Preserve `UNKNOWN_NOT_AUTHENTICALLY_OBSERVED` when authentic original evidence is inaccessible. Keep constraint/provenance evidence distinct from per-transition evaluation evidence, and retain exact predecessor-linked records for bounded Master Records reconstruction.

Time, heartbeat cadence, timestamps and freshness cannot generate authority or make prior ALLOW perpetual. Verify separately applicable current standing at the consequential boundary. Reuse existing protocol/admission/transition/roundtrip/custody tasks to test these limits; do not add a new evaluator, transport, runtime, or universal-monitoring requirement.

Source-only documentation clarification; no claimed resident disposition, deployment, proof of universal mediation, or change to Task Registry coordination state.
