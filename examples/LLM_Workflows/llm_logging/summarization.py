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

import os
import tempfile
from typing import Generator, Union

import tiktoken
from openai import OpenAI
from pypdf import PdfReader

from hamilton.htypes import Collect, Parallelizable


def openai_client() -> OpenAI:
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def raw_text(pdf_source: Union[str, bytes, tempfile.SpooledTemporaryFile]) -> str:
    """Takes a filepath to a PDF and returns a string of the PDF's contents
    :param pdf_source: the path, or the temporary file, to the PDF.
    :return: the text of the PDF.
    """
    reader = PdfReader(pdf_source)
    _pdf_text = ""
    page_number = 0
    for page in reader.pages:
        page_number += 1
        _pdf_text += page.extract_text() + f"\nPage Number: {page_number}"
    return _pdf_text


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
    raw_text: str, tokenizer: tiktoken.core.Encoding, max_token_length: int = 800
) -> list[str]:
    """Tokenize text; create chunks of size `max_token_length`;
    for each chunk, convert tokens back to text string
    """
    _encoded_chunks = _create_chunks(raw_text, tokenizer, max_token_length)
    _decoded_chunks = [tokenizer.decode(chunk) for chunk in _encoded_chunks]
    return _decoded_chunks


def chunk_to_summarize(chunked_text: list[str]) -> Parallelizable[str]:
    """Iterate over chunks that didn't have a stored summary"""
    for chunk in chunked_text:
        yield chunk


def _summarize_text__openai(openai_client: OpenAI, prompt: str, openai_gpt_model: str) -> str:
    """Use OpenAI chat API to ask a model to summarize content contained in a prompt"""
    response = openai_client.chat.completions.create(
        model=openai_gpt_model, messages=[{"role": "user", "content": prompt}], temperature=0
    )
    return response.choices[0].message.content


def prompt_to_summarize_chunk() -> str:
    """Base prompt for summarize a chunk of text"""
    return f"Extract key points with reasoning into a bulleted format.\n\nContent:{{content}}"  # noqa: F541


def chunk_summary(
    openai_client: OpenAI,
    chunk_to_summarize: str,
    prompt_to_summarize_chunk: str,
    openai_gpt_model: str,
) -> str:
    """Fill a base prompt with a chunk's content and summarize it;
    Store the summary in the chunk object
    """
    filled_prompt = prompt_to_summarize_chunk.format(content=chunk_to_summarize)
    return _summarize_text__openai(openai_client, filled_prompt, openai_gpt_model)


def prompt_to_reduce_summaries() -> str:
    """Prompt for a "reduce" operation to summarize a list of summaries into a single text"""
    return f"""Write a summary from this collection of key points.
    First answer the question in two sentences. Then, highlight the core argument, conclusions and evidence.
    User query: {{query}}
    The summary should be structured in bulleted lists following the headings Answer, Core Argument, Evidence, and Conclusions.
    Key points:\n{{chunks_summary}}\nSummary:\n"""  # noqa: F541


def chunk_summary_collection(chunk_summary: Collect[str]) -> list[str]:
    """Collect chunks for which a summary was just computed"""
    return chunk_summary


def final_summary(
    openai_client: OpenAI,
    query: str,
    chunk_summary_collection: list[str],
    prompt_to_reduce_summaries: str,
    openai_gpt_model: str,
) -> str:
    """Concatenate the list of chunk summaries into a single text,fill the prompt template,
    and use OpenAI to reduce the content into a single summary;
    """
    concatenated_summaries = " ".join(chunk_summary_collection)
    filled_prompt = prompt_to_reduce_summaries.format(
        query=query, chunks_summary=concatenated_summaries
    )
    return _summarize_text__openai(openai_client, filled_prompt, openai_gpt_model)


if __name__ == "__main__":
    import summarization

    from hamilton import driver

    dr = (
        driver.Builder()
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_modules(summarization)
        .build()
    )
    dr.display_all_functions("./docs/summary", {"view": False, "format": "png"}, orient="TB")

    inputs = dict(
        pdf_source="./data/hamilton_paper.pdf",
        openai_gpt_model="gpt-3.5-turbo-0613",
        query="What are the main benefits of this tool?",
    )

    results = dr.execute(["final_summary"], inputs=inputs)
