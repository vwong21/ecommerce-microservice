import connexion
import json
import logging
import logging.config
import os
import time
import yaml

from base import Base
from events import Events
from pykafka import KafkaClient
from pykafka.common import OffsetType
from sqlalchemy import create_engine
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker
from threading import Thread

app = connexion.FlaskApp(__name__, specification_dir="")
app.add_api(
    "openapi.yaml",
    base_path="/event-logger",
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

with open(log_conf_file, "r") as f:
    log_config = yaml.safe_load(f.read())

logging.config.dictConfig(log_config)
logger = logging.getLogger("basicLogger")
logger.info("App Conf File: %s" % app_conf_file)
logger.info("Log Conf File: %s" % log_conf_file)

DB_ENGINE = create_engine("sqlite:///%s" % app_config["datastore"]["filename"])
Base.metadata.bind = DB_ENGINE
Base.metadata.create_all(DB_ENGINE)
DB_SESSION = sessionmaker(bind=DB_ENGINE)


def process_events():
    max_retries = app_config["event_log"]["max_retries"]
    retry_count = 0

    while retry_count < max_retries:
        try:
            logging.info(f"Connecting to Kafka. Current attempt: {retry_count}")
            event_log = app_config["event_log"]
            hostname = "%s:%d" % (event_log["hostname"], event_log["port"])
            client = KafkaClient(hosts=hostname)
            topic = client.topics[str.encode(event_log["topic"])]
            consumer = topic.get_simple_consumer(
                consumer_group=b"event_group",
                reset_offset_on_start=False,
                auto_offset_reset=OffsetType.LATEST,
            )
            logging.info("Successfully connected to Kafka")
            for msg in consumer:
                msg_str = msg.value.decode("utf-8")
                msg = json.loads(msg_str)
                logger.info("Message: %s" % msg)

                payload = msg["payload"]

                events = Events(message=payload["message"], code=payload["code"])

                session = DB_SESSION()
                logging.info("Connected to database. Logging event to database.")
                session.add(events)
                session.commit()
                session.close()
                logger.debug(
                    f"Stored event type {payload['code']} with message {payload['message']}"
                )
                consumer.commit_offsets()
            break
        except Exception as e:
            logger.error(e)
            retry_count += 1
            sleep_time = app_config["event_log"]["retry_sleep_value"]
            time.sleep(sleep_time)


def stats():
    logging.info("Request for event stats has started")
    try:
        session = DB_SESSION()
        event_counts = (
            session.query(Events.code, func.count(Events.id))
            .group_by(Events.code)
            .all()
        )
        session.close()
        stats = {}
        for code, count in event_counts:
            stats[code] = count
        return stats, 200
    except Exception as e:
        logger.error("Error retrieving event stats: %s" % e)
        return {"error": "Failed to retrieve event stats"}, 500


if __name__ == "__main__":
    t1 = Thread(target=process_events)
    t1.daemon = True
    t1.start()
    app.run(host="0.0.0.0", port=8120)
