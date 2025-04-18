import logging
import re
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from pydantic import BaseModel, ValidationError
from typing import Any

logger = logging.getLogger(__name__)


class MessageBody(BaseModel):
    data: Any
    metadata: dict = {}


def validate_payload(model, payload):
    try:
        options = model.model_validate(payload)
    except ValidationError as e:
        logger.warning(f"Invalid payload: {e} {payload}")
        return
    return options


def setup_vectorstore(embedding_model: str, db_uri: str, collection: str):
    embeddings = OpenAIEmbeddings(model=embedding_model)
    return PGVector(
        embeddings=embeddings,
        collection_name=collection,
        connection=db_uri,
        use_jsonb=True,
    )


def clean_text_body(text: str) -> str:
    return strip_duplicate_newlines(strip_duplicate_whitespace(text))


def strip_duplicate_whitespace(text: str) -> str:
    return re.sub(r" +", " ", text)


def strip_duplicate_newlines(text: str) -> str:
    return re.sub(r"(\n\s*)+\n", "\n\n", text)
