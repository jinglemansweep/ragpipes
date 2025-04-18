from dynaconf import Dynaconf
from langchain.chat_models import init_chat_model
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

import json
import paho.mqtt.client as mqtt
import pprint

from .config import VALIDATORS
from .handlers import handler

settings = Dynaconf(
    envvar_prefix="RAGPIPE",
    settings_files=["settings.yml", "secrets.yml"],
    validators=VALIDATORS,
)

print(settings.to_dict())

# =========
# AI MODELS
# =========

chat_model = init_chat_model(
    model=settings.openai.chat_model,
    temperature=settings.openai.temperature,
    max_tokens=settings.openai.max_tokens,
)
embeddings = OpenAIEmbeddings(model=settings.openai.embedding_model)

# ========
# PGVECTOR
# ========

database_url = f"postgresql+psycopg://{settings.pgvector.user}:{settings.pgvector.password}@{settings.pgvector.host}:{settings.pgvector.port}/{settings.pgvector.database}"

vector_store = PGVector(
    connection=database_url,
    collection_name=settings.pgvector.collection,
    embeddings=embeddings,
    async_mode=False,
    use_jsonb=True,
)


# ===========
# MQTT CLIENT
# ===========


mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
if settings.mqtt.username and settings.mqtt.password:
    mqttc.username_pw_set(settings.mqtt.username, settings.mqtt.password)


@mqttc.connect_callback()
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    client.subscribe("ragpipe/#")


@mqttc.message_callback()
def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode("utf-8")
    try:
        json_payload = json.loads(payload)
    except json.JSONDecodeError:
        print(f"Invalid JSON payload: {payload}")
        return
    return handler(topic, json_payload)


mqttc.connect(
    host=settings.mqtt.broker,
    port=settings.mqtt.port,
    keepalive=settings.mqtt.keepalive,
)


mqttc.loop_forever()
