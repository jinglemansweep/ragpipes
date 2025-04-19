from __future__ import annotations

import logging
import re
from typing import Any
from typing import Dict

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from pydantic import BaseModel
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class MessageBody(BaseModel):
    docs: list[Document] = []
    options: Dict[str, Any] = {}
    outputs: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}


def validate_options(options: Dict[str, Any], required_keys: list[str]):
    for key in required_keys:
        if key not in options:
            raise ValueError(f"Key '{key}' must be present in options")
    return options


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
