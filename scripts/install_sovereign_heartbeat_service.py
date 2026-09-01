#!/usr/bin/env python3
"""Sovereign service installer entrypoint with Workspace DEVICE_KV source."""
from __future__ import annotations
import importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location("stegverse_installer_base",ROOT/"scripts/install_sovereign_heartbeat_service_base.py")
if spec is None or spec.loader is None:raise RuntimeError("installer_base_loader_unavailable")
BASE=importlib.util.module_from_spec(spec);spec.loader.exec_module(BASE)
EXTRA=("scripts/consume_device_kv_intr_materialization_request_base.py","scripts/workspace_device_kv_query_extension.py","scripts/personal_profile_device_kv_extension.py","scripts/refresh_sovereign_worker_runtime_source_base.py","scripts/bootstrap_sovereign_runtime_base.py","scripts/install_sovereign_heartbeat_service_base.py")
BASE.COPY_FILES=tuple(dict.fromkeys(BASE.COPY_FILES+EXTRA))
for _name in dir(BASE):
    if _name not in globals() and not _name.startswith("__"):globals()[_name]=getattr(BASE,_name)
if __name__=="__main__":raise SystemExit(BASE.main())
