import logging
from dynaconf import Dynaconf
from langchain_community.document_loaders import WikipediaLoader
from pydantic import field_validator
from .utils import MessageBody, validate_payload
from typing import Optional

logger = logging.getLogger(__name__)


class InputModel(MessageBody):
    @field_validator("data", mode="before")
    @classmethod
    def validate_keys(cls, v):
        if "query" not in v:
            raise ValueError("Keys 'query' must be present")
        return v


class OutputModel(MessageBody):
    @field_validator("data", mode="before")
    @classmethod
    def validate_keys(cls, v):
        if "docs" not in v:
            raise ValueError("Keys 'docs' must be present")
        return v


def loader_wikipedia_handler(
    _payload: MessageBody, settings: Dynaconf
) -> Optional[MessageBody]:

    payload = validate_payload(InputModel, _payload)
    if not payload:
        return None

    query = payload.data["query"]
    logger.info(
        f"loader.wikipedia.handler: query='{query}' metadata={payload.metadata}"
    )

    docs = WikipediaLoader(query=query, load_max_docs=3).load()

    for doc in docs:
        # doc.id = str(uuid.uuid4())
        doc.metadata = doc.metadata | payload.metadata

    data = dict(docs=docs)
    logger.info(f"loader.wikipedia.response: docs_count={len(docs)}")
    return OutputModel(data=data, metadata=payload.metadata)
