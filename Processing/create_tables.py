import sqlite3

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

conn.commit()
conn.close()
