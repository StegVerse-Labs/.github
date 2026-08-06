#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def canon(v): return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def fail(m): print(f'ERROR: {m}',file=sys.stderr); raise SystemExit(1)
def main():
 out=ROOT/'heartbeats/outbound'; ret=ROOT/'heartbeats/returns'; obs=ROOT/'heartbeats/observations'; obs.mkdir(parents=True,exist_ok=True)
 count=0
 for rp in sorted(ret.glob('*.json')) if ret.exists() else []:
  r=json.loads(rp.read_text()); ap=out/r['assertion_file'];
  if not ap.exists(): fail(f'missing assertion {ap.name}')
  a=json.loads(ap.read_text()); expected=a['payload_sha256']; raw=dict(a); raw.pop('payload_sha256',None)
  if hashlib.sha256(canon(raw)).hexdigest()!=expected: fail(f'assertion digest mismatch {ap.name}')
  if r.get('nonce')!=a['nonce']: fail(f'nonce mismatch {rp.name}')
  delta={'epoch':a['epoch']-r.get('epoch',-1),'claims':sorted(set(json.dumps(x,sort_keys=True) for x in a['claims'])^set(json.dumps(x,sort_keys=True) for x in r.get('claims',[]))),'fencing_token':a['fencing_token']-r.get('fencing_token',-1),'scope':a.get('scope')!=r.get('scope'),'policy_version':a['policy_version']!=r.get('policy_version'),'evidence_pointer_changed':a.get('evidence_pointer')!=r.get('evidence_pointer'),'nonce':0}
  deterministic_ok=delta['epoch']==0 and not delta['claims'] and delta['fencing_token']==0 and not delta['scope'] and not delta['policy_version']
  (obs/rp.name).write_text(json.dumps({'schema':'stegverse.org-heartbeat-observation/v1','assertion':ap.name,'return':rp.name,'delta':delta,'deterministic_ok':deterministic_ok,'authority_effect':'none'},indent=2,sort_keys=True)+'\n'); count+=1
 print(json.dumps({'validated_returns':count},sort_keys=True))
if __name__=='__main__': main()
