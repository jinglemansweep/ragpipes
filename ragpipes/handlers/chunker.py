import logging
import re
from dynaconf import Dynaconf
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import field_validator
from .utils import MessageBody, validate_payload
from typing import Optional

logger = logging.getLogger(__name__)


class InputModel(MessageBody):
    @field_validator("data", mode="before")
    @classmethod
    def validate_keys(cls, v):
        if "docs" not in v:
            raise ValueError("Keys 'docs' must be present")
        return v


class OutputModel(MessageBody):
    @field_validator("data", mode="before")
    @classmethod
    def validate_keys(cls, v):
        if "docs" not in v:
            raise ValueError("Keys 'docs' must be present")
        return v


def chunker_handler(_payload: MessageBody, settings: Dynaconf) -> Optional[MessageBody]:
    payload = validate_payload(InputModel, _payload)
    if not payload:
        return None

    docs = payload.data["docs"]
    output_docs = []

    logger.info(
        f"chunker.handler: docs_count={len(docs)} chunk_size={settings.chunker.chunk_size} chunk_overlap={settings.chunker.chunk_overlap} metadata={payload.metadata}"
    )

    chunker = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunker.chunk_size,
        chunk_overlap=settings.chunker.chunk_overlap,
    )

    for doc in docs:

        input_text = re.sub(r"(\n\s*)+\n", "\n\n", doc["page_content"])
        chunks = chunker.split_text(input_text)

        for chunk in chunks:
            output_docs.append(Document(chunk, id=doc["id"], metadata=doc["metadata"]))

    data = dict(docs=output_docs)
    logger.info(f"chunker.response: docs_count={len(output_docs)}")
    return OutputModel(data=data, metadata=payload.metadata)
