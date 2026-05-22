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

import json
import os
import re
from typing import Any, Literal

from openai import OpenAI
from pydantic import BaseModel, Field


class ProductFeedback(BaseModel):
    product: str = Field(description="Product or feature mentioned by the customer.")
    sentiment: Literal["positive", "negative", "neutral", "mixed"]
    issues: list[str] = Field(default_factory=list)
    requested_features: list[str] = Field(default_factory=list)
    summary: str


class FeedbackExtraction(BaseModel):
    feedback: list[ProductFeedback]


def sample_feedback_text() -> str:
    """Customer feedback to extract from."""
    return (
        "The mobile app search is fast, but checkout froze twice before I could pay. "
        "I still like the recommendations tab because it found the right headphones. "
        "Please add order status alerts and make saved cards easier to update."
    )


def output_schema() -> dict[str, Any]:
    """JSON schema for the extraction."""
    schema_method = getattr(FeedbackExtraction, "model_json_schema", FeedbackExtraction.schema)
    return schema_method()


def extraction_prompt(input_text: str, output_schema: dict[str, Any]) -> str:
    """Prompt sent to the LLM."""
    return f"""Extract structured product feedback from the text.

Return only JSON that matches this schema:
{json.dumps(output_schema, indent=2)}

Text:
{input_text}
"""


def llm_client() -> OpenAI:
    """OpenAI client."""
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def extraction_messages(extraction_prompt: str) -> list[dict[str, str]]:
    """Chat messages for extraction."""
    return [
        {
            "role": "system",
            "content": "You extract structured data and return valid JSON only.",
        },
        {"role": "user", "content": extraction_prompt},
    ]


def extraction_response(
    llm_client: OpenAI,
    extraction_messages: list[dict[str, str]],
    openai_model: str = "gpt-4o-mini",
) -> str:
    """Raw LLM response."""
    response = llm_client.chat.completions.create(
        model=openai_model,
        messages=extraction_messages,
        response_format={"type": "json_object"},
        temperature=0,
    )
    return response.choices[0].message.content or ""


def parsed_extraction(extraction_response: str) -> dict[str, Any]:
    """Parsed JSON response."""
    cleaned_response = re.sub(r"^```(?:json)?|```$", "", extraction_response.strip()).strip()
    return json.loads(cleaned_response)


def validated_extraction(parsed_extraction: dict[str, Any]) -> FeedbackExtraction:
    """Validated extraction."""
    return FeedbackExtraction(**parsed_extraction)


def extracted_feedback(validated_extraction: FeedbackExtraction) -> list[dict[str, Any]]:
    """Serializable feedback records."""
    model_dump = getattr(validated_extraction, "model_dump", validated_extraction.dict)
    return model_dump()["feedback"]
