# StegVerse Test Lanes Direct Run Mirror Handoff

Updated: 2026-08-22T07:03:00-05:00

## Goal

```text
goal_id: STEGVERSE-TEST-LANES-DIRECT-RUN-002
repository: StegVerse-Labs/.github
canonical_runner: scripts/run_test_lanes_direct.py
canonical_one_command: scripts/run_test_lanes_with_tvc_registration.py
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

## Fastest authorized execution

From the current `StegVerse-Labs/.github` checkout on the authorized TV/TVC Linux runtime:

```text
sudo python3 scripts/run_test_lanes_with_tvc_registration.py
```

The wrapper derives the canonical workload roots from the invoking operator's home. If all four protected TVC provider files already exist, registration is skipped. Otherwise it invokes the existing hidden-TTY registrar; secret values remain confined to `/dev/tty` -> inherited FD -> protected tmpfs provisioning. The same command then continues directly into the 9/9 run.

## Direct pipeline

```text
StegVerse-controlled runtime
-> current .github + TVC + Test Lanes + micro-node + stegfIn-governance source trees
-> reject hosted runtime and provider/GitHub secret-bearing environment
-> existing StegVerse loopback PRIMARY OR bounded canonical tools/run_sovereign_model.py test process
-> verify stegverse-reference-lm-v1 READY/private/credential-free/no-third-party
-> existing TVC vault-agent/broker OR bootstrap the existing services from already-provisioned protected provider files using run-local Unix sockets
-> live Provider Capsule readiness/materialization
-> exact READY nine-lane plan
-> canonical model selection
-> 1 StegVerse PRIMARY candidate + 4 TVC external candidates
-> exactly nine sanitized lane evidence records
-> deterministic comparison PASS
-> direct-run receipt
-> stop only bounded PRIMARY/vault processes started by this run
```

## Canonical models

```text
OpenAI    gpt-5.6-sol
Anthropic claude-opus-5
DeepSeek  deepseek-v4-pro
Kimi      kimi-k3
```

TVC independently revalidates every external model against the provider operation profile and local Provider Capsule before access.

## Launch boundaries

Required:
- current materialized source trees;
- all four provider refs genuinely resolvable through TV/TVC;
- private StegVerse PRIMARY, pre-existing or bounded-test-launched;
- exact READY 9/9 plan;
- writable local evidence path.

Not required:
- heartbeat state or ordinal;
- G18 claim/fence/status;
- WorkerCoordinator state;
- product activation proof;
- GitHub Actions runtime authority;
- third-party PRIMARY infrastructure.

## Credential boundary

The runner never receives or reads provider secret values. It rejects provider/GitHub secret environment variables. When TVC services are absent, it checks only protected provider-file existence/type/permissions/size and starts the existing descriptor-backed vault agent/broker. Missing files produce `TVC_PROVIDER_CREDENTIAL_REGISTRATION_REQUIRED`. No GitHub/chat/env migration is permitted.

## Source evidence

```text
25dd4c9b9babf51e41659cd1b30c91a6004b7811  direct runner initial
16a3ef8f8319f41a53d945f7c946a8773527908e  heartbeat-independence tests
a72efb8ad45c2855792611db27dafe8a31129094  bounded PRIMARY bootstrap
6af983b789b4046a7d6727f60cbb131eaf11eafb  bounded PRIMARY tests
efd399fba50e9eee040328ce443e88befc46f77a  TVC service bootstrap from provisioned files
f2aa1be64cdfc0863331a9f1dfad0e75e74370ac  vault bootstrap/registration boundary tests
2c3771ecce3675aa3b99951d9abd2d2330cc9011  registration-to-direct-run wrapper
68845068f3b97312f76781575206f39227ac4df7  one-command canonical workload defaults
2baec18a0807057ca4e7f9160010a73c8e33b2e2  wrapper boundary tests
2b70ef524257bb8c62b511620f4448679abb2031  terminal PASS accounting fix
dddd8a1a67a7738ccd9fe5aadbfa61ab925986c1  terminal PASS regression test
StegVerse-Labs/TVC@a87db85d221a506eba865ab8dade21ea783b8ade  model allowlists
StegVerse-Labs/TVC@493af17f2829433dc3ac85fafc8ae8fbdcdda3ce  canonical model selection
StegVerse-Labs/TVC@15b60cb6d893e3d9d86943d25a0b05adb12a8348 Provider Capsule direct-run handoff
StegVerse-Labs/TVC@e718abdacfce1a0c6d524464f549cbbb54af7724 credential task one-command continuation
GCAT-BCAT-Engine/workflows@19d5c43555792b2e60c803e1e4b976c57698285c Test Lanes direct-run handoff
```

## Validation/live distinction

The repository-wide validation workflow includes `scripts/**` and `tests/**` pushes and full unittest discovery, but no exact-head hosted result has yet been directly observed for the newest direct-run commits. Local clone validation from this chat environment was attempted and failed because that environment cannot resolve `github.com`; no local PASS is claimed.

Live state remains:

```text
one-command direct-run source: INSTALLED
bounded PRIMARY bootstrap: INSTALLED
bounded TVC service bootstrap: INSTALLED
canonical external model IDs: BOUND IN SOURCE
live four-provider TVC readiness: NOT DIRECTLY OBSERVED
live five-candidate execution: NOT OBSERVED
live nine evidence records: NOT OBSERVED
comparison PASS: NOT OBSERVED
```

## Completion

Terminal only when a direct-run receipt records `state=PASS`, observed `candidate_execution_count=5`, observed `lane_evidence_count=9`, `comparison_state=PASS`, StegVerse PRIMARY, TV/TVC credential authority, no credential material in evidence, and all external providers remain CONTROL_OR_FALLBACK_ONLY.

Source, plan, model selection, READY, assignment, handoff, heartbeat state, product activation or workflow success never substitute for that runtime result.
