"""StegVerse heartbeat carrier and worker coordination primitives.

`CarrierHeartbeatRuntime` is the canonical non-authorizing system carrier.
`HeartbeatRuntime` is retained temporarily as a compatibility alias for the
legacy worker coordinator so existing worker-lifecycle consumers do not break;
new code must use `WorkerCoordinator` explicitly for lifecycle work.
"""

from .engine_v11 import HeartbeatRuntime, WorkerResponse
from .engine_v12 import HeartbeatRuntime as CarrierHeartbeatRuntime
from .worker_runtime import WorkerCoordinator
from .process_adapter import ProcessWorkerAdapter

__all__ = [
    "CarrierHeartbeatRuntime",
    "WorkerCoordinator",
    "HeartbeatRuntime",
    "WorkerResponse",
    "ProcessWorkerAdapter",
]
