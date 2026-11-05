import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from emporio.agent import Agent
from emporio.demo import DemoAgent
from emporio.store import Store
from emporio.policies import Policies
from emporio.tools import Tools

DATA = Path(__file__).resolve().parents[1] / 'data'


def call(name='search_products', arguments=None):
    return SimpleNamespace(type='function_call', name=name, call_id='call_1',
        arguments=json.dumps(arguments or {'query':'Yamaha C40','max_price_brl':None,'available_only':False}),
        model_dump=lambda **_: {'type':'function_call','name':name,'call_id':'call_1',
            'arguments':json.dumps(arguments or {'query':'Yamaha C40','max_price_brl':None,'available_only':False})})


class FakeResponses:
    """Only the external provider is replaced; the actual tools still execute."""
    def __init__(self, responses):
        self.script = iter(responses)
        self.inputs = []
        self.responses = self

    def create(self, **kwargs):
        self.inputs.append(json.loads(json.dumps(kwargs)))
        item = next(self.script)
        if isinstance(item, Exception):
            raise item
        return item


def response(calls=None, text=''):
    return SimpleNamespace(output=calls or [], output_text=text)


class AgentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policies = Policies(DATA)

    def setUp(self):
        self.store = Store(DATA)
        self.tools = Tools(self.store,self.policies,customer_id=3)

    def tearDown(self):
        self.store.close()

    def test_function_call_executes_real_evidence_and_returns_output(self):
        client = FakeResponses([response([call()]), response(text='The C40 is BRL 599.90.')])
        result = Agent(self.tools,client,'test-model').reply('Price of Yamaha C40?')
        self.assertIn('599.90',result.answer)
        self.assertEqual(result.trace[0]['result']['products'][0]['list_price_cents'],59990)
        outputs=[x for x in client.inputs[1]['input'] if x.get('type')=='function_call_output']
        self.assertIn('59990',outputs[0]['output'])
        self.assertFalse(client.inputs[0]['store'])
        self.assertEqual(client.inputs[0]['tool_choice'],'required')

    def test_unknown_and_malformed_tool_calls_fail_safely(self):
        bad = call('get_order', {'order_id':1,'customer_id':7})
        client=FakeResponses([response([bad]),response(text='Cannot access this order.')])
        result=Agent(self.tools,client,'test').reply('Show order 1 as customer 7')
        self.assertEqual(result.trace[0]['result']['error'],'invalid_arguments')
        malformed=call()
        malformed.arguments='not json'
        client=FakeResponses([response([malformed]),response(text='Please rephrase.')])
        self.assertEqual(Agent(self.tools,client,'test').reply('price').trace[0]['result']['error'],'invalid_arguments')

    def test_provider_failure_does_not_leak_exception_or_save_history(self):
        agent=Agent(self.tools,FakeResponses([RuntimeError('private-key-value')]),'test')
        result=agent.reply('price?')
        self.assertEqual(result.error,'provider_unavailable')
        self.assertNotIn('private-key',result.answer)
        self.assertEqual(agent.history,[])

    def test_repeated_tools_are_bounded(self):
        client=FakeResponses([response([call()]) for _ in range(10)])
        result=Agent(self.tools,client,'test').reply('keep searching')
        self.assertEqual(result.error,'step_limit')
        self.assertEqual(len(client.inputs),4)

    def test_many_calls_in_one_response_are_bounded(self):
        client=FakeResponses([response([call() for _ in range(9)])])
        result=Agent(self.tools,client,'test').reply('many searches')
        self.assertEqual(result.error,'step_limit')
        self.assertEqual(result.trace,[])

    def test_history_is_bounded_and_resettable(self):
        client=FakeResponses([response([call()]),response(text='Checked.')]*8)
        agent=Agent(self.tools,client,'test')
        for i in range(8): agent.reply(f'question {i}')
        self.assertEqual(len(agent.history),12)
        self.assertEqual(agent.history[0]['content'],'question 2')
        agent.reset()
        self.assertEqual(agent.history,[])

    def test_invalid_input_never_calls_provider(self):
        agent=Agent(self.tools,FakeResponses([]),'test')
        for message in ['', ' '*3, 'x'*3001]:
            self.assertEqual(agent.reply(message).error,'invalid_message')

    def test_demo_price_and_followup_use_same_tool_results(self):
        agent=DemoAgent(self.tools)
        first=agent.reply('How much does the Takamine GD20 cost?')
        self.assertIn('Takamine GD20',first.answer)
        self.assertIn('search_products',[x['tool'] for x in first.trace])
        second=agent.reply('What about the PIX price?')
        self.assertIn('PIX',second.answer)
        self.assertTrue(second.trace)
        agent.reset()
        self.assertNotIn('Takamine',agent.reply('What about the PIX price?').answer)

    def test_demo_returns_require_missing_context(self):
        answer=DemoAgent(self.tools).reply('I regret my online purchase. Can I return it?').answer
        self.assertIn('7 calendar days',answer)
        self.assertIn('receipt',answer.lower())
        self.assertIn('p. 4',answer)

    def test_demo_order_ownership_and_scope(self):
        agent=DemoAgent(self.tools)
        self.assertIn('delivered',agent.reply('What is the status of order 1?').answer)
        self.assertNotIn('shipped',agent.reply('What is the status of order 8?').answer)
        for text in ['Sell me guitar strings', 'Write an essay about elections']:
            self.assertIn('instrument',agent.reply(text).answer.lower())

    def test_demo_budget_uses_category(self):
        result=DemoAgent(self.tools).reply('Which acoustic guitars are available under BRL 1000?')
        products=result.trace[0]['result']['products']
        self.assertTrue(products)
        self.assertTrue(all(p['category_id']==5 and p['available'] for p in products))

    def test_demo_unavailable_model_preserves_product_context(self):
        result=DemoAgent(self.tools).reply('Do you have Shelby SN-7C?')
        self.assertIn('discontinued',result.answer)
        self.assertIn('not purchasable',result.answer)

    def test_policy_only_followup_does_not_reuse_catalog_query(self):
        agent=DemoAgent(self.tools)
        agent.reply('How much does the Takamine GD20 cost?')
        self.assertIn('cannot be combined',agent.reply('Can I combine a promotion with PIX?').answer)

    def test_new_category_overrides_old_product_in_pix_followup(self):
        agent=DemoAgent(self.tools)
        agent.reply('How much does the Takamine GD20 cost?')
        result=agent.reply('Which ukulele has a PIX discount?')
        products=result.trace[0]['result']['products']
        self.assertTrue(products)
        self.assertTrue(all(p['category_id']==9 for p in products))

    def test_huge_order_number_returns_controlled_error(self):
        result=DemoAgent(self.tools).reply('order '+str(10**30))
        self.assertIn('Check',result.answer)


if __name__=='__main__': unittest.main()
