from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field
from .utils import validate_payload


class InputModel(BaseModel):
    body: str = Field(description="The text to be processed")
    chunk_size: int = Field(description="The size of each chunk", default=1000)
    chunk_overlap: int = Field(description="The overlap between chunks", default=200)


def text_handler(payload) -> None:
    options = validate_payload(InputModel, payload)
    if not options:
        return
    print("OPTIONS", options)

    chunker = RecursiveCharacterTextSplitter(
        chunk_size=options.chunk_size, chunk_overlap=options.chunk_overlap
    )

    chunks = chunker.split_text(options.body)

    print("CHUNKS", chunks)
