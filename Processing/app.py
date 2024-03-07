import connexion
import yaml
import logging
import logging.config
import requests
from flask import jsonify
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from base import Base
from stats import Stats


with open("app_conf.yaml", "r") as f:
    app_config = yaml.safe_load(f.read())

DB_ENGINE = create_engine("sqlite:///%s" % app_config["datastore"]["filename"])
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)

eventstore_url = app_config["eventstore"]["url"]

with open("log_conf.yaml", "r") as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger("basicLogger")


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
        product_res_json = product_res.json()
        order_res_json = order_res.json()

        latest_stat = session.query(Stats).order_by(Stats.created_at.desc()).first()

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
    logger.info("Start Periodic Processing")
    current_datetime_object = datetime.utcnow()
    current_datetime = current_datetime_object.strftime("%Y-%m-%d %H:%M:%S")
    session = DB_SESSION()
    try:
        stats = session.query(Stats).order_by(desc(Stats.created_at)).first()
        if stats is None:
            stats = Stats(
                number_products=0,
                number_orders=0,
                highest_product_price=0.0,
                highest_order_price=0.0,
                highest_product_quantity=0,
                highest_order_quantity=0,
                created_at=current_datetime_object,
            )
            session.add(stats)
            session.commit()

        # last_datetime = get_latest_datetime(current_datetime)
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
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    init_scheduler()
    app.run(port=8100)
