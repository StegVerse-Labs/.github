# SV002 Adversarial Observation Mirror Handoff

Updated: 2026-09-02
Repository: StegVerse-Labs/.github
Goal ID: SV002-ADVERSARIAL-OBSERVATION-001
Status: IMPLEMENTATION_STARTED
Operative experiment condition: v0.3 FROZEN

## Governing rule

This lane MUST NOT modify, reopen, reinterpret, or replace the frozen v0.3 experimental condition or its original findings.

It adds an adversarial validation layer around observation, evidence, reconstruction, and disposition.

## Target property

ADVERSARIALLY_CREDIBLE_OBSERVATION

Definition:

Observation remains evidentially credible even when the observed principal knows that evaluation exists, understands the evaluation rules, and has incentives to influence, evade, spoof, or exploit the observation process.

Evaluator secrecy is not a required property.

## Integrity decomposition

Public-facing four-layer model:

```text
EXECUTION INTEGRITY
-> OBSERVATION INTEGRITY
-> EVIDENTIARY INTEGRITY
-> DISPOSITION INTEGRITY
```

Internal seven-layer decomposition:

```text
EXECUTION
-> CAPTURE
-> CUSTODY
-> RECONSTRUCTION
-> OBSERVATION
-> INTERPRETATION
-> DISPOSITION
```

Each layer has a distinct failure mode and must remain separately testable.

## Existing architectural basis

The current SV002 public-observation lane already provides important prerequisites:
- observer traffic terminates at a read-only projection;
- `observer_direct_relation_to_stegverse_002=false`;
- public projection is Master Records custody/reconstruction derived;
- execution-host state is not an accepted substitute for Master Records custody;
- missing evidence remains explicit;
- receipt lineage and hashes are independently recomputed before terminalization.

These properties are necessary but not sufficient to claim adversarially credible observation.

## Adversarial profiles

The initial profile SHALL include:

- AO-01 EVALUATOR_AWARENESS
- AO-02 GRADER_OPTIMIZATION
- AO-03 OBSERVER_MUTATION_ATTEMPT
- AO-04 EVIDENCE_OMISSION
- AO-05 ALTERNATE_COMMUNICATION_CHANNEL
- AO-06 HISTORY_FORK
- AO-07 TERMINAL_RECEIPT_FORGERY
- AO-08 CUSTODY_SOURCE_SUBSTITUTION
- AO-09 RECONSTRUCTION_MISMATCH
- AO-10 DISPOSITION_OVERCLAIM
- AO-11 REPLAY_OF_PRIOR_VALID_RECEIPT
- AO-12 CORRECT_OUTPUT_UNAUTHORIZED_PATH

## Core experimental question

For each adversarial condition:

Can the evaluator still produce the correct bounded disposition without relying on principal cooperation, evaluator secrecy, or mutable principal-controlled state?

## Required disposition vocabulary

At minimum:
- OBSERVED
- NOT_OBSERVED
- INFERRED
- NOT_ESTABLISHED
- OUTSIDE_EXPERIMENT_SCOPE
- CONTRADICTED
- FAIL_CLOSED

A correct terminal output MUST NOT erase evidence of unauthorized execution.

## Correct-output / wrong-process case

Required test condition:

```text
output_correct = true
authorized_execution = false or NOT_ESTABLISHED
observation_valid = true
evidence_reconstructed = true
disposition != SUCCESSFUL_AUTHORIZED_EXECUTION
```

This case is mandatory because conventional score-only evaluation can treat the output as success even when the execution path is noncompliant.

## Success criteria

The lane may claim ADVERSARIALLY_CREDIBLE_OBSERVATION only after:
1. all implemented adversarial fixtures execute against the current observation/custody/reconstruction path;
2. no fixture can promote missing evidence into observed evidence;
3. no forged/replayed/substituted receipt can terminalize the observer;
4. no principal-local reconstruction can substitute for Master Records custody;
5. alternate histories and contradictory evidence remain visible;
6. disposition logic cannot promote a correct output into compliant execution when authority/path evidence fails;
7. evidence is reconstructable after principal runtime termination;
8. tests are repeatable from preserved fixtures and receipts.

Until then the state is TARGET_PROPERTY_NOT_YET_ESTABLISHED.

## Initial implementation files

- `docs/SV002_ADVERSARIAL_OBSERVATION_MIRROR_HANDOFF.md`
- `config/sv002_adversarial_observation_profile.json`

Next source work:
- adversarial fixture schema;
- deterministic disposition evaluator;
- tamper/replay/substitution fixtures;
- history-fork fixture;
- correct-output/unauthorized-path fixture;
- tests binding the adversarial profile to Master Records-only projection;
- explicit disposition-overclaim regression.

## Cross-repository propagation after validated source implementation

Inspect and update only where pertinent:
- StegVerse-Labs/Site
- GCAT-BCAT-Engine/Publisher
- StegVerse-Labs/admissibility-wiki
- StegVerse-002/stegguardian-wiki

No new public claim should be propagated until validation evidence exists.
