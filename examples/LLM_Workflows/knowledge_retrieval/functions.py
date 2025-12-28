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

"""Module to house functions for an LLM agent to use."""

import logging

import arxiv_articles
import pandas as pd
import summarize_text

from hamilton import base, driver
from hamilton.execution.executors import MultiThreadingExecutor

logger = logging.getLogger(__name__)


def get_articles(query: str) -> pd.DataFrame:
    """Use this function to get academic papers from arXiv to answer user questions.

    :param query: User query in JSON. Responses should be summarized and should include the article URL reference
    :return: List of dictionaries with title, summary, article_url, pdf_url
    """
    dr = (
        driver.Builder()
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_modules(arxiv_articles)
        .with_config({"mock_openai": True})
        .with_remote_executor(MultiThreadingExecutor(max_tasks=10))
        .with_adapter(base.SimplePythonDataFrameGraphAdapter())
        .build()
    )

    inputs = {
        "embedding_model_name": "text-embedding-ada-002",
        "max_arxiv_results": 5,
        "article_query": query,
        "data_dir": "./data",
        "library_file_path": "./data/arxiv_library.csv",
    }
    dr.display_all_functions("./get_articles", {"format": "png"})
    return dr.execute(["arxiv_result_df", "save_arxiv_result_df"], inputs=inputs)


def read_article_and_summarize(query: str) -> str:
    """Use this function to read whole papers and provide a summary for users.

    You should NEVER call this function before get_articles has been called in the conversation.

    :param query: Description of the article in plain text based on the user's query.
    :return: Summarized text of the article given the query.
    """
    dr = driver.Driver({}, summarize_text, adapter=base.DefaultAdapter())
    inputs = {
        "embedding_model_name": "text-embedding-ada-002",
        "openai_gpt_model": "gpt-3.5-turbo-0613",
        "user_query": query,
        "top_n": 1,
        "max_token_length": 1500,
        "library_file_path": "./data/arxiv_library.csv",
    }
    dr.display_all_functions("./read_article_and_summarize", {"format": "png"})
    result = dr.execute(["summarize_text"], inputs=inputs)
    return result["summarize_text"]


if __name__ == "__main__":
    """Code to quickly integration test."""
    from hamilton import log_setup

    log_setup.setup_logging(log_level=log_setup.LOG_LEVELS["DEBUG"])
    _df = get_articles("ppo reinforcement learning")
    print(_df)
    _summary = read_article_and_summarize("PPO reinforcement learning sequence generation")
    print(_summary)
