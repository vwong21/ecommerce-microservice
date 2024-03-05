import mysql.connector

db_conn = mysql.connector.connect(
    host="localhost", user="root", password="password", database="ecommerce"
)

db_cursor = db_conn.cursor()

db_cursor.execute(
    """
        CREATE TABLE products
            (id INT NOT NULL AUTO_INCREMENT,
            product_id varchar(250) NOT NULL,
            name VARCHAR(250) NOT NULL,
            price FLOAT NOT NULL,
            quantity INT NOT NULL,
            date_created DATETIME DEFAULT CURRENT_TIMESTAMP,
            trace_id varchar(250) NOT NULL,
            CONSTRAINT products_pk PRIMARY KEY (id))
            """
)
db_cursor.execute(
    """
        CREATE TABLE orders
            (id INT NOT NULL AUTO_INCREMENT,
            customer_id varchar(250) NOT NULL,
            order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            quantity INT NOT NULL,
            total_price FLOAT NOT NULL,
            date_created DATETIME DEFAULT CURRENT_TIMESTAMP,
            trace_id varchar(250) NOT NULL,
            CONSTRAINT orders_pk PRIMARY KEY (id))
                  """
)
db_conn.commit()
db_conn.close()
