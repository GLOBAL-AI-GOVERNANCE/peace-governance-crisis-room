from __future__ import annotations
import hashlib, json, unittest

def canonical(value):
    if isinstance(value,dict):
        return '{'+','.join(json.dumps(str(k),separators=(',',':'))+':'+canonical(value[k]) for k in sorted(value))+'}'
    if isinstance(value,list): return '['+','.join(canonical(x) for x in value)+']'
    if value is True: return 'true'
    if value is False: return 'false'
    if value is None: return 'null'
    if isinstance(value,str): return json.dumps(value,separators=(',',':'))
    return str(value)

def digest(value): return hashlib.sha256(canonical(value).encode()).hexdigest()

class DecisionDigestContractTests(unittest.TestCase):
    def test_key_order_does_not_change_digest(self):
        self.assertEqual(digest({'b':2,'a':1}),digest({'a':1,'b':2}))

    def test_material_change_changes_digest(self):
        base={'scenario_id':'s1','confidence':'Unverified','human_confirmation':True}
        changed=dict(base); changed['confidence']='Confirmed'
        self.assertNotEqual(digest(base),digest(changed))

    def test_digest_is_sha256_hex(self):
        value=digest({'a':1})
        self.assertEqual(len(value),64)
        int(value,16)

if __name__=='__main__': unittest.main()
