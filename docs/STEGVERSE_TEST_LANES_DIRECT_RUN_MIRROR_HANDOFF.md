# StegVerse Test Lanes Direct Run Mirror Handoff

Updated: 2026-08-22T07:03:00-05:00

## Goal

```text
goal_id: STEGVERSE-TEST-LANES-DIRECT-RUN-002
repository: StegVerse-Labs/.github
canonical_runner: scripts/run_test_lanes_direct.py
portable_test_owner: GCAT-BCAT-Engine/workflows/experiments/stegverse-test-lanes
provider_execution_owner: StegVerse-Labs/TVC
primary_provider: stegverse_local
third_party_role: CONTROL_OR_FALLBACK_ONLY
credential_authority: TV/TVC
heartbeat_required: false
g18_required: false
worker_coordinator_required: false
```

The canonical nine-lane experiment is independently executable. Heartbeat/G18/WorkerCoordinator may automate or observe it, but are not execution prerequisites.

## Direct pipeline

```text
StegVerse-controlled runtime
-> materialized TVC + Test Lanes + micro-node source trees
-> reject hosted runtime and secret-bearing environment
-> use existing live StegVerse loopback runtime OR start bounded canonical tools/run_sovereign_model.py test process
-> verify stegverse-reference-lm-v1 READY/private/credential-free/no-third-party
-> verify TVC vault-agent socket
-> verify TVC vault-broker socket
-> live Provider Capsule readiness/materialization
-> exact READY nine-lane plan
-> canonical model selection
-> one StegVerse PRIMARY candidate
-> OpenAI candidate
-> Anthropic candidate
-> DeepSeek candidate
-> Kimi candidate
-> exactly nine sanitized lane evidence records
-> deterministic comparison PASS
-> direct-run receipt
-> stop only the bounded primary process started by this run
```

## Canonical model selection

Owned/enforced by `StegVerse-Labs/TVC:config/test_lanes_model_selection.sv-cost-nine-lane.v1.json`:

```text
OpenAI:    gpt-5.6-sol
Anthropic: claude-opus-5
DeepSeek:  deepseek-v4-pro
Kimi:      kimi-k3
```

TVC independently revalidates each external model against its provider operation profile and local Provider Capsule before provider access.

## Launch boundaries

Required:

- materialized current source trees;
- TVC vault-agent and vault-broker Unix sockets;
- all four provider refs live READY through TV/TVC;
- loopback-only StegVerse PRIMARY, pre-existing or bounded-test-launched;
- exact 9/9 READY plan;
- writable local run/evidence path.

Not required:

- heartbeat carrier state;
- HB30/HB31 or any heartbeat ordinal;
- G18 state/claim/fence;
- WorkerCoordinator runtime state;
- product activation proof;
- GitHub Actions runtime authority;
- third-party infrastructure as PRIMARY.

## Credential boundary

Provider secret material may exist only inside the existing TV/TVC vault/provisioner/broker path. The direct runner refuses provider or GitHub secret environment variables and receives no raw credentials. Credential registration, if still required, remains the existing hidden-TTY TV/TVC boundary in `TVC-PROVIDER-CREDENTIAL-BINDING-011`.

## Source evidence

```text
25dd4c9b9babf51e41659cd1b30c91a6004b7811  heartbeat-independent direct runner initial
16a3ef8f8319f41a53d945f7c946a8773527908e  direct-run dependency regression tests
 a72efb8ad45c2855792611db27dafe8a31129094  bounded canonical StegVerse PRIMARY auto-start
6af983b789b4046a7d6727f60cbb131eaf11eafb  bounded-primary direct-run tests
StegVerse-Labs/TVC@a87db85d221a506eba865ab8dade21ea783b8ade  exact Anthropic/Kimi model allowlists
StegVerse-Labs/TVC@493af17f2829433dc3ac85fafc8ae8fbdcdda3ce  canonical four-provider model selection
StegVerse-Labs/TVC@d5fff7548b76a987bdd8edcf130bc434eb6a804b  TVC task decoupled from heartbeat
GCAT-BCAT-Engine/workflows@ef084633e922ffbdc5323465bf8f6ac5858b4bc0  portable task decoupled from heartbeat
```

## Current live state

```text
direct runner source: INSTALLED
canonical external model IDs: BOUND
bounded StegVerse test-primary bootstrap: INSTALLED
TVC live four-provider credential readiness: NOT DIRECTLY OBSERVED
TVC vault sockets on an executing StegVerse node: NOT DIRECTLY OBSERVED
canonical direct five-candidate execution: NOT YET OBSERVED
nine evidence records: NOT YET OBSERVED
comparison PASS: NOT YET OBSERVED
```

## Completion

Terminal only when one direct-run receipt records PASS, `candidate_execution_count=5`, the evidence bundle contains exactly 9 lanes, comparison state is PASS, StegVerse is PRIMARY, credential authority is TV/TVC, credential material is absent from evidence, and all four external providers remain CONTROL_OR_FALLBACK_ONLY.

Source, plan, model selection, READY, assignment, handoff, heartbeat state, product activation, or workflow success never substitute for that runtime result.
