"""StegVerse heartbeat carrier and worker coordination primitives.

`CarrierHeartbeatRuntime` is the canonical non-authorizing production carrier.
`WorkerCoordinator` is the separated worker/control-plane runtime. The historical
package-level `HeartbeatRuntime` remains the versioned-v11 compatibility API for
existing worker/control-plane consumers; production deployment selects the
fragment-aware separated carrier explicitly.
"""

from .engine_v13 import HeartbeatRuntime as CarrierHeartbeatRuntime
from .engine_v11 import HeartbeatRuntime, WorkerResponse
from .worker_runtime import WorkerCoordinator
from .process_adapter import ProcessWorkerAdapter

__all__ = [
    "HeartbeatRuntime",
    "CarrierHeartbeatRuntime",
    "WorkerCoordinator",
    "WorkerResponse",
    "ProcessWorkerAdapter",
]
