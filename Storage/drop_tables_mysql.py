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
                DROP TABLE products, orders
"""
)

db_conn.commit()
db_conn.close()
