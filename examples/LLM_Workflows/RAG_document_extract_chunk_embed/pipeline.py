"""
Modules that mirrors the pipeline the code in the notebook creates.
"""

from typing import NamedTuple, Optional


class Chunk(NamedTuple):
    """Chunk of a Document - text & embedding."""

    index: int
    document_id: str
    text: str
    embedding: Optional[list[float]]
    metadata: Optional[dict[str, str]]

    def add_embedding(self, embedding: list[float]) -> "Chunk":
        """Required to update chunk with embeddings"""
        return Chunk(self.index, self.document_id, self.text, embedding, self.metadata)

    def add_metadata(self, metadata: dict[str, str]) -> "Chunk":
        """Required to update chunk with metadata"""
        return Chunk(self.index, self.document_id, self.text, self.embedding, metadata)


class Document(NamedTuple):
    """Document containing a full raw text, along with pointers to chunks."""

    id: str
    url: str
    raw_text: str
    chunks: Optional[list[Chunk]]

    def add_chunks(self, chunks: list[Chunk]) -> "Document":
        """Required to update the document when Chunks are created"""
        return Document(self.id, self.url, self.raw_text, chunks)


import re
import uuid

import requests


def html_regex() -> str:
    """Context dependent logic for getting the right part of the HTML document."""
    return r'<article role="main" id="furo-main-content">(.*?)</article>'


def raw_document(url: str, html_regex: str) -> Document:
    """Loads and parses the HTML from a URL, returning the html text of interest.

    :param url: the url to pull.
    :param html_regex: the regext to use to get the contents out of.
    :return: sub-portion of the HTML
    """
    html_text = requests.get(url).text
    article = re.findall(html_regex, html_text, re.DOTALL)
    if not article:
        raise ValueError(f"No article found in {url}")
    raw_text = article[0].strip()
    return Document(str(uuid.uuid4()), url, raw_text, None)


from langchain import text_splitter


def html_chunker() -> text_splitter.HTMLHeaderTextSplitter:
    """Object to help split HTML into chunks"""
    headers_to_split_on = [
        ("h1", "Header 1"),
        ("h2", "Header 2"),
        ("h3", "Header 3"),
    ]
    html_chunker = text_splitter.HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    return html_chunker


def text_chunker(
    chunk_size: int = 256, chunk_overlap: int = 0
) -> text_splitter.RecursiveCharacterTextSplitter:
    """Object to further split chunks"""
    return text_splitter.RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )


def chunked_document(
    raw_document: Document,
    html_chunker: text_splitter.HTMLHeaderTextSplitter,
    text_chunker: text_splitter.RecursiveCharacterTextSplitter,
) -> Document:
    """This function takes in HTML, chunks the HTML, and then chunks it into text chunks."""
    header_splits = html_chunker.split_text(raw_document.raw_text)
    text_chunks = text_chunker.split_documents(header_splits)
    chunks = []
    for i, text_chunk in enumerate(text_chunks):
        chunks.append(
            Chunk(
                index=i,
                document_id=raw_document.id,
                text=text_chunk.page_content,
                embedding=None,
                metadata=text_chunk.metadata,
            )
        )
    # create new raw_document object
    raw_document = raw_document.add_chunks(chunks)
    return raw_document


import openai


def client() -> openai.OpenAI:
    return openai.OpenAI()


def embedded_document(
    chunked_document: Document,
    client: openai.OpenAI,
) -> Document:
    """This function takes in a list of documents and outputs a list of documents with embeddings."""
    for idx, chunk in enumerate(chunked_document.chunks):
        response = client.embeddings.create(input=chunk.text, model="text-embedding-3-small")
        chunk = chunk.add_embedding(response.data[0].embedding)
        # mutate existing document
        chunked_document.chunks[idx] = chunk
    return chunked_document


import pandas as pd


def store(
    embedded_document: Document,
) -> pd.DataFrame:
    """Function to index & store the document. Here we just put it into a pandas dataframe."""
    # make a pandas dataframe from the document
    # want a column for the document id, the chunk index, the text, the embedding, and the metadata
    rows = []
    for chunk in embedded_document.chunks:
        # need to
        rows.append(
            {
                "document_id": embedded_document.id,
                "chunk_index": chunk.index,
                "url": embedded_document.url,
                "text": chunk.text,
                "embedding": chunk.embedding,
                "metadata": chunk.metadata,
            }
        )
    data_set = pd.DataFrame(rows)
    # we create an index using the document_id and chunk_index
    data_set.set_index(["document_id", "chunk_index"], inplace=True)
    return data_set


if __name__ == "__main__":
    import __main__ as doc_pipeline
    from hamilton import driver

    # create the driver
    pipeline_driver = driver.Builder().with_modules(doc_pipeline).build()

    # execute the pipeline for the given URL
    results = pipeline_driver.execute(["store"], inputs={"url": "https://hamilton.apache.org/"})

    # show the dataframe for this document
    print(results["store"].head())
