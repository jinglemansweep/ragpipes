import logging
import re
from dynaconf import Dynaconf
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .utils import MessageBody, validate_payload
from typing import Optional

logger = logging.getLogger(__name__)


class InputModel(MessageBody):
    pass


def chunk_handler(_payload: MessageBody, settings: Dynaconf) -> Optional[MessageBody]:
    payload = validate_payload(InputModel, _payload)
    if not payload:
        return None

    logger.info(
        f"chunk.handler: payload={payload} chunk_size={settings.chunking.chunk_size} chunk_overlap={settings.chunking.chunk_overlap}"
    )

    chunker = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunking.chunk_size,
        chunk_overlap=settings.chunking.chunk_overlap,
    )
    text = re.sub(r"(\n\s*)+\n", "\n\n", payload.data)
    chunks = chunker.split_text(text)
    logger.info(f"chunk.data: chunks={chunks}")
    return MessageBody(data=chunks, metadata=payload.metadata)
