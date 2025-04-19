from __future__ import annotations

import json
import logging
import traceback

import paho.mqtt.client as mqtt
from dynaconf import Dynaconf

from .config import VALIDATORS
from .handlers.chat import handler as chat_handler
from .handlers.chunker import handler as chunker_handler
from .handlers.loader_text import handler as loader_text_handler
from .handlers.loader_web import handler as loader_web_handler
from .handlers.loader_wikipedia import handler as loader_wikipedia_handler
from .handlers.translate_llmtranslate import (
    handler as translate_llmtranslate_handler,
)
from .handlers.vectorstore import handler as vectorstore_handler
from .utils import setup_logger

TOPIC_DELIMITER = ","

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
if settings.mqtt.username is not None and settings.mqtt.password is not None:
    mqttc.username_pw_set(settings.mqtt.username, settings.mqtt.password)


@mqttc.connect_callback()
def on_connect(client, userdata, flags, reason_code, properties):
    connected = reason_code == 0
    topics_in = settings.mqtt.topic_in.split(TOPIC_DELIMITER)
    topics_out = settings.mqtt.topic_out.split(TOPIC_DELIMITER)

    logger.info(
        f"MQTT connected={connected} handler={settings.mqtt.handler} topics_in={len(topics_in)} topics_out={len(topics_out)}"
    )

    for topic in topics_in:
        client.subscribe(topic)


HANDLERS = {
    "chunker": chunker_handler,
    "loader.text": loader_text_handler,
    "loader.web": loader_web_handler,
    "loader.wikipedia": loader_wikipedia_handler,
    "translate.llmtranslate": translate_llmtranslate_handler,
    "vectorstore": vectorstore_handler,
    "chat": chat_handler,
}


@mqttc.message_callback()
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except json.JSONDecodeError:
        logger.error("Invalid JSON payload")
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
            topics = settings.mqtt.topic_out.split(TOPIC_DELIMITER)
            for topic in topics:
                mqttc.publish(topic, response.model_dump_json())

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        logger.error(traceback.format_exc())


mqttc.connect(
    host=settings.mqtt.broker,
    port=settings.mqtt.port,
    keepalive=settings.mqtt.keepalive,
)


mqttc.loop_forever()
