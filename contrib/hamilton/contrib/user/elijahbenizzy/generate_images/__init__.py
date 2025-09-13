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


def image_prompt(
    image_generation_prompt: str, image_style: str = None, additional_image_prompt: str = None
) -> str:
    """Returns the prompt used to generate an image"""
    prompt_out = image_generation_prompt
    if image_style is not None:
        prompt_out += f" The image should be in the {image_style} style."
    if additional_image_prompt is not None:
        prompt_out += f" {additional_image_prompt}"
    return prompt_out


def generated_image(image_prompt: str, size: str = "1024x1024", hd: bool = False) -> str:
    """Returns the generated image"""
    client = openai.OpenAI()

    response = client.images.generate(
        model="dall-e-3",
        prompt=image_prompt,
        size=size,
        quality="standard" if not hd else "hd",
        n=1,
    )
    image_url = response.data[0].url
    return image_url


if __name__ == "__main__":
    import __init__ as generate_images

    from hamilton import base, driver

    dr = driver.Driver(
        {},
        generate_images,
        adapter=base.DefaultAdapter(),
    )
    # saves to current working directory creating dag.png.
    dr.display_all_functions("dag", {"format": "png", "view": False}, show_legend=False)
