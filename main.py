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
from langchain_postgres import PGVector


# Classes
class State(TypedDict):
    question: str
    context: List[Document]
    answer: str


# Constants
ENABLE_LOADER = False
SPLITTER_CHUNK_SIZE = 1000
SPLITTER_CHUNK_OVERLAP = 200

# Load environment variables from .env file
load_dotenv()
POSTGRES_HOST = os.environ.get("POSTGRES_HOST")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT")
POSTGRES_USER = os.environ.get("POSTGRES_USER")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
POSTGRES_DB = os.environ.get("POSTGRES_DB")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "agent-docs")
OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_LLM_MODEL = os.environ.get("OPENAI_LLM_MODEL", "gpt-4o-mini")
OPENAI_EMBEDDINGS_MODEL = os.environ.get(
    "OPENAI_EMBEDDINGS_MODEL", "text-embedding-3-large"
)
FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY")


def main():

    # Initialize LLM and Embedding models
    llm = init_chat_model(model=OPENAI_LLM_MODEL)
    embeddings = OpenAIEmbeddings(model=OPENAI_EMBEDDINGS_MODEL)

    # Initialize PGVector vector store
    database_url = f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=COLLECTION_NAME,
        connection=database_url,
        use_jsonb=True,
    )

    # Text Splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=SPLITTER_CHUNK_SIZE, chunk_overlap=SPLITTER_CHUNK_OVERLAP
    )

    # Load documents from FireCrawl if enabled
    if ENABLE_LOADER:
        loader = FireCrawlLoader(
            api_key=FIRECRAWL_API_KEY, url="https://firecrawl.dev", mode="scrape"
        )
        splits = loader.load_and_split(text_splitter=text_splitter)
        _ = vector_store.add_documents(documents=splits)

    # Define prompt for question-answering
    prompt = hub.pull("rlm/rag-prompt")

    # Define document retrieval stage
    def retrieve(state: State):
        retrieved_docs = vector_store.similarity_search(state["question"])
        return {"context": retrieved_docs}

    # Define document generation stage
    def generate(state: State):
        docs_content = "\n\n".join(doc.page_content for doc in state["context"])
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
    response = graph.invoke({"question": "What is Firecrawl?"})
    print(response["answer"])


if __name__ == "__main__":
    main()
