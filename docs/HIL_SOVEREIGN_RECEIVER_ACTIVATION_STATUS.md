# HIL Sovereign Receiver Activation Status

Canonical source of truth: `docs/HIL_SOVEREIGN_RECEIVER_ACTIVATION_MIRROR_HANDOFF.md`.

This status surface records the current implementation boundary after merge of the sovereign receiver bridge and installation of the resident worker binding.

```text
LLM-adapter receiver source: MERGED
sovereign carrier bridge: MERGED
resident worker implementation: INSTALLED_MAIN
worker registry fragment: INSTALLED_MAIN
process adapter fragment: INSTALLED_MAIN
executable handoff: HANDOFF_READY
participant/developer/iMachine prerequisite: NONE
GitHub-token runtime authority: NONE
credential authority: TV/TVC
local carrier READY observation: NOT YET PRESERVED
public HTTPS rendezvous: NOT YET PROVEN
Site HIL-RECEIVER-RECEIPT-v2: NOT YET PRESERVED
post-restart exact-byte proof: NOT YET PRESERVED
TVC lifecycle handoff: NOT YET PROVEN
```

Repository implementation and worker registration do not imply product activation. The next legitimate state transition is execution by the admitted resident worker, followed by the public HTTPS/browser/restart/TVC evidence chain.
