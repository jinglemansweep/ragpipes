from __future__ import annotations

import logging
from typing import Optional

from dynaconf import Dynaconf

from .utils import MessageBody
from .utils import setup_vectorstore
from .utils import validate_payload

logger = logging.getLogger(__name__)


def handler(
    _payload: MessageBody, settings: Dynaconf
) -> Optional[MessageBody]:

    payload = validate_payload(MessageBody, _payload)
    if not payload:
        return None

    db_uri = f"postgresql+psycopg://{settings.pgvector.user}:{settings.pgvector.password}@{settings.pgvector.host}:{settings.pgvector.port}/{settings.pgvector.database}"

    logger.info(
        f"vectorstore.handler: docs_count={len(payload.docs)} metadata={payload.metadata}"
    )

    vector_store = setup_vectorstore(
        settings.openai.embedding_model, db_uri, settings.pgvector.collection
    )

    try:
        vector_store.add_documents(payload.docs)
    except Exception as e:
        logger.error(f"vectorstore.handler: error={e}")
        return None

    logger.info(
        f"vectorstore.data: docs_added={len(payload.docs)} collection={settings.pgvector.collection} "
    )

    return MessageBody(
        docs=payload.docs,
        outputs=dict(collection=settings.pgvector.collection),
        metadata=payload.metadata,
    )
