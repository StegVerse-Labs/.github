#!/usr/bin/env python3
"""Static validator for the StegVerse external-AI state-transition admission contract.

This validates source contracts only. It does not claim live Interlock/InTr, SKAP,
TVC, Master Records, or external-AI runtime activation.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "data" / "external-ai-transition-policy.json"
DEV = ROOT / "data" / "developer-capability-packages.json"
SCHEMA = ROOT / "schemas" / "external-ai-transition-relationship.schema.json"
HANDOFF = ROOT / "docs" / "EXTERNAL_AI_STATE_TRANSITION_ADMISSION_MIRROR_HANDOFF.md"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL_CLOSED: {message}")


def main() -> int:
    policy = load_json(POLICY)
    dev = load_json(DEV)
    relationship_schema = load_json(SCHEMA)
    handoff = HANDOFF.read_text(encoding="utf-8")

    require(
        policy.get("invariant")
        == "EXTERNAL_CONNECTIVITY_GOVERNED_BY_ADMISSIBLE_STATE_TRANSITION_CAPABILITY_NOT_API_ACCESS",
        "state-transition capability invariant missing",
    )
    require(policy.get("production_external_ai_execution_principal") is False, "production external AI must not be an execution principal")
    require(policy.get("api_route_possession_grants_authority") is False, "API route possession must grant no authority")
    require(policy.get("endpoint_possession_grants_authority") is False, "endpoint possession must grant no authority")

    ingress = policy.get("ingress", {})
    require(ingress.get("interlock_required") is True, "ingress Interlock must be required")
    require(ingress.get("intr_required") is True, "ingress InTr must be required")
    require(ingress.get("successful_ingress_effect") == "ADMITTED_INGRESS_TRANSITION_ONLY", "ingress effect must be boundary-transition only")
    require(ingress.get("post_ingress_capability_source") == "SKAP_VAULT_RELATIONSHIP_PACKAGE", "SKAP relationship must be post-ingress capability source")
    require(set(ingress.get("allowed_recipients", [])) == {"STEGVERSE_ASSISTANT", "STEGVERSE_AI_ENTITY"}, "production external AI recipients must be StegVerse AI boundary only")

    production = policy.get("production", {})
    require(production.get("direct_mutation_by_external_ai") is False, "production external AI direct mutation must be denied")
    require(production.get("internal_direct_targets") == [], "production external AI must have no direct internal targets")
    require(production.get("consequential_work_origin") == "GOVERNED_STEGVERSE_PRINCIPAL_ONLY", "consequential work must originate from governed StegVerse principal")
    require(production.get("egress_interlock_required") is True, "egress Interlock must be required")
    require(production.get("egress_intr_required") is True, "egress InTr must be required")

    require(policy.get("interaction_class_admission") == "MUST_MATCH_SKAP_RELATIONSHIP_ALLOWANCE", "interaction classes must be controlled by SKAP relationship")

    standard = dev.get("packages", {}).get("DEVELOPER_PACKAGE_STANDARD")
    require(isinstance(standard, dict), "DEVELOPER_PACKAGE_STANDARD missing")
    require(standard.get("environment") == "DEVELOPMENT", "standard developer package must be development-only")
    require(standard.get("implicit_promotion_to_production") is False, "developer package must not promote to production")
    require(standard.get("extension_required_for_any_unlisted_capability") is True, "unlisted developer capability must require extension")

    upgrade = dev.get("capability_extension_application", {})
    require(upgrade.get("admission_effect") == "AMEND_OR_REPLACE_SKAP_RELATIONSHIP_PACKAGE_ONLY_AFTER_APPROVAL", "developer upgrade must materialize through approved SKAP relationship change")
    require(upgrade.get("rejection_effect") == "PRIOR_RELATIONSHIP_PACKAGE_UNCHANGED", "rejected developer upgrade must not alter prior package")

    authority_props = relationship_schema.get("properties", {}).get("authority_model", {}).get("properties", {})
    require(authority_props.get("api_access_is_authority", {}).get("const") is False, "relationship schema must deny API-as-authority")
    require(authority_props.get("post_ingress_capability_source", {}).get("const") == "SKAP_VAULT_RELATIONSHIP_PACKAGE", "relationship schema must bind SKAP capability source")
    require(authority_props.get("production_external_ai_execution_principal", {}).get("const") is False, "relationship schema must deny production external-AI execution-principal status")

    required_handoff_phrases = [
        "admissible state-transition capability",
        "Successful ingress grants only the admitted ingress transition",
        "DEVELOPER_PACKAGE_STANDARD",
        "No direct production/external-AI operational API",
        "Existing user-data disclosure and Master Records reconstruction invariants remain controlling",
    ]
    for phrase in required_handoff_phrases:
        require(phrase in handoff, f"handoff missing required statement: {phrase}")

    print("PASS: external AI state-transition source contract is internally consistent")
    print("NONCLAIM: live runtime enforcement not proven by this validator")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
