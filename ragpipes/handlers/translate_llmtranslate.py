from __future__ import annotations

import logging
from typing import Optional

from dynaconf import Dynaconf
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from llmtranslate import Translator

from .utils import MessageBody
from .utils import validate_payload

logger = logging.getLogger(__name__)


def handler(
    _payload: MessageBody, settings: Dynaconf
) -> Optional[MessageBody]:

    payload = validate_payload(MessageBody, _payload)
    if not payload:
        return None

    docs = payload.options.get("docs")
    output_docs = []

    logger.info(
        f"translate.llmtranslate.handler: docs_count={len(docs)} language={settings.translate.language} metadata={payload.metadata}"
    )

    llm = ChatOpenAI(model=settings.openai.translate_model)
    translator = Translator(llm=llm)

    for doc in docs:
        text_language = translator.get_text_language(doc["page_content"])
        if text_language:
            output_docs.append(
                Document(
                    page_content=translator.translate(
                        doc["page_content"], settings.translate.language
                    ),
                    metadata=(
                        doc.get("metadata", {})
                        | payload.metadata
                        | {"language": settings.translate.language}
                    ),
                )
            )
        else:
            logger.info("Language not detected")

    logger.info(f"translate.llmtranslate.response: docs_count={len(docs)}")
    return MessageBody(docs=docs, metadata=payload.metadata)
