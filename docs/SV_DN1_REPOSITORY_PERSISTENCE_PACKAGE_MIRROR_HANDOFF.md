# SV-DN-1 Repository Persistence Package Mirror Handoff

Updated: 2026-08-30
Repository: `StegVerse-Labs/.github`
Goal: `SV-DN1-REPOSITORY-PERSISTENCE-PACKAGE-001`
Task: `SV-DN1-REPOSITORY-PERSISTENCE-PACKAGE-001`
Parent task: `SV-DN1-PUBLIC-PROMOTION-001`
Canonical product owner: `StegVerse-org/stegverse-demo-suite`
Credential authority: `TV/TVC`
GitHub token runtime authority: `NONE`
Authority effect: `NONE_PERSISTENCE_PACKAGE_ONLY`

## Goal

Close the machine-execution gap after `SV_DN1_PUBLIC_PROMOTION_READY` without inventing repository credentials or depending on an unadmitted broker.

The task consumes the authentic local public-promotion receipt plus the five already-promoted public artifacts and freezes one self-contained, content-addressed persistence package:

```text
SV_DN1_PUBLIC_PROMOTION_READY
  -> validate exact five-file hash map
  -> read exact local public bytes
  -> bind target repository/ref/paths
  -> encode exact bytes without semantic transformation
  -> hash canonical persistence package body
  -> write bounded local package + receipt
  -> SV_DN1_REPOSITORY_PERSISTENCE_PACKAGE_READY
```

The package is transport-neutral. It can later be consumed by any separately admitted TV/TVC-governed repository mutation authority. This task itself performs no network access, credential use, commit, push, merge, deployment, publication decision, release, or certification.

## Required inputs

Promotion receipt:

```text
~/.stegverse/state/sv-dn1-public-promotion/receipts/latest.json
schema = stegverse.sv-dn1.public-promotion-worker-receipt/v1
state = COMPLETE
transition_id = SV_DN1_PUBLIC_PROMOTION_READY
observation_class = LIVE
publication_state in {PUBLIC_OBSERVED, PUBLIC_WITH_LIMITATIONS}
exact_bytes_preserved = true
semantic_rewrite_performed = false
network_fetch_performed = false
credential_used = false
repository_writeback_performed = false
deployment_performed = false
release_performed = false
certification_claimed = false
authority_effect = NONE_STATIC_PROJECTION_ONLY
```

Already-local demo-suite public projection:

```text
public/sv-dn1/
  first-round-analysis.json
  production-pipeline-observation.json
  result-receipt.json
  report.md
  index.html
```

The SHA-256 of every file MUST match the promotion receipt destination hash map exactly.

## Persistence package contract

Schema: `stegverse.sv-dn1.repository-persistence-package/v1`

Required immutable fields:

```text
state = READY_FOR_ADMITTED_REPOSITORY_MUTATION
target_repository = StegVerse-org/stegverse-demo-suite
target_ref = main
target_root = public/sv-dn1
exchange_id = <promotion exchange>
manifest_receipt_id = <promotion manifest receipt>
publication_state = <existing non-WITHHELD state>
observation_class = LIVE
files = exactly five entries
exact_bytes_preserved = true
semantic_rewrite_performed = false
network_fetch_performed = false
credential_used = false
repository_writeback_performed = false
deployment_performed = false
authority_effect = NONE_PERSISTENCE_PACKAGE_ONLY
```

Each file entry includes:
- relative target path;
- SHA-256;
- size;
- exact bytes encoded as base64.

`package_sha256` is SHA-256 over the canonical JSON body excluding the `package_sha256` field itself.

## Authority boundary

This task MAY:
- validate the predecessor receipt;
- read only the five already-local promoted public artifacts;
- encode exact bytes into a bounded package;
- freeze target repository/ref/path metadata;
- emit local package/receipt evidence.

This task MUST NOT:
- fetch or mutate a remote repository;
- use GitHub/provider credentials;
- rely on GitHub as source authority;
- commit, push, merge, deploy, release, or certify;
- change the publication state;
- re-run SDK/evaluator/governance/custody;
- alter, normalize, or re-render artifact bytes.

## Bound state

```text
~/.stegverse/state/sv-dn1-repository-persistence-package/
  packages/latest.json
  receipts/latest.json
```

Existing frozen package conflict fails closed.

## Completion

Terminal transition:

`SV_DN1_REPOSITORY_PERSISTENCE_PACKAGE_READY`

Completion means the exact authentic public projection is frozen into a self-contained persistence package ready for a separately admitted repository mutation authority. It does NOT mean repository persistence, merge, deployment, public HTTPS observation, release, or certification occurred.

## Runtime truth at creation

```text
authentic HF observation: OBSERVED
Universal InTr hop: OBSERVED
fresh governed first-round request 006: MERGED / REQUESTED
SDK authentic first round: NOT YET OBSERVED
public promotion task: MERGED / WAITING ON SDK
repository persistence package task: MERGED / VALIDATED / WAITING ON AUTHENTIC PUBLIC PROMOTION
remote repository persistence of authentic result: NOT OBSERVED
Pages deployment of authentic governed result: NOT OBSERVED
```

Newer authentic runtime evidence overrides this handoff.
