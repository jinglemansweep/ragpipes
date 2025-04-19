from __future__ import annotations

import logging
from typing import List
from typing import Optional

from dynaconf import Dynaconf
from langchain import hub
from langchain.chat_models import init_chat_model
from langchain_core.documents import Document
from langgraph.graph import START
from langgraph.graph import StateGraph
from pydantic import field_validator
from typing_extensions import TypedDict

from .utils import MessageBody
from .utils import setup_vectorstore
from .utils import validate_options
from .utils import validate_payload

logger = logging.getLogger(__name__)


class InputModel(MessageBody):
    @field_validator("options", mode="before")
    @classmethod
    def validate_keys(cls, v):
        return validate_options(v, ["query"])


class State(TypedDict):
    question: str
    context: List[Document]
    answer: str


def handler(
    _payload: MessageBody, settings: Dynaconf
) -> Optional[MessageBody]:

    payload = validate_payload(InputModel, _payload)
    if not payload:
        return None

    query = payload.options.get("query")
    db_uri = f"postgresql+psycopg://{settings.pgvector.user}:{settings.pgvector.password}@{settings.pgvector.host}:{settings.pgvector.port}/{settings.pgvector.database}"

    logger.info(f"chat.handler: query='{query}' metadata={payload.metadata}")

    vector_store = setup_vectorstore(
        settings.openai.embedding_model, db_uri, settings.pgvector.collection
    )

    prompt = hub.pull("rlm/rag-prompt")
    llm = init_chat_model(model=settings.openai.chat_model)

    # Define document retrieval stage
    def retrieve(state: State):
        retrieved_docs = vector_store.similarity_search(
            state["question"], k=5, filter=payload.metadata
        )
        return {"context": retrieved_docs}

    # Define document generation stage
    def generate(state: State):
        docs_content = "\n\n".join(
            doc.page_content for doc in state["context"]
        )
        messages = prompt.invoke(
            {"question": state["question"], "context": docs_content}
        )
        response = llm.invoke(messages)
        return {"answer": response.content}

    # Build state graph with stages
    graph_builder = StateGraph(State).add_sequence([retrieve, generate])
    graph_builder.add_edge(START, "retrieve")
    graph = graph_builder.compile()

    # Invoke graph with question
    response = graph.invoke({"question": query})
    answer = response["answer"]

    # Build context extract
    context = [
        dict(id=doc.id, content=doc.page_content, metadata=doc.metadata)
        for doc in response["context"][:2]
    ]

    outputs = dict(answer=answer, context=context)
    logger.info(
        f"chat.response: answer='{answer}' context_count={len(context)}"
    )
    return MessageBody(outputs=outputs, metadata=payload.metadata)
