import connexion
import json
import logging
import logging.config
import os
import requests
import time
import uuid
import yaml

from connexion import NoContent
from datetime import datetime
from pykafka import KafkaClient

app = connexion.FlaskApp(__name__, specification_dir="")
app.add_api("openapi.yaml", base_path="/receiver", strict_validation=True, validate_responses=True)
logging.info("Connected on port 8080")

MAX_EVENTS = 5
EVENT_FILE = "events.json"

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

retry_count = 0
max_retries = app_config["events"]["max_retries"]
producer = None
while retry_count < max_retries:
    try:
        events = app_config["events"]
        kafka_server = events["hostname"]
        kafka_port = events["port"]
        kafka_topic = events["topic"]

        client = KafkaClient(hosts=f"{kafka_server}:{kafka_port}")
        topic = client.topics[str.encode(kafka_topic)]
        producer = topic.get_sync_producer()
        logging.info(f"Successfully Connected to Kafka on attempt {retry_count}")

        break
    except Exception as e:
        logging.info(f"Connection to Kafka failed on attempt {retry_count}")
        retry_count += 1
        sleep_time = app_config["events"]["retry_sleep_value"]
        time.sleep(sleep_time)


def send_to_kafka(event_type, event_data, producer):
    try:
        trace_id = str(uuid.uuid4())
        event_data["trace_id"] = trace_id

        msg = {
            "type": event_type,
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "payload": event_data,
        }
        msg_str = json.dumps(msg)
        producer.produce(msg_str.encode("utf-8"))
        logging.info(msg)

    except Exception as e:
        logger.error(e)


def createProduct(body):
    send_to_kafka("products", body, producer)
    return {"message": "Product creation request received successfully"}, 201


def processOrder(body):
    send_to_kafka("orders", body, producer)
    return {"message": "Order creation request received successfully"}, 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
