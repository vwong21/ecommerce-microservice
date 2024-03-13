import connexion
import mysql.connector
import json
import logging
import logging.config
import yaml

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from connexion import NoContent
from datetime import datetime, timezone
from dateutil.parser import parse as parse_date
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread
from base import Base
from products import Products
from orders import Orders

with open("log_conf.yaml", "r") as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger("basicLogger")

with open("app_conf.yaml", "r") as f:
    app_config = yaml.safe_load(f.read())
    DATABASE_CONFIG = app_config["database"]

DB_ENGINE = create_engine(
    f"mysql+pymysql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
)
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)


def getProductEvents(start_timestamp, end_timestamp):
    session = DB_SESSION()
    logging.info(
        f"Connecting to DB. Hostname: {DATABASE_CONFIG['host']}, Port: {DATABASE_CONFIG['port']}"
    )

    try:
        start_timestamp_datetime = datetime.strptime(
            start_timestamp, "%Y-%m-%d %H:%M:%S"
        )
        end_timestamp_datetime = datetime.strptime(end_timestamp, "%Y-%m-%d %H:%M:%S")

        results = (
            session.query(Products)
            .filter(
                Products.date_created >= start_timestamp_datetime,
                Products.date_created < end_timestamp_datetime,
            )
            .all()
        )

        results_list = []
        for row in results:
            reading_dict = {
                "id": row.id,
                "product_id": row.product_id,
                "name": row.name,
                "price": row.price,
                "quantity": row.quantity,
                "date_created": row.date_created,
                "trace_id": row.trace_id,
            }
            results_list.append(reading_dict)
        session.close()
        logging.info(results_list)
        return results_list
    except Exception as e:
        logger.error(e)
        return None
    finally:
        logging.info(
            "Query for products after %s returns %d results"
            % (start_timestamp, len(results_list))
        )


def getOrderEvents(start_timestamp, end_timestamp):
    try:
        session = DB_SESSION()
        logging.info(
            f"Connecting to DB. Hostname: {DATABASE_CONFIG['host']}, Port: {DATABASE_CONFIG['port']}"
        )

        start_timestamp_datetime = datetime.strptime(
            start_timestamp, "%Y-%m-%d %H:%M:%S"
        )
        end_timestamp_datetime = datetime.strptime(end_timestamp, "%Y-%m-%d %H:%M:%S")

        results = (
            session.query(Orders)
            .filter(
                Orders.date_created >= start_timestamp_datetime,
                Orders.date_created < end_timestamp_datetime,
            )
            .all()
        )

        results_list = []
        for row in results:
            reading_dict = {
                "id": row.id,
                "customer_id": row.customer_id,
                "order_date": row.order_date,
                "quantity": row.quantity,
                "total_price": row.total_price,
                "date_created": row.date_created,
                "trace_id": row.trace_id,
            }
            results_list.append(reading_dict)

        session.close()
        logging.info(results_list)
        return results_list
    except Exception as e:
        logger.error(e)
    finally:
        logging.info(
            "Query for orders after %s returns %d results"
            % (start_timestamp, len(results_list))
        )


def process_messages():
    max_retries = 10
    retry_count = 0

    while retry_count < max_retries:
        try:
            events = app_config["events"]
            hostname = "%s:%d" % (events["hostname"], events["port"])
            client = KafkaClient(hosts=hostname)
            topic = client.topics[str.encode(events["topic"])]
            consumer = topic.get_simple_consumer(
                consumer_group=b"event_group",
                reset_offset_on_start=False,
                auto_offset_reset=OffsetType.LATEST,
            )

            for msg in consumer:
                msg_str = msg.value.decode("utf-8")
                msg = json.loads(msg_str)
                logging.info("Message: %s" % msg)

                payload = msg["payload"]

                if msg["type"] == "products":

                    products = Products(
                        product_id=payload["product_id"],
                        name=payload["name"],
                        price=payload["price"],
                        quantity=payload["quantity"],
                        date_created=datetime.now(timezone.utc).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        trace_id=payload["trace_id"],
                    )
                    session = DB_SESSION()
                    logging.info("Connected to database")
                    session.add(products)
                    session.commit()
                    session.close()

                    logger.debug(
                        f"Stored event 'create_product' request with a trace id of {payload['trace_id']}"
                    )

                elif msg["type"] == "orders":
                    order_date_str = payload["order_date"]
                    order_date = parse_date(order_date_str)
                    orders = Orders(
                        customer_id=payload["customer_id"],
                        order_date=order_date.strftime("%Y-%m-%d %H:%M:%S"),
                        quantity=payload["quantity"],
                        total_price=payload["total_price"],
                        date_created=datetime.now(timezone.utc).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        trace_id=payload["trace_id"],
                    )

                    session = DB_SESSION()
                    logging.info("Connected to database")
                    session.add(orders)
                    session.commit()
                    session.close()

                    logger.debug(
                        f"Stored event 'create_order' request with a trace id of {payload['trace_id']}"
                    )

                consumer.commit_offsets()

            break
            consumer.commit_offsets()
        except Exception as e:
            logger.error(e)
            retry_count += 1


app = connexion.FlaskApp(__name__, specification_dir="")
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    t1 = Thread(target=process_messages)
    t1.daemon = True
    t1.start()
    app.run(host="0.0.0.0", port=8090)
