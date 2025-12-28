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

import fastapi
import pydantic
import summarization

from hamilton import base, driver
from hamilton.experimental import h_async

# instantiate FastAPI app
app = fastapi.FastAPI()


# define constants for Hamilton driver
driver_config = dict(file_type="pdf")

# instantiate the Hamilton driver; it will power all API endpoints
# async driver for use with async functions
async_dr = h_async.AsyncDriver(
    driver_config,
    summarization,  # python module containing function logic
    result_builder=base.DictResult(),
)

# Uncomment this to get started with DAGWorks - see docs.dagworks.io for more info.
# import os
# from dagworks import adapters
# tracker = adapters.DAGWorksTracker(
#     project_id=66,
#     api_key=os.environ["DAGWORKS_API_KEY"],
#     username="YOUR@EMAIL",
#     dag_name="pdf_summarizer",
#     tags={"env": "local", "origin": "fastAPI"}
# )

# sync driver for use with regular functions
sync_dr = (
    driver.Builder()
    .with_config(driver_config)
    .with_modules(summarization)  # python module containing function logic
    # .with_adapters(tracker)  # uncomment this to get started with DAGWorks
    .build()
)


class SummarizeResponse(pydantic.BaseModel):
    """Response to the /summarize endpoint"""

    summary: str


@app.post("/summarize")
async def summarize_pdf(
    pdf_file: fastapi.UploadFile,
    openai_gpt_model: str = fastapi.Form(...),  # = "gpt-3.5-turbo-0613",
    content_type: str = fastapi.Form(...),  # = "Scientific article",
    user_query: str = fastapi.Form(...),  # = "Can you ELI5 the paper?",
) -> SummarizeResponse:
    """Request `summarized_text` from Hamilton driver with `pdf_file` and `user_query`"""
    results = await async_dr.execute(
        ["summarized_text"],
        inputs=dict(
            pdf_source=pdf_file.file,
            openai_gpt_model=openai_gpt_model,
            content_type=content_type,
            user_query=user_query,
        ),
    )

    return SummarizeResponse(summary=results["summarized_text"])


@app.post("/summarize_sync")
def summarize_pdf_sync(
    pdf_file: fastapi.UploadFile,
    openai_gpt_model: str = fastapi.Form(...),  # = "gpt-3.5-turbo-0613",
    content_type: str = fastapi.Form(...),  # = "Scientific article",
    user_query: str = fastapi.Form(...),  # = "Can you ELI5 the paper?",
) -> SummarizeResponse:
    """Request `summarized_text` from Hamilton driver with `pdf_file` and `user_query`"""
    results = sync_dr.execute(
        ["summarized_text"],
        inputs=dict(
            pdf_source=pdf_file.file,
            openai_gpt_model=openai_gpt_model,
            content_type=content_type,
            user_query=user_query,
        ),
    )

    return SummarizeResponse(summary=results["summarized_text"])


# add to SwaggerUI the execution DAG png
# see http://localhost:8080/docs#/default/summarize_pdf_summarize_post
base64_viz = base64.b64encode(open("summarization_module.png", "rb").read()).decode("utf-8")
extra_docs = f"""<h1>Execution DAG</h1><img alt="" src="data:image/png;base64,{base64_viz}"/>"""
app.routes[-1].description += extra_docs
app.routes[-2].description += extra_docs


if __name__ == "__main__":
    # run as a script to test server locally
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
