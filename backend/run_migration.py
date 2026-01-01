from db import init_db, seed_products
import sqlite3

# Initialize Schema (Adds image_url column)
print("Running Schema Migration...")
init_db()

# Run Seeding (Updates existing products with images)
print("Running Image Seeding...")
conn = sqlite3.connect("cartalk.db")
seed_products(conn)
conn.close()

print("Migration Complete! Restart Backend to serve new data.")
