"""StegVerse heartbeat carrier and worker coordination primitives.

`CarrierHeartbeatRuntime` is the canonical non-authorizing carrier and production
heartbeat target. `HeartbeatRuntime` remains the historical worker/control-plane
compatibility alias so existing admitted worker tests and integrations do not
silently change authority semantics. Production deployment selects engine v12
explicitly and never infers carrier authority from this compatibility alias.
"""

from .engine_v12 import HeartbeatRuntime as CarrierHeartbeatRuntime
from .engine_v11 import WorkerResponse
from .worker_runtime import WorkerCoordinator
from .worker_runtime import WorkerCoordinator as HeartbeatRuntime
from .process_adapter import ProcessWorkerAdapter

__all__ = [
    "HeartbeatRuntime",
    "CarrierHeartbeatRuntime",
    "WorkerCoordinator",
    "WorkerResponse",
    "ProcessWorkerAdapter",
]
