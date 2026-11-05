"""Behavioral checks against the supplied fixtures, without an LLM."""
import json
import unittest
from pathlib import Path

from emporio.store import Store
from emporio.policies import Policies
from emporio.tools import Tools

DATA = Path(__file__).resolve().parents[1] / 'data'


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(DATA)
        self.policies = Policies(DATA)
        self.tools = Tools(self.store, self.policies, customer_id=3)

    def tearDown(self):
        self.store.close()

    def test_catalog_budget_and_stock(self):
        rows = self.store.search_products('acoustic guitar', 1000, True)['products']
        self.assertTrue(rows)
        self.assertTrue(all(p['category_id'] == 5 for p in rows))
        self.assertTrue(all(p['effective_price_cents'] <= 100000 and p['available'] for p in rows))
        yamaha = self.store.search_products('Yamaha C40', None, False)['products'][0]
        self.assertEqual(yamaha['list_price_cents'], 59990)
        self.assertEqual(yamaha['stock_quantity'], 12)

    def test_active_promotion_applied_without_pix_stacking(self):
        product = self.store.search_products('Crafter HT-100', None, False)['products'][0]
        self.assertEqual(product['product_id'], 90)
        self.assertEqual(product['discount_percent'], 18)
        self.assertEqual(product['effective_price_cents'], 196718)
        self.assertEqual(product['pix_price_cents'], 196718)

    def test_expired_promotion_not_applied(self):
        product = self.store.search_products('Martin D-28', None, False)['products'][0]
        self.assertEqual(product['discount_percent'], 0)

    def test_sql_payload_does_not_expand_results(self):
        self.assertEqual(self.store.search_products("' OR 1=1 --", None, False)['products'], [])
        self.assertTrue(self.store.search_products('Yamaha', None, False)['products'])

    def test_budget_invalid_values_rejected(self):
        for value in [-1, float('nan'), float('inf'), True]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.store.search_products('Yamaha', value, True)

    def test_order_scope_is_enforced_and_minimized(self):
        result = self.store.get_order(1, 3)
        self.assertEqual(result['order']['status'], 'delivered')
        self.assertNotIn('customer_id', result['order'])
        self.assertNotIn('notes', result['order'])
        self.assertNotIn('received_at', result['order'])
        self.assertEqual(self.store.get_order(1, 7), self.store.get_order(999, 7))
        self.assertEqual(self.store.get_order(1, None)['error'], 'identity_required')

    def test_model_cannot_supply_customer_identity(self):
        result = self.tools.execute('get_order', {'order_id': 1, 'customer_id': 7})
        self.assertEqual(result['error'], 'invalid_arguments')

    def test_policy_retrieval_bilingual_and_unknown(self):
        for query in ['return online purchase', 'devolver compra online']:
            with self.subTest(query=query):
                hit = self.policies.search(query)['matches'][0]
                self.assertEqual(hit['id'], 'returns')
                self.assertIn('7', hit['summary_en'])
                self.assertEqual(hit['pages'], [4])
                self.assertIn('arrependimento', hit['original_text'].lower())
        self.assertEqual(self.policies.search('quantum spacetime')['matches'], [])

    def test_policy_ambiguities_are_visible(self):
        hit = self.policies.search('phone whatsapp')['matches'][0]
        self.assertIn('3341', hit['summary_en'])
        self.assertIn('3321', hit['summary_en'])
        self.assertTrue(hit['requires_confirmation'])

    def test_tool_validation_and_unknown_tool(self):
        for name,args in [('execute_sql', {'sql':'select *'}), ('get_order', {'order_id':True}),
                          ('search_products', {'query':12,'max_price_brl':None,'available_only':True})]:
            with self.subTest(name=name):
                self.assertIn('error', self.tools.execute(name,args))
        self.assertNotIn('phone', json.dumps(self.tools.execute('get_order', {'order_id':1})))

    def test_non_active_products_are_never_purchasable(self):
        for query in ['Shelby SN-7C','KA-ABP-CTG','Giannini GF-3D']:
            with self.subTest(query=query):
                p=self.store.search_products(query,None,False)['products'][0]
                self.assertFalse(p['available'])
                self.assertEqual(self.store.search_products(query,None,True)['products'],[])

    def test_effective_price_budget_includes_exact_boundary(self):
        rows=self.store.search_products('Kalani KAL-700T',323.10,True)['products']
        self.assertEqual(rows[0]['effective_price_cents'],32310)
        self.assertEqual(self.store.search_products('Kalani KAL-700T',323.09,True)['products'],[])

    def test_model_cannot_send_numeric_string_as_budget(self):
        result=self.tools.execute('search_products',{'query':'Yamaha','max_price_brl':'1000','available_only':True})
        self.assertEqual(result['error'],'invalid_arguments')


if __name__ == '__main__':
    unittest.main()
