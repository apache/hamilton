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
from contextlib import asynccontextmanager
from dataclasses import dataclass

import fastapi
import pydantic
from fastapi.responses import JSONResponse

from hamilton import driver


@dataclass
class GlobalContext:
    vector_db_url: str
    hamilton_driver: driver.Driver


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI) -> None:
    """Startup and shutdown logic of the FastAPI app
    Above yield statement is at startup and below at shutdown
    Import the Hamilton modules and instantiate the Hamilton driver
    """
    import ingestion
    import retrieval
    import vector_db

    driver_config = dict()

    dr = (
        driver.Builder()
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_config(driver_config)
        .with_modules(ingestion, retrieval, vector_db)
        .build()
    )

    global global_context
    global_context = GlobalContext(vector_db_url="http://weaviate_storage:8083", hamilton_driver=dr)

    # make sure to instantiate the Weaviate class schemas
    global_context.hamilton_driver.execute(
        ["initialize_weaviate_instance"], inputs=dict(vector_db_url=global_context.vector_db_url)
    )

    yield


# instantiate FastAPI app
app = fastapi.FastAPI(
    title="Retrieval Augmented Generation with Hamilton",
    lifespan=lifespan,
)


class SummaryResponse(pydantic.BaseModel):
    summary: str
    chunks: list[dict]


@app.post("/store_arxiv", tags=["Ingestion"])
async def store_arxiv(arxiv_ids: list[str] = fastapi.Form(...)) -> JSONResponse:  # noqa: B008
    """Retrieve PDF files of arxiv articles for arxiv_ids\n
    Read the PDF as text, create chunks, and embed them using OpenAI API\n
    Store chunks with embeddings in Weaviate.
    """
    global_context.hamilton_driver.execute(
        ["store_documents"],
        inputs=dict(
            arxiv_ids=arxiv_ids,
            embedding_model_name="text-embedding-ada-002",
            data_dir="./data",
            vector_db_url=global_context.vector_db_url,
        ),
    )

    return JSONResponse(content=dict(stored_arxiv_ids=arxiv_ids))


@app.post("/store_pdfs", tags=["Ingestion"])
async def store_pdfs(pdf_files: list[fastapi.UploadFile]) -> JSONResponse:
    """For each PDF file, read as text, create chunks, and embed them using OpenAI API\n
    Store chunks with embeddings in Weaviate.
    """
    global_context.hamilton_driver.execute(
        ["store_documents"],
        inputs=dict(
            arxiv_ids=[],
            data_dir="",
            embedding_model_name="text-embedding-ada-002",
            vector_db_url=global_context.vector_db_url,
        ),
        overrides=dict(
            local_pdfs=pdf_files,
        ),
    )

    print([pdf.file for pdf in pdf_files])

    return JSONResponse(content=dict(stored_pdfs=True))


@app.get("/rag_summary", tags=["Retrieval"])
async def rag_summary(
    rag_query: str = fastapi.Form(...),
    hybrid_search_alpha: float = fastapi.Form(...),
    retrieve_top_k: int = fastapi.Form(...),
) -> SummaryResponse:
    """Retrieve most relevant chunks stored in Weaviate using hybrid search\n
    Generate text summaries using ChatGPT for each chunk\n
    Concatenate all chunk summaries into a single query, and reduce into a
    final summary
    """
    results = global_context.hamilton_driver.execute(
        ["rag_summary", "all_chunks"],
        inputs=dict(
            rag_query=rag_query,
            hybrid_search_alpha=hybrid_search_alpha,
            retrieve_top_k=retrieve_top_k,
            embedding_model_name="text-embedding-ada-002",
            summarize_model_name="gpt-3.5-turbo-0613",
            vector_db_url=global_context.vector_db_url,
        ),
    )
    return SummaryResponse(summary=results["rag_summary"], chunks=results["all_chunks"])


@app.get("/documents", tags=["Retrieval"])
async def documents():
    """Retrieve the file names of all stored PDFs in the Weaviate instance"""
    results = global_context.hamilton_driver.execute(
        ["all_documents_file_name"],
        inputs=dict(
            vector_db_url=global_context.vector_db_url,
        ),
    )
    return JSONResponse(content=dict(documents=results["all_documents_file_name"]))


def _add_figures_to_api_routes(app: fastapi.FastAPI) -> None:
    """"""
    routes_with_figures = ["store_arxiv", "store_pdfs", "rag_summary", "documents"]
    for route in app.routes:
        if route.name not in routes_with_figures:
            continue

        base64_str = base64.b64encode(open(f"docs/{route.name}.png", "rb").read()).decode("utf-8")
        base64_wrapped = (
            f"""<h1>Execution DAG</h1><img alt="" src="data:image/png;base64,{base64_str}"/>"""
        )
        route.description += base64_wrapped


_add_figures_to_api_routes(app)


if __name__ == "__main__":
    # run as a script to test server locally
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8082)
