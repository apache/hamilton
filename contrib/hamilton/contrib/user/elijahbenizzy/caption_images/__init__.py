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

import base64
import datetime
import logging
from typing import IO, Any, Dict, List, Optional, Union

from hamilton.function_modifiers import config

logger = logging.getLogger(__name__)

import urllib

from hamilton import contrib

with contrib.catch_import_errors(__name__, __file__, logger):
    # non-hamilton imports go here
    import boto3
    import openai


def openai_client() -> openai.OpenAI:
    """OpenAI client to use"""
    return openai.OpenAI()


def _encode_image(image_path_or_file: Union[str, IO], ext: str):
    """Helper fn to return a base-64 encoded image"""
    file_like_object = (
        image_path_or_file
        if hasattr(image_path_or_file, "read")
        else open(image_path_or_file, "rb")
    )
    with file_like_object as image_file:
        out = base64.b64encode(image_file.read()).decode("utf-8")
    return f"data:image/{ext};base64,{out}"


def core_prompt() -> str:
    """This is the core prompt. You can override this if needed."""
    return "Please provide a caption for this image."


def processed_image_url(image_url: str) -> str:
    """Returns a processed image URL -- base-64 encoded if it is local,
    otherwise remote if it is a URL"""
    is_local = urllib.parse.urlparse(image_url).scheme == ""
    is_s3 = urllib.parse.urlparse(image_url).scheme == "s3"
    ext = image_url.split(".")[-1]
    if is_local:
        # In this case we load up/encode
        return _encode_image(image_url, ext)
    elif is_s3:
        # In this case we just return the URL
        client = boto3.client("s3")
        bucket = urllib.parse.urlparse(image_url).netloc
        key = urllib.parse.urlparse(image_url).path[1:]
        obj = client.get_object(Bucket=bucket, Key=key)
        return _encode_image(obj["Body"], ext)
    # In this case we just return the URL
    return image_url


def caption_prompt(
    core_prompt: str,
    additional_prompt: Optional[str] = None,
    descriptiveness: Optional[str] = None,
) -> str:
    """Returns the prompt used to describe an image"""
    out = core_prompt
    if descriptiveness is not None:
        out += f" The caption should be {descriptiveness} descriptive."
    if additional_prompt is not None:
        out += f" {additional_prompt}"
    return out


DEFAULT_MODEL = "gpt-4-vision-preview"
DEFAULT_EMBEDDINGS_MODEL = "text-embedding-ada-002"


def generated_caption(
    processed_image_url: str,
    caption_prompt: str,
    openai_client: openai.OpenAI,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 2000,
) -> str:
    """Returns the response to a given chat"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": caption_prompt,
                },
                {"type": "image_url", "image_url": {"url": f"{processed_image_url}"}},
            ],
        }
    ]
    response = openai_client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


@config.when(include_embeddings=True)
def caption_embeddings(
    openai_client: openai.OpenAI,
    embeddings_model: str = DEFAULT_EMBEDDINGS_MODEL,
    generated_caption: str = None,
) -> List[float]:
    """Returns the embeddings for a generated caption"""
    data = (
        openai_client.embeddings.create(
            input=[generated_caption],
            model=embeddings_model,
        )
        .data[0]
        .embedding
    )
    return data


def caption_metadata(
    image_url: str,
    generated_caption: str,
    caption_prompt: str,
    model: str = DEFAULT_MODEL,
) -> dict:
    """Returns metadata for the caption portion of the workflow"""
    return {
        "original_image_url": image_url,
        "generated_caption": generated_caption,
        "caption_model": model,
        "caption_prompt": caption_prompt,
    }


@config.when(include_embeddings=True)
def embeddings_metadata(
    caption_embeddings: List[float],
    embeddings_model: str = DEFAULT_EMBEDDINGS_MODEL,
) -> dict:
    """Returns metadata for the embeddings portion of the workflow"""
    return {
        "caption_embeddings": caption_embeddings,
        "embeddings_model": embeddings_model,
    }


def metadata(
    embeddings_metadata: dict,
    caption_metadata: Optional[dict] = None,
    additional_metadata: Optional[dict] = None,
) -> Dict[str, Any]:
    """Returns the response to a given chat"""
    out = embeddings_metadata
    if caption_metadata is not None:
        out.update(caption_metadata)
    if additional_metadata is not None:
        out.update(additional_metadata)
    out.update({"execution_time": datetime.datetime.utcnow().isoformat()})
    return out


if __name__ == "__main__":
    # Code to create an imaging showing on DAG workflow.
    # run as a script to test Hamilton's execution
    import __init__ as image_captioning

    from hamilton import base, driver

    dr = driver.Driver(
        {"include_embeddings": True},  # CONFIG: fill as appropriate
        image_captioning,
        adapter=base.DefaultAdapter(),
    )
    # saves to current working directory creating dag.png.
    dr.display_all_functions("dag", {"format": "png", "view": False}, show_legend=False)
