import connexion
import yaml
import logging
import logging.config
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


def populate_stats():
    logger.info("Start Periodic Processing")
    session = DB_SESSION()
    try:

        # Create sample Stats objects
        sample_stats = [
            Stats(
                number_products=100,
                number_orders=50,
                highest_product_price=99.99,
                highest_order_price=199.99,
                highest_product_quantity=200,
                highest_order_quantity=100,
            ),
            Stats(
                number_products=150,
                number_orders=75,
                highest_product_price=149.99,
                highest_order_price=299.99,
                highest_product_quantity=250,
                highest_order_quantity=125,
            ),
        ]

        # Add sample Stats objects to the session
        session.add_all(sample_stats)

        # Commit the session to save the data to the database
        session.commit()

        # Close the session

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
