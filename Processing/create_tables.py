import sqlite3
from datetime import datetime

conn = sqlite3.connect("stats.sqlite")

c = conn.cursor()
c.execute(
    """
        CREATE TABLE stats
          (id INTEGER PRIMARY KEY ASC,
          number_products INTEGER NOT NULL,
          number_orders INTEGER NOT NULL,
          highest_product_price REAL NOT NULL,
          highest_order_price REAL NOT NULL,
          highest_product_quantity INTEGER NOT NULL,
          highest_order_quantity INTEGER NOT NULL,
          created_at TEXT NOT NULL
          )
"""
)

data = (
    0,  # number_products
    0,  # number_orders
    0.0,  # highest_product_price
    0.0,  # highest_order_price
    0,  # highest_product_quantity
    0,  # highest_order_quantity
    datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),  # created_at
)

# Insert data into the table
c.execute(
    """
    INSERT INTO stats 
    (number_products, number_orders, highest_product_price, highest_order_price,
    highest_product_quantity, highest_order_quantity, created_at) 
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
    data,
)
conn.commit()
conn.close()
