import mysql.connector
import yaml

with open("app_conf.yaml", "r") as f:
    app_config = yaml.safe_load(f.read())
    DATABASE_CONFIG = app_config["database"]

db_conn = mysql.connector.connect(
    host=DATABASE_CONFIG["host"],
    user=DATABASE_CONFIG["user"],
    password=DATABASE_CONFIG["password"],
    database=DATABASE_CONFIG["database"],
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
