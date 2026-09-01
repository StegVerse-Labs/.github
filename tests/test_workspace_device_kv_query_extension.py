import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('workspace_ext',ROOT/'scripts/workspace_device_kv_query_extension.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def query(node='SV-NODE-abc'):
 return {'schema_version':'kv.interlock.request.v1','operation':'REQUEST','request_id':'q1','requester':{'module':'Site','component':'Workspace'},'purpose':'Project Workspace','record_class':'WORKSPACE_PERSONAL_PROJECTION','requested_scope':['workspace_identity','principals','relationships','organizations','memberships','feed','assistant'],'minimum_necessary_justification':'Bounded Workspace metadata only.','authority_ref':'stegos-node://'+node,'disclosure_mode':'BOUNDED_CONTEXT','selector':{'workspace_type':'PERSONAL'}}

def test_exact_workspace_query_validates(): assert m.validate_workspace_query(query(),node_id='SV-NODE-abc')['record_class']==m.RECORD_CLASS
def test_wrong_node_fails_closed():
 try:m.validate_workspace_query(query(),node_id='SV-NODE-other');assert False
 except m.WorkspaceDeviceKVQueryError:pass
def test_org_selector_is_not_accepted():
 q=query();q['selector']={'workspace_type':'ORGANIZATIONAL'}
 try:m.validate_workspace_query(q,node_id='SV-NODE-abc');assert False
 except m.WorkspaceDeviceKVQueryError:pass
