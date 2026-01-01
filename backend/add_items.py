import sqlite3
import os

DB_FILE = "cartalk.db"

def add_new_items():
    print(f"Adding new items to {DB_FILE}...")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    new_products = [
        ('Milk', 'പാൽ', 'Dairy', 50.0, 50),
        ('Eggs', 'മുട്ട', 'Dairy', 6.0, 300),
        ('Sugar', 'പഞ്ചസാര', 'Pantry', 45.0, 100),
        ('Tea Powder', 'ചായപ്പൊടി', 'Beverages', 250.0, 60),
        ('Banana', 'വാഴപ്പഴം', 'Fruits', 60.0, 150),
        ('Apple', 'ആപ്പിൾ', 'Fruits', 180.0, 80),
        ('Chicken (1kg)', 'കോഴി ഇറച്ചി', 'Meat', 220.0, 30),
        ('Beef (1kg)', 'ബീഫ്', 'Meat', 380.0, 20),
        ('Potato', 'ഉ ഉരുളക്കിഴങ്ങ്', 'Vegetables', 35.0, 120),
        ('Ginger', 'ഇഞ്ചി', 'Vegetables', 120.0, 40),
        ('Garlic', 'വെളുത്തുള്ളി', 'Vegetables', 140.0, 50),
        ('Coriander Powder', 'മല്ലിപ്പൊടി', 'Spices', 120.0, 45),
        ('Chili Powder', 'മുളകുപൊടി', 'Spices', 160.0, 45),
    ]

    for prod in new_products:
        name_en = prod[0]
        # Check if exists
        c.execute("SELECT id FROM products WHERE name_en=?", (name_en,))
        if not c.fetchone():
            print(f"Inserting {name_en}...")
            c.execute('INSERT INTO products (name_en, name_ml, category, price, stock) VALUES (?, ?, ?, ?, ?)', prod)
        else:
            print(f"Skipping {name_en} (Already exists)")

    conn.commit()
    conn.close()
    print("New items added.")

if __name__ == "__main__":
    add_new_items()
