from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "canonical-work-exact-ephemeral-invocation.yml"


def test_exact_ephemeral_invocation_surface_is_compute_only():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert '"invoke/canonical-work-coordination-*"' in text
    assert "permissions:\n  contents: read" in text
    assert "RT-CANONICAL-WORK-PORTABLE-DISPATCH-001" in text
    assert "--task-id STEGVERSE-CANONICAL-WORK-COORDINATION-001" in text
    assert "--cosv-task-vector 10100000100000" in text
    assert '"only_consumer\\":\\"canonical_work_coordination' in text
    assert '"goal_task_id\\":\\"STEGVERSE-CANONICAL-WORK-COORDINATION-001' in text
    assert "secrets." not in text
    assert "GITHUB_TOKEN:" not in text
    assert "write-all" not in text
    assert "contents: write" not in text
