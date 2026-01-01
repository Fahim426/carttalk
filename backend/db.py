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
    
    # Auto-Migration: Check for missing columns in existing tables
    c.execute("PRAGMA table_info(products)")
    prod_cols = [row[1] for row in c.fetchall()]
    
    if 'image_url' not in prod_cols:
        try:
            print("Migrating DB: Adding image_url column to products...")
            c.execute("ALTER TABLE products ADD COLUMN image_url TEXT")
        except Exception as e:
            print(f"Migration Error (image_url): {e}")

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

def seed_products(conn):
    """Add sample products with Images"""
    c = conn.cursor()
    
    # Image Mapping (Unsplash)
    images = {
        'Basmati Rice': 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=400',
        'Yellow Onions': 'https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?w=400',
        'Red Onions': 'https://images.unsplash.com/photo-1620574387735-3624d75b2dbc?w=400',
        'Green Chili': 'https://images.unsplash.com/photo-1565557782987-bf7867375a32?w=400',
        'Tomatoes': 'https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=400',
        'Coconut Oil': 'https://images.unsplash.com/photo-1589133464197-0bf0922830f8?w=400',
        'Turmeric Powder': 'https://images.unsplash.com/photo-1615485500704-8e99099d9d0f?w=400',
        'Salt': 'https://images.unsplash.com/photo-1518110925495-5925a3dcf509?w=400',
        'Milk': 'https://images.unsplash.com/photo-1563636619-e9143da7973b?w=400',
        'Eggs': 'https://images.unsplash.com/photo-1506976785307-8732e854ad03?w=400',
        'Sugar': 'https://images.unsplash.com/photo-1605307672076-29175c57aa96?w=400',
        'Tea Powder': 'https://images.unsplash.com/photo-1558160074-4d7d8bdf4256?w=400',
        'Banana': 'https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=400',
        'Apple': 'https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=400',
        'Chicken (1kg)': 'https://images.unsplash.com/photo-1587593810167-a84920ea0781?w=400',
        'Beef (1kg)': 'https://images.unsplash.com/photo-1607623814075-e51df1bdc82f?w=400',
        'Potato': 'https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=400',
        'Ginger': 'https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=400',
        'Garlic': 'https://images.unsplash.com/photo-1557080517-5788d752dd7d?w=400',
        'Coriander Powder': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400',
        'Chili Powder': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400',
    }

    products = [
        ('Basmati Rice', 'പാസ്‌മതി അരി', 'Grains', 80.0, 50, images.get('Basmati Rice')),
        ('Yellow Onions', 'മഞ്ഞ ഉള്ളി', 'Vegetables', 40.0, 100, images.get('Yellow Onions')),
        ('Red Onions', 'ചുവന്ന ഉള്ളി', 'Vegetables', 50.0, 80, images.get('Red Onions')),
        ('Green Chili', 'പച്ച മുളകി', 'Vegetables', 30.0, 60, images.get('Green Chili')),
        ('Tomatoes', 'തക്കാളി', 'Vegetables', 35.0, 70, images.get('Tomatoes')),
        ('Coconut Oil', 'തെങ്ങ എണ്ണ', 'Oils', 150.0, 40, images.get('Coconut Oil')),
        ('Turmeric Powder', 'മഞ്ഞൾ പൊടി', 'Spices', 100.0, 25, images.get('Turmeric Powder')),
        ('Salt', 'ഉപ്പ്', 'Spices', 20.0, 200, images.get('Salt')),
        ('Milk', 'പാൽ', 'Dairy', 50.0, 50, images.get('Milk')),
        ('Eggs', 'മുട്ട', 'Dairy', 6.0, 300, images.get('Eggs')),
        ('Sugar', 'പഞ്ചസാര', 'Pantry', 45.0, 100, images.get('Sugar')),
        ('Tea Powder', 'ചായപ്പൊടി', 'Beverages', 250.0, 60, images.get('Tea Powder')),
        ('Banana', 'വാഴപ്പഴം', 'Fruits', 60.0, 150, images.get('Banana')),
        ('Apple', 'ആപ്പിൾ', 'Fruits', 180.0, 80, images.get('Apple')),
        ('Chicken (1kg)', 'കോഴി ഇറച്ചി', 'Meat', 220.0, 30, images.get('Chicken (1kg)')),
        ('Beef (1kg)', 'ബീഫ്', 'Meat', 380.0, 20, images.get('Beef (1kg)')),
        ('Potato', 'ഉ ഉരുളക്കിഴങ്ങ്', 'Vegetables', 35.0, 120, images.get('Potato')),
        ('Ginger', 'ഇഞ്ചി', 'Vegetables', 120.0, 40, images.get('Ginger')),
        ('Garlic', 'വെളുത്തുള്ളി', 'Vegetables', 140.0, 50, images.get('Garlic')),
        ('Coriander Powder', 'മല്ലിപ്പൊടി', 'Spices', 120.0, 45, images.get('Coriander Powder')),
        ('Chili Powder', 'മുളകുപൊടി', 'Spices', 160.0, 45, images.get('Chili Powder')),
    ]
    
    # Smart Seed: Insert if not exists AND Update Image if missing
    print("Seeding/Updating products...")
    for prod in products:
        name = prod[0]
        image_url = prod[5]
        
        try:
            # Check if product exists
            # We first try to select WITH image_url. If it fails (no col), we catch it.
            c.execute('SELECT id, image_url FROM products WHERE name_en = ?', (name,))
            row = c.fetchone()
            
            if not row:
                print(f"Adding new product: {name}")
                c.execute('INSERT INTO products (name_en, name_ml, category, price, stock, image_url) VALUES (?, ?, ?, ?, ?, ?)', prod)
            else:
                # Update Image ONLY if it's currently missing in DB
                # This prevents overwriting user-uploaded images on restart
                current_db_image = row[1]
                if not current_db_image and image_url:
                     # print(f"Seeding missing image for: {name}")
                     c.execute('UPDATE products SET image_url = ? WHERE id = ?', (image_url, row[0]))
        except sqlite3.OperationalError as e:
            # Fallback for when image_url column doesn't exist yet (during first run before migration)
            # This allows init_db to proceed, and then migration adds the column.
            # Next restart will fill the images.
            # print(f"Skipping image update for {name} (Schema not ready): {e}")
            
            # Still try to insert if product missing (legacy mode)
            c.execute('SELECT id FROM products WHERE name_en = ?', (name,))
            if not c.fetchone():
                 print(f"Adding product (No Image Support yet): {name}")
                 c.execute('INSERT INTO products (name_en, name_ml, category, price, stock) VALUES (?, ?, ?, ?, ?)', 
                           (prod[0], prod[1], prod[2], prod[3], prod[4]))
    
    conn.commit()

def get_products():
    """Get all products"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Check if image_url exists
    try:
        c.execute('SELECT id, name_en, name_ml, price, stock, category, image_url FROM products')
        products = [{'id': row[0], 'name_en': row[1], 'name_ml': row[2], 'price': row[3], 'stock': row[4], 'category': row[5], 'image_url': row[6]} for row in c.fetchall()]
    except sqlite3.OperationalError:
        # Fallback if migration hasn't run yet (unlikely if called after init)
        c.execute('SELECT id, name_en, name_ml, price, stock, category FROM products')
        products = [{'id': row[0], 'name_en': row[1], 'name_ml': row[2], 'price': row[3], 'stock': row[4], 'category': row[5], 'image_url': ''} for row in c.fetchall()]
        
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
    # Check if image_url col exists
    try:
        c.execute('INSERT INTO products (name_en, name_ml, category, price, stock, image_url) VALUES (?, ?, ?, ?, ?, ?)',
                  (product_data['name_en'], product_data.get('name_ml', ''), product_data['category'], product_data['price'], product_data['stock'], product_data.get('image_url', '')))
    except sqlite3.OperationalError:
        c.execute('INSERT INTO products (name_en, name_ml, category, price, stock) VALUES (?, ?, ?, ?, ?)',
                  (product_data['name_en'], product_data.get('name_ml', ''), product_data['category'], product_data['price'], product_data['stock']))
    
    pid = c.lastrowid
    conn.commit()
    conn.close()
    return {'id': pid, 'name': product_data['name_en']}

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
        
    if not fields:
        conn.close()
        return None
        
    values.append(product_id)
    query = f"UPDATE products SET {', '.join(fields)} WHERE id = ?"
    
    c.execute(query, values)
    conn.commit()
    conn.close()
    return {'id': product_id, 'status': 'updated'}

def get_orders():
    """Get all orders"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM orders ORDER BY created_at DESC')
    columns = [description[0] for description in c.description]
    orders = [dict(zip(columns, row)) for row in c.fetchall()]
    conn.close()
    return orders
