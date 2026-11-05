"""Run the real OpenAI SDK over a local in-memory HTTP transport, never the network."""
import importlib.util
import json
import unittest
from pathlib import Path
from emporio.agent import Agent
from emporio.policies import Policies
from emporio.store import Store
from emporio.tools import Tools


@unittest.skipUnless(importlib.util.find_spec('openai'), 'Install requirements-live.txt for the SDK contract test')
class SdkContractTests(unittest.TestCase):
    def test_real_sdk_serializes_function_output_and_parses_final_message(self):
        import httpx
        from openai import OpenAI
        data=Path(__file__).resolve().parents[1]/'data'
        requests=[]
        def handle(request):
            payload=json.loads(request.content)
            requests.append(payload)
            if len(requests)==1:
                output=[{'id':'fc_1','type':'function_call','status':'completed',
                    'call_id':'call_1','name':'search_products',
                    'arguments':'{"query":"Yamaha C40","max_price_brl":null,"available_only":false}'}]
            else:
                output=[{'id':'msg_1','type':'message','status':'completed','role':'assistant',
                    'content':[{'type':'output_text','text':'Yamaha C40: BRL 599.90. [products.csv]', 'annotations':[]}]}]
            return httpx.Response(200,json={'id':f'resp_{len(requests)}','object':'response',
                'created_at':0,'status':'completed','model':'contract-test-model','output':output})
        store=Store(data)
        try:
            with OpenAI(api_key='local-test-placeholder', max_retries=0,
                        http_client=httpx.Client(transport=httpx.MockTransport(handle))) as client:
                result=Agent(Tools(store,Policies(data)),client,'contract-test-model').reply('Yamaha C40 price?')
            self.assertIsNone(result.error)
            self.assertIn('599.90',result.answer)
            tool_outputs=[x for x in requests[1]['input'] if x.get('type')=='function_call_output']
            evidence=json.loads(tool_outputs[0]['output'])
            self.assertEqual(evidence['products'][0]['list_price_cents'],59990)
            self.assertFalse(requests[0]['store'])
        finally:
            store.close()
