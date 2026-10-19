#!/usr/bin/env python3
import argparse,hashlib,importlib.util,json,os,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];C=json.loads((ROOT/".stegverse/transition-ledger/contract.json").read_text())
# The heartbeat is the ecosystem's time base; the kernel owns its derivation so
# a receipt and a carrier frame cannot disagree about what an epoch is.
_spec=importlib.util.spec_from_file_location("kernel",ROOT/"org-kernel/kernel.py")
kernel=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(kernel)
# The repository ledger published HEAD with no lock and no atomic replacement,
# so two concurrent appends read one HEAD, bound receipts to the same
# predecessor, and the later HEAD write silently won -- forking the chain and
# orphaning a receipt. The organization ledger above it serializes its append;
# this one addresses the same store so it does too.
_sspec=importlib.util.spec_from_file_location("ledger_store",ROOT/"resident-runtime/ledger_store.py")
ledger_store=importlib.util.module_from_spec(_sspec);_sspec.loader.exec_module(ledger_store)
def canon(v):return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def sha(v):return "sha256:"+hashlib.sha256(v if isinstance(v,(bytes,bytearray)) else canon(v)).hexdigest()
def lr():
 o=os.getenv("STEGVERSE_REPO_LEDGER_ROOT")
 if o:return Path(o).expanduser().resolve()
 # Supplied, never derived from the host: see aggregate_repo_transition.ledger_root.
 raise ValueError("ledger_location_required_from_materializer: STEGVERSE_REPO_LEDGER_ROOT")
def repository_store():
 """The repository ledger store the materializer supplied.

 A filesystem path stays a POSIX root. A `git+<repository>#<ref>:<namespace>`
 locator is the repository subtree of the designated organization ledger ref:
 same ref, same fast-forward, no second history.
 """
 o=os.getenv("STEGVERSE_REPO_LEDGER_ROOT")
 if not o: raise ValueError("ledger_location_required_from_materializer: STEGVERSE_REPO_LEDGER_ROOT")
 if str(o).startswith(ledger_store.GIT_SCHEME): return ledger_store.open_store(o)
 return ledger_store.PosixLedgerStore(Path(o).expanduser().resolve())
# A chain is only as good as the nodes it walks. A missing node used to end the
# walk as though it were genesis, so a lookup answered "never recorded" and the
# append minted a second receipt on top of a broken chain; a node edited in
# place was believed. Every node reachable from HEAD is now read back as the
# receipt its address names, or the attempt fails closed and nothing is written.
CHAIN_BREAK="REPO_LEDGER_CHAIN_BREAK"
DIGEST=re.compile(r"^sha256:[0-9a-f]{64}$")
class RepoLedgerChainBreak(ValueError):
 """A node reachable from HEAD is missing, malformed or not the receipt its digest names."""
 failed_predicate=CHAIN_BREAK
 def __init__(self,receipt_sha256,detail):
  super().__init__(CHAIN_BREAK+": "+detail+": "+repr(receipt_sha256))
  self.receipt_sha256=receipt_sha256;self.detail=detail
def chain_break_refusal(exc):
 """The append attempt's own disposition when the chain it would extend is broken."""
 return {"schema":"stegverse.repo-ledger-append-refusal/v1","repository":C["repository"],"disposition":"FAIL_CLOSED","failed_predicate":exc.failed_predicate,"detail":exc.detail,"receipt_sha256":exc.receipt_sha256,"required_evidence_or_repair":"restore the receipt addressed by receipt_sha256, byte-for-byte as minted; a chain is never re-minted over a break","retry_entrypoint":".stegverse/transition-ledger/emit.py::append","consequence_committed":False,"authority_effect":"NONE_REFUSAL_ONLY"}
def node(target,cursor):
 """The receipt `cursor` addresses, recomputed and proven to be that receipt."""
 if not isinstance(cursor,str) or not DIGEST.match(cursor):raise RepoLedgerChainBreak(cursor,"malformed_receipt_address")
 try:receipt=target.get(ledger_store.receipt_key(cursor))
 except ValueError:raise RepoLedgerChainBreak(cursor,"unreadable_receipt") from None
 if receipt is None:raise RepoLedgerChainBreak(cursor,"missing_receipt")
 if not isinstance(receipt,dict):raise RepoLedgerChainBreak(cursor,"malformed_receipt")
 if sha({k:v for k,v in receipt.items() if k!="receipt_sha256"})!=cursor:raise RepoLedgerChainBreak(cursor,"receipt_body_does_not_hash_to_its_address")
 if receipt.get("receipt_sha256")!=cursor:raise RepoLedgerChainBreak(cursor,"stored_receipt_sha256_is_not_its_address")
 return receipt
def chain(target,head):
 """Every receipt reachable from `head`, newest first, each one verified."""
 if head is None:return
 # HEAD is only ever published naming a receipt; one that names none is not genesis.
 cursor=head.get("receipt_sha256") if isinstance(head,dict) else None
 if cursor is None:raise RepoLedgerChainBreak(None,"malformed_head")
 while cursor is not None:
  receipt=node(target,cursor);yield receipt
  cursor=receipt.get("previous_receipt_sha256")
# A transition occurring in this repository emits its receipt here. An
# in-process caller needs the same append the CLI performs, with the same lock
# and the same HEAD publication -- a second implementation of this would be a
# second writer to one store, which is the fork this lock exists to prevent.
def recorded(target,head,transition_id,transition_class):
 """The receipt this chain already holds for a transition, walking back from `head`.

 The whole chain is walked and verified even after a match, so an answer is
 never read off a chain that is broken further back.
 """
 found=None
 for receipt in chain(target,head):
  if found is None and receipt.get("transition_id")==transition_id and receipt.get("transition_class")==transition_class:found=receipt
 return found
_ABSENT=object()
EPOCH_RETRY_ENTRYPOINT=".stegverse/transition-ledger/emit.py::append (hb_epoch=, or --hb-epoch)"
RepoLedgerEpochRefused=kernel.SuppliedEpochRefused
def append(transition_id,transition_class,predecessor_state_sha256,successor_state_sha256,evidence=None,authority_effect="NONE",hb_epoch=None,store=None,idempotent_on=None):
 """Append one repository transition receipt through the substrate transaction.

 With `idempotent_on` (a tuple of evidence keys, possibly empty) a transition
 the chain already records is returned rather than minted again. Identity is
 the transition id and class; an exact retry must also carry the same
 predecessor state, successor state, authority effect and named evidence
 fields, or the call refuses with `ledger_receipt_collision` rather than
 calling a different transition a replay. The heartbeat reference is not
 compared: a retry legitimately arrives at another epoch. The lookup reads
 the chain at the HEAD the append compares against, so a writer that lands
 the same transition first makes this attempt lose the comparison, re-read,
 and return that writer's receipt.

 Every attempt, idempotent or not, first verifies the whole chain reachable
 from HEAD and raises `RepoLedgerChainBreak` on a missing or corrupted node,
 so no receipt is ever minted on top of a broken chain.

 `hb_epoch` is the epoch the caller supplies. An invalid one raises
 RepoLedgerEpochRefused (six-field FAIL_CLOSED) before the store is resolved
 or initialized. Absent, the reference is still derived from the host clock
 and says so; that fallback is WU-B13 slice g's to remove.
 """
 ref=kernel.supplied_hb_reference(hb_epoch,retry_entrypoint=EPOCH_RETRY_ENTRYPOINT) if hb_epoch is not None else kernel.hb_reference()
 target=store or repository_store();target.initialize()
 for _attempt in range(128):
  expected_head=target.get(ledger_store.HEAD_KEY)
  prev=(expected_head or {}).get("receipt_sha256")
  prior=recorded(target,expected_head,transition_id,transition_class)
  if idempotent_on is not None and prior is not None:
   mine=evidence if evidence is not None else {};theirs=prior.get("evidence")
   theirs=theirs if isinstance(theirs,dict) else {}
   if (prior.get("predecessor_state_sha256")!=predecessor_state_sha256
       or prior.get("successor_state_sha256")!=successor_state_sha256
       or prior.get("authority_effect")!=authority_effect
       or any(theirs.get(k,_ABSENT)!=mine.get(k,_ABSENT) for k in idempotent_on)):
    raise ValueError("ledger_receipt_collision")
   return prior
  b={"schema":"stegverse.repo-transition-receipt/v1","repository":C["repository"],"transition_id":transition_id,"transition_class":transition_class,"predecessor_state_sha256":predecessor_state_sha256,"successor_state_sha256":successor_state_sha256,"evidence":evidence if evidence is not None else {},"authority_effect":authority_effect,"hb_reference":ref,"previous_receipt_sha256":prev}
  dg=sha(b);r={**b,"receipt_sha256":dg};key=ledger_store.receipt_key(dg)
  new_head={"repository":C["repository"],"receipt_sha256":dg,"receipt_path":target.locator(key)}
  try: published=target.append_transaction(key,r,expected_head,new_head)
  except ledger_store.LedgerStoreRefused as exc:
   if exc.failed_predicate!=ledger_store.CAS_PREDICATE: raise
   published=False
  if published:
   return r
 raise SystemExit("REPO_LEDGER_APPEND_CONTENTION_EXHAUSTED")

def forwarded_epoch(receipt,hb_epoch):
 """The epoch an organization append consuming `receipt` is handed: the caller's.

 Never one read back from `receipt`. A read-back epoch is not supplied (absent,
 it is a clock reading), and carrying it would need CARRIED provenance the
 organization receipt does not record, so it would read as SUPPLIED. A replay
 completing a partial commit therefore takes the epoch its own caller supplies.
 """
 return hb_epoch

def cli_epoch(text,retry_entrypoint):
 """--hb-epoch as typed, checked by the kernel's supplied-epoch rule: (epoch, None) or (None, refusal).

 argparse hands over the raw text (type=str), so '+33', '\uff13\uff13', ' 33', 'True', '33.7'
 and '' reach supplied_epoch_failure uncoerced and are refused; nothing is
 appended. An omitted --hb-epoch stays None, as before.
 """
 if text is None:return None,None
 failure=kernel.supplied_epoch_failure(text)
 if failure is None:return int(text),None
 code,detail=failure
 return None,{"disposition":"FAIL_CLOSED","failure_code":code,"failed_predicate":kernel.HB_EPOCH_PREDICATE,"detail":detail,"required_evidence_or_repair":"pass --hb-epoch as the carrier supplied it: ASCII digits with value >= "+str(kernel.HB_ANCHOR_EPOCH)+"; it is never coerced","retry_entrypoint":retry_entrypoint+" (--hb-epoch)","owning_existing_goal":kernel.HB_EPOCH_OWNING_EXISTING_GOAL,"next_attempt":"run again with the supplied epoch; nothing was appended or written","consequence_committed":False,"authority_effect":"NONE_REFUSAL_ONLY"}

def main():
 p=argparse.ArgumentParser();p.add_argument("--transition-id",required=True);p.add_argument("--transition-class",required=True);p.add_argument("--predecessor-state-sha256",required=True);p.add_argument("--successor-state-sha256",required=True);p.add_argument("--evidence-json",default="{}");p.add_argument("--authority-effect",default="NONE");p.add_argument("--hb-epoch",type=str,default=None,help="carrier-supplied heartbeat epoch, ASCII digits >= 32; never coerced");p.add_argument("--idempotent-on",default=None,help="comma-separated evidence keys: an exact retry returns the recorded receipt");a=p.parse_args()
 hb_epoch,refused=cli_epoch(a.hb_epoch,".stegverse/transition-ledger/emit.py")
 if refused is not None:print(json.dumps(refused,sort_keys=True));raise SystemExit(1)
 try:r=append(a.transition_id,a.transition_class,a.predecessor_state_sha256,a.successor_state_sha256,kernel.cli_json_text(a.evidence_json,"--evidence-json",retry_entrypoint=".stegverse/transition-ledger/emit.py"),a.authority_effect,hb_epoch,idempotent_on=None if a.idempotent_on is None else tuple(k for k in a.idempotent_on.split(",") if k))
 except RepoLedgerChainBreak as exc:
  print(json.dumps(chain_break_refusal(exc),sort_keys=True));raise SystemExit(1)
 print(json.dumps(r,sort_keys=True))
if __name__=="__main__":raise SystemExit(kernel.run_writer_cli(lambda:main() or 0,retry_entrypoint=".stegverse/transition-ledger/emit.py"))
