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

import logging
import os

logger = logging.getLogger(__name__)

from hamilton import contrib
from hamilton.function_modifiers import config

with contrib.catch_import_errors(__name__, __file__, logger):
    import openai

    # use langchain implementation of vector store
    from langchain_community.vectorstores import FAISS
    from langchain_core.vectorstores import VectorStoreRetriever

    # use langchain embedding wrapper with vector store
    from langchain_openai import OpenAIEmbeddings


def vector_store(input_texts: list[str]) -> VectorStoreRetriever:
    """A Vector store. This function populates and creates one for querying.

    This is a cute function encapsulating the creation of a vector store. In real life
    you could replace this with a more complex function, or one that returns a
    client to an existing vector store.

    :param input_texts: the input "text" i.e. documents to be stored.
    :return: a vector store that can be queried against.
    """
    vectorstore = FAISS.from_texts(input_texts, embedding=OpenAIEmbeddings())
    retriever = vectorstore.as_retriever()
    return retriever


def context(question: str, vector_store: VectorStoreRetriever, top_k: int = 5) -> str:
    """This function returns the string context to put into a prompt for the RAG model.

    :param question: the user question to use to search the vector store against.
    :param vector_store: the vector store to search against.
    :param top_k: the number of results to return.
    :return: a string with all the context.
    """
    _results = vector_store.invoke(question, search_kwargs={"k": top_k})
    return "\n".join(map(lambda d: d.page_content, _results))


def rag_prompt(context: str, question: str) -> str:
    """Creates a prompt that includes the question and context for the LLM to makse sense of.

    :param context: the information context to use.
    :param question: the user question the LLM should answer.
    :return: the full prompt.
    """
    template = (
        "Answer the question based only on the following context:\n"
        "{context}\n\n"
        "Question: {question}"
    )

    return template.format(context=context, question=question)


@config.when_not(provider="minimax")
def llm_client__openai() -> openai.OpenAI:
    """The OpenAI LLM client (default).

    Uses the OPENAI_API_KEY environment variable for authentication.
    """
    return openai.OpenAI()


@config.when(provider="minimax")
def llm_client__minimax() -> openai.OpenAI:
    """The MiniMax LLM client via OpenAI-compatible API.

    Uses the MINIMAX_API_KEY environment variable for authentication.
    MiniMax provides an OpenAI-compatible endpoint at https://api.minimax.io/v1.
    """
    return openai.OpenAI(
        base_url="https://api.minimax.io/v1",
        api_key=os.environ.get("MINIMAX_API_KEY"),
    )


@config.when_not(provider="minimax")
def model__openai() -> str:
    """The model to use for OpenAI (default)."""
    return "gpt-3.5-turbo"


@config.when(provider="minimax")
def model__minimax() -> str:
    """The model to use for MiniMax."""
    return "MiniMax-M2.7"


def rag_response(rag_prompt: str, llm_client: openai.OpenAI, model: str) -> str:
    """Creates the RAG response using the configured LLM.

    :param rag_prompt: the prompt to send to the LLM.
    :param llm_client: the LLM client to use.
    :param model: the model name to use.
    :return: the response from the LLM.
    """
    response = llm_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": rag_prompt}],
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    import __init__ as hamilton_faiss_rag

    from hamilton import driver, lifecycle

    # Default: uses OpenAI (config={} or config={"provider": "openai"})
    dr = (
        driver.Builder()
        .with_modules(hamilton_faiss_rag)
        .with_config({})
        # this prints the inputs and outputs of each step.
        .with_adapters(lifecycle.PrintLn(verbosity=2))
        .build()
    )
    dr.display_all_functions("dag.png")
    print(
        dr.execute(
            ["rag_response"],
            inputs={
                "input_texts": [
                    "harrison worked at kensho",
                    "stefan worked at Stitch Fix",
                ],
                "question": "where did stefan work?",
            },
        )
    )

    # To use MiniMax instead, set MINIMAX_API_KEY and use:
    # dr = (
    #     driver.Builder()
    #     .with_modules(hamilton_faiss_rag)
    #     .with_config({"provider": "minimax"})
    #     .with_adapters(lifecycle.PrintLn(verbosity=2))
    #     .build()
    # )
