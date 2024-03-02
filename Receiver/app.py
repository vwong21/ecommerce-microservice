import connexion
from connexion import NoContent
import json
from datetime import datetime
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


def send_to_storage_service(event_type, event_data):

    storage_url = app_config.get(event_type, {}).get("url")
    headers = {"Content-Type": "application/json"}
    trace_id = str(uuid.uuid4())

    if not storage_url:
        logger.error(f"Unknown event type {event_type}")
        return

    try:
        logger.info(
            f"Received event {event_type} request with a trace id of {trace_id}"
        )
        event_data["trace_id"] = trace_id
        response = requests.post(storage_url, json=event_data, headers=headers)
        response.raise_for_status()
        logger.info(
            f"Returned event {event_type} response (Id: {trace_id}) with status {response.status_code}"
        )
    except requests.exceptions.RequestException as e:
        logger.error(e)


def createProduct(body):
    send_to_storage_service("products", body)
    return NoContent, 201


def processOrder(body):
    send_to_storage_service("orders", body)
    return NoContent, 201


if __name__ == "__main__":
    app.run(port=8080)
