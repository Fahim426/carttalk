import sqlite3
import json
conn = sqlite3.connect('cartalk.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute('SELECT id, status, total FROM orders')
rows = [dict(r) for r in c.fetchall()]
with open('debug_orders.json', 'w') as f:
    json.dump(rows, f)
