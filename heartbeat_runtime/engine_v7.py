from __future__ import annotations

from typing import Any
import hashlib
import json

from .engine_v6 import HeartbeatRuntime as HeartbeatRuntimeV6, WorkerResponse


class HeartbeatRuntime(HeartbeatRuntimeV6):
    """Single-heartbeat runtime with policy continuity and canonical checkpoints.

    The control plane, not the worker, owns the canonical checkpoint envelope.
    A live worker may not continue under a changed policy version unless a
    separately admitted policy-rebind record binds the same task/claim/fence to
    the new HANDOFF hash. The heartbeat transports and evaluates the evidence;
    it never grants the rebind.
    """

    def _checkpoint_hash(self, checkpoint: dict[str, Any]) -> str:
        value = dict(checkpoint)
        value.pop("checkpoint_sha256", None)
        payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _apply_policy_rebind(
        self,
        task: dict[str, Any],
        handoff: dict[str, Any],
        epoch: int,
        events: list[dict[str, Any]],
    ) -> bool:
        current_policy = str((handoff.get("authority") or {}).get("policy_version") or "")
        authorized_policy = task.get("authorized_policy_version")
        if not authorized_policy:
            # Initial checkout binds the policy already present in the admitted
            # HANDOFF. This is not a heartbeat-created authorization.
            task["authorized_policy_version"] = current_policy
            return True
        if authorized_policy == current_policy:
            return True

        ref = task.get("policy_rebind_ref")
        if not isinstance(ref, str) or not ref:
            return False
        path = self.root / ref
        if not path.exists():
            self._event(events, epoch, "policy_rebind_rejected", task_id=task.get("task_id"), reason="POLICY_REBIND_RECORD_MISSING", policy_rebind_ref=ref)
            return False
        try:
            record = self._load(path)
        except Exception:
            self._event(events, epoch, "policy_rebind_rejected", task_id=task.get("task_id"), reason="POLICY_REBIND_RECORD_INVALID", policy_rebind_ref=ref)
            return False

        timing = task.get("heartbeat_timing") or {}
        authority = handoff.get("authority") or {}
        valid = all([
            record.get("schema") == "stegverse.worker-policy-rebind/v0.1",
            record.get("status") == "ADMITTED",
            record.get("heartbeat_grants_rebind") is False,
            record.get("task_id") == task.get("task_id"),
            record.get("claim_id") == task.get("claim_id"),
            record.get("fencing_token") == timing.get("fencing_token"),
            record.get("old_policy_version") == authorized_policy,
            record.get("new_policy_version") == current_policy,
            record.get("handoff_sha256") == self._handoff_hash(handoff),
            record.get("authority_source") == authority.get("authority_source"),
            isinstance(record.get("evidence_refs"), list) and bool(record.get("evidence_refs")),
        ])
        if not valid:
            self._event(events, epoch, "policy_rebind_rejected", task_id=task.get("task_id"), reason="POLICY_REBIND_BINDING_MISMATCH", policy_rebind_ref=ref)
            return False

        task["authorized_policy_version"] = current_policy
        task["policy_rebind_ref"] = None
        task["archive_reason_codes"] = [code for code in task.get("archive_reason_codes", []) if code != "POLICY_REBIND_REQUIRED"]
        if ref not in task.setdefault("evidence_refs", []):
            task["evidence_refs"].append(ref)
        if task.get("state") == "EXPIRING":
            task["state"] = "ACTIVE"
        self._event(
            events,
            epoch,
            "policy_rebound",
            task_id=task.get("task_id"),
            claim_id=task.get("claim_id"),
            fencing_token=timing.get("fencing_token"),
            old_policy_version=authorized_policy,
            new_policy_version=current_policy,
            policy_rebind_ref=ref,
            heartbeat_granted_rebind=False,
        )
        return True

    def _hold_for_policy_rebind(
        self,
        task: dict[str, Any],
        handoff: dict[str, Any],
        epoch: int,
        events: list[dict[str, Any]],
    ) -> None:
        task["state"] = "EXPIRING"
        task["archive_eligible"] = False
        task["archive_reason_codes"] = sorted(set(task.get("archive_reason_codes", []) + ["POLICY_REBIND_REQUIRED"]))
        self._event(
            events,
            epoch,
            "policy_drift_detected",
            task_id=task.get("task_id"),
            claim_id=task.get("claim_id"),
            fencing_token=(task.get("heartbeat_timing") or {}).get("fencing_token"),
            authorized_policy_version=task.get("authorized_policy_version"),
            observed_policy_version=(handoff.get("authority") or {}).get("policy_version"),
            handoff_sha256=self._handoff_hash(handoff),
            heartbeat_grants_rebind=False,
        )

    def _write_canonical_checkpoint(
        self,
        task: dict[str, Any],
        handoff: dict[str, Any],
        epoch: int,
        snapshot: dict[str, Any],
        events: list[dict[str, Any]],
    ) -> str:
        timing = task.get("heartbeat_timing") or snapshot.get("heartbeat_timing") or {}
        transition = {
            "heartbeat_epoch": epoch,
            "transition_id": str(timing.get("current_transition") or "UNKNOWN"),
            "transition_sequence": int(timing.get("transition_sequence", 0)),
            "response_state": str(task.get("state") or "UNKNOWN"),
        }
        history = list(task.get("transition_history") or [])
        if not history or history[-1] != transition:
            history.append(transition)
        task["transition_history"] = history

        worker_checkpoint_ref = snapshot.get("worker_checkpoint_ref")
        authority = handoff.get("authority") or {}
        completion = handoff.get("completion") or {}
        unresolved = [] if task.get("state") == "COMPLETED" else [str(completion.get("next_authorized_action") or "Continue bounded task work")]
        evidence_refs = list(dict.fromkeys(str(ref) for ref in task.get("evidence_refs", []) if ref))
        fence = int(snapshot.get("fencing_token") or timing.get("fencing_token") or 0)
        checkpoint = {
            "schema": "stegverse.worker-checkpoint/v0.1",
            "checkpoint_id": f"CP-{task['task_id']}-HB{epoch}-G{fence}",
            "heartbeat_epoch": epoch,
            "task_id": task["task_id"],
            "goal_id": task.get("goal_id") or (handoff.get("goal") or {}).get("goal_id"),
            "worker_id": snapshot["worker_id"],
            "worker_instance_id": snapshot["worker_instance_id"],
            "claim_id": snapshot["claim_id"],
            "fencing_token": fence,
            "current_state": str(task.get("state")),
            "completed_transitions": history,
            "unresolved_work": unresolved,
            "evidence_refs": evidence_refs,
            "next_authorized_action": str(completion.get("next_authorized_action") or "No additional action authorized"),
            "policy_version": str(task.get("authorized_policy_version") or authority.get("policy_version")),
            "authority_source": str(authority.get("authority_source")),
            "handoff_ref": task["handoff_ref"],
            "handoff_sha256": self._handoff_hash(handoff),
            "worker_checkpoint_ref": worker_checkpoint_ref,
            "resource_budget": task.get("resource_budget"),
            "execution_authority": False,
        }
        checkpoint["checkpoint_sha256"] = self._checkpoint_hash(checkpoint)
        ref = f"checkpoints/workers/{task['task_id']}/HB{epoch}-G{fence}.json"
        self._atomic_write(self.root / ref, checkpoint)
        task["last_checkpoint_ref"] = ref
        if ref not in task.setdefault("evidence_refs", []):
            task["evidence_refs"].append(ref)
        self._event(
            events,
            epoch,
            "canonical_worker_checkpoint_written",
            task_id=task.get("task_id"),
            checkpoint_ref=ref,
            checkpoint_sha256=checkpoint["checkpoint_sha256"],
            policy_version=checkpoint["policy_version"],
            fencing_token=fence,
            execution_authority=False,
        )
        return ref

    def _canonical_checkpoint_valid(self, ref: str, proof: dict[str, Any]) -> bool:
        if not ref.startswith("checkpoints/workers/"):
            return True
        path = self.root / ref
        if not path.exists():
            return False
        try:
            checkpoint = self._load(path)
        except Exception:
            return False
        return all([
            checkpoint.get("schema") == "stegverse.worker-checkpoint/v0.1",
            checkpoint.get("execution_authority") is False,
            checkpoint.get("checkpoint_sha256") == self._checkpoint_hash(checkpoint),
            checkpoint.get("checkpoint_sha256") == proof.get("checkpoint_sha256"),
            checkpoint.get("fencing_token") == proof.get("last_valid_fencing_token"),
            checkpoint.get("policy_version") == proof.get("policy_version"),
            isinstance(checkpoint.get("completed_transitions"), list) and bool(checkpoint.get("completed_transitions")),
            isinstance(checkpoint.get("handoff_sha256"), str) and len(checkpoint.get("handoff_sha256")) == 64,
        ])

    def _successor_reconstruction(self, registry: dict[str, Any], handoff: dict[str, Any]) -> tuple[bool, str | None, dict[str, Any] | None]:
        ok, reason, proof = super()._successor_reconstruction(registry, handoff)
        if not ok or proof is None:
            return ok, reason, proof
        checkpoint_ref = (handoff.get("continuity") or {}).get("checkpoint_ref")
        if isinstance(checkpoint_ref, str) and not self._canonical_checkpoint_valid(checkpoint_ref, proof):
            return False, "SUCCESSOR_CANONICAL_CHECKPOINT_INVALID", proof
        return True, None, proof

    def _invoke(self, registry: dict[str, Any], task: dict[str, Any], epoch: int, cost_log: dict[str, Any], events: list[dict[str, Any]]) -> None:
        handoff = self._handoff(task)
        timing_before = dict(task.get("heartbeat_timing") or {})
        snapshot = {
            "worker_id": task.get("worker_id"),
            "worker_instance_id": task.get("worker_instance_id"),
            "claim_id": task.get("claim_id"),
            "fencing_token": timing_before.get("fencing_token"),
            "worker_checkpoint_ref": task.get("last_checkpoint_ref"),
            "heartbeat_timing": timing_before,
        }

        if not self._apply_policy_rebind(task, handoff, epoch, events):
            self._hold_for_policy_rebind(task, handoff, epoch, events)
            return

        super()._invoke(registry, task, epoch, cost_log, events)

        timing_after = task.get("heartbeat_timing") or {}
        responded = timing_after.get("last_response_epoch") == epoch
        if not responded:
            return
        if not all(isinstance(snapshot.get(key), str) and snapshot.get(key) for key in ("worker_id", "worker_instance_id", "claim_id")):
            return
        self._write_canonical_checkpoint(task, handoff, epoch, snapshot, events)


__all__ = ["HeartbeatRuntime", "WorkerResponse"]
