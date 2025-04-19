from __future__ import annotations

import logging
import re
from typing import Optional

from dynaconf import Dynaconf
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .utils import MessageBody
from .utils import validate_payload

logger = logging.getLogger(__name__)


def handler(
    _payload: MessageBody, settings: Dynaconf
) -> Optional[MessageBody]:

    payload = validate_payload(MessageBody, _payload)
    if not payload:
        return None

    docs = []

    logger.info(
        f"chunker.handler: docs_count={len(payload.docs)} chunk_size={settings.chunker.chunk_size} chunk_overlap={settings.chunker.chunk_overlap} metadata={payload.metadata}"
    )

    chunker = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunker.chunk_size,
        chunk_overlap=settings.chunker.chunk_overlap,
    )

    for doc in payload.docs:

        input_text = re.sub(r"(\n\s*)+\n", "\n\n", doc.page_content)
        chunks = chunker.split_text(input_text)

        for chunk in chunks:
            docs.append(Document(chunk, id=doc.id, metadata=doc.metadata))

    logger.info(f"chunker.response: docs_count={len(docs)}")
    return MessageBody(docs=docs, metadata=payload.metadata)
