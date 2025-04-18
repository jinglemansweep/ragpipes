import logging
from dynaconf import Dynaconf
from .utils import MessageBody, setup_vectorstore, validate_payload
from typing import Optional

logger = logging.getLogger(__name__)


class InputModel(MessageBody):
    pass


def vectorstore_handler(
    _payload: MessageBody, settings: Dynaconf
) -> Optional[MessageBody]:
    payload = validate_payload(InputModel, _payload)
    if not payload:
        return None
    logger.info(f"vectorstore.handler: payload={payload}")

    db_uri = f"postgresql+psycopg://{settings.pgvector.user}:{settings.pgvector.password}@{settings.pgvector.host}:{settings.pgvector.port}/{settings.pgvector.database}"
    vector_store = setup_vectorstore(
        settings.openai.embedding_model, db_uri, settings.pgvector.collection
    )

    vector_store.add_texts(payload.data, [payload.metadata])

    logger.info(
        f"vectorstore.data: collection={settings.pgvector.collection} added={len(payload.data)}"
    )

    return MessageBody(
        data=dict(
            added=len(payload.data),
            collection=settings.pgvector.collection,
        ),
        metadata=payload.metadata,
    )
