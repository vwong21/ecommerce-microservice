import connexion
import yaml
import logging

with open("app_conf.yaml", "r") as f:
    app_config = yaml.safe_load(f.read())

with open("log_conf.yaml", "r") as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger("basicLogger")


def get_stats():
    pass


app = connexion.FlaskApp(__name__, specification_dir="")
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    app.run(port=8100)
