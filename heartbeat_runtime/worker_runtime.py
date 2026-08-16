"""Worker lifecycle coordinator separated from the heartbeat carrier.

This module preserves the admitted-task/claim/worker lifecycle behavior that was
historically bundled into heartbeat engine v11. It is intentionally not exported
as the canonical HeartbeatRuntime.
"""

from .engine_v11 import HeartbeatRuntime as WorkerCoordinator, WorkerResponse
from .process_adapter import ProcessWorkerAdapter

__all__ = ["WorkerCoordinator", "WorkerResponse", "ProcessWorkerAdapter"]
