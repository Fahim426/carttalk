import sqlite3
import os

import sys
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cartalk.db")

def fix_schema():
    print(f"Checking schema for {DB_FILE}...")
    sys.stdout.flush()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Get current columns
    c.execute("PRAGMA table_info(orders)")
    current_cols = [row[1] for row in c.fetchall()]
    print(f"Current columns: {current_cols}")
    
    # Add customer_name
    if 'customer_name' not in current_cols:
        print("Adding customer_name...")
        try:
            c.execute("ALTER TABLE orders ADD COLUMN customer_name TEXT")
        except Exception as e:
            print(f"Error adding customer_name: {e}")
            
    # Add customer_address
    if 'customer_address' not in current_cols:
        print("Adding customer_address...")
        try:
            c.execute("ALTER TABLE orders ADD COLUMN customer_address TEXT")
        except Exception as e:
            print(f"Error adding customer_address: {e}")

    conn.commit()
    conn.close()
    print("Schema fix complete.")

if __name__ == "__main__":
    fix_schema()
