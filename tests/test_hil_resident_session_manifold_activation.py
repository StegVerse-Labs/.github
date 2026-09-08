from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSUMER = ROOT / "control" / "resident-execution-request.d" / "consume-hil-resident-session-manifold-activation.py"

spec = importlib.util.spec_from_file_location("hil_session_manifold", CONSUMER)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def _materialize_runtime(tmp_path: Path) -> Path:
    for rel in (
        module.REQUEST_REL,
        module.LINEAGE_REL,
    ):
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, target)
    for rel in (module.DISPATCHER_REL, module.WORKER_REL):
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# materialized\n", encoding="utf-8")
    return tmp_path


def test_hil_manifold_visits_all_declared_children_without_merging_authority(tmp_path: Path) -> None:
    runtime = _materialize_runtime(tmp_path)
    commands: list[list[str]] = []

    def fake_runner(command, **kwargs):
        commands.append(list(command))
        return subprocess.CompletedProcess(command, 0, stdout=json.dumps({"state": "ATTEMPT_RECORDED"}) + "\n", stderr="")

    receipt = module.consume(ROOT, runtime, runner=fake_runner)
    assert receipt["state"] == "MANIFOLD_VISIT_RECORDED"
    assert receipt["declared_child_count"] == 7
    assert receipt["visited_child_count"] == 7
    assert receipt["full_declared_set_visited"] is True
    assert receipt["aggregate_visit_satisfies_child_completion"] is False
    assert receipt["g18_completion_required_for_hil"] is False
    assert receipt["ecosystem_chat_completion_required_for_hil"] is False
    assert receipt["credential_authority"] == "TV/TVC"
    assert receipt["github_token_runtime_authority"] == "NONE"
    assert receipt["second_machine_required"] is False

    selector_commands = [cmd for cmd in commands if "--only-consumer" in cmd]
    selectors = [cmd[cmd.index("--only-consumer") + 1] for cmd in selector_commands]
    assert selectors == ["hil", "g18", "ecosystem_chat"]

    worker_commands = [cmd for cmd in commands if "--task-id" in cmd]
    worker_tasks = [cmd[cmd.index("--task-id") + 1] for cmd in worker_commands]
    assert worker_tasks == [
        "COSV-LIVE-PACKET-AUTOMATION-006",
        "SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001",
        "SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001",
        "SHWP-TV-TVC-RESIDENT-PROOF-001",
    ]


def test_hil_manifold_continues_after_child_failure(tmp_path: Path) -> None:
    runtime = _materialize_runtime(tmp_path)
    calls = 0

    def fake_runner(command, **kwargs):
        nonlocal calls
        calls += 1
        returncode = 1 if calls == 1 else 0
        return subprocess.CompletedProcess(command, returncode, stdout=json.dumps({"state": "ATTEMPT_RECORDED"}) + "\n", stderr="")

    receipt = module.consume(ROOT, runtime, runner=fake_runner)
    assert calls == 7
    assert receipt["visited_child_count"] == 7
    assert receipt["child_visit_failures_observed"] is True
    assert receipt["full_declared_set_visited"] is True


def test_umbrella_request_matches_lineage_and_supports_aggregate_gadi() -> None:
    lineage = json.loads((ROOT / "control/manifold-lineage.d/governed-multilane-manifold-activation-001.json").read_text())
    request = json.loads((ROOT / "control/resident-execution-request.d/governed-multilane-manifold-activation-001.json").read_text())
    node_ids = {row["task_id"] for row in lineage["nodes"]}
    assert node_ids == set(request["subordinate_task_ids"])
    assert "HIL-RESIDENT-SESSION-MANIFOLD-ACTIVATION-001" in node_ids
    assert request["execution_dispositions"]["GADI-001"] == "EXECUTE_INCOMPLETE_CANONICAL_CHILDREN_THROUGH_EXISTING_OWNERS"
    consumer_source = (ROOT / "scripts/consume_governed_multilane_manifold_activation_request.py").read_text()
    assert '"EXECUTE_INCOMPLETE_CANONICAL_CHILDREN_THROUGH_EXISTING_OWNERS"' in consumer_source
