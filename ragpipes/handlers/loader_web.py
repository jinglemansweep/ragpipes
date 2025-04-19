import logging
from dynaconf import Dynaconf
from langchain_community.document_loaders import WebBaseLoader
from pydantic import field_validator
from .utils import MessageBody, validate_payload, clean_text_body
from typing import Optional

logger = logging.getLogger(__name__)


class InputModel(MessageBody):
    @field_validator("data", mode="before")
    @classmethod
    def validate_keys(cls, v):
        if "url" not in v:
            raise ValueError("Keys 'url' must be present")
        return v


class OutputModel(MessageBody):
    @field_validator("data", mode="before")
    @classmethod
    def validate_keys(cls, v):
        if "docs" not in v:
            raise ValueError("Keys 'docs' must be present")
        return v


def loader_web_handler(
    _payload: MessageBody, settings: Dynaconf
) -> Optional[MessageBody]:
    payload = validate_payload(InputModel, _payload)
    if not payload:
        return None

    url = payload.data["url"]

    logger.info(f"loader.web.handler: url='{url}' metadata={payload.metadata}")

    try:

        loader = WebBaseLoader(url)
        docs = loader.load()

        for doc in docs:
            # doc.id = str(uuid.uuid4())
            doc.page_content = clean_text_body(doc.page_content)
            doc.metadata = doc.metadata | payload.metadata

        data = dict(docs=docs)
        logger.info(f"loader.web.response: docs_count={len(docs)}")
        return OutputModel(data=data, metadata=payload.metadata)

    except Exception as e:
        logger.error(f"loader.web.handler: error={e}")
        return None
