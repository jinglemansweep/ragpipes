import os
from dotenv import load_dotenv
from langchain import hub
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders.firecrawl import FireCrawlLoader
from langgraph.graph import START, StateGraph
from typing_extensions import List, TypedDict
from langchain.chat_models import init_chat_model
from langchain_openai import OpenAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_postgres import PGVector


load_dotenv()

OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_LLM_MODEL = os.environ.get("OPENAI_LLM_MODEL", "gpt-4o-mini")
OPENAI_EMBEDDINGS_MODEL = os.environ.get(
    "OPENAI_EMBEDDINGS_MODEL", "text-embedding-3-large"
)
FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY")

SPLITTER_CHUNK_SIZE = 1000
SPLITTER_CHUNK_OVERLAP = 200


class State(TypedDict):
    question: str
    context: List[Document]
    answer: str


def main():

    # Initialize models
    llm = init_chat_model(model=OPENAI_LLM_MODEL)
    embeddings = OpenAIEmbeddings(model=OPENAI_EMBEDDINGS_MODEL)

    # Vector Store
    connection = "postgresql+psycopg://langchain:langchain@localhost:5432/langchain"
    collection_name = "agent-docs"
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=connection,
        use_jsonb=True,
    )

    # Text Splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=SPLITTER_CHUNK_SIZE, chunk_overlap=SPLITTER_CHUNK_OVERLAP
    )

    # Loader
    # loader = FireCrawlLoader(
    #    api_key=FIRECRAWL_API_KEY, url="https://firecrawl.dev", mode="scrape"
    # )
    # splits = loader.load_and_split(text_splitter=text_splitter)

    # Index chunks
    # _ = vector_store.add_documents(documents=splits)

    # Define prompt for question-answering
    prompt = hub.pull("rlm/rag-prompt")

    # Define application steps
    def retrieve(state: State):
        retrieved_docs = vector_store.similarity_search(state["question"])
        return {"context": retrieved_docs}

    def generate(state: State):
        docs_content = "\n\n".join(doc.page_content for doc in state["context"])
        messages = prompt.invoke(
            {"question": state["question"], "context": docs_content}
        )
        response = llm.invoke(messages)
        return {"answer": response.content}

    graph_builder = StateGraph(State).add_sequence([retrieve, generate])
    graph_builder.add_edge(START, "retrieve")
    graph = graph_builder.compile()

    response = graph.invoke({"question": "What is Firecrawl?"})
    print(response["answer"])


if __name__ == "__main__":
    main()
