"""Bounded PE-01..PE-08 model fixtures; not physical or cross-repo certification."""
import hashlib,json,unittest
def h(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def record(states,receipts,start=True,finish=True,emitter=None,clocks=None):
    edges=[{'index':i,'from':states[i],'to':states[i+1]} for i in range(len(states)-1)]
    return {'edges':edges,'valid':bool(start and finish and receipts==[h(e) for e in edges]),'emitter':emitter,'clocks':clocks or {}}
def derived(source,gaps,method):
    return {'id':h([source,gaps,method]),'source':source,'gaps':gaps,'method':method,'original_complete':False}
def decision(origin_proven,publication_allowed,execution_authorized=False):
    return {'origin':'ALLOW' if origin_proven else 'DENY','publication':'ALLOW' if publication_allowed else 'DENY','execute':bool(publication_allowed and execution_authorized)}
class PEFixtures(unittest.TestCase):
    def setUp(self):
        self.states=['s0','s1','s2']
        self.receipts=[h({'index':i,'from':self.states[i],'to':self.states[i+1]}) for i in range(2)]
    def test_PE_01(self):
        r=record(self.states,self.receipts);self.assertTrue(r['valid']);self.assertEqual(len(r['edges']),2)
    def test_PE_02(self):
        r=record(self.states,self.receipts);self.assertTrue(r['valid']);self.assertIsNone(r['emitter']);self.assertEqual(decision(False,True)['origin'],'DENY')
    def test_PE_03(self):
        clocks={'device':100,'system':200,'hb':3,'uncertainty':150}
        r=record(self.states,self.receipts,clocks=clocks);self.assertTrue(r['valid']);self.assertEqual(r['clocks'],clocks);self.assertNotEqual(clocks['device'],clocks['system'])
    def test_PE_04(self):
        self.assertFalse(record(self.states,self.receipts[:1])['valid']);self.assertFalse(derived('source',[1],'interpolation')['original_complete'])
    def test_PE_05(self):
        self.assertTrue(record(self.states,self.receipts)['valid']);self.assertEqual(decision(True,False)['publication'],'DENY')
    def test_PE_06(self):
        p=derived('original',[1],'interpolation');self.assertNotEqual(p['id'],p['source']);self.assertFalse(p['original_complete']);self.assertEqual(p['gaps'],[1])
    def test_PE_07(self):
        a={'id':'a','ancestor':'root'};b={'id':'b','ancestor':'root'};self.assertNotEqual(a['id'],b['id']);self.assertEqual(a['ancestor'],b['ancestor'])
    def test_PE_08(self):
        g=decision(True,True,False);self.assertEqual(g['publication'],'ALLOW');self.assertFalse(g['execute'])
if __name__=='__main__':unittest.main(verbosity=2)
