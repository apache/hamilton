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

import os.path
from typing import Dict

import arxiv
import openai
import pandas as pd

from hamilton.function_modifiers import extract_fields
from hamilton.htypes import Collect, Parallelizable


def arxiv_search_result(
    article_query: str,
    max_arxiv_results: int,
    sort_by: arxiv.SortCriterion.Relevance = arxiv.SortCriterion.Relevance,
) -> Parallelizable[arxiv.Result]:
    """Goes to arxiv and returns a list articles that match the provided query.

    :param article_query: the query to search for.
    :param max_arxiv_results: the maximum number of results to return.
    :param sort_by: sort the results by this criterion.
    :return: list of arxiv.Result objects.
    """
    _search = arxiv.Search(
        query=article_query,
        max_results=max_arxiv_results,
        sort_by=sort_by,
    )
    for item in _search.results():
        yield item


@extract_fields({"title": str, "summary": str, "article_url": str, "pdf_url": str})
def result(arxiv_search_result: arxiv.Result) -> Dict[str, str]:
    return {
        "title": arxiv_search_result.title,
        "summary": arxiv_search_result.summary,
        "article_url": arxiv_search_result.links[0],
        "pdf_url": arxiv_search_result.links[1],
    }
    pass


def arxiv_result_embedding(
    title: str,
    embedding_model_name: str,
) -> list[float]:
    """Generates an embedding, indexed by title for each arxiv search result.

    :param title of the arxiv search result:
    :param embedding_model_name: the name of the embedding model to use.
    :return: the embedding as a vector of floats
    """
    response = openai.Embedding.create(input=title, model=embedding_model_name)
    return response["data"][0]["embedding"]


def arxiv_pdf(arxiv_search_result: arxiv.Result, data_dir: str) -> str:
    """Processes the arxiv search results and downloads the PDFs.

    :param arxiv_search_result: search result object.
    :param data_dir: the directory to save the PDFs to.
    :return: The filepath to the pdf after downloading
    """
    if not os.path.exists(data_dir):
        os.path.makedirs(data_dir)
    return arxiv_search_result.download_pdf(dirpath=data_dir)


def arxiv_processed_result(
    title: str,
    summary: str,
    article_url: str,
    pdf_url: str,
    arxiv_pdf: str,
    arxiv_result_embedding: list[float],
) -> Dict[str, str]:
    """creates dict with parameters as keys/values"""
    return {
        "title": title,
        "summary": summary,
        "article_url": article_url,
        "pdf_url": pdf_url,
        "arxiv_pdfs": arxiv_pdf,
        "arxiv_result_embeddings": arxiv_result_embedding,
    }


def arxiv_result_df(arxiv_processed_result: Collect[Dict[str, str]]) -> pd.DataFrame:
    """Joins the arxiv results back to a dataframe.

    :param arxiv_processed_result: result of all the joined arxiv result information
    :return:  a dataframe with the arxiv results.
    """
    all_results = list(arxiv_processed_result)
    return pd.DataFrame.from_records(all_results).set_index("title", drop=False)


def save_arxiv_result_df(arxiv_result_df: pd.DataFrame, library_file_path: str) -> dict:
    """Saves the arxiv result dataframe to a csv file.

    Appends if it already exists. Does not protect against duplicates.

    :param arxiv_result_df: the dataframe to save.
    :param library_file_path: the path to the library file.
    :return: a dictionary with the number of articles newly written.
    """
    if os.path.exists(library_file_path):
        arxiv_result_df.to_csv(library_file_path, mode="a", header=False, index=False)
    else:
        arxiv_result_df.to_csv(library_file_path, index=False)
    return {"num_articles_written": len(arxiv_result_df)}
