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

# hamilton_async.py
from typing import List

import openai


def llm_client() -> openai.AsyncOpenAI:
    return openai.AsyncOpenAI()


def joke_prompt(topic: str) -> str:
    return f"Tell me a short joke about {topic}"


def joke_messages(joke_prompt: str) -> List[dict]:
    return [{"role": "user", "content": joke_prompt}]


async def joke_response(llm_client: openai.AsyncOpenAI, joke_messages: List[dict]) -> str:
    response = await llm_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=joke_messages,
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    import asyncio

    import hamilton_async
    from hamilton import base
    from hamilton.experimental import h_async

    dr = h_async.AsyncDriver({}, hamilton_async, result_builder=base.DictResult())
    dr.display_all_functions("hamilton-async.png")
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(dr.execute(["joke_response"], inputs={"topic": "ice cream"}))
    print(result)
