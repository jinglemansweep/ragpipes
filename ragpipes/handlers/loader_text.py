from __future__ import annotations

import logging
from typing import Optional

from dynaconf import Dynaconf
from langchain_core.documents import Document
from pydantic import field_validator

from .utils import MessageBody
from .utils import validate_options
from .utils import validate_payload

logger = logging.getLogger(__name__)


class InputModel(MessageBody):
    @field_validator("options", mode="before")
    @classmethod
    def validate_keys(cls, v):
        return validate_options(v, ["text"])


def handler(
    _payload: MessageBody, settings: Dynaconf
) -> Optional[MessageBody]:

    payload = validate_payload(InputModel, _payload)
    if not payload:
        return None

    text = payload.options.get("text")

    logger.info(
        f"loader.text.handler: text='{text}' metadata={payload.metadata}"
    )

    try:

        doc = Document(page_content=text, metadata=payload.metadata)
        logger.info(f"loader.text.response: text={text}")
        return MessageBody(docs=[doc], metadata=payload.metadata)

    except Exception as e:
        logger.error(f"loader.web.handler: error={e}")
        return None
