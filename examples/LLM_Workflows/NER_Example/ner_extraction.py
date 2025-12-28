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

from typing import Union

import torch
from datasets import Dataset, load_dataset  # noqa: F401
from datasets.formatting.formatting import LazyBatch
from sentence_transformers import SentenceTransformer
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    PreTrainedModel,
    PreTrainedTokenizer,
    pipeline,
)
from transformers.pipelines import base

from hamilton.function_modifiers import load_from, save_to, source, value

# Could explicitly load the dataset this way
# def medium_articles() -> Dataset:
#     """Loads medium dataset into a hugging face dataset"""
#     ds = load_dataset(
#         "fabiochiu/medium-articles",
#         data_files="medium_articles.csv",
#         split="train"
#     )
#     return ds


@load_from.hf_dataset(
    path=value("fabiochiu/medium-articles"),
    data_files=value("medium_articles.csv"),
    split=value("train"),
)
def medium_articles(dataset: Dataset) -> Dataset:
    """Loads medium dataset into a hugging face dataset"""
    return dataset


def sampled_articles(
    medium_articles: Dataset,
    sample_size: int = 104,
    random_state: int = 32,
    max_text_length: int = 1000,
) -> Dataset:
    """Samples the articles and does some light transformations.
    Transformations:
     - selects the first 1000 characters of text. This is for performance here. But in real life you'd \
     do something for your use case.
      - Joins article title and the text to create one text string.
    """
    # Filter out entries with NaN values in 'text' or 'title' fields
    dataset = medium_articles.filter(
        lambda example: example["text"] is not None and example["title"] is not None
    )

    # Shuffle and take the first 10000 samples
    dataset = dataset.shuffle(seed=random_state).select(range(sample_size))

    # Truncate the 'text' to the first 1000 characters
    dataset = dataset.map(lambda example: {"text": example["text"][:max_text_length]})

    # Concatenate the 'title' and truncated 'text'
    dataset = dataset.map(lambda example: {"title_text": example["title"] + ". " + example["text"]})
    return dataset


def device() -> str:
    """Whether this is a CUDA or CPU enabled device."""
    return "cuda" if torch.cuda.is_available() else "cpu"


def NER_model_id() -> str:
    """Model ID to use
    To extract named entities, we will use a NER model finetuned on a BERT-base model.
    The model can be loaded from the HuggingFace model hub.
    Use `overrides={"NER_model_id": VALUE}` to switch this without changing code.
    """
    return "dslim/bert-base-NER"


def tokenizer(NER_model_id: str) -> PreTrainedTokenizer:
    """Loads the tokenizer for the NER model ID from huggingface"""
    return AutoTokenizer.from_pretrained(NER_model_id)


def model(NER_model_id: str) -> PreTrainedModel:
    """Loads the NER model from huggingface"""
    return AutoModelForTokenClassification.from_pretrained(NER_model_id)


def ner_pipeline(
    model: PreTrainedModel, tokenizer: PreTrainedTokenizer, device: str
) -> base.Pipeline:
    """Loads the tokenizer and model into a NER pipeline. That is it combines them."""
    device_no = torch.cuda.current_device() if device == "cuda" else None
    return pipeline(
        "ner", model=model, tokenizer=tokenizer, aggregation_strategy="max", device=device_no
    )


def retriever(
    device: str, retriever_model_id: str = "flax-sentence-embeddings/all_datasets_v3_mpnet-base"
) -> SentenceTransformer:
    """Our retriever model to create embeddings.

    A retriever model is used to embed passages (article title + first 1000 characters)
     and queries. It creates embeddings such that queries and passages with similar
     meanings are close in the vector space. We will use a sentence-transformer model
      as our retriever. The model can be loaded as follows:
    """
    return SentenceTransformer(retriever_model_id, device=device)


def _extract_named_entities_text(
    title_text_batch: Union[LazyBatch, list[str]], _ner_pipeline
) -> list[list[str]]:
    """Helper function to extract named entities given a batch of text."""
    # extract named entities using the NER pipeline
    extracted_batch = _ner_pipeline(title_text_batch)
    # this should be extracted_batch = dataset.map(ner_pipeline)
    entities = []
    # loop through the results and only select the entity names
    for text in extracted_batch:
        ne = [entity["word"] for entity in text]
        entities.append(ne)
    _named_entities = [list(set(entity)) for entity in entities]
    return _named_entities


def _batch_map(dataset: LazyBatch, _retriever, _ner_pipeline) -> dict:
    """Helper function to created the embedding vectors and extract named entities"""
    title_text_list = dataset["title_text"]
    emb = _retriever.encode(title_text_list)
    _named_entities = _extract_named_entities_text(title_text_list, _ner_pipeline)
    return {
        "vector": emb,
        "named_entities": _named_entities,
    }


def columns_of_interest() -> list[str]:
    """The columns we expect to pull from the dataset to be saved to lancedb"""
    return ["vector", "named_entities", "title", "url", "authors", "timestamp", "tags"]


@save_to.lancedb(
    db_client=source("db_client"),
    table_name=source("table_name"),
    columns_to_write=source("columns_of_interest"),
    output_name_="load_into_lancedb",
)
def final_dataset(
    sampled_articles: Dataset,
    retriever: SentenceTransformer,
    ner_pipeline: base.Pipeline,
) -> Dataset:
    """The final dataset to be pushed to lancedb.

    This adds two columns:

     - vector -- the vector embedding
     - named_entities -- the names of entities extracted from the text
    """
    # goes over the data in batches so that the GPU can be properly utilized.
    final_ds = sampled_articles.map(
        _batch_map,
        batched=True,
        fn_kwargs={"_retriever": retriever, "_ner_pipeline": ner_pipeline},
        desc="extracting entities",
    )
    return final_ds


def named_entities(query: str, ner_pipeline: base.Pipeline) -> list[str]:
    """The entities to extract from the query via the pipeline."""
    return _extract_named_entities_text([query], ner_pipeline)[0]
