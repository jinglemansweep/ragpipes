import logging
from dynaconf import Dynaconf
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import Field
from .utils import MessageBody, validate_payload
from typing import Optional

logger = logging.getLogger(__name__)


class InputModel(MessageBody):
    chunk_size: int = Field(description="The size of each chunk", default=1000)
    chunk_overlap: int = Field(description="The overlap between chunks", default=200)


def text_handler(_payload: MessageBody, settings: Dynaconf) -> Optional[MessageBody]:
    payload = validate_payload(InputModel, _payload)
    if not payload:
        return None
    logger.info(f"handler.text: payload={payload}")

    chunker = RecursiveCharacterTextSplitter(
        chunk_size=payload.chunk_size, chunk_overlap=payload.chunk_overlap
    )
    chunks = chunker.split_text(payload.data)
    logger.info(f"text: chunks={chunks}")
    return MessageBody(data=chunks, metadata=payload.metadata)
