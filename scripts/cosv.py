#!/usr/bin/env python3
import argparse, json, sys, math
from pathlib import Path

LIFECYCLE={"UNKNOWN":0,"UNCLAIMED":1,"CLAIMED_IMPLEMENTATION":2,"CLAIMED_VALIDATION":3,"CLAIMED_INTEGRATION":4,"MACHINE_OWNED":5,"BLOCKED":6,"COMPLETE":7,"SUPERSEDED":8,"MERGED_INTO_CANONICAL_WORKSTREAM":9}
FACTOR_BANDS=[(0,0,0),(1,12,1),(13,24,2),(25,37,3),(38,49,4),(50,62,5),(63,74,6),(75,87,7),(88,99,8),(100,100,9)]
MID={0:0,1:6.5,2:18.5,3:31,4:43.5,5:56,6:68.5,7:81,8:93.5,9:100}
TASK_FIELDS=["lifecycle","archive_ready","unassigned_work","chat_owned_implementation","chat_owned_validation","chat_owned_integration","chat_owned_observation","chat_owned_credentials","canonical_owner_installed","thread_required","blocker_count","evidence_complete","activated","propagated"]
AGG_FIELDS=["lifecycle","developed","validation","integration","propagation","activation","readiness","ownership","evidence","critical_blockers","conflicting_claims","unassigned_work","stale_claims","thread_required"]
TASK_TERNARY={1,8,9,11,12,13}
AGG_TERNARY={13}

def qty(v): return 9 if int(v)>=9 else max(0,int(v))
def tern(v):
    if v in (0,1,2): return int(v)
    if v is True:return 1
    if v is False:return 0
    if v is None:return 2
    raise ValueError("ternary must be true/false/null or 0/1/2")
def factor(p):
    p=float(p)
    if not 0<=p<=100: raise ValueError("factor percent out of range")
    if p >= 100: return 9
    if p <= 0: return 0
    d=min(99,max(1,math.floor(p)))
    for lo,hi,band in FACTOR_BANDS:
        if lo<=d<=hi:return band
    raise ValueError("factor encoding failed")
def lifecycle(v):
    if isinstance(v,int) and 0<=v<=9:return v
    return LIFECYCLE[v]
def encode_task(m):
    vals=[lifecycle(m["lifecycle"]),tern(m["archive_ready"]),qty(m["unassigned_work"]),qty(m["chat_owned_implementation"]),qty(m["chat_owned_validation"]),qty(m["chat_owned_integration"]),qty(m["chat_owned_observation"]),qty(m["chat_owned_credentials"]),tern(m["canonical_owner_installed"]),tern(m["thread_required"]),qty(m["blocker_count"]),tern(m["evidence_complete"]),tern(m["activated"]),tern(m["propagated"])]
    return ''.join(map(str,vals))
def encode_aggregate(m):
    vals=[lifecycle(m["lifecycle"]),factor(m["developed"]),factor(m["validation"]),factor(m["integration"]),factor(m["propagation"]),factor(m["activation"]),factor(m["readiness"]),factor(m["ownership"]),factor(m["evidence"]),qty(m["critical_blockers"]),qty(m["conflicting_claims"]),qty(m["unassigned_work"]),qty(m["stale_claims"]),tern(m["thread_required"])]
    return ''.join(map(str,vals))
def validate_vector(profile,v):
    if not isinstance(v,str) or len(v)!=14 or not v.isdigit(): return False
    d=list(map(int,v))
    if profile=="task.v1": return all(d[i] in (0,1,2) for i in TASK_TERNARY)
    if profile=="aggregate.v1": return all(d[i] in (0,1,2) for i in AGG_TERNARY)
    if profile=="transition.v1": return True
    return False
def thread_roll(values):
    vals=[tern(v) for v in values]
    if 1 in vals:return 1
    if all(v==0 for v in vals):return 0
    return 2
def aggregate(children,lifecycle_state="MACHINE_OWNED"):
    if not children: raise ValueError("children required")
    factor_names=["developed","validation","integration","propagation","activation","readiness","ownership","evidence"]
    exact={k:0.0 for k in factor_names}; totalw=0
    totals={k:0 for k in ["critical_blockers","conflicting_claims","unassigned_work","stale_claims"]}; threads=[]
    for c in children:
        w=int(c.get("weight",1))
        if not 1<=w<=9: raise ValueError("weight must be 1..9")
        totalw+=w; metrics=c.get("exact_metrics",{}); vec=c["vector"]
        if not validate_vector("aggregate.v1",vec): raise ValueError("child vector invalid")
        digits=list(map(int,vec))
        for i,k in enumerate(factor_names,1): exact[k]+=float(metrics.get(k,MID[digits[i]]))*w
        for i,k in enumerate(["critical_blockers","conflicting_claims","unassigned_work","stale_claims"],9): totals[k]+=int(metrics.get(k,digits[i]))
        threads.append(digits[13])
    pct={k:exact[k]/totalw for k in factor_names}
    m={"lifecycle":lifecycle_state,**pct,**totals,"thread_required":thread_roll(threads)}
    return {"vector":encode_aggregate(m),"exact_metrics":{**pct,**totals,"thread_required":m["thread_required"]}}
def transition(profile,a,b):
    if not validate_vector(profile,a) or not validate_vector(profile,b): raise ValueError("invalid vectors")
    count_lower={2,3,4,5,6,7,10} if profile=="task.v1" else {9,10,11,12}
    factor_higher=set(range(1,9)) if profile=="aggregate.v1" else set()
    ternary=TASK_TERNARY if profile=="task.v1" else AGG_TERNARY
    out=[]
    for i,(x,y) in enumerate(zip(map(int,a),map(int,b))):
        if x==y: out.append(0); continue
        if i in ternary and x==2 and y in (0,1): out.append(3); continue
        if i in ternary and y==2 and x in (0,1): out.append(4); continue
        if profile=="task.v1" and i==8: out.append(5); continue
        if i==0:
            if y==6: out.append(6)
            elif x==6: out.append(7)
            elif y in (7,8,9): out.append(8)
            else: out.append(9)
            continue
        if i in count_lower: out.append(1 if y<x else 2)
        elif i in factor_higher: out.append(1 if y>x else 2)
        else: out.append(9)
    return ''.join(map(str,out))
def validate_record(r):
    req=["identity","profile","level","vector","evidence_refs","observed_at","exact_metrics"]
    if any(k not in r for k in req) or not r["evidence_refs"]: return False
    level_ok=(r["profile"]=="task.v1" and r["level"]=="task") or (r["profile"]=="aggregate.v1" and r["level"] in {"goal","component","subsystem","system","ecosystem"}) or (r["profile"]=="transition.v1" and r["level"]=="transition")
    return level_ok and validate_vector(r["profile"],r["vector"])
def self_test():
    v=encode_task({"lifecycle":"MERGED_INTO_CANONICAL_WORKSTREAM","archive_ready":True,"unassigned_work":0,"chat_owned_implementation":0,"chat_owned_validation":0,"chat_owned_integration":0,"chat_owned_observation":0,"chat_owned_credentials":0,"canonical_owner_installed":True,"thread_required":False,"blocker_count":0,"evidence_complete":True,"activated":False,"propagated":None})
    assert v=="91000000100102",v
    a=encode_aggregate({"lifecycle":"MACHINE_OWNED","developed":100,"validation":88,"integration":75,"propagation":50,"activation":25,"readiness":62,"ownership":100,"evidence":99,"critical_blockers":12,"conflicting_claims":0,"unassigned_work":0,"stale_claims":2,"thread_required":False})
    assert a=="59875359890020",a
    assert factor(0)==0 and factor(0.5)==1 and factor(12.5)==1 and factor(99.5)==8 and factor(100)==9
    assert transition("task.v1","91200000100102","91100000100102")[2]=="1"
    assert validate_vector("task.v1",v)
    assert transition("task.v1",v,v)=="0"*14
    print("COSV_SELF_TEST_PASS")
def main():
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest="cmd",required=True); sp.add_parser("self-test")
    p=sp.add_parser("validate"); p.add_argument("file"); args=ap.parse_args()
    if args.cmd=="self-test": self_test(); return
    data=json.loads(Path(args.file).read_text()); records=data if isinstance(data,list) else data.get("records",[data])
    bad=[r.get("identity","<unknown>") for r in records if not validate_record(r)]
    if bad: print("COSV_VALIDATION_FAIL",','.join(bad)); sys.exit(1)
    print(f"COSV_VALIDATION_PASS records={len(records)}")
if __name__=="__main__": main()
