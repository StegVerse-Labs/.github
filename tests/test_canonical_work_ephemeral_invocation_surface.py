from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
# Retired under StegVerse-Labs/.github#3039 (H6b): GitHub Actions holds no
# runtime authority, so no workflow may be the execution surface for this path.
RETIRED = WORKFLOWS / "canonical-work-exact-ephemeral-invocation.yml"


def test_no_workflow_is_the_canonical_work_execution_surface():
    assert not RETIRED.exists()
    for path in sorted(WORKFLOWS.glob("*.y*ml")):
        text = path.read_text(encoding="utf-8")
        assert "invoke/canonical-work-coordination-" not in text, path.name
        assert "RT-CANONICAL-WORK-PORTABLE-DISPATCH-001" not in text, path.name
        assert "trigger_reusable_task.py" not in text, path.name
