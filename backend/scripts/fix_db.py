import sqlite3
import json

db_file = 'cartalk.db'
conn = sqlite3.connect(db_file)
c = conn.cursor()

# Get product prices
c.execute('SELECT id, price FROM products')
prices = {p[0]: p[1] for p in c.fetchall()}

# Get all order_items and update their price if missing or 0
c.execute('SELECT id, order_id, product_id, quantity FROM order_items')
items = c.fetchall()

for item in items:
    # item[0]=id, item[1]=order_id, item[2]=product_id, item[3]=quantity
    pid = item[2]
    pr = prices.get(pid, 0)
    c.execute('UPDATE order_items SET price = ? WHERE id = ?', (pr, item[0]))

# Update the order total based on order_items
c.execute('SELECT id FROM orders')
orders = c.fetchall()

for o in orders:
    oid = o[0]
    c.execute('SELECT SUM(price * quantity) FROM order_items WHERE order_id = ?', (oid,))
    total = c.fetchone()[0] or 0.0
    c.execute('UPDATE orders SET total = ? WHERE id = ?', (total, oid))

conn.commit()
conn.close()
print("Fixed DB prices and totals!")
