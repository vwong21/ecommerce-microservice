import mysql.connector

db_conn = mysql.connector.connect(
    host="localhost", user="root", password="password", database="ecommerce"
)

db_cursor = db_conn.cursor()
db_cursor.execute(
    """
                DROP TABLE products, orders
"""
)

db_conn.commit()
db_conn.close()
