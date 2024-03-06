import connexion
from connexion import NoContent
import mysql.connector
from datetime import datetime
from dateutil.parser import parse as parse_date
import yaml
import logging.config
import logging

with open("log_conf.yaml", "r") as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

with open("app_conf.yaml", "r") as f:
    app_config = yaml.safe_load(f.read())
    DATABASE_CONFIG = app_config["database"]


def get_db_connection():
    return mysql.connector.connect(**DATABASE_CONFIG)


logger = logging.getLogger("basicLogger")


def createProduct(body):
    try:
        db_conn = get_db_connection()
        db_cursor = db_conn.cursor()

        product_id = body.get("product_id")
        name = body.get("name")
        price = body.get("price")
        quantity = body.get("quantity")
        date_created = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        trace_id = body.get("trace_id")

        query = "INSERT INTO products (product_id, name, price, quantity, date_created, trace_id) VALUES (%s, %s, %s, %s, %s, %s)"
        values = (product_id, name, price, quantity, date_created, trace_id)

        db_cursor.execute(query, values)
        db_conn.commit()

        logger.debug(
            f"Stored event 'create_product' request with a trace id of {trace_id}"
        )

        return NoContent, 201

    except Exception as e:
        logger.error(e)
        return NoContent, 500

    finally:
        db_cursor.close()
        db_conn.close()


def processOrder(body):
    try:
        db_conn = get_db_connection()
        db_cursor = db_conn.cursor()

        customer_id = body.get("customer_id")
        order_date_str = body.get("order_date")
        order_date = parse_date(order_date_str)
        order_date_formatted = order_date.strftime("%Y-%m-%d %H:%M:%S")
        quantity = body.get("quantity")
        total_price = body.get("total_price")
        date_created = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        trace_id = body.get("trace_id")

        query = "INSERT INTO orders (customer_id, order_date, quantity, total_price, date_created, trace_id) VALUES (%s, %s, %s, %s, %s, %s)"
        values = (
            customer_id,
            order_date_formatted,
            quantity,
            total_price,
            date_created,
            trace_id,
        )

        db_cursor.execute(query, values)
        db_conn.commit()

        trace_id = body.get("trace_id")
        logger.debug(
            f"Stored event 'create_order' request with a trace id of {trace_id}"
        )

        return NoContent, 201

    except Exception as e:
        logger.error(e)
        return NoContent, 500

    finally:
        db_cursor.close()
        db_conn.close()


def getProductEvents(start_timestamp, end_timestamp):
    logging.info("connected")
    db_conn = get_db_connection()
    db_cursor = db_conn.cursor()
    try:
        start_timestamp_datetime = datetime.strptime(
            start_timestamp, "%Y-%m-%d %H:%M:%S"
        )
        end_timestamp_datetime = datetime.strptime(end_timestamp, "%Y-%m-%d %H:%M:%S")

        query = "SELECT * FROM products WHERE date_created >= %s AND date_created < %s"
        db_cursor.execute(query, (start_timestamp_datetime, end_timestamp_datetime))

        results = db_cursor.fetchall()

        db_cursor.close()
        db_conn.close()

        results_list = []
        for row in results:
            reading_dict = {
                "id": row[0],
                "product_id": row[1],
                "name": row[2],
                "price": row[3],
                "quantity": row[4],
                "date_created": row[5],
                "trace_id": row[6],
            }
            results_list.append(reading_dict)
        logger.info(results_list)
        return results_list
    except Exception as e:
        logging.error(e)
        return None
    finally:
        logger.info(
            "Query for products after %s returns %d results"
            % (start_timestamp, len(results_list))
        )


def getOrderEvents(start_timestamp, end_timestamp):
    try:
        db_conn = get_db_connection()
        db_cursor = db_conn.cursor()

        start_timestamp_datetime = datetime.strptime(
            start_timestamp, "%Y-%m-%d %H:%M:%S"
        )
        end_timestamp_datetime = datetime.strptime(end_timestamp, "%Y-%m-%d %H:%M:%S")

        query = "SELECT * FROM orders WHERE date_created >= %s AND date_created < %s"
        db_cursor.execute(query, (start_timestamp_datetime, end_timestamp_datetime))

        results = db_cursor.fetchall()

        db_cursor.close()
        db_conn.close()

        results_list = []
        for row in results:
            reading_dict = {
                "id": row[0],
                "customer_id": row[1],
                "order_date": row[2],
                "quantity": row[3],
                "total_price": row[4],
                "date_created": row[5],
                "trace_id": row[6],
            }
            results_list.append(reading_dict)
        logger.info(results_list)
        return results_list
    except Exception as e:
        logging.error(e)
    finally:
        logger.info(
            "Query for orders after %s returns %d results"
            % (start_timestamp, len(results_list))
        )


app = connexion.FlaskApp(__name__, specification_dir="")
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    app.run(port=8090)
