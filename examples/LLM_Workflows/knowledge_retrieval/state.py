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
Module that contains code to house state for an agent. The dialog
right now is hardcoded at the bottom of this file.
"""

import json
import logging
import sys

import functions
import openai
from tenacity import retry, stop_after_attempt, wait_random_exponential
from termcolor import colored

logger = logging.getLogger(__name__)

GPT_MODEL = "gpt-3.5-turbo-0613"

# TODO: create a programmatic way to generate this from the function definitions themselves.
arxiv_functions = [
    {
        "name": "get_articles",
        "description": """Use this function to get academic papers from arXiv to answer user questions.""",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": """
                            User query in JSON. Responses should be summarized and should include the article URL reference
                            """,
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "read_article_and_summarize",
        "description": """Use this function to read whole papers and provide a summary for users.
        You should NEVER call this function before get_articles has been called in the conversation.""",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": """
                            Description of the article in plain text based on the user's query
                            """,
                }
            },
            "required": ["query"],
        },
    },
]


class Conversation:
    """Class that houses the conversation history and displays it in a nice way."""

    def __init__(self):
        self.conversation_history = []

    def add_message(self, role, content):
        message = {"role": role, "content": content}
        self.conversation_history.append(message)

    def display_conversation(self):
        role_to_color = {
            "system": "red",
            "user": "green",
            "assistant": "blue",
            "function": "magenta",
        }
        for message in self.conversation_history:
            print(
                colored(
                    f"{message['role']}: {message['content']}\n\n",
                    role_to_color[message["role"]],
                )
            )


@retry(wait=wait_random_exponential(min=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, openai_gpt_model: str, functions=None, temperature: int = 0):
    """This function makes a ChatCompletion API call with the option of adding functions"""
    kwargs = dict(model=openai_gpt_model, messages=messages, temperature=temperature)
    if functions:
        kwargs["functions"] = functions
    try:
        response = openai.ChatCompletion.create(**kwargs)
        return response
    except Exception as e:
        logger.error("Unable to generate ChatCompletion response")
        logger.error(f"Exception: {e}")
        return e


def chat_completion_with_function_execution(messages, functions=None):
    """This function makes a ChatCompletion API call with the option of adding functions"""
    response = chat_completion_request(messages, openai_gpt_model=GPT_MODEL, functions=functions)
    full_message = response["choices"][0]
    if full_message["finish_reason"] == "function_call":
        logger.info("Function generation requested, calling function")
        return call_arxiv_function(messages, full_message)
    else:
        logger.info("Function not required, responding to user")
        return response["choices"][0]["message"]["content"]


def call_arxiv_function(messages, full_message):
    """Function calling function which executes function calls when the model believes it is necessary.
    Currently extended by adding clauses to this if statement.

    This code is pulled directly from the cookbook -- it is not well structured.
    """

    if full_message["message"]["function_call"]["name"] == "get_articles":
        try:
            parsed_output = json.loads(full_message["message"]["function_call"]["arguments"])
            logger.info("Getting search results")
            results = functions.get_articles(parsed_output["query"])
        except Exception as e:
            logger.info(parsed_output)
            logger.info("Function execution failed")
            logger.info(f"Error message: {e}")
            raise e
        messages.append(
            {
                "role": "function",
                "name": full_message["message"]["function_call"]["name"],
                "content": str(results),
            }
        )
        try:
            logger.info("Got search results, summarizing content")
            response = chat_completion_request(messages, openai_gpt_model=GPT_MODEL)
            return response
        except Exception as e:
            logger.error(type(e))
            raise Exception("Function chat request failed") from e

    elif full_message["message"]["function_call"]["name"] == "read_article_and_summarize":
        parsed_output = json.loads(full_message["message"]["function_call"]["arguments"])
        logger.info("Finding and reading paper")
        summary = functions.read_article_and_summarize(parsed_output["query"])
        return summary

    else:
        raise Exception("Function does not exist and cannot be called")


if __name__ == "__main__":
    """Here is is some example dialog interactions."""
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    paper_system_message = """You are arXivGPT, a helpful assistant pulls academic papers to answer user questions.
    You summarize the papers clearly so the customer can decide which to read to answer their question.
    You always provide the article_url and title so the user can understand the name of the paper and click through to access it.
    Begin!"""
    paper_conversation = Conversation()
    paper_conversation.add_message("system", paper_system_message)

    # Add a user message
    paper_conversation.add_message("user", "Hi, how does PPO reinforcement learning work?")
    chat_response = chat_completion_with_function_execution(
        paper_conversation.conversation_history, functions=arxiv_functions
    )
    if isinstance(chat_response, openai.openai_object.OpenAIObject):
        assistant_message = chat_response["choices"][0]["message"]["content"]
    else:
        assistant_message = chat_response
    paper_conversation.add_message("assistant", assistant_message)
    print(assistant_message)

    paper_conversation.add_message(
        "user",
        "Can you read the PPO sequence generation paper for me and give me a summary",
    )
    updated_response = chat_completion_with_function_execution(
        paper_conversation.conversation_history, functions=arxiv_functions
    )
    if isinstance(updated_response, openai.openai_object.OpenAIObject):
        assistant_message = updated_response["choices"][0]["message"]["content"]
    else:
        assistant_message = updated_response
    paper_conversation.add_message("assistant", assistant_message)
    print(updated_response)
    paper_conversation.add_message(
        "user",
        "Can you read the A2C PPO paper for me and give me a summary",
    )
    updated_response = chat_completion_with_function_execution(
        paper_conversation.conversation_history, functions=arxiv_functions
    )
    if isinstance(updated_response, openai.openai_object.OpenAIObject):
        assistant_message = updated_response["choices"][0]["message"]["content"]
    else:
        assistant_message = updated_response
    paper_conversation.add_message("assistant", updated_response)
    print(updated_response)
    print("Conversation history:")
    paper_conversation.display_conversation()
