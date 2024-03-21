import connexion
import json
import logging
import logging.config
import yaml
from connexion.middleware import MiddlewarePosition
from pykafka import KafkaClient
from starlette.middleware.cors import CORSMiddleware

with open("app_conf.yaml", "r") as f:
    app_config = yaml.safe_load(f.read())

with open("log_conf.yaml", "r") as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger("basicLogger")


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
app.add_middleware(
    CORSMiddleware,
    position=MiddlewarePosition.BEFORE_EXCEPTION,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8110)
