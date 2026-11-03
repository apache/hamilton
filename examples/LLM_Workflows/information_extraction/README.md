<!--
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
-->

# Information Extraction

This example shows how to model an LLM information extraction task as a Hamilton dataflow.
It takes customer feedback text, builds a JSON schema from Pydantic models, creates an extraction prompt, sends it to the OpenAI chat API, parses the JSON response, and validates the result.

The dataflow is intentionally small so each part of the extraction pipeline is visible as a Hamilton node:

- `output_schema`: the expected JSON shape
- `extraction_prompt`: prompt built from the schema and input text
- `extraction_response`: OpenAI API response
- `parsed_extraction`: JSON parsing
- `validated_extraction`: Pydantic validation
- `extracted_feedback`: serializable extracted records

## Run

Install the requirements:

```bash
pip install -r requirements.txt
```

Run with a mocked LLM response:

```bash
python run.py --mock-response
```

Run with OpenAI:

```bash
export OPENAI_API_KEY=...
python run.py
```

You can pass custom text directly:

```bash
python run.py --text "The app search is great, but checkout keeps failing."
```

Or read text from a file:

```bash
python run.py --text-file feedback.txt
```
