import connexion
from connexion import NoContent
import json
from datetime import datetime
from pykafka import KafkaClient
import requests
import yaml
import logging
import logging.config
import uuid

app = connexion.FlaskApp(__name__, specification_dir="")
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)

MAX_EVENTS = 5
EVENT_FILE = "events.json"

with open("log_conf.yaml", "r") as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger("basicLogger")

with open("app_conf.yaml", "r") as f:
    app_config = yaml.safe_load(f.read())


def send_to_kafka(event_type, event_data):
    try:

        events = app_config["events"]
        kafka_server = events["hostname"]
        kafka_port = events["port"]
        kafka_topic = events["topic"]

        client = KafkaClient(hosts=f"{kafka_server}:{kafka_port}")
        topic = client.topics[str.encode(kafka_topic)]
        producer = topic.get_sync_producer()

        trace_id = str(uuid.uuid4())
        event_data["trace_id"] = trace_id

        msg = {
            "type": event_type,
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "payload": event_data,
        }
        msg_str = json.dumps(msg)
        producer.produce(msg_str.encode("utf-8"))

    except Exception as e:
        logger.error(e)


def createProduct(body):
    send_to_kafka("products", body)
    return NoContent, 201


def processOrder(body):
    send_to_kafka("orders", body)
    return NoContent, 201


if __name__ == "__main__":
    app.run(port=8080)
