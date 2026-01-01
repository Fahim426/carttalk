import sqlite3
import os

DB_FILE = "cartalk.db"

def check_products():
    if not os.path.exists(DB_FILE):
        print("DB file not found!")
        return

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name_en, category, stock FROM products")
    rows = c.fetchall()
    
    print(f"Total Products: {len(rows)}")
    print("-" * 40)
    print(f"{'ID':<4} {'Name':<20} {'Category':<10} {'Stock'}")
    print("-" * 40)
    
    found_eggs = False
    for row in rows:
        print(f"{row[0]:<4} {row[1]:<20} {row[2]:<10} {row[3]}")
        if 'Egg' in row[1]:
            found_eggs = True
            
    print("-" * 40)
    if found_eggs:
        print("SUCCESS: Eggs found in DB.")
    else:
        print("FAILURE: Eggs NOT found in DB.")

    conn.close()

if __name__ == "__main__":
    check_products()
