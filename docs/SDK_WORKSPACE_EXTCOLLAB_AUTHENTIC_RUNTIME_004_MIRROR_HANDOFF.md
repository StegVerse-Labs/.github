# SDK WorkSpace External-Collaboration Authentic Runtime 004 Mirror Handoff

Updated: 2026-09-12
Repository: `StegVerse-Labs/.github`
Goal Task ID: `SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004`
Parent Goal Task ID: `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003`
COSV: `71000000100110`
Status: `ACTIVE / RESOLVER REPAIR MERGED + VALIDATED / SOURCE COMPATIBILITY PINNED / KV-SKAP USER-VERIFIER + INTERCHANGEABLE-STEGOS-NODE INVARIANT ALIGNED / AUTHENTIC RESIDENT OBSERVATION REQUIRED`

## Purpose

This is the active canonical successor after parent `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003` retired at 20/20. It owns the remaining authentic resident reseal/listener, custody, callback, owner-present consent, provider probe, SDK re-evaluation, MIR, Master Records, one-device, propagation, and public-distribution predicates.

## Authority boundary

Task Registry is coordination only. WorkerCoordinator owns claim/fence authority; Interlock/InTr owns governed transition authority; TV/TVC owns credential/provider/release authority; **KV/SKAP Vault is the sole user-verification authority**; Master Records owns observed reality/reconstruction; `StegVerse-org/LLM-adapter#72` remains the Service Gateway owner. GitHub has no runtime authority. No hosted fallback or second user-operated device is authorized.

StegOS devices are interchangeable transport nodes. A device, node identifier, transport identity, Secure Enclave identity, or runtime-presence subject MUST NOT become an independent user verifier or user-identity authority. User verification remains continuous through KV/SKAP Vault regardless of which eligible StegOS node is currently carrying the work.

## Reconciled merged source state

The existing source chain remains merged and validated through `.github` #1393, SDK #196, `.github` #1402, LLM-adapter #332, SDK #199, `.github` #1415, TVC #403, SDK #201, `.github` #1427, `.github` #1460, `.github` #1478, `.github` #1485, `.github` #1547, `.github` #1552, shared runtime-presence subject propagation `.github` #1562, and global KV/SKAP-verifier/interchangeable-node invariant `.github` #1627.

PR #1460 merged at `3bc8898655d344ba12f47bb4120e38f2ac1ded6e` from exact head `a926d04e563fa6f89920bd608a2ff359b272ca13`. Exact-head validation passed in all three required lanes: Deterministic Repository Suite `34615578871`, Organization Control `34615578937`, and Heartbeat Worker Project validation `34615578890`.

PR #1485 merged at `329b65cf5f50883001ee90c7ee03120c67a7375d` from exact head `9b5d5c8e25f0a53ff208827bf8881edc5e84df52`. Exact-head validation passed in Deterministic Repository Suite `34635461458`, Heartbeat Worker Project `34635461437`, and Organization Control `34635461393`.

PR #1562 merged at `cc53257c7e57347d2481dd4fd680aed9b8cf2f6d` from exact head `a9264f70f94c647932f3c5662468b9f6e972294b`. Exact-head validation passed in Deterministic Repository Suite `34670772330`, Organization Control `34670772342`, and Heartbeat Worker Project `34670772383`.

PR #1627 merged at `b27114d812c8ee9c9584ebe9a99cef4fa2297cfb` and established the ecosystem-wide invariant used here: KV/SKAP Vault is the sole user verifier, while StegOS devices are interchangeable transport nodes with no independent device/node/transport user-verifier authority.

The merged resolver repair falls back to the exact standalone canonical task record when the aggregate registry has no row, fails closed on duplicate aggregate identities and standalone record-ID mismatch, and aligns `resident_request_dispatch` discovery with `mutation_required=false`. Mutation/execution authority remains with WorkerCoordinator + Interlock/InTr; no runtime authority is created.

## Runtime source compatibility boundary

`canonical-resident-substrate-v1` satisfies every static requirement for this task: `resident_request_dispatch`, `SOVEREIGN_RESIDENT`, `INTERNAL`, no mutation requirement, and no deployment requirement. The profile remains `DECLARED_ONLY`, while this task requires a current observed runtime.

The exact remaining resolver rejection is:

```text
CURRENT_OBSERVATION_REQUIRED:DECLARED_ONLY
```

There is no remaining known source-side capability/environment/direction/mutation/deployment mismatch. Focused regression coverage pins this boundary so the resolver must continue to return zero candidates until an authentic current observation exists, while preserving non-authorizing discovery semantics.

## KV/SKAP verifier and interchangeable-node boundary

The current runtime must still be bound to the exact runtime subject so evidence from one resident instance cannot be silently reused for another. That subject binding is **evidence correlation only**. It is not user verification, user identity, credential authority, execution authority, or a requirement that one physical device remain permanent.

The correct separation is:

```text
user verification / user authority continuity -> KV/SKAP Vault
eligible current transport/execution surface -> interchangeable StegOS node
runtime evidence subject correlation -> runtime_root + resident.node_id + WorkerCoordinator identity
transition authority -> Interlock/InTr
credential/provider/release authority -> TV/TVC
observed reality/reconstruction -> Master Records
```

Therefore `resident.node_id` may distinguish which actual runtime instance produced a receipt, but it MUST NOT be treated as the user's verifier, identity authority, or permanent device binding. A different eligible StegOS node may lawfully carry subsequent work when KV/SKAP continuity and the other governed predicates are satisfied.

## Canonical runtime-presence reuse boundary

The sole canonical presence producer remains `heartbeat_runtime/runtime_presence_projection.py`, with output `receipts/sovereign-host/runtime-presence.latest.json`. Do not create another liveness/presence probe.

PR #1562 improves that existing producer's subject projection without changing liveness semantics. Existing `node_id` remains first priority, `sovereign_node` remains second priority, and a preserved `resident_rendezvous_node_ref` may now populate `resident.node_id` only when it matches canonical `SV-NODE-<24 lowercase hex>`. The projection also records `resident.node_identity_source`. Malformed rendezvous references remain unusable, and the rendezvous field is not itself a liveness signal.

This means exact retained-node identity is no longer structurally lost when authentic runtime-presence/self-heal evidence already carries the selected StegBrowser/StegOS rendezvous node. It does **not** create a current observation, prove a resident online, authorize this task to reuse another consumer's presence evidence, or elevate node identity into user verification.

Cross-task reuse remains intentionally unauthorized until authentic evidence binds the exact runtime subject:

```text
runtime_root identity
+ resident.node_id when available
+ canonical WorkerCoordinator identity
```

A profile-level or WorkerCoordinator-class match alone must not allow one runtime instance to satisfy a different consumer. This is an evidence-integrity rule, not a device-locking rule. The canonical cross-task coordination handoff remains `docs/RUNTIME_PRESENCE_CROSS_TASK_COORDINATION_MIRROR_HANDOFF.md`.

## Fresh authentic observation

At `2026-09-12T03:25:00Z`, this continuation rechecked available evidence channels and recorded the non-authorizing observation at `receipts/preflight/SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004-OBSERVATION-20260912.json`:

- authorized remote-resident connector: zero devices;
- retained Google Drive exact reseal receipt matches: zero;
- retained Google Drive exact listener receipt matches: zero;
- GitHub repository search: no authentic committed `runtime-presence.latest.json`, reseal receipt, or listener receipt; only source/documentation/reference surfaces were found.

A fresh continuation recheck after merged #1562 again found zero authorized remote devices and zero exact retained-Drive matches for both required receipts. Repository search still found no authentic committed `runtime-presence.latest.json`; #1562 changes what subject identity can be projected *when* authentic presence exists, not whether such presence currently exists.

Therefore runtime resolution remains unresolved solely at the authentic-current-observation boundary. No resident execution, target custody/readback, listener health, CMC-029 live TLS adoption, sovereign callback reachability, Google consent, provider probe, MIR, Master Records reconstruction, one-device completion, downstream propagation, or public distribution is claimed.

Expected resident receipts remain:

```text
receipts/sovereign-host/sdk-workspace-external-collab-client-secret-reseal.latest.json
receipts/sovereign-host/sdk-workspace-external-collab-consent-listener.latest.json
```

## Current proof boundary

```text
portable exact dispatch: MERGED / VALIDATED
Service Gateway three-route source: MERGED / VALIDATED
resolver standalone-record fallback: MERGED / VALIDATED
successor dispatcher discovery mutation semantic: MERGED / VALIDATED
static resolver source compatibility: PROVEN
KV/SKAP sole user-verifier invariant: MERGED / ENFORCED GLOBALLY
interchangeable StegOS node invariant: MERGED / ENFORCED GLOBALLY
canonical runtime-presence producer: EXISTING / REUSE REQUIRED
retained rendezvous node -> resident.node_id projection: MERGED / VALIDATED
resident.node_id authority role: EVIDENCE SUBJECT ONLY / NOT USER VERIFIER
cross-task presence subject binding: NOT YET ADMISSIBLE
remaining resolver condition: CURRENT_OBSERVATION_REQUIRED:DECLARED_ONLY
resident reseal receipt: NOT OBSERVED
resident listener receipt: NOT OBSERVED
authorized remote runtime online: NOT OBSERVED
target client-secret custody/readback: NOT PROVEN
resident listener health 127.0.0.1:8786: NOT PROVEN
sovereign stegverse.org callback/public HTTPS reachability: NOT PROVEN
owner-present Google consent/session: NOT PROVEN
authoritative provider-file probe: NOT PROVEN
SDK complete-predicate re-evaluation: NOT PROVEN
MIR transition reporting: NOT PROVEN
Master Records reconstruction: NOT PROVEN
one-current-device end-to-end: NOT PROVEN
downstream propagation complete: FALSE
public distributions complete: FALSE
```

## Exact next sequence

1. Recheck the existing authorized resident connection and current runtime observation. No additional resolver/source remediation is presently indicated.
2. If authentic `runtime-presence.latest.json` appears, require exact `runtime_root` plus projected `resident.node_id`/WorkerCoordinator subject binding before using it for this task. Treat that binding strictly as runtime-instance evidence correlation; user verification remains KV/SKAP-only and the StegOS node remains interchangeable.
3. When an eligible current resident is present and resolves lawfully, exact-dispatch only `sdk_workspace_external_collab_client_secret_reseal` and `sdk_workspace_external_collab_consent_listener` from already-local canonical source. Do not require the same physical StegOS device used by a prior step if KV/SKAP continuity and governed runtime predicates are satisfied.
4. Accept only authentic reseal `TARGET_ALREADY_PRESENT`, `COMPLETED`, or exact `BLOCKED`; validate custody/readback without overwrite.
5. Accept only authentic listener `SERVICE_ALREADY_HEALTHY`, `COMPLETED` with `loopback_health_verified=true`, or exact `BLOCKED`; remediate only the exact resident prerequisite if blocked.
6. After listener health, prove the existing Service Gateway public routes and CMC-029/native-TLS adoption without callback-query leakage.
7. Only after target custody plus sovereign callback reachability, perform owner-present Google consent on the current iPhone, with user verification continuing through KV/SKAP Vault rather than a device-local verifier.
8. Run one exact authoritative provider-file metadata probe, then SDK re-evaluation, MIR, Master Records reconstruction, one-current-device proof, downstream propagation, and public-distribution proof.
9. Do not manually publish StegCore; wait for authentic TV/TVC GRANTED release authority and required resident SKAP/double-Interlock evidence.

## README review

Root `README.md` remains accurate. This change reconciles the already-merged global KV/SKAP user-verifier/interchangeable-node invariant into this task's runtime-evidence semantics; it introduces no new public capability, execution authority, or runtime activation claim.

## Human action

None now. Do not initiate Google consent and do not manually publish StegCore `v0.3.0`.
