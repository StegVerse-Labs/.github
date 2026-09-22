# Ecosystem Ingress + AI Boundaries — Mirror Handoff

Updated: 2026-09-21
Goal Task ID: `ECOSYSTEM-INGRESS-AI-BOUNDARIES-001`
COSV: `NOT ESTABLISHED`
Status: `ACTIVE`

PR #1678 merged as `069fe51538acfa4c29b0512262ea8ab2e155cae6` after exact-head validation. PR #1702 merged as `66a694372219f07b073be76d190a6f81934f6a25` after deterministic `34736129198`, organization-control `34736129204`, and Heartbeat `34736129210` passed.

The Goal remains componentized. Component 010 owns Task Registry AI/session actor gating; RTC-MANIFEST-001 owns manifested evaluator ingress; RT-EXTERNAL-ADAPTER-ESTABLISH-001 owns reusable external protocol translation; component 011 is now source-defined as the reusable **Ungoverned AI Defensive Envelope** at StegVerse-controlled consequence boundaries; canonical runtime measurement remains the evidence observer. The External AI Meeting Room is one component-011 instantiation and creates no new authority plane.

Current branch `ecosystem-ai-checkin-gate` adds `data/task-registry-general-checkin-caller-policy.json`. The general collision evaluator accepts only declared production surfaces `AI_SESSION_GATE` and `INTERNAL_CANONICAL_WORK_BOOTSTRAP`; missing or unknown surfaces fail closed outside pytest. The AI/session wrapper and Canonical Work bootstrap bind their expected surface. The evaluator records that caller-surface attestation is not proven.

This reconciliation defines source-level component-011 boundary semantics only. The external AI remains sovereign internally; StegVerse constrains only controlled consequence paths. Filesystem/network/tool scope, ambient-credential isolation, protected-authority unreachability, denied-consequence unreachability, governed egress separation, authentic runtime origin, LLM Adapter -> SDK exclusivity, evaluator SDK-only runtime ingress, and representative runtime evidence remain unproven.

Authority remains separated: Task Registry coordination only; WorkerCoordinator claim/fence; Interlock/InTr transition/admission; TV/TVC credentials/provider/release; KV/SKAP Vault user verification; Master Records custody/reconstruction; HeartBeat observability only; GitHub no runtime authority.

PR #2568 merged as `eeec8ba16a7e534dcd09143e359339ec90770667` after exact-head `Cross-Task Coordination Validation - Non-Authorizing`, `validate-deepseek-resident`, and `Validate KV AI Memory Resident Binding` all succeeded on head `de5730f2f4dfa0b2ea6c3665b71eca2644c23d42`. Component 011 is therefore source-defined and merged as the reusable Ungoverned AI Defensive Envelope; runtime enforcement remains unproven. Next: materialize/reuse the minimum existing runtime boundary needed to prove one representative capability-bounded admission and one denial with `consumed=false` and `consequence_reachable=false` where supported, without granting the external AI Task Registry, TV/TVC, Interlock/InTr, Master Records, Publisher, or host-runtime authority.


## Representative runtime boundary materialization — 2026-09-21

The minimum existing boundary selected for component 011 is TVC's already-existing SES stdio isolated-process provider, not the general `ProcessWorkerAdapter`. TVC PR #465 merged as `0b82b45de7d214fbdb2f24bc4027a6aeb31a7312` after exact-head SES Genesis, credential-model, Google Drive consent HTTP, and Goal-completion notification validations passed. The SES harness emits one bounded ALLOW computation and denied filesystem, network/import, and environment/import probes with `consumed=false` and `consequence_reachable=false`. It explicitly records `external_provider_observed=false`; this representative probe must not be promoted into external-provider-origin evidence.

The `.github` continuation reuses the existing sovereign WorkerCoordinator targeted independent-task path through `scripts/refresh_and_execute_resident_task.py --task-id ECOSYSTEM-INGRESS-AI-BOUNDARIES-001`. The trusted wrapper receives only `STEGVERSE_TVC_ROOT` and `PATH`; the untrusted candidate receives neither locator nor credentials. `ProcessWorkerAdapter` is used only for existing mutation fencing and is not claimed as a general-purpose candidate security sandbox. The worker requires local TVC source descended from `0b82b45de7d214fbdb2f24bc4027a6aeb31a7312`, a fresh WorkerCoordinator claim/fence, exact component-011 invariants, capability non-exposure, denied-consequence evidence, temporary-state destruction, and evidence-only egress.

No authorized remote execution device is currently connected to this ChatGPT session, so no authentic resident execution is claimed. Source/CI may validate the binding, but the remaining runtime predicates stay `NOT_PROVEN` until the sovereign resident retains `receipts/ai-defensive-envelope/ECOSYSTEM-INGRESS-AI-BOUNDARIES-001.json`.


## Resident dispatcher carriage repair — 2026-09-21

PR #2575 merged the representative component-011 resident probe as `e529982fc01029e6c7016c8e3f1f80413212da1e` after exact-head Cross-Task run `35688957026`, DeepSeek resident run `35688957020`, and KV AI Memory run `35688957129` all passed. Those checks prove source/CI compatibility only; they do not prove resident execution.

Post-merge carriage tracing exposed the first concrete existing-path defect: `dispatch_resident_execution_requests.py` uses an explicit selector table, and the new standing request had no registered consumer. The repair reuses that dispatcher by adding only `ungoverned_ai_defensive_envelope -> scripts/consume_ungoverned_ai_defensive_envelope_request.py`. The consumer validates the exact request, strips protected credential/provider variables, invokes only `refresh_and_execute_resident_task.py --task-id ECOSYSTEM-INGRESS-AI-BOUNDARIES-001`, records nonterminal attempts without consuming retryability, and becomes terminal only after the exact completed boundary transition is observed. The existing source-refresh allowlist is extended to materialize this consumer; no source transport, dispatcher, scheduler, runtime, credential path, authority plane, device, or second machine is added.

Runtime remains `NOT_PROVEN` until the standing resident path retains both the request-consumption receipt and `receipts/ai-defensive-envelope/ECOSYSTEM-INGRESS-AI-BOUNDARIES-001.json`.
