import connexion
import yaml
import logging
import logging.config
import requests
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from base import Base
from stats import Stats


with open("app_conf.yaml", "r") as f:
    app_config = yaml.safe_load(f.read())

DB_ENGINE = create_engine("sqlite:///%s" % app_config["datastore"]["filename"])
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)

with open("log_conf.yaml", "r") as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger("basicLogger")


def get_latest_datetime():
    session = DB_SESSION()
    try:
        latest_stat = session.query(Stats).order_by(Stats.created_at.desc()).first()
        if latest_stat:
            latest_datetime = latest_stat.created_at
        else:
            latest_datetime = datetime.now()
    except Exception as e:
        logger.error(e)
    finally:
        session.close()
    return latest_datetime


def populate_stats():
    logger.info("Start Periodic Processing")
    session = DB_SESSION()
    try:
        stats = session.query(Stats).first()
        if stats is None:
            stats = Stats(
                number_products=0,
                number_orders=0,
                highest_product_price=0.0,
                highest_order_price=0.0,
                highest_product_quantity=0,
                highest_order_quantity=0,
                created_at=datetime.now(),
            )
            session.add(stats)
            session.commit()

        current_datetime = datetime.now()
        last_datetime = get_latest_datetime()
        product_endpoint = "http://localhost:8090/products"
        order_endpoint = "http://localhost:8090/orders"

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

        logger.info(f"Product response status code: {response_product.status_code}")
        logger.info(f"Order response status code: {response_order.status_code}")

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
    pass


app = connexion.FlaskApp(__name__, specification_dir="")
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    init_scheduler()
    app.run(port=8100)
