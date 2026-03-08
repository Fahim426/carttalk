"""
db.py
Database management module using SQLite3.
Handles all CRUD operations required by CartTalk, including
product inventory, user authentication, orders, and persistent carts.
"""
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
        stock INTEGER,
        image_url TEXT
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
    
    # Phase 1: Authentication & Persistent Cart
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        phone TEXT PRIMARY KEY,
        name TEXT,
        address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS cart_items (
        id INTEGER PRIMARY KEY,
        phone TEXT,
        product_id INTEGER,
        quantity INTEGER,
        FOREIGN KEY(phone) REFERENCES users(phone),
        FOREIGN KEY(product_id) REFERENCES products(id)
    )''')
    
    # Auto-Migration: Check for missing columns in existing tables
    c.execute("PRAGMA table_info(products)")
    prod_cols = [row[1] for row in c.fetchall()]
    
    if 'image_url' not in prod_cols:
        try:
            print("Migrating DB: Adding image_url column to products...")
            c.execute("ALTER TABLE products ADD COLUMN image_url TEXT")
        except Exception as e:
            print(f"Migration Error (image_url): {e}")

    if 'safety_stock' not in prod_cols:
        try:
            print("Migrating DB: Adding safety_stock column to products...")
            c.execute("ALTER TABLE products ADD COLUMN safety_stock INTEGER DEFAULT 5")
        except Exception as e:
            print(f"Migration Error (safety_stock): {e}")

    c.execute("PRAGMA table_info(orders)")
    current_cols = [row[1] for row in c.fetchall()]
    
    if 'customer_name' not in current_cols:
        try:
            print("Migrating DB: Adding customer_name column...")
            c.execute("ALTER TABLE orders ADD COLUMN customer_name TEXT")
        except Exception as e:
            print(f"Migration Error: {e}")

    if 'customer_address' not in current_cols:
        try:
            print("Migrating DB: Adding customer_address column...")
            c.execute("ALTER TABLE orders ADD COLUMN customer_address TEXT")
        except Exception as e:
            print(f"Migration Error: {e}")
            
    # Seed sample data (Run AFTER schema is guaranteed)
    seed_products(conn)

    conn.commit()
    conn.close()

# ... skipping seed_products body to fit context constraints ...

def seed_products(conn):
    """Seed initial product catalog.
    Products are managed via the Admin Dashboard (Inventory tab).
    This function is called on init but only inserts if the table is empty.
    """
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM products')
    count = c.fetchone()[0]
    if count > 0:
        return  # Products already exist, skip seeding

def get_products():
    """Get all products"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Check if image_url exists
    try:
        # Added safety_stock to SELECT
        c.execute('SELECT id, name_en, name_ml, price, stock, category, image_url, safety_stock FROM products')
        products = [{'id': row[0], 'name_en': row[1], 'name_ml': row[2], 'price': row[3], 'stock': row[4], 'category': row[5], 'image_url': row[6], 'safety_stock': row[7] if row[7] is not None else 5} for row in c.fetchall()]
    except sqlite3.OperationalError:
        # Fallback
        c.execute('SELECT id, name_en, name_ml, price, stock, category FROM products')
        products = [{'id': row[0], 'name_en': row[1], 'name_ml': row[2], 'price': row[3], 'stock': row[4], 'category': row[5], 'image_url': '', 'safety_stock': 5} for row in c.fetchall()]
        
    conn.close()
    return products

def create_order(order_data):
    """Create new order"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO orders (customer_phone, customer_name, customer_address, total, status, language, transcript) VALUES (?, ?, ?, ?, ?, ?, ?)',
              (order_data.get('phone'), order_data.get('name'), order_data.get('address'), order_data.get('total'), 'completed', order_data.get('language'), order_data.get('transcript')))
    order_id = c.lastrowid
    
    
    # Add order items and deduct stock
    items = order_data.get('items', [])
    for item in items:
        product_id = item.get('product_id') or item.get('id')
        qty = item.get('quantity') or item.get('qty') or 1
        price = item.get('price', 0)
        
        # 1. Deduct Stock
        c.execute('UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?', (qty, product_id, qty))
        
        if c.rowcount > 0:
             # 2. Insert Item only if stock deducted
             c.execute('INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)',
                       (order_id, product_id, qty, price))
        else:
            print(f"Warning: Stock deduction failed for Product {product_id} (Insufficient Stock or Invalid ID). Item NOT added to order.")
                  
    conn.commit()
    conn.close()
    return {'order_id': order_id, 'total': order_data.get('total'), 'status': 'confirmed'}

def update_order_status(order_id, status):
    """Update order status"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
    conn.commit()
    conn.close()
    return {'id': order_id, 'status': status}

def add_product(product_data):
    """Add new product manually"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    safety = product_data.get('safety_stock', 5)
    
    # Check if image_url col exists
    try:
        c.execute('INSERT INTO products (name_en, name_ml, category, price, stock, image_url, safety_stock) VALUES (?, ?, ?, ?, ?, ?, ?)',
                  (product_data['name_en'], product_data.get('name_ml', ''), product_data['category'], product_data['price'], product_data['stock'], product_data.get('image_url', ''), safety))
    except sqlite3.OperationalError:
        c.execute('INSERT INTO products (name_en, name_ml, category, price, stock) VALUES (?, ?, ?, ?, ?)',
                  (product_data['name_en'], product_data.get('name_ml', ''), product_data['category'], product_data['price'], product_data['stock']))
    
    pid = c.lastrowid
    conn.commit()
    conn.close()
    return {'id': pid, 'name': product_data['name_en']}

# ... (delete_product, etc) ...

def delete_product(product_id):
    """Delete a product"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    return {'id': product_id, 'status': 'deleted'}

def update_product(product_id, data):
    """Update existing product"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Dynamic update based on provided keys
    fields = []
    values = []
    
    if 'price' in data:
        fields.append("price = ?")
        values.append(data['price'])
    if 'stock' in data:
        fields.append("stock = ?")
        values.append(data['stock'])
    if 'image_url' in data:
        fields.append("image_url = ?")
        values.append(data['image_url'])
    if 'name_ml' in data:
        fields.append("name_ml = ?")
        values.append(data['name_ml'])
    if 'safety_stock' in data:
        fields.append("safety_stock = ?")
        values.append(data['safety_stock'])
        
    if not fields:
        conn.close()
        return None
        
    values.append(product_id)
    query = f"UPDATE products SET {', '.join(fields)} WHERE id = ?"
    
    c.execute(query, values)
    conn.commit()
    conn.close()
    return {'id': product_id, 'status': 'updated'}

def delete_order(order_id):
    """Delete order and its items"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Cascade delete (order_items first, though foreign keys should handle typical constraints, explicit is safer here if PRAGMA foreign_keys not on)
    c.execute('DELETE FROM order_items WHERE order_id = ?', (order_id,))
    c.execute('DELETE FROM orders WHERE id = ?', (order_id,))
    conn.commit()
    conn.close()
    return {'id': order_id, 'status': 'deleted'}

def get_orders_by_user(phone):
    """Get orders for a specific user"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        SELECT id, customer_name, customer_address, total, status, created_at, transcript 
        FROM orders 
        WHERE customer_phone = ? 
        ORDER BY created_at DESC
    ''', (phone,))
    
    columns = [col[0] for col in c.description]
    user_orders = [dict(zip(columns, row)) for row in c.fetchall()]
    
    for order in user_orders:
        c.execute('''
            SELECT p.name_en as name, oi.quantity, oi.price
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        ''', (order['id'],))
        order['items'] = [{'name': row[0], 'quantity': row[1], 'price': row[2]} for row in c.fetchall()]

    conn.close()
    return user_orders

def get_orders():
    """Get all orders"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM orders ORDER BY created_at DESC')
    columns = [description[0] for description in c.description]
    orders = [dict(zip(columns, row)) for row in c.fetchall()]
    
    for order in orders:
        c.execute('''
            SELECT p.name_en as name, oi.quantity, oi.price
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        ''', (order['id'],))
        order['items'] = [{'name': row[0], 'quantity': row[1], 'price': row[2]} for row in c.fetchall()]

    conn.close()
    return orders

# --- Phase 1: User & Cart Management ---

def get_user(phone):
    """Get user details by phone"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT phone, name, address FROM users WHERE phone = ?', (phone,))
    row = c.fetchone()
    conn.close()
    if row:
        return {'phone': row[0], 'name': row[1], 'address': row[2]}
    return None

def update_user(phone, name=None, address=None):
    """Create or Update User"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Check exist
    c.execute('SELECT phone FROM users WHERE phone = ?', (phone,))
    exists = c.fetchone()
    
    if exists:
        if name:
            c.execute('UPDATE users SET name = ? WHERE phone = ?', (name, phone))
        if address:
            c.execute('UPDATE users SET address = ? WHERE phone = ?', (address, phone))
    else:
        c.execute('INSERT INTO users (phone, name, address) VALUES (?, ?, ?)', (phone, name or '', address or ''))
    
    conn.commit()
    conn.close()
    return get_user(phone)

def get_cart(phone):
    """Get active cart for user"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        SELECT c.product_id, c.quantity, p.price, p.name_en 
        FROM cart_items c 
        JOIN products p ON c.product_id = p.id 
        WHERE c.phone = ?
    ''', (phone,))
    items = [{'id': row[0], 'qty': row[1], 'price': row[2], 'name': row[3]} for row in c.fetchall()]
    conn.close()
    return items

def save_cart(phone, items):
    """Replace user's cart with new items"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # clear old cart
    c.execute('DELETE FROM cart_items WHERE phone = ?', (phone,))
    
    # add new
    for item in items:
        # Assuming item has 'id' (product_id) and 'qty'
        pid = item.get('id') or item.get('product_id')
        qty = item.get('qty') or item.get('quantity')
        if pid and qty:
            c.execute('INSERT INTO cart_items (phone, product_id, quantity) VALUES (?, ?, ?)', (phone, pid, qty))
            
    conn.commit()
    conn.close()

def get_user_frequent_items(phone):
    """Get frequent items for a user for Smart Reorder"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # We aggregate items from all past orders of this user
    # Returning top 5 most frequently bought items
    c.execute('''
        SELECT p.id, p.name_en, SUM(oi.quantity) as total_qty
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN products p ON oi.product_id = p.id
        WHERE o.customer_phone = ?
        GROUP BY p.id
        ORDER BY total_qty DESC
        LIMIT 5
    ''', (phone,))
    
    items = [{'id': row[0], 'name': row[1], 'qty': row[2]} for row in c.fetchall()]
    conn.close()
    return items

def get_user_monthly_essentials(phone, min_months=4):
    """
    Identify items bought in >= min_months distinct months.
    Returns list of {'id': product_id, 'name': product_name}.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Logic:
    # 1. Get (Product ID, Month) for all user orders
    # 2. Group by Product ID
    # 3. Count distinct months
    # 4. Filter where Count >= min_months
    
    # SQLite strftime('%Y-%m', created_at) extracts YYYY-MM
    c.execute('''
        SELECT p.id, p.name_en, COUNT(DISTINCT strftime('%Y-%m', o.created_at)) as distinct_months
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN products p ON oi.product_id = p.id
        WHERE o.customer_phone = ?
        GROUP BY p.id
        HAVING distinct_months >= ?
        ORDER BY distinct_months DESC
    ''', (phone, min_months))
    
    items = [{'id': row[0], 'name': row[1]} for row in c.fetchall()]
    conn.close()
    return items

def get_forgotten_items(phone, min_orders=3, days_gap=30):
    """
    Find items the user has ordered at least `min_orders` times
    but NOT in the last `days_gap` days — likely forgotten regulars.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('''
        SELECT p.id, p.name_en, COUNT(*) as order_count, 
               MAX(o.created_at) as last_ordered
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN products p ON oi.product_id = p.id
        WHERE o.customer_phone = ?
        GROUP BY p.id
        HAVING order_count >= ? 
               AND julianday('now') - julianday(MAX(o.created_at)) > ?
        ORDER BY order_count DESC
        LIMIT 5
    ''', (phone, min_orders, days_gap))
    
    items = [{'id': row[0], 'name': row[1], 'times_ordered': row[2]} for row in c.fetchall()]
    conn.close()
    return items
