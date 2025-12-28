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

# hamilton_completion.py
from typing import List

import openai

from hamilton.function_modifiers import config


def llm_client() -> openai.OpenAI:
    return openai.OpenAI()


def joke_prompt(topic: str) -> str:
    return f"Tell me a short joke about {topic}"


def joke_messages(joke_prompt: str) -> List[dict]:
    return [{"role": "user", "content": joke_prompt}]


@config.when(type="completion")
def joke_response__completion(llm_client: openai.OpenAI, joke_prompt: str) -> str:
    response = llm_client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=joke_prompt,
    )
    return response.choices[0].text


@config.when(type="chat")
def joke_response__chat(llm_client: openai.OpenAI, joke_messages: List[dict]) -> str:
    response = llm_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=joke_messages,
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    import hamilton_completion
    from hamilton import driver

    dr = (
        driver.Builder()
        .with_modules(hamilton_completion)
        .with_config({"type": "completion"})
        .build()
    )
    dr.display_all_functions("hamilton-completion.png")
    print(dr.execute(["joke_response"], inputs={"topic": "ice cream"}))

    dr = driver.Builder().with_modules(hamilton_completion).with_config({"type": "chat"}).build()
    dr.display_all_functions("hamilton-chat.png")
    print(dr.execute(["joke_response"], inputs={"topic": "ice cream"}))
