import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_device_replaceability_invariant_validator_passes():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/validate_device_replaceability_invariant.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    assert "DEVICE_REPLACEABILITY_INVARIANT=PASS" in result.stdout
    assert "SPECIFIC_DEVICE_CONTINUITY_AUTHORITY=NONE" in result.stdout
    assert "PROVIDER_NEUTRAL_KV_DEVICE_INDEPENDENCE=PASS" in result.stdout
    assert "LEGACY_CURRENT_IPHONE_LABELS=NORMATIVE_FALSE" in result.stdout
