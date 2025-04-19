import json
import logging
import os
import paho.mqtt.client as mqtt
from dynaconf import Dynaconf
from .config import VALIDATORS
from .handlers.chat import chat_handler
from .handlers.chunker import chunker_handler
from .handlers.vectorstore import vectorstore_handler
from .handlers.loader_web import loader_web_handler
from .handlers.loader_wikipedia import loader_wikipedia_handler
from .utils import setup_logger

if "LANGCHAIN_TRACING_V2" in os.environ:
    del os.environ["LANGCHAIN_TRACING_V2"]

settings = Dynaconf(
    envvar_prefix="RAGPIPE",
    settings_files=["settings.yml", "secrets.yml"],
    validators=VALIDATORS,
    merge_enabled=True,
    load_dotenv=True,
)


setup_logger(settings.general.log_level)

logger = logging.getLogger(__name__)

logger.debug(f"settings: {settings.to_dict()}")

# ===========
# MQTT CLIENT
# ===========

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


@mqttc.message_callback()
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except json.JSONDecodeError:
        print(f"Invalid JSON payload: {payload}")
        return
    response = None

    try:
        if settings.mqtt.handler == "chunker":
            response = chunker_handler(payload, settings)

        elif settings.mqtt.handler == "loader.web":
            response = loader_web_handler(payload, settings)

        elif settings.mqtt.handler == "loader.wikipedia":
            response = loader_wikipedia_handler(payload, settings)

        elif settings.mqtt.handler == "vectorstore":
            response = vectorstore_handler(payload, settings)

        elif settings.mqtt.handler == "chat":
            response = chat_handler(payload, settings)

        else:
            logger.error(f"Unknown handler: {settings.mqtt.handler}")
            return

        if response:
            logger.debug(f"response: {response}")
            mqttc.publish(f"{settings.mqtt.topic_response}", response.model_dump_json())

    except Exception as e:
        logger.error(f"Error processing message: {e}")


mqttc.connect(
    host=settings.mqtt.broker,
    port=settings.mqtt.port,
    keepalive=settings.mqtt.keepalive,
)


mqttc.loop_forever()
