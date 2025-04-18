import logging
from dynaconf import Dynaconf
from langchain_community.document_loaders import WikipediaLoader
from pydantic import Field
from .utils import MessageBody, validate_payload
from typing import Optional

logger = logging.getLogger(__name__)


class InputModel(MessageBody):
    max_docs: int = Field(
        description="The maximum number of documents to load", default=1
    )


def loader_wikipedia_handler(
    _payload: MessageBody, settings: Dynaconf
) -> Optional[MessageBody]:
    payload = validate_payload(InputModel, _payload)
    if not payload:
        return None
    logger.info(f"loader.wikipedia.handler: payload={payload}")

    docs = WikipediaLoader(query=payload.data, load_max_docs=payload.max_docs).load()

    body = "\n".join([doc.page_content for doc in docs])

    logger.info(f"loader.wikipedia.data: docs={len(docs)}")
    return MessageBody(data=body, metadata=payload.metadata)
