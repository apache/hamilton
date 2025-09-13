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

logger = logging.getLogger(__name__)

from hamilton import contrib

with contrib.catch_import_errors(__name__, __file__, logger):
    import openai

    # use langchain implementation of vector store
    from langchain_community.vectorstores import FAISS
    from langchain_core.vectorstores import VectorStoreRetriever

    # use langchain embedding wrapper with vector store
    from langchain_openai import OpenAIEmbeddings


def standalone_question_prompt(chat_history: list[str], question: str) -> str:
    """Prompt for getting a standalone question given the chat history.

    This is then used to query the vector store with.

    :param chat_history: the history of the conversation.
    :param question: the current user question.
    :return: prompt to use.
    """
    chat_history_str = "\n".join(chat_history)
    return (
        "Given the following conversation and a follow up question, "
        "rephrase the follow up question to be a standalone question, "
        "in its original language.\n\n"
        "Chat History:\n"
        "{chat_history}\n"
        "Follow Up Input: {question}\n"
        "Standalone question:"
    ).format(chat_history=chat_history_str, question=question)


def standalone_question(standalone_question_prompt: str, llm_client: openai.OpenAI) -> str:
    """Asks the LLM to create a standalone question from the prompt.

    :param standalone_question_prompt: the prompt with context.
    :param llm_client: the llm client to use.
    :return: the standalone question.
    """
    response = llm_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": standalone_question_prompt}],
    )
    return response.choices[0].message.content


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


def context(standalone_question: str, vector_store: VectorStoreRetriever, top_k: int = 5) -> str:
    """This function returns the string context to put into a prompt for the RAG model.

    It queries the provided vector store for information.

    :param standalone_question: the question to use to search the vector store against.
    :param vector_store: the vector store to search against.
    :param top_k: the number of results to return.
    :return: a string with all the context.
    """
    _results = vector_store.invoke(standalone_question, search_kwargs={"k": top_k})
    return "\n\n".join(map(lambda d: d.page_content, _results))


def answer_prompt(context: str, standalone_question: str) -> str:
    """Creates a prompt that includes the question and context for the LLM to make sense of.

    :param context: the information context to use.
    :param standalone_question: the user question the LLM should answer.
    :return: the full prompt.
    """
    template = (
        "Answer the question based only on the following context:\n"
        "{context}\n\n"
        "Question: {question}"
    )

    return template.format(context=context, question=standalone_question)


def llm_client() -> openai.OpenAI:
    """The LLM client to use for the RAG model."""
    return openai.OpenAI()


def conversational_rag_response(answer_prompt: str, llm_client: openai.OpenAI) -> str:
    """Creates the RAG response from the LLM model for the given prompt.

    :param answer_prompt: the prompt to send to the LLM.
    :param llm_client: the LLM client to use.
    :return: the response from the LLM.
    """
    response = llm_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": answer_prompt}],
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    import __init__ as conversational_rag

    from hamilton import driver, lifecycle

    dr = (
        driver.Builder()
        .with_modules(conversational_rag)
        .with_config({})
        # this prints the inputs and outputs of each step.
        .with_adapters(lifecycle.PrintLn(verbosity=2))
        .build()
    )
    dr.display_all_functions("dag.png")

    # shows no question is reworded
    print(
        dr.execute(
            ["conversational_rag_response"],
            inputs={
                "input_texts": [
                    "harrison worked at kensho",
                    "stefan worked at Stitch Fix",
                ],
                "question": "where did stefan work?",
                "chat_history": [],
            },
        )
    )

    # this will now reword the question to then be
    # used to query the vector store.
    print(
        dr.execute(
            ["conversational_rag_response"],
            inputs={
                "input_texts": [
                    "harrison worked at kensho",
                    "stefan worked at Stitch Fix",
                ],
                "question": "where did he work?",
                "chat_history": ["Human: Who wrote this example?", "AI: Stefan"],
            },
        )
    )
