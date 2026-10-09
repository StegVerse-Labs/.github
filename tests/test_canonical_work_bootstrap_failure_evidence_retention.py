from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "control" / "resident-execution-request.d" / "consume-canonical-work-coordination-bootstrap.legacy.py"


def test_bootstrap_consumer_retains_bounded_child_output():
    text = LEGACY.read_text(encoding="utf-8")
    assert '"stdout_tail": completed.stdout[-4000:]' in text
    assert '"stderr_tail": completed.stderr[-4000:]' in text
