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

import ast
import concurrent
from typing import Callable, Generator, List

import openai
import pandas as pd
import tiktoken
from PyPDF2 import PdfReader
from scipy import spatial
from tenacity import retry, stop_after_attempt, wait_random_exponential
from tqdm import tqdm

from hamilton.function_modifiers import extract_columns


def summarize_chunk_of_text_prompt() -> str:
    """Base prompt for summarizing chunks of text."""
    return "Summarize this text from an academic paper. Extract any key points with reasoning.\n\nContent:"


def summarize_paper_from_summaries_prompt() -> str:
    """Prompt for summarizing a paper from a list of summaries."""
    return """Write a summary collated from this collection of key points extracted from an academic paper.
    The summary should highlight the core argument, conclusions and evidence, and answer the user's query.
    User query: {query}
    The summary should be structured in bulleted lists following the headings Core Argument, Evidence, and Conclusions.
    Key points:\n{results}\nSummary:\n"""


@retry(wait=wait_random_exponential(min=1, max=40), stop=stop_after_attempt(3))
def user_query_embedding(user_query: str, embedding_model_name: str) -> List[float]:
    """Get the embedding for a user query from OpenAI API."""
    response = openai.Embedding.create(input=user_query, model=embedding_model_name)
    return response["data"][0]["embedding"]


def relatedness(
    user_query_embedding: List[float],
    embeddings: pd.Series,
    relatedness_fn: Callable = lambda x, y: 1 - spatial.distance.cosine(x, y),
) -> pd.Series:
    """Computes the relatedness of a user query embedding to a series of individual embeddings.

    :param user_query_embedding: the embedding of the user query.
    :param embeddings: a series of individual embeddings to compare to the user query embedding.
    :param relatedness_fn: the function to use to compute relatedness.
    :return: series of relatedness scores, indexed by the index of the embeddings series.
    """
    return embeddings.apply(lambda x: relatedness_fn(user_query_embedding, x))


def pdf_text(pdf_path: pd.Series) -> pd.Series:
    """Takes a filepath to a PDF and returns a string of the PDF's contents

    :param pdf_path: Series of filepaths to PDFs
    :return: Series of strings of the PDFs' contents
    """
    _pdf_text = []
    for _i, file_path in pdf_path.items():
        # creating a pdf reader object
        reader = PdfReader(file_path)
        text = ""
        page_number = 0
        for page in reader.pages:
            page_number += 1
            text += page.extract_text() + f"\nPage Number: {page_number}"
        _pdf_text.append(text)
    return pd.Series(_pdf_text, index=pdf_path.index)


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


def chunked_pdf_text(
    pdf_text: pd.Series, max_token_length: int, tokenizer_encoding: str = "cl100k_base"
) -> pd.Series:
    """Chunks the pdf text into smaller chunks of size max_token_length.

    :param pdf_text: the Series of individual pdf texts to chunk.
    :param max_token_length: the maximum length of tokens in each chunk.
    :param tokenizer_encoding: the encoding to use for the tokenizer.
    :return: Series of chunked pdf text. Each element is a list of chunks.
    """
    tokenizer = tiktoken.get_encoding(tokenizer_encoding)
    _chunked = pdf_text.apply(lambda x: _create_chunks(x, max_token_length, tokenizer))
    _chunked = _chunked.apply(lambda x: [tokenizer.decode(chunk) for chunk in x])
    return _chunked


def top_n_related_articles(
    relatedness: pd.Series, top_n: int, chunked_pdf_text: pd.Series
) -> pd.Series:
    """Given relatedness scores, returns the top n related articles by way of chunks of text.

    :param relatedness: the relatedness scores for each article.
    :param top_n: the number of top related articles to return.
    :param chunked_pdf_text: the chunked pdf text to return out of.
    :return: filtered chunked pdf text, sorted by relatedness.
    """
    return chunked_pdf_text[relatedness.sort_values(ascending=False).head(top_n).index]


@retry(wait=wait_random_exponential(min=1, max=40), stop=stop_after_attempt(3))
def _summarize_chunk(content: str, template_prompt: str, openai_gpt_model: str) -> str:
    """This function applies a prompt to some input content. In this case it returns a summarized chunk of text.

    :param content: the content to summarize.
    :param template_prompt: the prompt template to use to put the content into.
    :param openai_gpt_model: the openai gpt model to use.
    :return: the response from the openai API.
    """
    prompt = template_prompt + content
    response = openai.ChatCompletion.create(
        model=openai_gpt_model, messages=[{"role": "user", "content": prompt}], temperature=0
    )
    return response["choices"][0]["message"]["content"]


def summarized_pdf(
    top_n_related_articles: pd.Series, summarize_chunk_of_text_prompt: str, openai_gpt_model: str
) -> str:
    """Summarizes a series of chunks of text.

    Note: this takes the first result from the top_n_related_articles series and summarizes it. This is because
    the top_n_related_articles series is sorted by relatedness, so the first result is the most related.

    :param top_n_related_articles: series with each entry being a list of chunks of text for an article.
    :param summarize_chunk_of_text_prompt:  the prompt to use to summarize each chunk of text.
    :param openai_gpt_model: the openai gpt model to use.
    :return: a single string of each chunk of text summarized, concatenated together.
    """
    text_chunks = top_n_related_articles[0]
    results = ""
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(text_chunks)) as executor:
        futures = [
            executor.submit(
                _summarize_chunk, chunk, summarize_chunk_of_text_prompt, openai_gpt_model
            )
            for chunk in text_chunks
        ]
        with tqdm(total=len(text_chunks)) as pbar:
            for _ in concurrent.futures.as_completed(futures):
                pbar.update(1)
        for future in futures:
            data = future.result()
            results += data
    return results


@extract_columns(*["pdf_path", "embeddings"])
def library_df(library_file_path: str) -> pd.DataFrame:
    """Loads the library file into a dataframe.

    :param library_file_path: the path to the library file.
    :return: the library dataframe.
    """
    _library_df = pd.read_csv(library_file_path)
    _library_df.columns = ["title", "pdf_path", "embeddings", "summary", "article_url", "pdf_url"]
    _library_df["embeddings"] = _library_df["embeddings"].apply(ast.literal_eval)
    _library_df.index = _library_df["title"]
    return _library_df


def summarize_text(
    user_query: str,
    summarized_pdf: str,
    summarize_paper_from_summaries_prompt: str,
    openai_gpt_model: str,
) -> str:
    """Summarizes the text from the summarized chunks of the pdf.

    :param user_query: the original user query.
    :param summarized_pdf: a long string of chunked summaries of a PDF.
    :param summarize_paper_from_summaries_prompt: the template to use
    :param openai_gpt_model: which openai gpt model to use.
    :return: the string response from the openai API.
    """
    response = openai.ChatCompletion.create(
        model=openai_gpt_model,
        messages=[
            {
                "role": "user",
                "content": summarize_paper_from_summaries_prompt.format(
                    query=user_query, results=summarized_pdf
                ),
            }
        ],
        temperature=0,
    )
    return response["choices"][0]["message"]["content"]
