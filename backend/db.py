import sqlite3
import os

DB_FILE = "cartalk.db"

def init_db():
    """Initialize database with schema"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name_en TEXT,
        name_ml TEXT,
        category TEXT,
        price REAL,
        stock INTEGER
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        customer_phone TEXT,
        customer_name TEXT,
        customer_address TEXT,
        total REAL,
        status TEXT,
        language TEXT,
        transcript TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY,
        order_id INTEGER,
        product_id INTEGER,
        quantity REAL,
        price REAL,
        FOREIGN KEY(order_id) REFERENCES orders(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    )''')
    
    # Seed sample data
    seed_products(conn)
    conn.commit()
    conn.close()

def seed_products(conn):
    """Add sample products"""
    c = conn.cursor()
    products = [
        ('Basmati Rice', 'പാസ്‌മതി അരി', 'Grains', 80.0, 50),
        ('Yellow Onions', 'മഞ്ഞ ഉള്ളി', 'Vegetables', 40.0, 100),
        ('Red Onions', 'ചുവന്ന ഉള്ളി', 'Vegetables', 50.0, 80),
        ('Green Chili', 'പച്ച മുളകി', 'Vegetables', 30.0, 60),
        ('Tomatoes', 'തക്കാളി', 'Vegetables', 35.0, 70),
        ('Coconut Oil', 'തെങ്ങ എണ്ണ', 'Oils', 150.0, 40),
        ('Turmeric Powder', 'ഞാണ്ടൽ പൊടി', 'Spices', 100.0, 25),
        ('Salt', 'ഉപ്പ്', 'Spices', 20.0, 200),
    ]
    # Check if products exist to avoid duplicates on restart (simple check)
    c.execute('SELECT count(*) FROM products')
    if c.fetchone()[0] == 0:
        c.executemany('INSERT INTO products (name_en, name_ml, category, price, stock) VALUES (?, ?, ?, ?, ?)', products)

def get_products():
    """Get all products"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, name_en, name_ml, price, stock FROM products')
    products = [{'id': row[0], 'name_en': row[1], 'name_ml': row[2], 'price': row[3], 'stock': row[4]} for row in c.fetchall()]
    conn.close()
    return products

def create_order(order_data):
    """Create new order"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO orders (customer_phone, customer_name, customer_address, total, status, language, transcript) VALUES (?, ?, ?, ?, ?, ?, ?)',
              (order_data.get('phone'), order_data.get('name'), order_data.get('address'), order_data.get('total'), 'completed', order_data.get('language'), order_data.get('transcript')))
    order_id = c.lastrowid
    
    # Add order items
    # order_data['items'] is expected to be a list of dicts with product_id, quantity, price
    for item in order_data.get('items', []):
        c.execute('INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)',
                  (order_id, item['product_id'], item['quantity'], item['price']))
    conn.commit()
    conn.close()
    return {'order_id': order_id, 'total': order_data.get('total')}

def get_orders():
    """Get all orders"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM orders ORDER BY created_at DESC')
    columns = [description[0] for description in c.description]
    orders = [dict(zip(columns, row)) for row in c.fetchall()]
    conn.close()
    return orders
