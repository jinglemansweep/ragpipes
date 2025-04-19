import logging
from dynaconf import Dynaconf
from langchain_core.documents import Document
from pydantic import field_validator
from .utils import MessageBody, setup_vectorstore, validate_payload
from typing import Optional

logger = logging.getLogger(__name__)


class InputModel(MessageBody):
    @field_validator("data", mode="before")
    @classmethod
    def validate_keys(cls, v):
        if "docs" not in v:
            raise ValueError("Keys 'docs' must be present")
        return v


class OutputModel(MessageBody):
    @field_validator("data", mode="before")
    @classmethod
    def validate_keys(cls, v):
        if "added" not in v:
            raise ValueError("Keys 'added' must be present")
        if "collection" not in v:
            raise ValueError("Keys 'collection' must be present")
        return v


def vectorstore_handler(
    _payload: MessageBody, settings: Dynaconf
) -> Optional[MessageBody]:
    payload = validate_payload(InputModel, _payload)
    if not payload:
        return None

    db_uri = f"postgresql+psycopg://{settings.pgvector.user}:{settings.pgvector.password}@{settings.pgvector.host}:{settings.pgvector.port}/{settings.pgvector.database}"
    docs = payload.data["docs"]
    output_docs = []

    logger.info(
        f"vectorstore.handler: docs_count={len(docs)} metadata={payload.metadata}"
    )

    vector_store = setup_vectorstore(
        settings.openai.embedding_model, db_uri, settings.pgvector.collection
    )

    for doc in docs:

        output_docs.append(
            Document(
                id=doc["id"],
                page_content=doc["page_content"],
                metadata=doc["metadata"],
            )
        )

    try:
        vector_store.add_documents(output_docs)
    except Exception as e:
        logger.error(f"vectorstore.handler: error={e}")
        return None

    data = dict(added=len(output_docs), collection=settings.pgvector.collection)
    logger.info(
        f"vectorstore.data: docs_added={len(output_docs)} collection={settings.pgvector.collection} "
    )
    return OutputModel(
        data=data,
        metadata=payload.metadata,
    )
