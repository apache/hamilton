# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import base64
import io
from pathlib import Path
from typing import Generator

import arxiv
import fastapi
import openai
import PyPDF2
import tiktoken
import weaviate
from weaviate.util import generate_uuid5

from hamilton.htypes import Collect, Parallelizable


def arxiv_to_download(arxiv_ids: list[str], data_dir: str | Path) -> Parallelizable[arxiv.Result]:
    """Iterate over arxiv search resulsts for given arxiv ids"""
    for arxiv_result in arxiv.Search(id_list=arxiv_ids).results():
        yield arxiv_result


def created_data_dir(data_dir: str | Path) -> str:
    """Create the directory to download PDFs if it doesn't exist already;
    NOTE. if you try to create it in the Parallelizable threads, you could face race conditions
    """
    data_dir = Path(data_dir)
    if data_dir.exists():
        data_dir.mkdir(parents=True)

    return str(data_dir)


def download_arxiv_pdf(arxiv_to_download: arxiv.Result, created_data_dir: str) -> str:
    """Download the PDF for the arxiv resutl and return PDF path"""
    return arxiv_to_download.download_pdf()  # dirpath=created_data_dir)


def arxiv_pdf_path(download_arxiv_pdf: str) -> str:
    """Extend the PDF path to its full path"""
    return str(Path(download_arxiv_pdf).absolute())


def arxiv_pdf_path_collection(arxiv_pdf_path: Collect[str]) -> list[str]:
    """Collect local PDF files full path"""
    return arxiv_pdf_path


def local_pdfs(
    arxiv_pdf_path_collection: list[str],
) -> list[str | fastapi.UploadFile]:
    """List of local PDF files, either string paths or in-memory files (on the FastAPI server)
    NOTE. This function is overriden by the driver to use arbitrary local PDFs and
    don't need to query arxiv. It is necessary because Parallelizable and Collect nodes
    cannot be overriden safely at the moment (sf-hamilton==1.26.0)
    """
    return arxiv_pdf_path_collection


def pdf_file(
    local_pdfs: list[str | fastapi.UploadFile],
) -> Parallelizable[str | fastapi.UploadFile]:
    """Iterate over local PDF files, either string paths or in-memory files (on the FastAPI server)"""
    for pdf_file in local_pdfs:
        yield pdf_file


def pdf_content(pdf_file: str | fastapi.UploadFile) -> io.BytesIO:
    """Read the content of the PDF file as a bytes buffer that will be passed to a PDF reader;
    The implementation differs if the file is passed as path or in-memory
    """
    if isinstance(pdf_file, str):
        return io.BytesIO(Path(pdf_file).read_bytes())
    elif isinstance(pdf_file, fastapi.UploadFile):
        return io.BytesIO(pdf_file.file.read())
    else:
        raise TypeError


def file_name(pdf_file: str | fastapi.UploadFile) -> str:
    """Read the content of the PDF file as a bytes buffer that will be passed to a PDF reader;
    The implementation differs if the file is passed as path or in-memory
    """
    if isinstance(pdf_file, str):
        file_path = Path(pdf_file)
    elif isinstance(pdf_file, fastapi.UploadFile):
        file_path = Path(pdf_file.filename)
    else:
        raise TypeError

    return file_path.stem


def raw_text(pdf_content: io.BytesIO) -> str:
    """Read local PDF files and return the raw text as string;
    Throw exception if unable to read PDF
    """
    reader = PyPDF2.PdfReader(pdf_content)
    pdf_text = " ".join((page.extract_text() for page in reader.pages))
    return pdf_text


def tokenizer(tokenizer_encoding: str = "cl100k_base") -> tiktoken.core.Encoding:
    """Get OpenAI tokenizer"""
    return tiktoken.get_encoding(tokenizer_encoding)


def _create_chunks(
    text: str, tokenizer: tiktoken.core.Encoding, max_length: int
) -> Generator[str, None, None]:
    """Return successive chunks of size `max_length` tokens from provided text.
    Split a text into smaller chunks of size n, preferably ending at the end of a sentence
    """
    tokens = tokenizer.encode(text)
    i = 0
    while i < len(tokens):
        # Find the nearest end of sentence within a range of 0.5 * n and 1.5 * n tokens
        j = min(i + int(1.5 * max_length), len(tokens))
        while j > i + int(0.5 * max_length):
            # Decode the tokens and check for full stop or newline
            chunk = tokenizer.decode(tokens[i:j])
            if chunk.endswith(".") or chunk.endswith("\n"):
                break
            j -= 1
        # If no end of sentence found, use n tokens as the chunk size
        if j == i + int(0.5 * max_length):
            j = min(i + max_length, len(tokens))
        yield tokens[i:j]
        i = j


def chunked_text(
    raw_text: str, tokenizer: tiktoken.core.Encoding, max_token_length: int = 500
) -> list[str]:
    """Tokenize text; create chunks of size `max_token_length`;
    for each chunk, convert tokens back to text string
    """
    _encoded_chunks = _create_chunks(raw_text, tokenizer, max_token_length)
    _decoded_chunks = [tokenizer.decode(chunk) for chunk in _encoded_chunks]
    return _decoded_chunks


def _get_embeddings__openai(texts: list[str], embedding_model_name: str) -> list[list[float]]:
    """Get the OpenAI embeddings for each text in texts"""
    response = openai.Embedding.create(input=texts, model=embedding_model_name)
    return [item["embedding"] for item in response["data"]]


def chunked_embeddings(chunked_text: list[str], embedding_model_name: str) -> list[list[float]]:
    """Convert each chunk of the arxiv article as an embedding vector"""
    return _get_embeddings__openai(texts=chunked_text, embedding_model_name=embedding_model_name)


def pdf_embedded(
    pdf_content: io.BytesIO,
    file_name: str,
    chunked_text: list[str],
    chunked_embeddings: list[list[float]],
) -> dict:
    """Gather information about each arxiv into a single object"""
    return dict(
        pdf_blob=base64.b64encode(pdf_content.getvalue()).decode("utf-8"),
        file_name=file_name,
        chunked_text=chunked_text,
        chunked_embeddings=chunked_embeddings,
    )


def pdf_collection(pdf_embedded: Collect[dict]) -> list[dict]:
    """Collect arxiv objects"""
    return list(pdf_embedded)


def store_documents(
    weaviate_client: weaviate.Client,
    pdf_collection: list[dict],
    batch_size: int = 50,
) -> None:
    """Store arxiv objects in Weaviate in batches.
    The vector and references between Document and Chunk are specified manually
    """
    weaviate_client.batch.configure(batch_size=batch_size, dynamic=True)

    with weaviate_client.batch as batch:
        for pdf_obj in pdf_collection:
            document_object = dict(
                pdf_blob=pdf_obj["pdf_blob"],
                file_name=pdf_obj["file_name"],
            )
            document_uuid = generate_uuid5(document_object, "Document")

            batch.add_data_object(
                class_name="Document",
                data_object=document_object,
                uuid=document_uuid,
            )

            chunk_iterator = zip(pdf_obj["chunked_text"], pdf_obj["chunked_embeddings"])
            for chunk_idx, (chunk_text, chunk_embedding) in enumerate(chunk_iterator):
                chunk_object = dict(content=chunk_text, chunk_index=chunk_idx)
                chunk_uuid = generate_uuid5(chunk_object, "Chunk")

                batch.add_data_object(
                    class_name="Chunk",
                    data_object=chunk_object,
                    uuid=chunk_uuid,
                    vector=chunk_embedding,
                )

                batch.add_reference(
                    from_object_class_name="Document",
                    from_property_name="containsChunk",
                    from_object_uuid=document_uuid,
                    to_object_class_name="Chunk",
                    to_object_uuid=chunk_uuid,
                )

                batch.add_reference(
                    from_object_class_name="Chunk",
                    from_property_name="fromDocument",
                    from_object_uuid=chunk_uuid,
                    to_object_class_name="Document",
                    to_object_uuid=document_uuid,
                )


if __name__ == "__main__":
    # run as a script to test Hamilton's execution
    import ingestion
    import vector_db

    from hamilton import driver

    inputs = dict(
        vector_db_url="http://localhost:8083",
        embedding_model_name="text-embedding-ada-002",
        data_dir="./data/",
        arxiv_ids=["2304.03254v1", "2307.13473v1"],
    )

    dr = (
        driver.Builder()
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_modules(ingestion, vector_db)
        .build()
    )

    results = dr.execute(
        final_vars=["store_documents"],
        inputs=inputs,
    )
