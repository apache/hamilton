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

# hamilton_anthropic.py
import anthropic
import openai

from hamilton.function_modifiers import config


@config.when(provider="openai")
def llm_client__openai() -> openai.OpenAI:
    return openai.OpenAI()


@config.when(provider="anthropic")
def llm_client__anthropic() -> anthropic.Anthropic:
    return anthropic.Anthropic()


def joke_prompt(topic: str) -> str:
    return ("Human:\n\n" "Tell me a short joke about {topic}\n\n" "Assistant:").format(topic=topic)


@config.when(provider="openai")
def joke_response__openai(llm_client: openai.OpenAI, joke_prompt: str) -> str:
    response = llm_client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=joke_prompt,
    )
    return response.choices[0].text


@config.when(provider="anthropic")
def joke_response__anthropic(llm_client: anthropic.Anthropic, joke_prompt: str) -> str:
    response = llm_client.completions.create(
        model="claude-2", prompt=joke_prompt, max_tokens_to_sample=256
    )
    return response.completion


if __name__ == "__main__":
    import hamilton_invoke_anthropic
    from hamilton import driver

    dr = (
        driver.Builder()
        .with_modules(hamilton_invoke_anthropic)
        .with_config({"provider": "anthropic"})
        .build()
    )
    dr.display_all_functions("hamilton-anthropic.png")
    print(dr.execute(["joke_response"], inputs={"topic": "ice cream"}))

    dr = (
        driver.Builder()
        .with_modules(hamilton_invoke_anthropic)
        .with_config({"provider": "openai"})
        .build()
    )
    print(dr.execute(["joke_response"], inputs={"topic": "ice cream"}))
