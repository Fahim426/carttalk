import sqlite3
import os

DB_FILE = "cartalk.db"

def migrate():
    if not os.path.exists(DB_FILE):
        print("Database not found, nothing to migrate.")
        return

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Check if columns exist in orders table
    c.execute("PRAGMA table_info(orders)")
    columns = [info[1] for info in c.fetchall()]
    
    print(f"Current columns in 'orders': {columns}")
    
    if 'customer_name' not in columns:
        print("Adding 'customer_name' column...")
        try:
            c.execute("ALTER TABLE orders ADD COLUMN customer_name TEXT")
        except Exception as e:
            print(f"Error adding customer_name: {e}")

    if 'customer_address' not in columns:
        print("Adding 'customer_address' column...")
        try:
            c.execute("ALTER TABLE orders ADD COLUMN customer_address TEXT")
        except Exception as e:
            print(f"Error adding customer_address: {e}")
            
    conn.commit()
    conn.close()
    print("Migration check complete.")

if __name__ == "__main__":
    migrate()
