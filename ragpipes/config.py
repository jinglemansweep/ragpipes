from __future__ import annotations

from dynaconf import Validator

# Env Var Format: RAGPIPES_GENERAL__LOG_LEVEL, RAGPIPES_MQTT__BROKER, RAGPIPES_PGVECTOR__HOST, etc.

VALIDATORS = [
    # GENERAL
    Validator(
        "general.log_level", default="info"
    ),  # error, warning, info, debug
    # MQTT
    Validator("mqtt.broker", default="localhost"),
    Validator("mqtt.port", default=1883, cast=int),
    Validator("mqtt.keepalive", default=60, cast=int),
    Validator("mqtt.username", default=None),
    Validator("mqtt.password", default=None),
    Validator("mqtt.topic_in", default=None),
    Validator("mqtt.topic_out", default=None),
    Validator("mqtt.handler", default=None),
    # PGVECTOR
    Validator("pgvector.host", default="localhost"),
    Validator("pgvector.port", default=5432, cast=int),
    Validator("pgvector.user", default="postgres"),
    Validator("pgvector.password", default="postgres"),
    Validator("pgvector.database", default="postgres"),
    Validator("pgvector.collection", default="ragpipe"),
    # CHUNKING
    Validator("chunker.chunk_size", default=1000),
    Validator("chunker.chunk_overlap", default=50),
    # TRANSLATE
    Validator("translate.language", default="en"),
    # OPENAI
    Validator("openai.chat_model", default="gpt-4o-mini"),
    Validator("openai.embedding_model", default="text-embedding-ada-002"),
    Validator("openai.translate_model", default="gpt-4o-mini"),
]
