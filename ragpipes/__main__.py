from __future__ import annotations

import json
import logging

import paho.mqtt.client as mqtt
from dynaconf import Dynaconf

from .config import VALIDATORS
from .handlers.chat import chat_handler
from .handlers.chunker import chunker_handler
from .handlers.loader_text import loader_text_handler
from .handlers.loader_web import loader_web_handler
from .handlers.loader_wikipedia import loader_wikipedia_handler
from .handlers.vectorstore import vectorstore_handler
from .utils import setup_logger


settings = Dynaconf(
    envvar_prefix="RAGPIPES",
    settings_files=["settings.yml", "secrets.yml"],
    validators=VALIDATORS,
    merge_enabled=True,
    load_dotenv=True,
)


setup_logger(settings.general.log_level)

logger = logging.getLogger(__name__)

logger.debug(f"settings: {settings.to_dict()}")

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
if settings.mqtt.username and settings.mqtt.password:
    mqttc.username_pw_set(settings.mqtt.username, settings.mqtt.password)


@mqttc.connect_callback()
def on_connect(client, userdata, flags, reason_code, properties):
    connected = reason_code == 0
    logger.info(
        f"MQTT connected={connected} handler={settings.mqtt.handler} command_topic={settings.mqtt.topic_command} response_topic={settings.mqtt.topic_response}"
    )
    client.subscribe(f"{settings.mqtt.topic_command}")


HANDLERS = {
    "chunker": chunker_handler,
    "loader.text": loader_text_handler,
    "loader.web": loader_web_handler,
    "loader.wikipedia": loader_wikipedia_handler,
    "vectorstore": vectorstore_handler,
    "chat": chat_handler,
}


@mqttc.message_callback()
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except json.JSONDecodeError:
        print(f"Invalid JSON payload: {payload}")
        return

    response = None

    try:

        if settings.mqtt.handler in HANDLERS:
            response = HANDLERS[settings.mqtt.handler](payload, settings)
        else:
            logger.error(f"Unknown handler: {settings.mqtt.handler}")
            return

        if response:
            logger.debug(f"response: {response}")
            mqttc.publish(
                f"{settings.mqtt.topic_response}", response.model_dump_json()
            )

    except Exception as e:
        logger.error(f"Error processing message: {e}")


mqttc.connect(
    host=settings.mqtt.broker,
    port=settings.mqtt.port,
    keepalive=settings.mqtt.keepalive,
)


mqttc.loop_forever()
