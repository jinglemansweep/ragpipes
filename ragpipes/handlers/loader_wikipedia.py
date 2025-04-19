from __future__ import annotations

import logging
from typing import Optional

from dynaconf import Dynaconf
from langchain_community.document_loaders import WikipediaLoader
from pydantic import field_validator

from .utils import MessageBody
from .utils import validate_options
from .utils import validate_payload

logger = logging.getLogger(__name__)


class InputModel(MessageBody):
    @field_validator("options", mode="before")
    @classmethod
    def validate_keys(cls, v):
        return validate_options(v, ["query"])


def handler(
    _payload: MessageBody, settings: Dynaconf
) -> Optional[MessageBody]:

    payload = validate_payload(InputModel, _payload)
    if not payload:
        return None

    query = payload.options.get("query")

    logger.info(
        f"loader.wikipedia.handler: query='{query}' metadata={payload.metadata}"
    )

    docs = WikipediaLoader(query=query, load_max_docs=3).load()

    for doc in docs:
        # doc.id = str(uuid.uuid4())
        doc.metadata = doc.metadata | payload.metadata

    logger.info(f"loader.wikipedia.response: docs_count={len(docs)}")
    return MessageBody(docs=docs, metadata=payload.metadata)
