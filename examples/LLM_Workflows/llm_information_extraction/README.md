# LLM Information Extraction with Hamilton and Groq

This example demonstrates how to use Apache Hamilton to build an LLM-powered information extraction pipeline.

It extracts structured product feedback from unstructured text using Groq and validates the generated JSON using Pydantic.

## Overview

The pipeline accepts a product review and extracts:

- Product name
- Sentiment (`positive`, `negative`, or `neutral`)
- Important feedback points

### Example input

```text
The battery life of the Samsung Galaxy S24 is excellent,
but the phone gets hot while gaming.
Overall, I am happy with the purchase.
```

### Expected output

```json
{
  "product": "Samsung Galaxy S24",
  "sentiment": "positive",
  "key_points": [
    "Battery life is excellent",
    "Phone gets hot while gaming",
    "Overall satisfaction with the purchase"
  ]
}
```

## Pipeline architecture

1. `review_text` – Accepts the product review.
2. `extraction_prompt` – Generates instructions for the LLM.
3. `llm_response` – Sends the prompt to Groq.
4. `validated_feedback` – Parses the JSON response and validates it against a Pydantic schema.

Hamilton automatically builds the dependency graph from the Python function parameters.

## Requirements

- Python 3.11 or later
- A Groq API key

## Installation

From the root of the Hamilton repository, install Hamilton:

```bash
python -m pip install -e .
```

Install the example dependencies:

```bash
python -m pip install -r examples/LLM_Workflows/llm_information_extraction/requirements.txt
```

## Configuration

Set your Groq API key as an environment variable.

**Windows PowerShell:**

```powershell
$env:GROQ_API_KEY="your_groq_api_key"
```

**Linux/macOS:**

```bash
export GROQ_API_KEY="your_groq_api_key"
```

Do not hardcode your API key in the source code.

## Run the example

From the root of the Hamilton repository:

```bash
python examples/LLM_Workflows/llm_information_extraction/run.py
```

## Validation

The example uses Pydantic to validate the generated JSON.

The sentiment field only accepts three values:

- `positive`
- `negative`
- `neutral`

Malformed JSON, missing required fields, and invalid sentiment values raise validation errors instead of being silently accepted.

## Run tests

Run the automated tests from the repository root:

```bash
python -m pytest examples/LLM_Workflows/llm_information_extraction/test_functions.py -v
```

The tests cover valid positive, negative, and neutral feedback, invalid sentiment, malformed JSON, and missing required fields.

## Dependencies

- Apache Hamilton
- Groq Python SDK
- Pydantic

## Notes

LLM-generated results may vary. The example demonstrates structured extraction and local schema validation; it does not guarantee that every extracted fact is correct.