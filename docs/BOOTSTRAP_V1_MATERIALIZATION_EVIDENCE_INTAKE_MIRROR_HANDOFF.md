# Bootstrap v1 Materialization Evidence Intake Mirror Handoff

Updated: 2026-08-29
Repository: `StegVerse-Labs/.github`

## Goal

Validate one authentic `stegverse.device-node-bootstrap-bundle-evidence/v1` exported by an established StegVerse node and convert it into one bounded release-gate proof that the exact frozen Bootstrap v1 rc.1 distribution bundle was materially retained and replayed on-device.

This lane validates evidence. It does **not** create source identities, build a bundle, mint a node identity, admit source for execution, activate Bootstrap v1, publish artifacts, or create a Git tag/release.

## Required upstream

The intake requires three already-local immutable inputs:

1. frozen Bootstrap v1 release candidate (`stegverse.bootstrap.release-candidate/v1 @ 1.0.0-rc.1`);
2. canonical distributable bundle (`stegverse.bootstrap.bundle/v1 @ 1.0.0-rc.1`);
3. exported device evidence (`stegverse.device-node-bootstrap-bundle-evidence/v1`).

The candidate and bundle must be the exact objects produced by their canonical Bootstrap v1 workers. Device evidence may arrive by any admitted transport; transport is not part of evidence identity.

## Validation order

```text
validate frozen rc.1 candidate
  -> validate canonical bundle identity
  -> bind bundle release_candidate to exact candidate
  -> validate bundle contains exactly four ordered component identities
  -> validate device evidence established node/device IDs
  -> require continuity_source is an established/replayed continuity mode
  -> bind evidence bundle_identity to exact canonical bundle
  -> bind evidence candidate_identity and source identity-set digest
  -> require exactly four ordered package materialization entries
  -> validate each package receipt component/source identity against bundle
  -> validate aggregate bundle materialization receipt
  -> replay complete continued_receipts journal from genesis to evidence tail
  -> require journal_replay PASS and exact tail equality
  -> require MATERIALIZED_UNADMITTED / execution_authority=NONE
  -> emit BOOTSTRAP_V1_DISTRIBUTION_MATERIALIZATION_PROVEN
```

## Required component order

```text
stegverse.sdk
stegverse.stegcore
stegverse.core-lite
stegverse.master-records
```

No alternate order, omitted component, duplicated component, or replacement identity is accepted.

## Evidence invariants

The accepted evidence must prove:

```text
state: MATERIALIZED_UNADMITTED
component_count: 4
all_components_materialized: true
new_node_identity_minted: false
credential_material_observed: false
github_platform_required: false
specific_external_platform_required: false
execution_authority: NONE
authority_effect: NONE
journal_replay.state: PASS
```

Each per-package receipt must remain `UNADMITTED` and carry no execution authority. The aggregate receipt must bind the same bundle identity, candidate identity, ordered component identities, established node ID, and established device-continuity ID.

## Bound state

Default:

```text
~/.stegverse/state/bootstrap-v1-materialization-evidence-intake/
  input/device-evidence.json
  receipts/latest.json
```

Canonical candidate and bundle roots are supplied through explicit non-secret locator environment variables. The worker performs no network acquisition.

## Output

Receipt schema:

`stegverse.bootstrap.materialization-proof/v1`

Terminal transition:

`BOOTSTRAP_V1_DISTRIBUTION_MATERIALIZATION_PROVEN`

The receipt includes exact candidate identity, bundle identity, ordered component/source identities, established node/device IDs, replay tail, evidence SHA-256, and zero-authority fields.

## Authority

```text
credential_authority: TV/TVC
github_token_required: false
github_token_runtime_authority: NONE
network_access: false
repository_writeback_authority: false
source_identity_freeze_authority: false
package_execution_authority: false
sdk_admission_authority: false
release_activation_authority: false
publication_authority: false
tag_authority: false
authority_effect: NONE_EVIDENCE_VALIDATION_ONLY
```

## Fail-closed conditions

Reject evidence when any of the following occurs:

- candidate or bundle is missing/unfrozen/mismatched;
- bundle identity recomputation fails;
- evidence bundle/candidate/source-set identity differs;
- journal sequence, previous hash, receipt hash, entry hash, or replay tail differs;
- package materialization entries are missing, duplicated, reordered, or identity-mismatched;
- aggregate receipt is absent or does not bind the exact package set;
- evidence claims a new node identity, credential material, platform dependency, execution authority, release activation, or publication;
- existing frozen proof differs from the newly validated proof.

## Runtime truth

```text
four-component Site receiver: IMPLEMENTED / MERGED
canonical bundle builder: IMPLEMENTED / MERGED
materialization evidence intake: IMPLEMENTING
first authentic frozen source catalog: NOT YET OBSERVED
Bootstrap v1 rc.1: NOT YET FROZEN
canonical runtime bundle: NOT YET BUILT
first authentic bundle materialization evidence: NOT YET OBSERVED
Bootstrap v1 distribution materialization proof: NOT YET OBSERVED
Bootstrap v1 release/tag: NOT YET AUTHORIZED
```

Newer authentic runtime evidence overrides source, PR, CI, and handoff descriptions.
