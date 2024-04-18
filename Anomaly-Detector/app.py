import connexion
import logging
import logging.config
import json
import os
import time
import yaml

from flask_cors import CORS
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread

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


def process_messages():
    max_retries = app_config["events"]["max_retries"]
    retry_count = 0
    while retry_count < max_retries:
        try:
            logging.info(f"connecting to Kafka. Current attempt: {retry_count}")
            events = app_config["events"]
            hostname = "%s:%d" % (events["hostname"], events["port"])
            client = KafkaClient(hosts=hostname)
            topic = client.topics[str.encode(events["topic"])]
            consumer = topic.get_simple_consumer(
                consumer_group=b"event_group",
                reset_offset_on_start=False,
                auto_offset_reset=OffsetType.LATEST,
            )
            logging.info(
                f"Successfully connected to Kafka topic {app_config['events']['topic']}"
            )
            for msg in consumer:
                msg_str = msg.value.decode("utf-8")
                msg = json.loads(msg_str)
                logging.info("Message: %s" % msg)

                payload = msg["payload"]

                if msg["type"] == "products":
                    if payload["price"] < 0:
                        logging.info("Anomaly detected")
                elif msg["type"] == "orders":
                    if payload["quantity"] < 0:
                        logging.info("Anomaly Detected")
            break
        except Exception as e:
            logger.error(e)
            retry_count += 1
            sleep_time = app_config["events"]["retry_sleep_value"]
            time.sleep(sleep_time)


app = connexion.FlaskApp(__name__, specification_dir="")
if "TARGET_ENV" not in os.environ or os.environ["TARGET_ENV"] != "test":
    CORS(app.app)
    app.app.config["CORS_HEADERS"] = "Content-Type"

app.add_api(
    "openapi.yaml",
    base_path="/anomaly-detector",
    strict_validation=True,
    validate_responses=True,
)

if __name__ == "__main__":
    t1 = Thread(target=process_messages)
    t1.daemon
    t1.start()
    logging.info("app running on port 8130")
    app.run(host="0.0.0.0", port=8130)
