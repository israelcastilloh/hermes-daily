import sys
import logging
import app.decorators.auxiliary as auxiliary
import json


def load_configurations(app):
    secrets = json.loads(auxiliary.get_secret())
    app.config["ACCESS_TOKEN"] = secrets['whatsapp_token']
    app.config["APP_ID"] = secrets['meta_app_id']
    app.config["APP_SECRET"] = secrets['meta_app_secret']
    #app.config["RECIPIENT_WAID"] = sys.argv[1]
    app.config["VERSION"] = "v18.0"
    app.config["PHONE_NUMBER_ID"] = secrets['whatsapp_phonenumber']
    app.config["VERIFY_TOKEN"] = secrets['ngrok_authtoken']


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )

    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)

