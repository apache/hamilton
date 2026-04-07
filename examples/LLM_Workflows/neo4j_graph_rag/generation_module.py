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
Hamilton generation DAG.

Takes the retrieved context from the retrieval DAG and the original
user query, constructs a grounded system prompt, and calls gpt-4o
to produce an answer.

DAG flow:
    retrieved_context + user_query + query_intent
        -> system_prompt
        -> prompt_messages
        -> answer
"""

import logging

import openai

logger = logging.getLogger(__name__)

SYSTEM_TEMPLATE = """You are a movie database assistant. \
The numbered results below are pre-filtered database records that \
directly answer the user's question. Each record is already the \
correct answer — do not question whether it matches the query.

Rules:
- "Movie: X" means X is a film title. List it.
- "Actor: X" means X appeared in the relevant films. List them.
- "Director: X" means X is a director. State it.
- The results are already filtered by the user's criteria \
  (company, director, genre, etc.) — do not say the company or \
  director is not specified.
- When asked for a list, list every numbered record.
- When asked yes/no, answer yes/no then cite the relevant record.
- When a single record answers "highest/most/best", state it directly.
- If there are genuinely no records, say so briefly.

Retrieval strategy: {intent}

Database records:
{context}"""


def system_prompt(
    retrieved_context: str,
    query_intent: str,
) -> str:
    """Build the system prompt by injecting retrieved context and intent metadata."""
    return SYSTEM_TEMPLATE.format(
        intent=query_intent,
        context=retrieved_context,
    )


def prompt_messages(system_prompt: str, user_query: str) -> list[dict]:
    """Assemble the message list for the OpenAI chat completion call."""
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query},
    ]


def answer(prompt_messages: list[dict], openai_api_key: str) -> str:
    """
    Call gpt-4o with the assembled prompt and return the answer string.
    Terminal node of the generation DAG.
    """
    client = openai.OpenAI(api_key=openai_api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=prompt_messages,
        temperature=0.0,
    )
    result = response.choices[0].message.content
    logger.info("Generated answer (%d chars)", len(result))
    return result