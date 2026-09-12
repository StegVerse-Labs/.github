import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_task_registration_substrate_resolution.py"
spec = importlib.util.spec_from_file_location("substrate_gate", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def review(substrate_id, disposition, limitation="NONE", evidence_refs=None):
    return {
        "substrate_id": substrate_id,
        "disposition": disposition,
        "limitation_class": limitation,
        "evidence_refs": evidence_refs or [],
    }


def record_with_resolution(reviews, selected, external=False):
    return {
        "task_id": "TEST-RUNTIME-TASK-001",
        "runtime_requirements": {"capabilities": ["bounded_execution"]},
        "execution_substrate_resolution": {
            "schema": "stegverse.execution-substrate-resolution/v1",
            "review_order": list(module.REVIEW_ORDER),
            "reviews": reviews,
            "selected_substrate_id": selected,
            "external_device_required": external,
            "second_user_operated_device_allowed": False,
            "authority_effect": "NONE",
        },
    }


class TaskRegistrationSubstrateResolutionTests(unittest.TestCase):
    def test_same_device_stegbrowser_can_be_selected_first(self):
        reviews = [
            review(module.REVIEW_ORDER[0], "SELECTED"),
            review(module.REVIEW_ORDER[1], "SUITABLE"),
            review(module.REVIEW_ORDER[2], "SUITABLE"),
            review(module.REVIEW_ORDER[3], "SUITABLE"),
            review(module.REVIEW_ORDER[4], "SUITABLE"),
            review(module.REVIEW_ORDER[5], "NOT_APPLICABLE", "NOT_APPLICABLE"),
        ]
        module.validate_resolution(record_with_resolution(reviews, module.REVIEW_ORDER[0]))

    def test_runtime_task_without_resolution_fails_registration(self):
        with self.assertRaisesRegex(ValueError, "requires execution_substrate_resolution"):
            module.validate_resolution({"task_id": "X", "runtime_requirements": {"capabilities": []}})

    def test_reachability_gap_cannot_be_called_unsuitable(self):
        reviews = [
            review(module.REVIEW_ORDER[0], "UNSUITABLE", "EVIDENCE_REACHABILITY", ["connector:no-device"]),
            *[review(sid, "NOT_APPLICABLE", "NOT_APPLICABLE") for sid in module.REVIEW_ORDER[1:]],
        ]
        with self.assertRaisesRegex(ValueError, "evidence/reachability gap may not be promoted"):
            module.validate_resolution(record_with_resolution(reviews, None))

    def test_external_device_requires_exhaustion_of_same_device_options(self):
        reviews = [
            review(module.REVIEW_ORDER[0], "PENDING_EVIDENCE", "EVIDENCE_REACHABILITY"),
            review(module.REVIEW_ORDER[1], "UNSUITABLE", "PLATFORM", ["evidence:platform"]),
            review(module.REVIEW_ORDER[2], "UNSUITABLE", "ARCHITECTURAL", ["evidence:architecture"]),
            review(module.REVIEW_ORDER[3], "NOT_APPLICABLE", "NOT_APPLICABLE"),
            review(module.REVIEW_ORDER[4], "UNSUITABLE", "AUTHORITY", ["evidence:authority"]),
            review(module.REVIEW_ORDER[5], "SELECTED"),
        ]
        with self.assertRaisesRegex(ValueError, "external device cannot be required"):
            module.validate_resolution(record_with_resolution(reviews, module.REVIEW_ORDER[5], external=True))

    def test_external_device_allowed_only_after_evidenced_exhaustion(self):
        reviews = [
            review(module.REVIEW_ORDER[0], "UNSUITABLE", "ARCHITECTURAL", ["evidence:a"]),
            review(module.REVIEW_ORDER[1], "UNSUITABLE", "PLATFORM", ["evidence:b"]),
            review(module.REVIEW_ORDER[2], "UNSUITABLE", "AUTHORITY", ["evidence:c"]),
            review(module.REVIEW_ORDER[3], "NOT_APPLICABLE", "NOT_APPLICABLE"),
            review(module.REVIEW_ORDER[4], "UNSUITABLE", "PLATFORM", ["evidence:d"]),
            review(module.REVIEW_ORDER[5], "SELECTED"),
        ]
        module.validate_resolution(record_with_resolution(reviews, module.REVIEW_ORDER[5], external=True))

    def test_non_runtime_task_is_grandfather_compatible(self):
        module.validate_resolution({"task_id": "DOCS-ONLY-001"})


if __name__ == "__main__":
    unittest.main()
