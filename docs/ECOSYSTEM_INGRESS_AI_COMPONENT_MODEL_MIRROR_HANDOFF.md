# Ecosystem Ingress AI Component Model — Mirror Handoff

Updated: 2026-09-21
Goal Task ID: `ECOSYSTEM-INGRESS-AI-BOUNDARIES-001`
COSV: `NOT ESTABLISHED`
Parent handoff: `docs/ECOSYSTEM_INGRESS_AI_BOUNDARIES_MIRROR_HANDOFF.md`

This projection records the Reusable Task Component Model composition for the existing Goal Task. It does not replace the Goal Task handoff or create a new Goal Task.

Selected capabilities:

- `RTC-TASK-REGISTRY-SESSION-ACTOR-GATE-010`: reusable, non-authorizing Task Registry session actor classification and lifecycle binding.
- `RTC-MANIFEST-001`: existing canonical SDK manifest component for external evaluator submissions.
- `RT-EXTERNAL-ADAPTER-ESTABLISH-001`: existing reusable External Adapter Establishment capability, parameterized for LLM Adapter -> canonical SDK delegation.
- `RTC-NONCHATGPT-AI-DECISION-SANDBOX-011`: reusable **Ungoverned AI Defensive Envelope** capability. It governs StegVerse-controlled consequence boundaries rather than hidden model state; requires explicit filesystem/network/tool capability scope, ambient-credential isolation, consequence mediation, denied-consequence unreachability evidence where supported, retained boundary evidence, and governed egress separation. External AI internal reasoning remains sovereign. The External AI Meeting Room is one concrete instantiation, not a new authority primitive. Runtime enforcement remains unproven.
- `GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001`: existing authentic runtime observation capability; source/CI cannot satisfy runtime predicates.

Conditional capabilities are selected only when a representative test actually requires them: `RTC-INTERLOCK-INTR-TRANSPORT-008`, `RTC-EVIDENCE-CUSTODY-004`, and TV/TVC credential/session handling.

Not forced into this goal: Publisher, mandatory SDK return assembly, mandatory StegVerse final egress, far-side final transition, or terminal cleanup/entropy recovery.

Authority remains external to reusable components: Task Registry coordination only; WorkerCoordinator claim/fence; Interlock/InTr governed transitions; TV/TVC credential/provider/release; KV/SKAP Vault sole user verification; Master Records observed-reality custody/reconstruction; HeartBeat observability only; GitHub runtime authority none.

The prior PR #1624 is historical provenance for the task-specific session-return/session-close implementation. Its reusable logic is being reconstituted on current main under component 010; do not merge the stale branch after the replacement is validated.

Source-level contract reconciliation now defines component 011's defensive-envelope semantics. No runtime enforcement, sandbox isolation, credential-unreachability, denied-consequence proof, or governed-egress execution is claimed by this projection.

PR #2568 merged as `eeec8ba16a7e534dcd09143e359339ec90770667`; exact-head source validation passed on `de5730f2f4dfa0b2ea6c3665b71eca2644c23d42`. This establishes the component-011 defensive-envelope contract in canonical source only. Runtime isolation/enforcement evidence remains required separately.
