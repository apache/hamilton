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

"""Module showing the summarization task but using the Parallelizable and Collect features.

That is, this code does not embed an executor within the logic of the code. Instead, that is handled by Hamilton.
"""

import tempfile
from typing import Generator, Union

import tiktoken
from openai import OpenAI
from PyPDF2 import PdfReader
from tenacity import retry, stop_after_attempt, wait_random_exponential

from hamilton.function_modifiers import config
from hamilton.htypes import Collect, Parallelizable


class SerializeableOpenAIClient:
    """This is an example object to get around serialization issues with the OpenAI client."""

    def __init__(self):
        self.client = OpenAI()

    def __getstate__(self):
        return {}

    def __setstate__(self, d):
        self.client = OpenAI()


def client() -> SerializeableOpenAIClient:
    return SerializeableOpenAIClient()


def summarize_chunk_of_text_prompt(content_type: str = "an academic paper") -> str:
    """Base prompt for summarizing chunks of text."""
    return f"Summarize this text from {content_type}. Extract any key points with reasoning.\n\nContent:"


def summarize_text_from_summaries_prompt(content_type: str = "an academic paper") -> str:
    """Prompt for summarizing a paper from a list of summaries."""
    return f"""Write a summary collated from this collection of key points extracted from {content_type}.
    The summary should highlight the core argument, conclusions and evidence, and answer the user's query.
    User query: {{query}}
    The summary should be structured in bulleted lists following the headings Core Argument, Evidence, and Conclusions.
    Key points:\n{{results}}\nSummary:\n"""


@config.when(file_type="pdf")
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


def _create_chunks(text: str, n: int, tokenizer: tiktoken.Encoding) -> Generator[str, None, None]:
    """Helper function. Returns successive n-sized chunks from provided text.
    Split a text into smaller chunks of size n, preferably ending at the end of a sentence
    :param text:
    :param n:
    :param tokenizer:
    :return:
    """
    tokens = tokenizer.encode(text)
    i = 0
    while i < len(tokens):
        # Find the nearest end of sentence within a range of 0.5 * n and 1.5 * n tokens
        j = min(i + int(1.5 * n), len(tokens))
        while j > i + int(0.5 * n):
            # Decode the tokens and check for full stop or newline
            chunk = tokenizer.decode(tokens[i:j])
            if chunk.endswith(".") or chunk.endswith("\n"):
                break
            j -= 1
        # If no end of sentence found, use n tokens as the chunk size
        if j == i + int(0.5 * n):
            j = min(i + n, len(tokens))
        yield tokens[i:j]
        i = j


def chunked_text(
    raw_text: str, tokenizer_encoding: str = "cl100k_base", max_token_length: int = 1500
) -> Parallelizable[str]:
    """Chunks the pdf text into smaller chunks of size max_token_length.
    :param raw_text: the Series of individual pdf texts to chunk.
    :param max_token_length: the maximum length of tokens in each chunk.
    :param tokenizer_encoding: the encoding to use for the tokenizer.
    :return: Series of chunked pdf text. Each element is a list of chunks.
    """
    tokenizer = tiktoken.get_encoding(tokenizer_encoding)
    _encoded_chunks = _create_chunks(raw_text, max_token_length, tokenizer)
    # _decoded_chunks = [tokenizer.decode(chunk) for chunk in _encoded_chunks]
    # return _decoded_chunks
    for chunk in _encoded_chunks:
        decoded_chunk = tokenizer.decode(chunk)
        yield decoded_chunk


# def local_client(chunked_text: str) -> openai.OpenAI:
#     """Alternative way to get around serialization issue -- create the client within the parallel block."""
#     client = OpenAI()
#     return client


@retry(wait=wait_random_exponential(min=1, max=40), stop=stop_after_attempt(3))
def summarized_chunk(
    chunked_text: str,
    summarize_chunk_of_text_prompt: str,
    openai_gpt_model: str,
    client: SerializeableOpenAIClient,
) -> str:
    """This helper function applies a prompt to some input content. In this case it returns a summarized chunk of text.

    :param chunked_text: a list of chunks of text for an article.
    :param summarize_chunk_of_text_prompt:  the prompt to use to summarize each chunk of text.
    :param openai_gpt_model: the openai gpt model to use.
    :return: the response from the openai API.
    """
    prompt = summarize_chunk_of_text_prompt + chunked_text
    response = client.client.chat.completions.create(
        model=openai_gpt_model, messages=[{"role": "user", "content": prompt}], temperature=0
    )
    return response.choices[0].message.content


def summarized_chunks(summarized_chunk: Collect[str]) -> str:
    """Joins the chunks from the parallel chunking process into a single chunk.
    :param summarized_chunk: the openai gpt model to use.
    :return: a single string of each chunk of text summarized, concatenated together.
    """
    return "".join(summarized_chunk)


def prompt_and_text_content(
    summarized_chunks: str,
    summarize_text_from_summaries_prompt: str,
    user_query: str,
) -> str:
    """Creates the prompt for summarizing the text from the summarized chunks of the pdf.
    :param summarized_chunks: a long string of chunked summaries of a file.
    :param summarize_text_from_summaries_prompt: the template to use to summarize the chunks.
    :param user_query: the original user query.
    :return: the prompt to use to summarize the chunks.
    """
    return summarize_text_from_summaries_prompt.format(query=user_query, results=summarized_chunks)


def global_client() -> OpenAI:
    return OpenAI()


def summarized_text(
    prompt_and_text_content: str,
    openai_gpt_model: str,
    client: SerializeableOpenAIClient,
) -> str:
    """Summarizes the text from the summarized chunks of the pdf.
    :param prompt_and_text_content: the prompt and content to send over.
    :param openai_gpt_model: which openai gpt model to use.
    :param global_client: client to use.
    :return: the string response from the openai API.
    """
    response = client.client.chat.completions.create(
        model=openai_gpt_model,
        messages=[
            {
                "role": "user",
                "content": prompt_and_text_content,
            }
        ],
        temperature=0,
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    # run as a script to test Hamilton's execution
    import parallel_summarization

    from hamilton import driver
    from hamilton.execution import executors

    config = {"file_type": "pdf"}
    dr = (
        driver.Builder()
        .with_modules(parallel_summarization)
        .with_config(config)
        .enable_dynamic_execution(allow_experimental_mode=True)
        # .with_remote_executor(h_ray.RayTaskExecutor(skip_init=True))
        .with_remote_executor(executors.MultiProcessingExecutor(max_tasks=4))
        .build()
    )
    dr.display_all_functions("summarization_module.png", deduplicate_inputs=True)
    result = dr.execute(
        ["summarized_text"],
        inputs={
            "pdf_source": "../run_on_spark/CDMS_HAMILTON_PAPER.pdf",
            "openai_gpt_model": "gpt-3.5-turbo-0613",
            "content_type": "Scientific Article",
            "user_query": "Can you ELI5 the paper?",
        },
    )
    print(result["summarized_text"])
