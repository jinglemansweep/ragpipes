from __future__ import annotations

import logging
from typing import Optional

from dynaconf import Dynaconf
from langchain_core.documents import Document
from pydantic import field_validator

from .utils import MessageBody
from .utils import validate_payload

logger = logging.getLogger(__name__)


class InputModel(MessageBody):
    @field_validator("data", mode="before")
    @classmethod
    def validate_keys(cls, v):
        if "text" not in v:
            raise ValueError("Keys 'text' must be present")
        return v


class OutputModel(MessageBody):
    @field_validator("data", mode="before")
    @classmethod
    def validate_keys(cls, v):
        if "docs" not in v:
            raise ValueError("Keys 'docs' must be present")
        return v


def loader_text_handler(
    _payload: MessageBody, settings: Dynaconf
) -> Optional[MessageBody]:

    payload = validate_payload(InputModel, _payload)
    if not payload:
        return None

    text = payload.data["text"]

    logger.info(
        f"loader.text.handler: text='{text}' metadata={payload.metadata}"
    )

    try:

        doc = Document(page_content=text, metadata=payload.metadata)
        data = dict(docs=[doc])
        logger.info(f"loader.text.response: docs_count={len(data['docs'])}")
        return OutputModel(data=data, metadata=payload.metadata)

    except Exception as e:
        logger.error(f"loader.web.handler: error={e}")
        return None
