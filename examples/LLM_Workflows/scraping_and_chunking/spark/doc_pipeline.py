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

"""
This module is a modified version to enable it to be used in a spark job.

Notably at the end we create a module level variable that contains a list of functions that are spark safe.
This is used by the `@h_spark.with_columns` decorator to tell it which functions define the subdag
and use the dataframe that the function declares a dependency upon.
"""

import json
import re

import requests
from langchain import text_splitter


def article_regex() -> str:
    """This assumes you're using the furo theme for sphinx"""
    return r'<article role="main" id="furo-main-content">(.*?)</article>'


def article_text(url: str, article_regex: str) -> str:
    """Pulls URL and takes out relevant HTML.

    :param url: the url to pull.
    :param article_regex: the regext to use to get the contents out of.
    :return: sub-portion of the HTML
    """
    try:
        html = requests.get(url)
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to get URL: {url}") from e
    article = re.findall(article_regex, html.text, re.DOTALL)
    if not article:
        raise ValueError(f"No article found in {url}")
    text = article[0].strip()
    return text


def html_chunker() -> text_splitter.HTMLHeaderTextSplitter:
    """Return HTML chunker object.

    :return:
    """
    headers_to_split_on = [
        ("h1", "Header 1"),
        ("h2", "Header 2"),
        ("h3", "Header 3"),
    ]
    return text_splitter.HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)


def text_chunker(
    chunk_size: int = 256, chunk_overlap: int = 32
) -> text_splitter.RecursiveCharacterTextSplitter:
    """Returns the text chunker object.

    :param chunk_size:
    :param chunk_overlap:
    :return:
    """
    return text_splitter.RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )


def chunked_text(
    article_text: str,
    html_chunker: text_splitter.HTMLHeaderTextSplitter,
    text_chunker: text_splitter.RecursiveCharacterTextSplitter,
) -> list[str]:
    """This function takes in HTML, chunks it, and then chunks it again.

    It then outputs a list of langchain "documents". Multiple documents for one HTML header section is possible.

    :param article_text:
    :param html_chunker:
    :param text_chunker:
    :return: need to return something we can make a pyspark column with
    """
    header_splits = html_chunker.split_text(article_text)
    splits = text_chunker.split_documents(header_splits)
    # TODO: make this a struct field compatible structure
    return [json.dumps(s.to_json()) for s in splits]


# this is a helper variable that we use to tell `@h_spark.with_columns` decorator which functions we want
# it to create the subdag with that will take in and operate over the dataframe depended on.
spark_safe = [
    article_regex,
    article_text,
    chunked_text,
]
