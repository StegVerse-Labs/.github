# Bootstrap v1 Sovereign Release-Prep Chain Mirror Handoff

Updated: 2026-08-30
Repository: `StegVerse-Labs/.github`
Goal: `BOOTSTRAP-V1-SOVEREIGN-RELEASE-PREP-CHAIN-001`

## Goal

Sequence the already-admitted Bootstrap v1 release-preparation tasks on one sovereign resident execution opportunity after authentic SV-DN-1 production-source preparation completes.

The chain owns orchestration only:

```text
SV-DN1-PRODUCTION-SOURCE-PREP-001 [prerequisite, not owned by this chain]
        |
        +--> BOOTSTRAP-V1-SOURCE-IDENTITY-FREEZE-001
        |
        +--> BOOTSTRAP-V1-SOURCE-PACKAGE-PRODUCTION-001
                 |
                 v
BOOTSTRAP-V1-RELEASE-CANDIDATE-FREEZE-001
                 |
                 v
BOOTSTRAP-V1-DISTRIBUTABLE-BUNDLE-001
```

The two first Bootstrap tasks are sibling consumers of the same authentic source-prep v2 receipt. The resident chain executes them sequentially for deterministic one-shot progression, but neither becomes the authority source for the other.

## Existing task authority remains unchanged

Each task retains its own:
- executable handoff;
- WorkerCoordinator claim;
- fresh fence;
- dependency gate;
- worker adapter;
- bound state;
- completion receipt;
- authority ceiling.

The chain does not mint claims or fences and does not alter dependency declarations.

## Sovereign execution boundary

The chain may run only on a non-hosted resident StegVerse runtime with:
- locally refreshed WorkerCoordinator source;
- separated carrier reference;
- mutable worker registry;
- authentic completed production-source-prep v2 receipt.

It rejects GitHub Actions, Render, Vercel, Cloudflare hosted execution, provider credentials, GitHub credentials, and arbitrary hosted CI.

It performs no network source acquisition.

## Durable prerequisite

Default:

`~/.stegverse/state/sv-dn1-production-source-prep/receipts/latest.json`

Required:
- schema `stegverse.sv-dn1.production-source-prep-receipt/v2`;
- state `COMPLETE`;
- transition `SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE`;
- four canonical `sha256-content-manifest` identities;
- four local source roots;
- `migration_anchors_verified=true`;
- zero network/platform/credential/repository authority predicates.

The mutable worker registry must also show `SV-DN1-PRODUCTION-SOURCE-PREP-001 = COMPLETED`.

## Step completion

After every targeted WorkerCoordinator cycle, the orchestrator must require both:
1. mutable task state `COMPLETED`;
2. exact durable receipt validation.

Required terminal transitions:

```text
BOOTSTRAP-V1-SOURCE-IDENTITY-FREEZE-001
  -> BOOTSTRAP_V1_SOURCE_IDENTITIES_FROZEN

BOOTSTRAP-V1-SOURCE-PACKAGE-PRODUCTION-001
  -> BOOTSTRAP_V1_SOURCE_PACKAGES_PRODUCED

BOOTSTRAP-V1-RELEASE-CANDIDATE-FREEZE-001
  -> BOOTSTRAP_V1_RELEASE_CANDIDATE_FROZEN

BOOTSTRAP-V1-DISTRIBUTABLE-BUNDLE-001
  -> BOOTSTRAP_V1_DISTRIBUTABLE_BUNDLE_BUILT
```

The chain stops on `ACTIVE`, `BLOCKED`, `HANDOFF_READY`, nonzero targeted execution, missing receipt, or receipt mismatch. It never skips a predecessor or fabricates completion.

## Resident request

Intent-only request:

`control/resident-execution-request.d/bootstrap-v1-release-prep-001.json`

Consumer:

`scripts/consume_bootstrap_v1_release_prep_request.py`

Entrypoint:

`scripts/run_bootstrap_v1_release_prep_chain.py`

The request grants no execution authority. A fresh request identity may be issued when runtime source or an upstream prerequisite materially changes.

## Chain terminal state

`BOOTSTRAP_V1_SOVEREIGN_RELEASE_PREP_COMPLETE`

This means:
- authentic source identities frozen;
- four exact local source packages produced;
- immutable rc.1 candidate frozen;
- canonical rc.1 distributable bundle built.

It does **not** mean:
- device materialization occurred;
- materialization evidence intake passed;
- release gate passed;
- a tag or publication was created;
- package execution was admitted;
- SDK/runtime authority was granted.

## Downstream

The next machine-owned stages remain separate:

```text
established device-node materialization
-> BOOTSTRAP-V1-MATERIALIZATION-EVIDENCE-INTAKE-001
-> BOOTSTRAP-V1-RELEASE-GATE-001
-> separate tag/publication mutation authority
```

## Authority boundary

```text
credential_authority: TV/TVC
github_token_runtime_authority: NONE
heartbeat_grants_execution_authority: false
network_source_fetch_performed: false
request_granted_authority: false
repository_writeback_authority: false
release/publication authority: false
package execution authority: false
SDK admission authority: false
second_machine_required: false
authority_effect: NONE_ORCHESTRATION_ONLY
```

Source merge, hosted validation, task assignment, or a chain request do not satisfy runtime completion.
