from db import init_db, create_order, get_products
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "libs"))
import sqlite3

# Initialize
init_db()

# Check initial stock
print("Initial Stock:")
products = get_products()
basmati = next(p for p in products if 'Basmati' in p['name_en'])
print(f"Basmati Stock: {basmati['stock']}")
initial_stock = basmati['stock']

# Create a test order
print("\nPlacing Order for 2 units...")
order_data = {
    'phone': 'TestUser',
    'name': 'Test Customer',
    'address': '123 Test Lane',
    'total': 160.0,
    'language': 'en',
    'transcript': 'Test transcript',
    'items': [
        {'id': basmati['id'], 'quantity': 2, 'price': 80.0}
    ]
}

create_order(order_data)

# Check stock again
print("\nStock after order:")
products = get_products()
basmati_new = next(p for p in products if 'Basmati' in p['name_en'])
print(f"Basmati Stock: {basmati_new['stock']}")

if basmati_new['stock'] == initial_stock - 2:
    print("\nSUCCESS: Stock deducted correctly.")
else:
    print("\nFAILURE: Stock NOT deducted correctly.")
