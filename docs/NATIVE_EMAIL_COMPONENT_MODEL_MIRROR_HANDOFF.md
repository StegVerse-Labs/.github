# Native Email Component Model Mirror Handoff

Updated: 2026-09-12
Goal Task ID: `STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001`
Runtime handoff: `docs/NATIVE_EMAIL_REUSABLE_HOURLY_MIRROR_HANDOFF.md`
COSV: `10100000100000`
Model merge: `StegVerse-Labs/.github#1652` -> `b9f8e5153aa1651f2d7f043fb902eacb7c113ed9`
Status: `ACTIVE / COMPONENT MODEL RECONCILED / RUNTIME EVIDENCE PENDING`

## Identity

The existing Goal Task remains valid. Componentization does not rename, duplicate, close, or reset it.

The decomposition policy score is 25: repeated subflows, multiple authority crossings, multiple round trips, cross-repository spread, growing handoff sequence, branching failure handling, independent reusability, optional subflows, and independent evidence predicates are present. Further bespoke orchestration growth is therefore superseded by reusable-component composition.

## Component composition

- Runtime observation: reuse the existing resident runtime surfaces. WorkerCoordinator owns claim/fence; HeartBeat is observability only. Expected evidence: fresh authentic claim/fence and worker/runtime observation.
- Source/execution materialization: reuse the existing ephemeral-construct/source-prep path and `SV-DN1-PRODUCTION-SOURCE-PREP-001`. Expected evidence: authentic `stegverse.sv-dn1.production-source-prep-receipt/v2` with `SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE` when source prep is required.
- Hourly schedule/retry: reuse `SHWP-HEALER-SOVEREIGN-SCHEDULER-001` and `RT-NATIVE-EMAIL-ACTION-MONITOR-001`. Only authentic successful trigger evidence satisfies a slot; retries remain bounded.
- Gmail search observation: reuse `RTC-ROUNDTRIP-003` with parameter `tvc_gmail_search_observation`; TV/TVC owns provider credential/session authority.
- Failure normalization/remediation: reuse the existing native-email normalizer and StegHealth corrective path. Do not create another evaluator. The model-level failure-remediation family remains a candidate, not a new Goal Task.
- KV persistence/readback: reuse the existing KV resolver/writer/guard. KV/SKAP Vault remains sole user-verification authority. Expected evidence: `KV_STORED_VERIFIED` for every represented failure incident.
- Governed archive decision: reuse `RTC-MANIFEST-001` + `RTC-GOVERNED-PROCESSING-002`; Interlock/InTr owns governed transition/admission. Exact reviewed IDs and verified KV receipts are inputs; caller cannot self-enable the provider consequence.
- Gmail archive consequence: reuse `RTC-ROUNDTRIP-003` with parameter `tvc_gmail_archive_consequence`; TV/TVC owns provider execution authority. Expected evidence: authentic provider result.
- Governed movement: reuse `RTC-INTERLOCK-INTR-TRANSPORT-008` only at actual governed transition boundaries.
- Evidence custody/reconstruction: reuse `RTC-EVIDENCE-CUSTODY-004`; Master Records owns observed reality, custody, readback, and reconstruction.

Transport selector: `data/goal-task-transport-profiles/STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001.json`.

Not selected: `RTC-PUBLISHER-005`, `RTC-SDK-RETURN-006`, `RTC-STEGVERSE-EGRESS-007`, and `RTC-FARSIDE-FINAL-009`. Publication, SDK return assembly, final StegVerse egress, and far-side final transition are not part of this Goal Task's completion semantics.

## Duplicate orchestration disposition

The long task-specific sequence remains runtime/provenance truth but is superseded as the primary architecture description by this component composition. Do not add another scheduler, runtime-presence probe, generic manifest route, Interlock/InTr adapter, credential route, source installer, KV verification authority, Master Records reconstruction path, or email-specific evaluator.

Existing native-email broker, KV guard/writer, source-prep adapter, and resident bridge remain task-specific bindings into canonical owners and must not grow into duplicate generic orchestration. Historical evidence remains preserved.

## Authority invariants

Task Registry coordinates only. WorkerCoordinator owns claim/fence. Interlock/InTr owns governed transition/admission. TV/TVC owns credential/provider/release authority. KV/SKAP Vault is sole user-verification authority. StegOS devices are interchangeable transport/execution nodes only. Master Records owns custody/reconstruction. HeartBeat is observability only. GitHub has no runtime authority. No device-local user verification is introduced.

## Remaining Goal predicates

Componentization does not prove runtime completion. The task still requires authentic evidence of resident execution; source-prep claim/fence and v2 receipt when needed; eligible hourly invocation; TV/TVC provider search; KV resolution and `KV_STORED_VERIFIED`; exact reviewed-ID/KV manifest binding; Interlock/InTr admission; canonical governed ALLOW/commit coherence; TV/TVC archive provider result; Master Records custody/reconstruction; bounded mailbox progression; and durable StegHealth/Canonical Work reconciliation.

## Canonical-source impact

The canonical Task Registry record remains valid and is not rewritten because identity, COSV, dependencies, targets, and completion predicates do not change. This handoff is the architecture projection; `docs/NATIVE_EMAIL_REUSABLE_HOURLY_MIRROR_HANDOFF.md` remains runtime truth.

`NO_README_CHANGE_REQUIRED`: PR #1652 already made the component model canonical in repository architecture.

## Next admissible work

Validate and merge this component projection, then continue through existing component/canonical-owner paths only. Re-observe authentic resident WorkerCoordinator/source-prep state first. If no resident surface exists, inspect only independently repairable component bindings and do not synthesize runtime/provider evidence.

## Human action

None.
