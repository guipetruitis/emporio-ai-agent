"""Deterministic demonstration, explicitly not an LLM or a general language agent."""
import re
from .agent import Reply, valid_message
from .store import ALIASES, normalize


def money(value):
    return f'BRL {value/100:,.2f}'


class DemoAgent:
    def __init__(self, tools):
        self.tools = tools
        self.last_product_query = None

    def reset(self):
        self.last_product_query = None

    def reply(self, message):
        if not valid_message(message):
            return Reply('Please send a message containing 1 to 3,000 characters.',error='invalid_message')
        text = normalize(message)
        trace = []
        def execute(name,arguments):
            result=self.tools.execute(name,arguments)
            trace.append({'tool':name,'result':result})
            return result
        if text.strip(' !?.') in ('hi','hello','ola','hey'):
            return Reply('Hi! Your music starts here. I can help with instruments, store policies or an order. What are you looking for?')
        if re.search(r'\b(strings|cables|picks|pedals|amplifiers|cases|cordas|cabos|palhetas|pedais|amplificadores)\b',text):
            result=execute('search_policies',{'query':'scope accessories'})
            return Reply('We specialize in musical instruments and do not sell accessories. Please ask the team for a suitable retailer. [Store policy, p. 2, 6]',trace)
        order_match=re.search(r'\b(?:order|pedido)\s*#?\s*(\d+)\b',text)
        if order_match:
            result=execute('get_order',{'order_id':int(order_match[1])})
            if 'error' in result:
                return Reply(result['message'],trace)
            order=result['order']
            answer=f"Order {order['order_id']} is {order['status']} in the supplied snapshot. Total: {money(order['total_cents'])}."
            if order['tracking_code']:
                answer+=f" Recorded tracking code: {order['tracking_code']}."
            if order['estimated_delivery']:
                answer+=f" Recorded estimated delivery: {order['estimated_delivery']}; this is not proof of receipt or a current delivery promise."
            answer+=' [orders.csv; not live carrier tracking]'
            if any(word in text for word in ['return','refund','devol','arrepend']):
                policy=execute('search_policies',{'query':'return online purchase'})['matches'][0]
                answer+='\n'+policy['summary_en']+' [Store policy, p. 4]'
            return Reply(answer,trace)
        policy_question=bool(re.search(r'\b(combine|stack|cumulative|combinar|cumulativo)\b',text))
        followup=bool(self.last_product_query and not policy_question and re.search(r'\b(pix|discount|desconto)\b',text))
        brand=re.search(r'\b(yamaha|takamine|tagima|giannini|crafter|martin|taylor|shelby|kala|kalani|ohana|ibanez|fender|roland|casio|korg)\b',text)
        category=next((key for key in sorted(ALIASES,key=len,reverse=True)
                       if re.search(r'\b'+re.escape(key)+r'\b',text)),None)
        if followup or brand or category:
            query=self.last_product_query if followup else category
            if brand:
                tail=text[brand.start():]
                tokens=re.findall(r'[a-z0-9-]+',tail)
                ignored={'cost','price','available','availability','stock','the','in','is','do','you','have','quanto','custa','preco'}
                keep=[]
                for token in tokens:
                    if token in ignored: break
                    keep.append(token)
                    if len(keep)==2: break
                query=' '.join(keep)
            budget_match=re.search(r'(?:under|below|up to|ate|budget)\s*(?:brl|r\$)?\s*(\d+(?:[.,]\d{1,2})?)',text)
            budget=float(budget_match[1].replace(',','.')) if budget_match else None
            result=execute('search_products',{'query':query,'max_price_brl':budget,'available_only':not bool(brand or followup)})
            self.last_product_query=query
            if not result.get('products'):
                return Reply('No matching products were found in the supplied snapshot. Try a model name or a category such as acoustic guitar. [products.csv]',trace)
            lines=['Here is what I found in the supplied catalog snapshot:']
            for p in result['products']:
                state=f"in stock ({p['stock_quantity']})" if p['available'] else f"not purchasable ({p['status']}; recorded stock {p['stock_quantity']})"
                line=f"- {p['name']}: {money(p['effective_price_cents'])}; {state}."
                if p['discount_percent']:
                    line+=f" List {money(p['list_price_cents'])}, {p['discount_percent']}% active discount. PIX is not cumulative."
                else:
                    line+=f" PIX: {money(p['pix_price_cents'])} (5% off list; no active promotion)."
                lines.append(line)
            if result['total_matches']>len(result['products']):
                lines.append(f"Showing {len(result['products'])} of {result['total_matches']} matches; narrow your search for more.")
            lines.append('[products.csv + promotions.csv; PIX policy, p. 3, 6. Not live inventory.]')
            return Reply('\n'.join(lines),trace)
        result=execute('search_policies',{'query':message[:300]})
        if result.get('matches'):
            hit=result['matches'][0]
            answer=hit['summary_en']+' [Store policy, p. '+', '.join(map(str,hit['pages']))+']'
            if hit['id']=='returns':
                answer+=' Was this an online purchase, when did you actually receive it, and is it unused in the original packaging?'
            return Reply(answer,trace)
        result=execute('handoff',{'reason':'Unsupported demo request'})
        return Reply(result['message']+' The offline demo understands only a small set of patterns; use --mode openai for flexible conversation.',trace)
