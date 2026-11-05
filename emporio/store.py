"""Read-only business operations. The model never receives a SQL interface."""
import csv
import json
import re
import sqlite3
import unicodedata
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

SNAPSHOT = 'Supplied CSV snapshot; not a live ERP or carrier feed.'


def normalize(text: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', text.lower())
                   if not unicodedata.combining(c))


def cents(value) -> int:
    if isinstance(value, bool):
        raise ValueError('Expected a finite non-negative monetary amount.')
    try:
        amount = Decimal(str(value))
        if not amount.is_finite() or amount < 0 or amount > 100000000:
            raise ValueError('Monetary amount is outside the supported range.')
        return int((amount * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    except (InvalidOperation, TypeError) as exc:
        raise ValueError('Expected a finite non-negative monetary amount.') from exc


ALIASES = {
    'acoustic guitar': 5, 'acoustic guitars': 5, 'classical guitar': 5,
    'violao': 5, 'violoes': 5, 'electric guitar': 1, 'electric guitars': 1,
    'guitarra': 1, 'guitarras': 1, 'bass': 2, 'baixo': 2,
    'drums': 3, 'bateria': 3, 'keyboard': 4, 'piano': 4,
    'woodwind': 6, 'brass': 7, 'violin': 8, 'violino': 8, 'ukulele': 9,
}


class Store:
    def __init__(self, data_dir: Path):
        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
            CREATE TABLE categories(id INTEGER PRIMARY KEY, name TEXT);
            CREATE TABLE products(id INTEGER PRIMARY KEY, name TEXT, category_id INTEGER,
                price INTEGER, stock INTEGER, status TEXT, description TEXT, specs TEXT, search TEXT);
            CREATE TABLE promotions(id INTEGER PRIMARY KEY, product_id INTEGER,
                discount INTEGER CHECK(discount BETWEEN 0 AND 100), active INTEGER);
            CREATE TABLE orders(id INTEGER PRIMARY KEY, customer_id INTEGER, status TEXT,
                total INTEGER, order_date TEXT, estimated_delivery TEXT, tracking TEXT);
            CREATE TABLE items(order_id INTEGER, product_id INTEGER, quantity INTEGER);
        ''')
        def rows(name):
            with (Path(data_dir) / f'{name}.csv').open(encoding='utf-8-sig', newline='') as f:
                return list(csv.DictReader(f))
        with self.db:
            self.db.executemany('INSERT INTO categories VALUES (?, ?)',
                [(int(r['category_id']), r['name']) for r in rows('categories')])
            self.db.executemany('INSERT INTO products VALUES (?,?,?,?,?,?,?,?,?)', [
                (int(r['product_id']), r['name'], int(r['category_id']), cents(r['price_brl']),
                 int(r['stock_quantity']), r['status'], r['description'], r['specs'],
                 normalize(r['name'] + ' ' + r['description'])) for r in rows('products')])
            self.db.executemany('INSERT INTO promotions VALUES (?,?,?,?)', [
                (int(r['promotion_id']), int(r['product_id']), int(r['discount_percent']),
                 int(r['is_active'])) for r in rows('promotions')])
            self.db.executemany('INSERT INTO orders VALUES (?,?,?,?,?,?,?)', [
                (int(r['order_id']), int(r['customer_id']), r['status'], cents(r['total_brl']),
                 r['order_date'], r['estimated_delivery'] or None, r['tracking_code'] or None)
                for r in rows('orders')])
            self.db.executemany('INSERT INTO items VALUES (?,?,?)', [
                (int(r['order_id']), int(r['product_id']), int(r['quantity'])) for r in rows('order_items')])
        self.db.execute('PRAGMA query_only = ON')

    def search_products(self, query: str, max_price_brl=None, available_only=True) -> dict:
        if not isinstance(query, str) or not 1 <= len(query.strip()) <= 200:
            raise ValueError('Search query must contain 1 to 200 characters.')
        if not isinstance(available_only, bool):
            raise ValueError('available_only must be boolean.')
        budget = cents(max_price_brl) if max_price_brl is not None else None
        query = normalize(query.strip())
        conditions, params = [], []
        if query in ALIASES:
            conditions.append('p.category_id = ?')
            params.append(ALIASES[query])
        else:
            for token in query.split():
                conditions.append("p.search LIKE ? ESCAPE '\\'")
                params.append('%' + token.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%')
        if available_only:
            conditions.append("p.status = 'active' AND p.stock > 0")
        sql = '''SELECT p.*, c.name category, COALESCE(MAX(CASE WHEN pr.active = 1
                 THEN pr.discount ELSE 0 END), 0) discount
                 FROM products p JOIN categories c ON c.id = p.category_id
                 LEFT JOIN promotions pr ON pr.product_id = p.id WHERE '''
        rows = self.db.execute(sql + ' AND '.join(conditions) + ' GROUP BY p.id', params)
        products = []
        for r in rows:
            discount = r['discount']
            effective = int((Decimal(r['price']) * (100-discount)/100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
            pix = effective if discount else int((Decimal(effective) * Decimal('.95')).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
            if budget is not None and effective > budget:
                continue
            products.append({'product_id':r['id'], 'name':r['name'], 'category_id':r['category_id'],
                'category':r['category'], 'list_price_cents':r['price'], 'effective_price_cents':effective,
                'discount_percent':discount, 'pix_price_cents':pix, 'stock_quantity':r['stock'],
                'status':r['status'], 'available':r['status']=='active' and r['stock']>0,
                'description':r['description'], 'specs':json.loads(r['specs'])})
        products.sort(key=lambda p:(p['effective_price_cents'],p['product_id']))
        return {'products':products[:8], 'total_matches':len(products),
                'source':'products.csv + categories.csv + promotions.csv; PIX rule: policy p. 3, 6',
                'freshness':SNAPSHOT}

    def get_order(self, order_id: int, customer_id: int | None) -> dict:
        if type(order_id) is not int or order_id < 1:
            raise ValueError('order_id must be a positive integer.')
        if customer_id is None:
            return {'error':'identity_required', 'message':'Use a trusted customer session; do not send personal details in chat.'}
        r = self.db.execute('SELECT * FROM orders WHERE id=? AND customer_id=?',
                            (order_id,customer_id)).fetchone()
        if r is None:
            return {'error':'order_unavailable', 'message':'This order is unavailable in the current customer session.'}
        items = [dict(x) for x in self.db.execute('''SELECT i.product_id, p.name, i.quantity
                 FROM items i JOIN products p ON p.id=i.product_id WHERE i.order_id=?''',(order_id,))]
        return {'order':{'order_id':r['id'], 'status':r['status'], 'total_cents':r['total'],
                'order_date':r['order_date'], 'estimated_delivery':r['estimated_delivery'],
                'tracking_code':r['tracking'], 'items':items}, 'source':'orders.csv + order_items.csv + products.csv',
                'freshness':SNAPSHOT, 'warning':'Estimated delivery is not proof of receipt. This is not live carrier tracking.'}

    def close(self):
        self.db.close()
