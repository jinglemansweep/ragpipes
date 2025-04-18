import logging
from dynaconf import Dynaconf
from langchain_community.document_loaders import WebBaseLoader

# from pydantic import Field
from .utils import MessageBody, validate_payload
from typing import Optional

logger = logging.getLogger(__name__)


class InputModel(MessageBody):
    pass


def loader_web_handler(
    _payload: MessageBody, settings: Dynaconf
) -> Optional[MessageBody]:
    payload = validate_payload(InputModel, _payload)
    if not payload:
        return None
    logger.info(f"loader.web.handler: payload={payload}")

    loader = WebBaseLoader(payload.data)
    docs = loader.load()
    body = "\n".join([doc.page_content for doc in docs])

    logger.info(f"loader.web.data: docs={len(docs)}")
    return MessageBody(data=body, metadata=payload.metadata)
