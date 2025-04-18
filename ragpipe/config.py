from dynaconf import Validator

VALIDATORS = [
    # GENERAL
    Validator("general.log_level", default="info"),  # error, warning, info, debug
    # MQTT
    Validator("mqtt.broker", default="localhost"),
    Validator("mqtt.port", default=1883, cast=int),
    Validator("mqtt.keepalive", default=60, cast=int),
    Validator("mqtt.username", default=None),
    Validator("mqtt.password", default=None),
    Validator("mqtt.topic", default="ragpipe"),
    # PGVECTOR
    Validator("pgvector.host", default="localhost"),
    Validator("pgvector.port", default=5432, cast=int),
    Validator("pgvector.user", default="postgres"),
    Validator("pgvector.password", default="postgres"),
    Validator("pgvector.database", default="postgres"),
    Validator("pgvector.collection", default="ragpipe"),
    # CHUNKER
    Validator("chunker.chunk_size", default=1000, cast=int),
    Validator("chunker.chunk_overlap", default=200, cast=int),
    # OPENAI
    Validator("openai.api_key", default=None),
    Validator("openai.chat_model", default="gpt-3.5-turbo"),
    Validator("openai.embedding_model", default="text-embedding-ada-002"),
    Validator("openai.temperature", default=0.0, cast=float),
    Validator("openai.max_tokens", default=1000, cast=int),
    # ANTHROPIC
    Validator("anthropic.api_key", default=None),
    Validator("anthropic.model", default="claude-3-5-sonnet-20240620"),
]
