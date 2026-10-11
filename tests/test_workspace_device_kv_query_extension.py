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

def tasks_query(node='SV-NODE-abc'):
 q=query(node);q['record_class']='WORKSPACE_TASKS_PROJECTION';q['requested_scope']=['tasks','commitments','timeline'];q['purpose']='Project the current owner\'s admitted Personal KnowledgeVault tasks and commitments.';return q

def test_tasks_query_validates_and_personal_scopes_are_not_interchangeable():
 assert m.validate_workspace_query(tasks_query(),node_id='SV-NODE-abc')['record_class']==m.TASKS_RECORD_CLASS
 assert set(m.RECORD_CLASSES)=={'WORKSPACE_PERSONAL_PROJECTION','WORKSPACE_TASKS_PROJECTION','WORKSPACE_FAMILY_PROJECTIONS','WORKSPACE_CONTINUITY_CHECKPOINT'}
 q=tasks_query();q['requested_scope']=m.SCOPES
 try:m.validate_workspace_query(q,node_id='SV-NODE-abc');assert False
 except m.WorkspaceDeviceKVQueryError as exc:assert 'workspace_query_scope_invalid' in str(exc)
 q=query();q['requested_scope']=m.TASKS_SCOPES
 try:m.validate_workspace_query(q,node_id='SV-NODE-abc');assert False
 except m.WorkspaceDeviceKVQueryError as exc:assert 'workspace_query_scope_invalid' in str(exc)
 q=tasks_query();q['record_class']='WORKSPACE_ORG_TASKS'
 try:m.validate_workspace_query(q,node_id='SV-NODE-abc');assert False
 except m.WorkspaceDeviceKVQueryError as exc:assert 'workspace_query_record_class_invalid' in str(exc)
 try:m.validate_workspace_query(tasks_query(),node_id='SV-NODE-other');assert False
 except m.WorkspaceDeviceKVQueryError:pass

def _fake_cvk(tmp_path):
 src=tmp_path/'cvk';(src/'runtime').mkdir(parents=True);(src/'runtime'/'__init__.py').write_text('')
 (src/'runtime'/'workspace_projection.py').write_text('class WorkspaceProjectionError(ValueError): pass\n'
  'def get_personal_workspace_projection(*,kv_data_root,clock=None):\n'
  ' return {"schema":"stegverse.kv.personal-workspace-projection/v1","workspace_type":"PERSONAL","state":"KV_WORKSPACE_EMPTY","principals":[],"organizations":[],"memberships":[],"feed":[],"assistant":None,"credential_material_present":False,"provider_operation_authorized":False,"workspace_grants_authority":False,"authority_effect":"NONE"}\n')
 (src/'runtime'/'workspace_tasks_projection.py').write_text('from runtime.workspace_projection import WorkspaceProjectionError\n'
  'def get_personal_tasks_projection(*,kv_data_root,clock=None):\n'
  ' return {"schema":"stegverse.kv.workspace-tasks-projection/v1","state":"KV_TASKS_EMPTY","workspace_type":"PERSONAL","tasks":[],"commitments":[],"timeline":[],"credential_material_present":False,"provider_operation_authorized":False,"workspace_grants_authority":False,"action_authority":"NONE","authority_effect":"NONE","projection_metadata":{"schema":"stegverse.kv.workspace-projection-metadata/v1"}}\n')
 data=tmp_path/'KnowledgeVault';data.mkdir();return src,data

def test_tasks_query_executes_the_tasks_producer_and_personal_query_the_personal_producer(tmp_path):
 src,data=_fake_cvk(tmp_path)
 t=m.execute_workspace_query(query=tasks_query(),node_id='SV-NODE-abc',kv_source_root=src,kv_data_root=data)
 assert t['schema']=='stegverse.kv.workspace-tasks-projection/v1' and t['action_authority']=='NONE'
 p=m.execute_workspace_query(query=query(),node_id='SV-NODE-abc',kv_source_root=src,kv_data_root=data)
 assert p['schema']=='stegverse.kv.personal-workspace-projection/v1'

def test_tasks_producer_claiming_action_authority_or_wrong_schema_fails_closed(tmp_path):
 src,data=_fake_cvk(tmp_path)
 (src/'runtime'/'workspace_tasks_projection.py').write_text('def get_personal_tasks_projection(*,kv_data_root,clock=None):\n return {"schema":"stegverse.kv.workspace-tasks-projection/v1","action_authority":"ALLOW","credential_material_present":False,"provider_operation_authorized":False,"workspace_grants_authority":False,"workspace_type":"PERSONAL"}\n')
 try:m.execute_workspace_query(query=tasks_query(),node_id='SV-NODE-abc',kv_source_root=src,kv_data_root=data);assert False
 except m.WorkspaceDeviceKVQueryError as exc:assert 'workspace_projection_authority_invalid' in str(exc)
 (src/'runtime'/'workspace_tasks_projection.py').write_text('def get_personal_tasks_projection(*,kv_data_root,clock=None):\n return {"schema":"stegverse.kv.personal-workspace-projection/v1"}\n')
 try:m.execute_workspace_query(query=tasks_query(),node_id='SV-NODE-abc',kv_source_root=src,kv_data_root=data);assert False
 except m.WorkspaceDeviceKVQueryError as exc:assert 'workspace_projection_invalid' in str(exc)
 (src/'runtime'/'workspace_tasks_projection.py').unlink()
 try:m.execute_workspace_query(query=tasks_query(),node_id='SV-NODE-abc',kv_source_root=src,kv_data_root=data);assert False
 except m.WorkspaceDeviceKVQueryError as exc:assert 'workspace_projection_source_missing' in str(exc)

def family_query(node='SV-NODE-abc'):
 q=query(node);q['record_class']='WORKSPACE_FAMILY_PROJECTIONS';q['requested_scope']=['projections'];return q

def checkpoint_query(node='SV-NODE-abc'):
 q=query(node);q['record_class']='WORKSPACE_CONTINUITY_CHECKPOINT';q['requested_scope']=['checkpoint','decision'];return q

def _fake_cvk_delivery(tmp_path):
 src,data=_fake_cvk(tmp_path)
 (src/'runtime'/'workspace_family_projections.py').write_text('def get_personal_family_projections(*,kv_data_root,clock=None):\n return {"schema":"stegverse.kv.workspace-family-projections/v1","state":"KV_FAMILY_PROJECTIONS_PROJECTED","workspace_type":"PERSONAL","projections":[{"schema":"stegverse.kv.cryptobot-portfolio-projection/v1","workspace_type":"PERSONAL"}],"projection_schemas":["stegverse.kv.cryptobot-portfolio-projection/v1"],"credential_material_present":False,"provider_operation_authorized":False,"workspace_grants_authority":False,"action_authority":"NONE","projection_metadata":{"schema":"stegverse.kv.workspace-projection-metadata/v1"},"authority_effect":"NONE"}\n')
 (src/'runtime'/'workspace_continuity_checkpoint_projection.py').write_text('def get_personal_continuity_checkpoint(*,kv_data_root,clock=None):\n return {"schema":"stegverse.kv.workspace-continuity-checkpoint-delivery/v1","state":"KV_CHECKPOINT_PROJECTED","workspace_type":"PERSONAL","checkpoint":{"schema":"stegverse.kv.workspace-continuity-checkpoint/v1"},"decision":{"schema":"stegverse.kv.workspace-continuity-checkpoint-decision/v1","disposition":"FAIL_CLOSED","predicate":"CHECKPOINT_ANCHOR_VERIFIER_UNAVAILABLE:FIRST_CHECKPOINT","replay_status":"UNKNOWN","authority_effect":"NONE"},"anchor_verified":False,"credential_material_present":False,"provider_operation_authorized":False,"workspace_grants_authority":False,"action_authority":"NONE","projection_metadata":{"schema":"stegverse.kv.workspace-projection-metadata/v1"},"authority_effect":"NONE"}\n')
 return src,data

def test_family_and_checkpoint_queries_validate_and_scopes_are_class_bound():
 assert m.validate_workspace_query(family_query(),node_id='SV-NODE-abc')['record_class']==m.FAMILY_RECORD_CLASS
 assert m.validate_workspace_query(checkpoint_query(),node_id='SV-NODE-abc')['record_class']==m.CHECKPOINT_RECORD_CLASS
 for bad in (dict(family_query(),requested_scope=m.CHECKPOINT_SCOPES),dict(checkpoint_query(),requested_scope=m.FAMILY_SCOPES),dict(family_query(),requested_scope=m.TASKS_SCOPES)):
  try:m.validate_workspace_query(bad,node_id='SV-NODE-abc');assert False
  except m.WorkspaceDeviceKVQueryError as exc:assert 'workspace_query_scope_invalid' in str(exc)
 for q in (family_query(),checkpoint_query()):
  try:m.validate_workspace_query(q,node_id='SV-NODE-other');assert False
  except m.WorkspaceDeviceKVQueryError:pass

def test_family_and_checkpoint_queries_execute_their_own_producers(tmp_path):
 src,data=_fake_cvk_delivery(tmp_path)
 f=m.execute_workspace_query(query=family_query(),node_id='SV-NODE-abc',kv_source_root=src,kv_data_root=data)
 assert f['schema']=='stegverse.kv.workspace-family-projections/v1' and f['projection_schemas']==['stegverse.kv.cryptobot-portfolio-projection/v1']
 c=m.execute_workspace_query(query=checkpoint_query(),node_id='SV-NODE-abc',kv_source_root=src,kv_data_root=data)
 assert c['schema']=='stegverse.kv.workspace-continuity-checkpoint-delivery/v1' and c['decision']['disposition']=='FAIL_CLOSED' and c['anchor_verified'] is False

def test_checkpoint_delivery_claiming_verification_or_authority_fails_closed(tmp_path):
 src,data=_fake_cvk_delivery(tmp_path)
 p=src/'runtime'/'workspace_continuity_checkpoint_projection.py';base=p.read_text()
 p.write_text(base.replace('"disposition":"FAIL_CLOSED"','"disposition":"ALLOW"'))
 try:m.execute_workspace_query(query=checkpoint_query(),node_id='SV-NODE-abc',kv_source_root=src,kv_data_root=data);assert False
 except m.WorkspaceDeviceKVQueryError as exc:assert 'workspace_projection_authority_invalid' in str(exc)
 p.write_text(base.replace('"anchor_verified":False','"anchor_verified":True'))
 try:m.execute_workspace_query(query=checkpoint_query(),node_id='SV-NODE-abc',kv_source_root=src,kv_data_root=data);assert False
 except m.WorkspaceDeviceKVQueryError as exc:assert 'workspace_projection_authority_invalid' in str(exc)
 f=src/'runtime'/'workspace_family_projections.py';f.write_text(f.read_text().replace('"action_authority":"NONE"','"action_authority":"ALLOW"'))
 try:m.execute_workspace_query(query=family_query(),node_id='SV-NODE-abc',kv_source_root=src,kv_data_root=data);assert False
 except m.WorkspaceDeviceKVQueryError as exc:assert 'workspace_projection_authority_invalid' in str(exc)
