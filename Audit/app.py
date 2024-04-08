import connexion
import json
import logging
import logging.config
import os
import yaml

from flask_cors import CORS
from pykafka import KafkaClient

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

# External Logging Configuration
with open(log_conf_file, "r") as f:
    log_config = yaml.safe_load(f.read())

logging.config.dictConfig(log_config)
logger = logging.getLogger("basicLogger")
logger.info("App Conf File: %s" % app_conf_file)
logger.info("Log Conf File: %s" % log_conf_file)


def get_event_by_index(event_type, index):
    events = app_config["events"]
    hostname = "%s:%d" % (events["hostname"], events["port"])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(events["topic"])]

    consumer = topic.get_simple_consumer(
        reset_offset_on_start=True, consumer_timeout_ms=1000
    )

    logger.info(f"Retrieving {event_type} at index {index}")

    try:
        count = 0
        for msg in consumer:
            msg_str = msg.value.decode("utf-8")
            msg_json = json.loads(msg_str)
            if msg_json["type"] == event_type:
                if count == index:
                    return msg_json["payload"], 200
                count += 1
    except Exception as e:
        logger.error(e)
        logger.error(f"Could not find {event_type} at index {index}: {e}")
    return {"message": "Not Found"}, 404


def getProductInformation(index):
    return get_event_by_index("products", index)


def getOrderInformation(index):
    return get_event_by_index("orders", index)


app = connexion.FlaskApp(__name__, specification_dir="")

if "TARGET_ENV" not in os.environ or os.environ["TARGET_ENV"] != "test":
    CORS(app.app)
    app.app.config["CORS_HEADERS"] = "Content-Type"

app.add_api("openapi.yaml", base_path="/audit", strict_validation=True, validate_responses=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8110)
