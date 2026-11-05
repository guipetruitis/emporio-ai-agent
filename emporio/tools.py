"""Allowlisted, validated tool dispatch and strict provider schemas."""


def schema(name, description, properties):
    return {'type':'function', 'name':name, 'description':description, 'strict':True,
            'parameters':{'type':'object','properties':properties,
                          'required':list(properties),'additionalProperties':False}}


SCHEMAS = [
    schema('search_products', 'Read catalog price, stock and active promotions. Use model names or a simple category, e.g. acoustic guitar. Monetary results are integer BRL cents.', {
        'query':{'type':'string'}, 'max_price_brl':{'type':['number','null']}, 'available_only':{'type':'boolean'}}),
    schema('search_policies', 'Retrieve original policy pages with English summaries. Use for address, hours, returns, payment, shipping, scope and ambiguity.', {'query':{'type':'string'}}),
    schema('get_order', 'Read order status in the trusted customer session. Never request identity or contact data in chat. Cannot confirm actual receipt.', {'order_id':{'type':'integer'}}),
    schema('handoff', 'Explain the prototype limits for unsupported, unrelated or ambiguous requests. Does not actually contact staff or create a ticket.', {'reason':{'type':'string'}}),
]


class Tools:
    def __init__(self, store, policies, customer_id=None):
        if customer_id is not None and (type(customer_id) is not int or customer_id < 1):
            raise ValueError('customer_id must be a positive integer.')
        self.store, self.policies, self.customer_id = store, policies, customer_id

    def execute(self, name, arguments):
        specs = {x['name']:x['parameters'] for x in SCHEMAS}
        if name not in specs:
            return {'error':'unknown_tool'}
        if not isinstance(arguments,dict) or set(arguments) != set(specs[name]['properties']):
            return {'error':'invalid_arguments'}
        for key, spec in specs[name]['properties'].items():
            expected=spec['type'] if isinstance(spec['type'],list) else [spec['type']]
            value=arguments[key]
            matches={'string':isinstance(value,str), 'number':type(value) in (int,float),
                     'integer':type(value) is int, 'boolean':type(value) is bool,
                     'null':value is None}
            if not any(matches[kind] for kind in expected):
                return {'error':'invalid_arguments'}
        try:
            if name == 'search_products':
                return self.store.search_products(**arguments)
            if name == 'search_policies':
                return self.policies.search(**arguments)
            if name == 'get_order':
                return self.store.get_order(arguments['order_id'],self.customer_id)
            reason = arguments['reason']
            if not isinstance(reason,str) or not 1 <= len(reason) <= 300:
                raise ValueError('Invalid handoff reason.')
            return {'message':'I can help with musical instruments and store policies. For this request, please speak with the store team. No ticket has been created.'}
        except (ValueError,TypeError):
            return {'error':'invalid_arguments', 'message':'Check the tool argument types and supported ranges.'}
