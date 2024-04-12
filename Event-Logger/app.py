import connexion
import json
import logging
import logging.config
import os
import time
import yaml

from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread

app = connexion.FlaskApp(__name__, specification_dir="")
app.add_api(
    "openapi.yaml",
    base_path="/event_stats",
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
                consumer.commit_offsets()
        except Exception as e:
            logger.error(e)
            retry_count += 1
            sleep_time = app_config["event_log"]["retry_sleep_value"]
            time.sleep(sleep_time)


def event_stats():
    pass


if __name__ == "__main__":
    t1 = Thread(target=process_events)
    t1.daemon = True
    t1.start()
    app.run(host="0.0.0.0", port=8120)
