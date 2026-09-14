#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

policy = json.loads((ROOT / "control/device-replaceability-invariant.json").read_text())
registry = json.loads((ROOT / "control/canonical-policy-context-registry.json").read_text())
model = json.loads((ROOT / "data/reusable-task-component-model.json").read_text())
global_task = json.loads((ROOT / "data/canonical-task-records/GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001.json").read_text())
handoff = (ROOT / "docs/GLOBAL_RUNTIME_EVIDENCE_CLOSURE_MIRROR_HANDOFF.md").read_text()
ingress = (ROOT / "docs/CANONICAL_INVARIANT_INGRESS_LOCK_MIRROR_HANDOFF.md").read_text()

assert policy["status"] == "ACTIVE_CANONICAL_INVARIANT"
assert policy["invariant"]["specific_device_identity_may_be_continuity_root"] is False
assert policy["invariant"]["specific_device_identity_may_be_runtime_completion_prerequisite"] is False
assert policy["invariant"]["specific_os_or_browser_may_be_continuity_prerequisite"] is False
assert policy["invariant"]["provider_storage_must_be_accessed_through_provider_neutral_kv_contract"] is True
assert policy["invariant"]["replacement_device_must_be_able_to_reconstruct_from_canonical_kv_and_receipts"] is True

required = {x["ref"] for x in registry["required_global_sources"] if x.get("required")}
assert "control/device-replaceability-invariant.json" in required
assert "docs/DEVICE_REPLACEABILITY_INVARIANT_MIRROR_HANDOFF.md" in required

inv = model["composition_invariants"]
assert inv["stegos_device_role"] == "INTERCHANGEABLE_ACCESS_AND_TRANSPORT_ENDPOINT"
assert inv["specific_device_identity_continuity_authority"] == "NONE"
assert inv["specific_device_identity_runtime_completion_authority"] == "NONE"
assert inv["kv_provider_access"] == "PROVIDER_NEUTRAL_AND_DEVICE_INDEPENDENT"

assert global_task["runtime_requirements"]["specific_user_device_required"] is False
assert global_task["runtime_requirements"]["specific_os_required"] is False
assert global_task["runtime_requirements"]["specific_browser_required"] is False
assert global_task["execution_substrate_resolution"]["device_replacement_allowed_at_any_point"] is True
assert global_task["execution_substrate_resolution"]["same_physical_device_continuity_required"] is False
assert global_task["runtime_resolution"]["current_first_unresolved_predicate"] == "TESTFLIGHT_AUTHORIZED_USER_DEVICE_RUNTIME_OBSERVED"
assert global_task["legacy_label_semantics"] == "NON_NORMATIVE_HISTORICAL_OR_IMPLEMENTATION_LABEL_ONLY"

prohibited_current_guidance = [
    "The next evidence must come from the established current iPhone",
    "On the established current iPhone",
    "do not switch devices",
    "ACTIVE_CURRENT_IPHONE_EXECUTION_REQUIRED",
]
for text in prohibited_current_guidance:
    assert text not in handoff, text

for required_text in [
    "Every user-operated device is an interchangeable access/transport endpoint",
    "NON_NORMATIVE_LEGACY_LABELS_ONLY",
    "provider-neutral MyKV/KV reconstruction",
    "DEVICE_BOUND_INTERPRETATION_INVALID",
]:
    assert required_text in handoff or required_text in ingress, required_text

print("DEVICE_REPLACEABILITY_INVARIANT=PASS")
print("SPECIFIC_DEVICE_CONTINUITY_AUTHORITY=NONE")
print("PROVIDER_NEUTRAL_KV_DEVICE_INDEPENDENCE=PASS")
print("LEGACY_CURRENT_IPHONE_LABELS=NORMATIVE_FALSE")
