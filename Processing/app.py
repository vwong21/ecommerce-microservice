import connexion
import yaml
import json
import logging
import logging.config
import os
import requests
import time

from apscheduler.schedulers.background import BackgroundScheduler
from base import Base
from datetime import datetime, timezone
from flask import jsonify
from flask_cors import CORS
from pykafka import KafkaClient
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from stats import Stats


def get_latest_datetime(current_datetime):
    session = DB_SESSION()
    try:
        latest_stat = session.query(Stats).order_by(Stats.created_at.desc()).first()
        if latest_stat:
            latest_datetime = latest_stat.created_at
        else:
            latest_datetime = current_datetime
    except Exception as e:
        logger.error(e)
    finally:
        session.close()
    return latest_datetime


def calculate_stats(product_res, order_res, current_datetime_object):
    try:
        session = DB_SESSION()
        latest_stat = session.query(Stats).order_by(Stats.created_at.desc()).first()
        product_res_json = product_res.json()
        order_res_json = order_res.json()

        number_products = latest_stat.number_products
        number_orders = latest_stat.number_orders
        highest_product_price = latest_stat.highest_product_price
        highest_order_price = latest_stat.highest_order_price
        highest_product_quantity = latest_stat.highest_product_quantity
        highest_order_quantity = latest_stat.highest_order_quantity

        for product in product_res_json:
            number_products += 1
            if product["price"] > highest_product_price:
                highest_product_price = product["price"]
            if product["quantity"] > highest_product_quantity:
                highest_product_quantity = product["quantity"]

        for order in order_res_json:
            number_orders += 1
            if order["total_price"] > highest_order_price:
                highest_order_price = order["total_price"]
            if order["quantity"] > highest_order_quantity:
                highest_order_quantity = order["quantity"]

        stats = Stats(
            number_products=number_products,
            number_orders=number_orders,
            highest_product_price=highest_product_price,
            highest_order_price=highest_order_price,
            highest_product_quantity=highest_product_quantity,
            highest_order_quantity=highest_order_quantity,
            created_at=current_datetime_object,
        )
        session.add(stats)
        session.commit()
    except Exception as e:
        logger.error("error in stats calculation", e)
    finally:
        session.close()


def populate_stats():
    event_count += 1
    logging.info(event_count)
    logger.info("Start Periodic Processing")
    current_datetime_object = datetime.now(timezone.utc)
    current_datetime = current_datetime_object.strftime("%Y-%m-%d %H:%M:%S")
    session = DB_SESSION()
    try:
        stats = session.query(Stats).order_by(desc(Stats.created_at)).first()
        last_datetime = stats.created_at.strftime("%Y-%m-%d %H:%M:%S")
        product_endpoint = f"{eventstore_url}/products"
        order_endpoint = f"{eventstore_url}/orders"

        response_product = requests.get(
            product_endpoint,
            params={
                "start_timestamp": last_datetime,
                "end_timestamp": current_datetime,
            },
        )

        response_order = requests.get(
            order_endpoint,
            params={
                "start_timestamp": last_datetime,
                "end_timestamp": current_datetime,
            },
        )
        calculate_stats(response_product, response_order, current_datetime_object)

        logger.info(f"Product response status code: {response_product.status_code}")
        logger.info(f"Order response status code: {response_order.status_code}")

        updated_stats = session.query(Stats).order_by(desc(Stats.created_at)).first()
        logger.debug(f"Updated statistics: {updated_stats.to_dict()}")

        logger.info("End Periodic Processing")

        if event_count % event_count == 0:
            logging.info(f"0004 - Logging on every {event_count} processes")
    except Exception as e:
        logger.error(e)
    finally:
        session.close()


def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(
        populate_stats, "interval", seconds=app_config["scheduler"]["period_sec"]
    )
    sched.start()


def get_stats():
    logger.info("Request for statistics has started")
    session = DB_SESSION()
    try:
        latest_stat = session.query(Stats).order_by(Stats.created_at.desc()).first()
        if latest_stat is None:
            logger.error("Statistics do not exist")
            return jsonify({"message": "Statistics do not exist"}), 404
        stats_dict = {
            "number_products": latest_stat.number_products,
            "number_orders": latest_stat.number_orders,
            "highest_product_price": latest_stat.highest_product_price,
            "highest_order_price": latest_stat.highest_order_price,
            "highest_product_quantity": latest_stat.highest_product_quantity,
            "highest_order_quantity": latest_stat.highest_order_quantity,
            "created_at": latest_stat.created_at,
        }

        logger.debug(f"Statistics dictionary: {stats_dict}")
        logger.info("Request for statistics has completed")

        return jsonify(stats_dict), 200
    except Exception as e:
        logger.error(e)
        return jsonify({"message": "Internal Server Error"}), 500
    finally:
        session.close()


app = connexion.FlaskApp(__name__, specification_dir="")
if "TARGET_ENV" not in os.environ or os.environ["TARGET_ENV"] != "test":
    CORS(app.app)
    app.app.config["CORS_HEADERS"] = "Content-Type"

app.add_api(
    "openapi.yaml",
    base_path="/processing",
    strict_validation=True,
    validate_responses=True,
)

if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    app_conf_file = "/config/app_conf.yaml"
    log_conf_file = "/config/log_conf.yaml"
else:
    print("In Dev Environment")
    app_conf_file = "app_conf.yaml"
    log_conf_file = "log_conf.yaml"

with open(app_conf_file, "r") as f:
    app_config = yaml.safe_load(f.read())

eventstore_url = app_config["eventstore"]["url"]

# External Logging Configuration
with open(log_conf_file, "r") as f:
    log_config = yaml.safe_load(f.read())

logging.config.dictConfig(log_config)
logger = logging.getLogger("basicLogger")
logger.info("App Conf File: %s" % app_conf_file)
logger.info("Log Conf File: %s" % log_conf_file)

event_log_retry_count = 0
event_log_max_retries = app_config["event_log"]["max_retries"]
event_log_producer = None
while event_log_retry_count < event_log_max_retries:
    try:
        event_log = app_config["event_log"]
        kafka_server = event_log["hostname"]
        kafka_port = event_log["port"]
        kafka_topic = event_log["topic"]

        client = KafkaClient(hosts=f"{kafka_server}:{kafka_port}")
        topic = client.topics[str.encode(kafka_topic)]
        event_log_producer = topic.get_sync_producer()
        payload = f"0003 - Connected to event_log topic"
        msg = {
            "payload": payload,
        }

        msg_str = json.dumps(msg)
        event_log_producer.produce(msg_str.encode("utf-8"))
        logging.info(payload)
        break
    except Exception as e:
        logger.error(e)
        event_log_retry_count += 1
        sleep_time = app_config["event_log"]["retry_sleep_value"]
        time.sleep(sleep_time)

DB_ENGINE = create_engine("sqlite:///%s" % app_config["datastore"]["filename"])
Base.metadata.bind = DB_ENGINE
Base.metadata.create_all(DB_ENGINE)
DB_SESSION = sessionmaker(bind=DB_ENGINE)

session = DB_SESSION()
test_stats = session.query(Stats).order_by(desc(Stats.created_at)).first()
current_datetime_object = datetime.now(timezone.utc)
if test_stats is None:
    test_stats = Stats(
        number_products=0,
        number_orders=0,
        highest_product_price=0.0,
        highest_order_price=0.0,
        highest_product_quantity=0,
        highest_order_quantity=0,
        created_at=current_datetime_object,
    )
    session.add(test_stats)
    session.commit()
session.close()

log_count = 0
event_count = app_config["event_log"]["event_count"]


if __name__ == "__main__":
    init_scheduler()
    logging.info("app running on port 8100")
    app.run(host="0.0.0.0", port=8100)
