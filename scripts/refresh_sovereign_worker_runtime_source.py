#!/usr/bin/env python3
"""Sovereign source refresh entrypoint with Workspace DEVICE_KV source extension."""
from __future__ import annotations
import importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location("stegverse_refresh_base",ROOT/"scripts/refresh_sovereign_worker_runtime_source_base.py")
if spec is None or spec.loader is None:raise RuntimeError("refresh_base_loader_unavailable")
BASE=importlib.util.module_from_spec(spec);spec.loader.exec_module(BASE)
EXTRA=(Path("scripts/consume_device_kv_intr_materialization_request_base.py"),Path("scripts/workspace_device_kv_query_extension.py"),Path("scripts/refresh_sovereign_worker_runtime_source_base.py"))
BASE.STATIC_FILES=tuple(dict.fromkeys(BASE.STATIC_FILES+EXTRA))
for _name in dir(BASE):
    if _name not in globals() and not _name.startswith("__"):globals()[_name]=getattr(BASE,_name)
if __name__=="__main__":raise SystemExit(BASE.main())
