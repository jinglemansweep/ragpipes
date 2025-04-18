from dynaconf import Validator

# Env Var Format: RAGPIPE_GENERAL__LOG_LEVEL, RAGPIPE_MQTT__BROKER, RAGPIPE_PGVECTOR__HOST, etc.

VALIDATORS = [
    # GENERAL
    Validator("general.log_level", default="info"),  # error, warning, info, debug
    # MQTT
    Validator("mqtt.broker", default="localhost"),
    Validator("mqtt.port", default=1883, cast=int),
    Validator("mqtt.keepalive", default=60, cast=int),
    Validator("mqtt.username", default=None),
    Validator("mqtt.password", default=None),
    Validator("mqtt.topic_command", default="ragpipe/command"),
    Validator("mqtt.topic_response", default="ragpipe/response"),
    Validator("mqtt.handler", default=None),
    # PGVECTOR
    Validator("pgvector.host", default="localhost"),
    Validator("pgvector.port", default=5432, cast=int),
    Validator("pgvector.user", default="postgres"),
    Validator("pgvector.password", default="postgres"),
    Validator("pgvector.database", default="postgres"),
    Validator("pgvector.collection", default="ragpipe"),
    # OPENAI
    Validator("openai.chat_model", default="gpt-4o-mini"),
    Validator("openai.embedding_model", default="text-embedding-ada-002"),
]
