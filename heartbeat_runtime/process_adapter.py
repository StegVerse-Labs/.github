from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any
import json
import os
import subprocess

from .engine_v2 import WorkerResponse


class ProcessWorkerAdapter:
    """Invoke a pre-admitted worker executable over a JSON stdin/stdout protocol.

    The executable is configured by the runtime owner, never by task-controlled
    input. The adapter itself grants no authority. It forwards the current task,
    handoff and heartbeat epoch and requires a typed worker response.
    """

    def __init__(
        self,
        command: list[str],
        *,
        cwd: str | Path,
        timeout_seconds: float = 30.0,
        env_allowlist: tuple[str, ...] = (),
    ) -> None:
        if not command or any(not isinstance(part, str) or not part for part in command):
            raise ValueError("command must be a non-empty list of strings")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0")
        self.command = tuple(command)
        self.cwd = Path(cwd).resolve()
        self.timeout_seconds = float(timeout_seconds)
        self.env_allowlist = tuple(env_allowlist)

    def _environment(self) -> dict[str, str]:
        env = {"PATH": os.environ.get("PATH", "")}
        for name in self.env_allowlist:
            if name in os.environ:
                env[name] = os.environ[name]
        return env

    def __call__(self, task: dict[str, Any], handoff: dict[str, Any], epoch: int) -> WorkerResponse:
        payload = {
            "schema": "stegverse.worker-invocation/v0.1",
            "heartbeat_epoch": epoch,
            "task": task,
            "handoff": handoff,
            "authority_effect": "none_adapter_only",
        }
        completed = subprocess.run(
            self.command,
            cwd=self.cwd,
            input=json.dumps(payload, sort_keys=True) + "\n",
            text=True,
            capture_output=True,
            timeout=self.timeout_seconds,
            check=False,
            env=self._environment(),
        )
        if completed.returncode != 0:
            stderr = completed.stderr.strip()[-2000:]
            raise RuntimeError(f"worker process exited {completed.returncode}: {stderr}")
        try:
            response = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError("worker process did not emit one valid JSON response") from exc
        if response.get("schema") != "stegverse.worker-response/v0.1":
            raise RuntimeError("unsupported worker response schema")

        state = str(response.get("state", ""))
        transition_id = str(response.get("transition_id", ""))
        transition_sequence = response.get("transition_sequence")
        if not state or not transition_id or not isinstance(transition_sequence, int) or transition_sequence < 0:
            raise RuntimeError("worker response missing state/transition_id/transition_sequence")

        evidence_refs = response.get("evidence_refs", [])
        if not isinstance(evidence_refs, list) or any(not isinstance(ref, str) for ref in evidence_refs):
            raise RuntimeError("worker response evidence_refs must be strings")
        cost = response.get("cost_observation")
        if cost is not None and not isinstance(cost, dict):
            raise RuntimeError("worker response cost_observation must be an object")

        return WorkerResponse(
            state=state,
            transition_id=transition_id,
            transition_sequence=transition_sequence,
            expected_next_transition=response.get("expected_next_transition"),
            expected_next_earliest_epoch=response.get("expected_next_earliest_epoch"),
            expected_next_latest_epoch=response.get("expected_next_latest_epoch"),
            checkpoint_ref=response.get("checkpoint_ref"),
            evidence_refs=tuple(evidence_refs),
            cost_observation=cost,
        )

    def describe(self) -> dict[str, Any]:
        return {
            "adapter_type": "process_json_v0.1",
            "command": list(self.command),
            "cwd": str(self.cwd),
            "timeout_seconds": self.timeout_seconds,
            "env_allowlist": list(self.env_allowlist),
            "task_controls_command": False,
            "adapter_grants_authority": False,
        }
