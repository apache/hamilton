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

import openai
import weaviate
from ingestion import _get_embeddings__openai
from tenacity import retry, stop_after_attempt, wait_random_exponential

from hamilton.function_modifiers import extract_fields
from hamilton.htypes import Collect, Parallelizable


def all_documents_file_name(weaviate_client: weaviate.Client) -> list[str]:
    """Get the `file_name` of all `Document` objects stored in Weaviate"""
    response = weaviate_client.query.get("Document", ["file_name"]).do()
    return [d["file_name"] for d in response["data"]["Get"]["Document"]]


def get_document_by_id(weaviate_client: weaviate.Client, document_id: str) -> dict:
    """Get a particular `Document` based on it's Weaviate UUID"""
    response = weaviate_client.data_object.get(class_name="Document", uuid=document_id)
    return dict(
        document_id=response["id"],
        pdf_blob=response["properties"]["pdf_blob"],
        file_name=response["properties"]["file_name"],
    )


def query_embedding(rag_query: str, embedding_model_name: str) -> list[float]:
    """Get the OpenAI embeddings for the RAG query
    NOTE. The embedding function is imported from `ingestion` to match
    how chunks are stored in the vectordb
    """
    return _get_embeddings__openai(texts=[rag_query], embedding_model_name=embedding_model_name)[0]


def document_chunk_hybrid_search_result(
    weaviate_client: weaviate.Client,
    rag_query: str,
    query_embedding: list[float],
    hybrid_search_alpha: float = 0.5,
    retrieve_top_k: int = 5,
) -> list[dict]:
    """Query `Document` objects stored in Weaviate using hybrid search;
    Return a list of k most relevant article objects
    reference for hybrid search: https://weaviate.io/developers/academy/zero_to_mvp/queries_2/hybrid
    """
    response = (
        weaviate_client.query.get(
            "Chunk",
            [
                "chunk_index",
                "content",
                "summary",
                "fromDocument {... on Document {_additional{id}}}",
            ],
        )
        .with_hybrid(
            query=rag_query,
            properties=["content"],
            vector=query_embedding,
            alpha=hybrid_search_alpha,
        )
        .with_additional(["score", "id"])
        .with_limit(retrieve_top_k)
        .do()
    )

    results = []
    for idx, chunk in enumerate(response["data"]["Get"]["Chunk"]):
        results.append(
            dict(
                document_id=chunk["fromDocument"][0]["_additional"]["id"],
                chunk_id=chunk["_additional"]["id"],
                chunk_index=chunk["chunk_index"],
                content=chunk["content"],
                summary=chunk["summary"],
                score=chunk["_additional"]["score"],
                rank=idx,
            )
        )

    return results


@extract_fields(
    dict(
        chunks_without_summary=list[dict],
        chunks_with_summary=list[dict],
    )
)
def check_if_summary_exists(document_chunk_hybrid_search_result: list[dict]) -> dict:
    """Conditional flag to separate chunks that have a store summary from those that didn't"""
    return dict(
        chunks_without_summary=[
            d for d in document_chunk_hybrid_search_result if not d.get("summary")
        ],
        chunks_with_summary=[d for d in document_chunk_hybrid_search_result if d.get("summary")],
    )


def chunk_without_summary(chunks_without_summary: list[dict]) -> Parallelizable[dict]:
    """Iterate over chunks that didn't have a stored summary"""
    for chunk in chunks_without_summary:
        yield chunk


@retry(wait=wait_random_exponential(min=1, max=40), stop=stop_after_attempt(3))
def _summarize_text__openai(prompt: str, summarize_model_name: str) -> str:
    """Use OpenAI chat API to ask a model to summarize content contained in a prompt"""
    response = openai.ChatCompletion.create(
        model=summarize_model_name, messages=[{"role": "user", "content": prompt}], temperature=0
    )
    return response["choices"][0]["message"]["content"]


def prompt_to_summarize_chunk() -> str:
    """Base prompt for summarize a chunk of text"""
    return f"Write a brief bulleted summary of this content.\n\nContent:{{content}}"  # noqa: F541


def chunk_with_new_summary(
    chunk_without_summary: dict,
    prompt_to_summarize_chunk: str,
    summarize_model_name: str,
) -> dict:
    """Fill a base prompt with a chunk's content and summarize it;
    Store the summary in the chunk object
    """
    filled_prompt = prompt_to_summarize_chunk.format(content=chunk_without_summary["content"])
    new_chunk = dict(**chunk_without_summary)
    new_chunk["summary"] = _summarize_text__openai(filled_prompt, summarize_model_name)
    return new_chunk


def store_chunk_summary(
    weaviate_client: weaviate.Client,
    chunk_with_new_summary: dict,
) -> dict:
    """Store in Weaviate the recently computed summary for chunks that previously didn't have one."""
    updated_chunk_object = dict(
        chunk_index=chunk_with_new_summary["chunk_index"],
        content=chunk_with_new_summary["content"],
        summary=chunk_with_new_summary["summary"],
    )
    weaviate_client.data.update(
        data_object=updated_chunk_object,
        class_name="Chunk",
        uuid=chunk_with_new_summary["id"],
    )
    return dict(updated_chunk_with_id=chunk_with_new_summary["id"])


def prompt_to_reduce_summaries() -> str:
    """Prompt for a "reduce" operation to summarize a list of summaries into a single text"""
    return f"""Write a summary from this collection of key points.
    First answer the question in two sentences. Then, highlight the core argument, conclusions and evidence.
    User query: {{query}}
    The summary should be structured in bulleted lists following the headings Answer, Core Argument, Evidence, and Conclusions.
    Key points:\n{{chunks_summary}}\nSummary:\n"""  # noqa: F541


def chunk_with_new_summary_collection(chunk_with_new_summary: Collect[dict]) -> list[dict]:
    """Collect chunks for which a new summary was just computed"""
    return chunk_with_new_summary


def all_chunks(
    chunk_with_new_summary_collection: list[dict],
    chunks_with_summary: list[dict],
) -> list[dict]:
    """Merge chunks back into a list and sort it by the original Weaviate relevance rank"""
    all_chunks = chunk_with_new_summary_collection + chunks_with_summary
    sorted_chunks = list(sorted(all_chunks, key=lambda chunk: chunk["rank"]))
    return sorted_chunks


def rag_summary(
    rag_query: str,
    all_chunks: list[dict],
    prompt_to_reduce_summaries: str,
    summarize_model_name: str,
) -> str:
    """Concatenate the list of chunk summaries into a single text,fill the prompt template,
    and use OpenAI to reduce the content into a single summary;
    """
    concatenated_summaries = " ".join(chunk["summary"] for chunk in all_chunks)
    filled_prompt = prompt_to_reduce_summaries.format(
        query=rag_query, chunks_summary=concatenated_summaries
    )
    return _summarize_text__openai(filled_prompt, summarize_model_name)


if __name__ == "__main__":
    # run as a script to test Hamilton's execution
    import retrieval
    import vector_db

    from hamilton import driver

    inputs = dict(
        vector_db_url="http://localhost:8083",
        rag_query="What are the main challenges of deploying ML models?",
        embedding_model_name="text-embedding-ada-002",
        summarize_model_name="gpt-3.5-turbo-0613",
    )

    dr = (
        driver.Builder()
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_modules(vector_db, retrieval)
        .build()
    )

    results = dr.execute(
        final_vars=["rag_summary"],
        inputs=inputs,
    )
