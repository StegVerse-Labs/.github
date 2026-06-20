# StegVerse-Labs Validator Registry

## Purpose

This registry records known repository validators and the gaps that remain before the organization can aggregate repository completion reliably.

It is an organization-level index only. Repository-local validators remain authoritative for repository-specific completion.

## Current Assessment Goal

```text
Continue building without manual actions needed through completion OR until task handoff and task completion is capable of being handled by the ecosystem's own management.
```

## Registry Status

```text
registry_state: repo_validator_refresh_installed
source_repository: StegVerse-Labs/.github
completion_class: self_managed_registry_completion
manual_action_requirement: none_for_registry_continuation
```

## Known Validators

| Repository | Validator | Status | Notes |
|---|---|---:|---|
| StegVerse-Labs/.github | scripts/check_org_operational_observer.py | present | validates org observer standard |
| StegVerse-Labs/.github | scripts/check_org_repository_inventory.py | present | validates org inventory structure |
| StegVerse-Labs/.github | scripts/check_org_completion_dashboard.py | present | validates org dashboard structure |
| StegVerse-Labs/.github | scripts/check_required_terms.py + checks/org_mirror_handoff_terms.txt | present | validates org mirror handoff terms |
| StegVerse-Labs/TV | scripts/check_tv_operational_handoff.py | present | validates TV operational handoff boundaries |
| StegVerse-Labs/TV | scripts/check_tv_operational_status.py | present | validates TV operational status boundary |
| StegVerse-Labs/TV | scripts/check_tv_operational_receipt.py | present | validates TV receipt promotion path |
| StegVerse-Labs/TV | scripts/selftest_tv_operational_paths.py | present | validates TV proof and observer wiring |
| StegVerse-Labs/StegCore | scripts/check_continuity_admissibility_mapping.py | present | validates continuity-to-admissibility mapping |
| StegVerse-Labs/stegfin-governance | scripts/check_stegfin_governance_handoff.py | present | validates StegFin governance docs and handoff |
| StegVerse-Labs/crypto-bot | scripts/check_crypto_bot_handoff.py | present | validates crypto-bot docs and handoff |

## Known Remaining Validator Installs

```text
No required validator installs remain for the current known handoff/docs/validator goal.
Optional future work: cross-repository aggregation workflow that calls repository-local validators across repos.
```

## Promotion Rule

```text
Validator listed as present != repository completion.
Repository completion requires repository-local acceptance criteria, current evidence, and any observer requirements defined by the repository handoff.
```

## Archive Readiness

```text
thread_archive_ready: true
archive_reason: the organization now has a repository-local validator registry for known validation surfaces and missing validator installs. Future sessions can continue validator installation without reconstructing registry state from chat.
```
