# HIL Universal InTr Sovereign Ingress Profile Mirror Handoff

Updated: 2026-08-29
Repository: `StegVerse-Labs/.github`
Parent HIL activation owner: #246

```text
goal_id: SHWP-HIL-INTR-INGRESS-PROFILE
state: IMPLEMENTATION_IN_PROGRESS
credential_authority: TV/TVC
github_token_runtime_authority: NONE
authority_effect: NONE_DISCOVERY_EVIDENCE_ONLY
runtime_profile_observed: false
public_https_rendezvous_observed: false
```

## Purpose

Add the missing machine-readable profile/readiness surface required for an authentic sovereign HIL materialization ingress runtime to earn downstream Site discovery. Source/CI cannot project a runtime URL.

The profile is non-authorizing and must expose only the ingress contract: active listener state, materialization path, supported transport origins, credential requirements, and authority boundaries. It must never claim HIL execution, receiver readiness/custody, TVC lifecycle admission, G18 completion, or activation.

A real runtime observation of this profile over an independently identified sovereign HTTPS rendezvous is required before Site may replace `ingress_url=null`.
