import sqlite3
import os
import sys

# Ensure we are in the backend directory context if run from scripts/
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
DB_PATH = os.path.join(BACKEND_DIR, 'cartalk.db')

def reset_and_seed():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        sys.exit(1)

    print("Connecting to database...")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        # 1. Clear existing products
        print("Clearing existing products...")
        c.execute('DELETE FROM cart_items') # Clear carts to avoid FK errors
        c.execute('DELETE FROM order_items') # Clear order items 
        c.execute('DELETE FROM products')
        
        # 2. Curated High-Quality Product List for Presentation
        print("Seeding premium demo products...")
        premium_products = [
            ('Organic Tomato', 'തക്കാളി', 'Vegetables', 45.0, 50, 'https://images.unsplash.com/photo-1546473427-e1ad6d6622aa?w=400&q=80', 5),
            ('Red Onion', 'സവാള', 'Vegetables', 38.0, 100, 'https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?w=400&q=80', 10),
            ('Fresh Broccoli', 'ബ്രോക്കോളി', 'Vegetables', 120.0, 20, 'https://images.unsplash.com/photo-1459411621453-7b03977f4bfc?w=400&q=80', 5),
            ('Premium Apple', 'ആപ്പിൾ', 'Fruits', 180.0, 30, 'https://images.unsplash.com/photo-1560806887-1e4cd0b6faa6?w=400&q=80', 5),
            ('Banana Robusta', 'ഏത്തപ്പഴം', 'Fruits', 65.0, 40, 'https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=400&q=80', 10),
            ('Fresh Milk', 'പാൽ', 'Dairy', 30.0, 25, 'https://images.unsplash.com/photo-1563636619-e91000f21fca?w=400&q=80', 5),
            ('Farm Eggs (6 Pack)', 'മുട്ട', 'Dairy', 45.0, 30, 'https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=400&q=80', 10),
            ('Basmati Rice', 'ബസുമതി അരി', 'Grains', 110.0, 50, 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=400&q=80', 10),
            ('Turmeric Powder', 'മഞ്ഞൾപ്പൊടി', 'Spices', 35.0, 40, 'https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=400&q=80', 5),
            ('Chicken (Skinless)', 'ചിക്കൻ', 'Meat', 240.0, 15, 'https://images.unsplash.com/photo-1604503468306-202f7280c008?w=400&q=80', 5),
            ('Virgin Coconut Oil', 'വെളിച്ചെണ്ണ', 'Oils', 220.0, 20, 'https://images.unsplash.com/photo-1598214817158-54753ca1ce11?w=400&q=80', 5),
            ('Whole Wheat Bread', 'ബ്രെഡ്', 'Pantry', 55.0, 15, 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400&q=80', 3)
        ]

        c.executemany('''
            INSERT INTO products (name_en, name_ml, category, price, stock, image_url, safety_stock)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', premium_products)

        conn.commit()
        print(f"Success! {len(premium_products)} beautiful products seeded.")

    except Exception as e:
        print(f"Error during seeding: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    reset_and_seed()
