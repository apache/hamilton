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

import argparse
import json
from pathlib import Path

import information_extraction
from hamilton import driver


MOCK_RESPONSE = {
    "feedback": [
        {
            "product": "mobile app search",
            "sentiment": "positive",
            "issues": [],
            "requested_features": [],
            "summary": "The customer says search is fast.",
        },
        {
            "product": "checkout",
            "sentiment": "negative",
            "issues": ["Checkout froze twice before payment."],
            "requested_features": [],
            "summary": "Checkout reliability blocked payment.",
        },
        {
            "product": "recommendations tab",
            "sentiment": "positive",
            "issues": [],
            "requested_features": [],
            "summary": "Recommendations helped find the right headphones.",
        },
        {
            "product": "orders and saved cards",
            "sentiment": "neutral",
            "issues": [],
            "requested_features": [
                "Order status alerts.",
                "Easier saved card updates.",
            ],
            "summary": "The customer asks for order alerts and card management improvements.",
        },
    ]
}


def _input_text(args: argparse.Namespace) -> str:
    if args.text_file:
        return Path(args.text_file).read_text()
    if args.text:
        return args.text
    return information_extraction.sample_feedback_text()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the information extraction example.")
    parser.add_argument("--text", help="Customer feedback text to extract from.")
    parser.add_argument("--text-file", help="Path to a text file to extract from.")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI chat model.")
    parser.add_argument("--mock-response", action="store_true", help="Run without an API call.")
    args = parser.parse_args()

    dr = driver.Builder().with_modules(information_extraction).build()
    inputs = {
        "input_text": _input_text(args),
        "openai_model": args.model,
    }
    overrides = {}
    if args.mock_response:
        overrides["extraction_response"] = json.dumps(MOCK_RESPONSE)

    result = dr.execute(["extracted_feedback"], inputs=inputs, overrides=overrides)
    print(json.dumps(result["extracted_feedback"], indent=2))
