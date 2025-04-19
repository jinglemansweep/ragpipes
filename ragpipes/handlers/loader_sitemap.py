from __future__ import annotations

import logging
from typing import Optional

from dynaconf import Dynaconf
from langchain_community.document_loaders import SitemapLoader
from pydantic import field_validator

from .utils import clean_text_body
from .utils import MessageBody
from .utils import validate_options
from .utils import validate_payload

logger = logging.getLogger(__name__)


class InputModel(MessageBody):
    @field_validator("options", mode="before")
    @classmethod
    def validate_keys(cls, v):
        return validate_options(v, ["url"])


def handler(
    _payload: MessageBody, settings: Dynaconf
) -> Optional[MessageBody]:

    payload = validate_payload(InputModel, _payload)
    if not payload:
        return None

    url = payload.options.get("url")

    logger.info(
        f"loader.sitemap.handler: url='{url}' metadata={payload.metadata}"
    )

    try:

        loader = SitemapLoader(url)
        docs = loader.load()

        for doc in docs:
            doc.page_content = clean_text_body(doc.page_content)
            doc.metadata = doc.metadata | payload.metadata

        logger.info(f"loader.sitemap.response: docs_count={len(docs)}")
        return MessageBody(docs=docs, metadata=payload.metadata)

    except Exception as e:
        logger.error(f"loader.sitemap.handler: error={e}")
        return None
