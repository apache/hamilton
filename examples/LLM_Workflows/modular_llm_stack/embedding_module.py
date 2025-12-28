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

from types import ModuleType

import cohere
import numpy as np
import openai
from fastembed import TextEmbedding
from sentence_transformers import SentenceTransformer

from hamilton.function_modifiers import config, extract_fields


@config.when(embedding_service="openai")
@extract_fields(
    dict(
        embedding_dimension=int,
        embedding_metric=str,
    )
)
def embedding_config__openai(model_name: str) -> dict:
    if model_name == "text-embedding-ada-002":
        return dict(embedding_dimension=1536, embedding_metric="cosine")
    # If you support more models, you would add that here
    raise ValueError(f"Invalid `model_name`[{model_name}] for openai was passed.")


@config.when(embedding_service="cohere")
@extract_fields(
    dict(
        embedding_dimension=int,
        embedding_metric=str,
    )
)
def embedding_config__cohere(model_name: str) -> dict:
    if model_name == "embed-english-light-v2.0":
        return dict(embedding_dimension=1024, embedding_metric="cosine")
    # If you support more models, you would add that here
    raise ValueError(f"Invalid `model_name`[{model_name}] for Cohere was passed.")


@config.when(embedding_service="sentence_transformer")
@extract_fields(
    dict(
        embedding_dimension=int,
        embedding_metric=str,
    )
)
def embedding_config__sentence_transformer(model_name: str) -> dict:
    if model_name == "multi-qa-MiniLM-L6-cos-v1":
        return dict(embedding_dimension=384, embedding_metric="cosine")
    # If you support more models, you would add that here
    raise ValueError(f"Invalid `model_name`[{model_name}] for SentenceTransformer was passed.")


@config.when(embedding_service="fastembed")
@extract_fields(
    dict(
        embedding_dimension=int,
        embedding_metric=str,
    )
)
def embedding_config__fastembed(model_name: str) -> dict:
    for model in TextEmbedding.list_supported_models():
        if model_name == model["model"]:
            return dict(embedding_dimension=model["dim"], embedding_metric="cosine")
    raise ValueError(f"Invalid `model_name`[{model_name}] for FastEmbed was passed.")


def metadata(embedding_service: str, model_name: str) -> dict:
    """Create metadata dictionary"""
    return dict(embedding_service=embedding_service, model_name=model_name)


@config.when(embedding_service="openai")
def embedding_provider__openai(api_key: str) -> ModuleType:
    """Set OpenAI API key"""
    openai.api_key = api_key
    return openai


@config.when(embedding_service="openai")
def embeddings__openai(
    embedding_provider: ModuleType,
    text_contents: list[str],
    model_name: str = "text-embedding-ada-002",
) -> list[np.ndarray]:
    """Convert text to vector representations (embeddings) using OpenAI Embeddings API
    reference: https://github.com/openai/openai-cookbook/blob/main/examples/Get_embeddings.ipynb
    """
    response = embedding_provider.Embedding.create(input=text_contents, engine=model_name)
    return [np.asarray(obj["embedding"]) for obj in response["data"]]


@config.when(embedding_service="cohere")
def embedding_provider__cohere(api_key: str) -> cohere.Client:
    """Create Cohere client based on API key"""
    return cohere.Client(api_key)


@config.when(embedding_service="cohere")
def embeddings__cohere(
    embedding_provider: cohere.Client,
    text_contents: list[str],
    model_name: str = "embed-english-light-v2.0",
) -> list[np.ndarray]:
    """Convert text to vector representations (embeddings) using Cohere Embed API
    reference: https://docs.cohere.com/reference/embed
    """
    response = embedding_provider.embed(
        texts=text_contents,
        model=model_name,
        truncate="END",
    )
    return [np.asarray(embedding) for embedding in response.embeddings]


@config.when(embedding_service="sentence_transformer")
def embeddings__sentence_transformer(
    text_contents: list[str], model_name: str = "multi-qa-MiniLM-L6-cos-v1"
) -> list[np.ndarray]:
    """Convert text to vector representations (embeddings)
    model card: https://huggingface.co/sentence-transformers/multi-qa-MiniLM-L6-cos-v1
    reference: https://www.sbert.net/examples/applications/computing-embeddings/README.html
    """
    embedding_provider = SentenceTransformer(model_name)
    embeddings = embedding_provider.encode(text_contents, convert_to_numpy=True)
    return list(embeddings)


@config.when(embedding_service="fastembed")
def embeddings__fastembed(
    text_contents: list[str], model_name: str = "BAAI/bge-small-en-v1.5"
) -> list[np.ndarray]:
    """CPU-first library for generating vector embeddings.
    Reference: https://qdrant.github.io/fastembed/
    """
    model = TextEmbedding(model_name)
    return list(model.embed(text_contents))
