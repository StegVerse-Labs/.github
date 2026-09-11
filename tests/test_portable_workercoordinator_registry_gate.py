from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "workercoordinator" / "portable_checkout.js"


def text() -> str:
    return MODULE.read_text(encoding="utf-8")


def test_portable_checkout_requires_registry_disposition_before_state_read():
    source = text()
    checkout = source.index("function checkout(pkg, store, registryDisposition)")
    validate = source.index("validateRegistryDisposition(registryDisposition, pkg.task.task_id);", checkout)
    state_read = source.index("store.read()", checkout)
    assert validate < state_read


def test_only_continue_can_reach_claim_issuance():
    source = text()
    assert 'disposition.disposition !== "CONTINUE"' in source
    assert 'fail("Task Registry disposition prohibits checkout: "' in source
    assert 'disposition.authority_effect !== "NONE"' in source
    assert 'disposition.task_id !== taskId' in source


def test_claim_receipt_binds_exact_registry_disposition_hash():
    source = text()
    assert "sha256Hex(registryDisposition)" in source
    assert 'registry_checkin_disposition: "CONTINUE"' in source
    assert 'registry_checkin_sha256: "sha256:" + registryDispositionHash' in source
    assert 'registry_checkin_authority_effect: "NONE"' in source
    assert "last_registry_checkin_sha256: receiptBody.registry_checkin_sha256" in source


def test_registry_gate_does_not_replace_workercoordinator_authority():
    source = text()
    assert 'global_workercoordinator_authority: true' in source
    assert 'authority_effect: "CANONICAL_WORKERCOORDINATOR_CLAIM_FENCE"' in source
    assert 'REGISTRY_DISPOSITION_SCHEMA = "stegverse.task-registry-checkin-disposition/v1"' in source
