# StegAgents Governed-Agent Registration Mirror Handoff

Updated: 2026-09-14
Repository: `StegVerse-Labs/.github`
Target repository: `StegVerse-Labs/StegAgents`
Goal Task ID: `STEGAGENTS-GOVERNED-AGENT-REGISTRATION-001`
COSV: `71000000100110`
Status: `ACTIVE / CANONICAL REGISTRATION VALIDATION PENDING`

## Purpose

Continue the completed StegCore/StegAgents activation sequence into the next eligible integration goal: the first governed-agent manifest and registration flow in `StegVerse-Labs/StegAgents`.

This task must reuse the existing `agents/registry.yml` and StegAgents proposal boundary. It must not create a parallel agent registry, policy engine, execution authority, provider credential path, transition authority, or durable evidence authority.

## Preconditions already proven

- StegCore 001/002 registry is `activated` on merged main commit `60c1e12d80decbafffbdda25b04c392a7735d13e`.
- StegAgents/StegCore handshake registry is `handshake_ready` on merged main commit `a7fbc77081330d074b0202c70a4fa835f04e7f39`.
- Canonical predecessor task `STEGCORE-STEGAGENTS-ACTIVATION-SEQUENCE-001` is `RETIRED / COMPLETED`.

These source and CI facts do not themselves activate any agent or prove resident execution.

## Registration-first rule

This Goal Task was absent from the canonical Task Registry when the continuation began. Therefore source mutation in StegAgents is not admitted yet.

Required sequence:

1. register this Goal Task and COSV in `StegVerse-Labs/.github`;
2. validate and merge canonical registration;
3. execute/reconstruct the canonical collision check-in for the exact `StegVerse-Labs/StegAgents` manifest/registry mutation scope;
4. proceed only when the returned disposition permits continuation;
5. implement the manifest/registration flow on one StegAgents branch;
6. require exact-head validation and merged-main revalidation;
7. update this handoff and canonical task record with authentic completion evidence;
8. retire the task only after the source flow is merged and validated.

## Intended StegAgents source shape

The initial bounded flow should include:

- one governed-agent manifest schema;
- one first governed-agent manifest bound to an existing `agents/registry.yml` identity;
- one validator that proves registry identity, governance dependency evidence, proposal-only posture, and authority boundaries;
- a deterministic registration representation in the existing registry surface rather than a second registry;
- unit tests and CI;
- a StegAgents-local `*_MIRROR_HANDOFF.md` recording exact state.

The first governed agent should be chosen from an existing provider-neutral/proposal-only identity where possible. `CodeRepair-001` is the preferred candidate because it is already provider-neutral and explicitly proposal-only; implementation must verify this from current main before binding it.

## Authority boundaries

- StegAgents proposes; it does not dispose consequential transitions.
- StegCore/InTr remains governance/state-transition authority.
- TV/TVC remains provider credential and provider-operation authority where applicable.
- KV/SKAP Vault remains sole user-verification authority.
- Master Records remains observed-reality custody/reconstruction authority.
- HeartBeat is synchronization/timing/freshness/liveness/correlation/observability only.
- GitHub is source/evidence coordination only and has runtime authority `NONE`.
- A governed-agent manifest cannot mint execution authority, user identity truth, provider credentials, continuity truth, or master-record truth.

## Completion predicates

Completion requires all of the following:

- canonical task registration validated and merged;
- collision check admits exact StegAgents mutation scope;
- first manifest schema valid;
- first manifest binds an existing agent identity without duplicating the registry;
- exact activated StegCore and handshake-ready evidence bound;
- manifest/refusal tests prove no self-authorization or raw-trace/master-record exposure;
- exact-head CI passes;
- source PR merges;
- merged-main validation passes;
- canonical handoff and task record updated with exact evidence.

## README review

No `.github` README change is required for task registration. A StegAgents README change is required only if the new manifest/registration flow becomes a supported repository-facing capability that is not already represented by current documentation.

## Human action

None.
