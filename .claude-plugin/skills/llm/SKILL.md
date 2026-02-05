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

---
name: hamilton-llm
description: LLM and AI workflow patterns for Hamilton including RAG pipelines, embeddings, vector databases, and prompt engineering. Use for building AI applications with Hamilton.
allowed-tools: Read, Grep, Glob, Bash(python:*), Bash(pytest:*)
user-invocable: true
disable-model-invocation: false
---

# Hamilton for LLM & AI Workflows

This skill covers patterns for building LLM applications, RAG pipelines, and AI workflows with Apache Hamilton.

## Why Hamilton for LLM Workflows?

**Key Benefits:**
- **Modular prompts**: Each prompt component is a testable function
- **Dependency tracking**: Clear lineage from data → embeddings → retrieval → generation
- **Async parallelization**: Multiple LLM calls happen concurrently
- **Caching**: Avoid redundant expensive API calls
- **Observability**: Track LLM calls, costs, and performance
- **Testing**: Unit test prompts, retrieval, and generation separately

## RAG Pipeline Pattern

**Complete RAG Implementation:**

```python
"""RAG pipeline with Hamilton."""
import openai
from typing import List, Dict
import aiohttp

# 1. Document Loading & Processing
async def document_text(document_url: str) -> str:
    """Fetch document from URL."""
    async with aiohttp.ClientSession() as session:
        async with session.get(document_url) as resp:
            return await resp.text()

def document_chunks(
    document_text: str,
    chunk_size: int = 1000,
    overlap: int = 100
) -> List[str]:
    """Split document into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(document_text):
        end = start + chunk_size
        chunks.append(document_text[start:end])
        start = end - overlap
    return chunks

# 2. Embedding Generation
async def embeddings(
    document_chunks: List[str],
    embedding_model: str = 'text-embedding-3-small'
) -> List[List[float]]:
    """Generate embeddings for chunks."""
    client = openai.AsyncOpenAI()
    response = await client.embeddings.create(
        input=document_chunks,
        model=embedding_model
    )
    return [item.embedding for item in response.data]

# 3. Vector Store
async def vector_store_ids(
    embeddings: List[List[float]],
    document_chunks: List[str]
) -> List[str]:
    """Store embeddings in vector database."""
    import pinecone
    index = pinecone.Index('documents')

    vectors = [
        (f"chunk_{i}", emb, {"text": chunk})
        for i, (emb, chunk) in enumerate(zip(embeddings, document_chunks))
    ]
    await index.upsert(vectors)
    return [v[0] for v in vectors]

# 4. Query & Retrieval
async def query_embedding(
    query: str,
    embedding_model: str = 'text-embedding-3-small'
) -> List[float]:
    """Generate embedding for query."""
    client = openai.AsyncOpenAI()
    response = await client.embeddings.create(
        input=[query],
        model=embedding_model
    )
    return response.data[0].embedding

async def retrieved_chunks(
    query_embedding: List[float],
    top_k: int = 5
) -> List[str]:
    """Retrieve relevant chunks from vector store."""
    import pinecone
    index = pinecone.Index('documents')

    results = await index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
    return [match['metadata']['text'] for match in results['matches']]

# 5. Prompt Construction
def rag_prompt(query: str, retrieved_chunks: List[str]) -> str:
    """Construct RAG prompt with context."""
    context = "\n\n".join(retrieved_chunks)
    return f"""Answer the question based on the context below.

Context:
{context}

Question: {query}

Answer:"""

# 6. LLM Generation
async def llm_response(
    rag_prompt: str,
    model: str = "gpt-4"
) -> str:
    """Generate response using LLM."""
    client = openai.AsyncOpenAI()
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": rag_prompt}]
    )
    return response.choices[0].message.content

# Execute the RAG pipeline
from hamilton import async_driver
import rag_pipeline

dr = await async_driver.Builder().with_modules(rag_pipeline).build()

# Indexing phase
await dr.execute(
    ['vector_store_ids'],
    inputs={'document_url': 'https://example.com/doc.pdf'}
)

# Query phase
result = await dr.execute(
    ['llm_response'],
    inputs={'query': 'What is the main topic?'}
)
```

## Multi-Provider Pattern

**Support multiple LLM providers:**

```python
"""Multi-provider LLM configuration."""
from hamilton.function_modifiers import config
import openai
import anthropic

@config.when(provider='openai')
def llm_client__openai() -> openai.AsyncOpenAI:
    """OpenAI client."""
    return openai.AsyncOpenAI()

@config.when(provider='anthropic')
def llm_client__anthropic() -> anthropic.AsyncAnthropic:
    """Anthropic client."""
    return anthropic.AsyncAnthropic()

@config.when(provider='openai')
async def llm_response__openai(
    llm_client: openai.AsyncOpenAI,
    prompt: str
) -> str:
    """Generate with OpenAI."""
    response = await llm_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

@config.when(provider='anthropic')
async def llm_response__anthropic(
    llm_client: anthropic.AsyncAnthropic,
    prompt: str
) -> str:
    """Generate with Anthropic."""
    response = await llm_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

# Switch providers via config
dr = await async_driver.Builder()\
    .with_config({'provider': 'anthropic'})\
    .with_modules(llm_module)\
    .build()
```

## Parallel LLM Calls

**Multiple analyses in parallel:**

```python
"""Run multiple LLM analyses concurrently."""
import openai

async def llm_client() -> openai.AsyncOpenAI:
    """Shared LLM client."""
    return openai.AsyncOpenAI()

def summarization_prompt(document: str) -> str:
    """Prompt for summarization."""
    return f"Summarize this document:\n\n{document}"

def keyword_prompt(document: str) -> str:
    """Prompt for keyword extraction."""
    return f"Extract 5 key topics from this document:\n\n{document}"

def sentiment_prompt(document: str) -> str:
    """Prompt for sentiment analysis."""
    return f"Analyze the sentiment of this document:\n\n{document}"

# These three run in parallel!
async def summary(llm_client: openai.AsyncOpenAI, summarization_prompt: str) -> str:
    """Generate summary."""
    response = await llm_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": summarization_prompt}]
    )
    return response.choices[0].message.content

async def keywords(llm_client: openai.AsyncOpenAI, keyword_prompt: str) -> List[str]:
    """Extract keywords."""
    response = await llm_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": keyword_prompt}]
    )
    return response.choices[0].message.content.split('\n')

async def sentiment(llm_client: openai.AsyncOpenAI, sentiment_prompt: str) -> str:
    """Analyze sentiment."""
    response = await llm_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": sentiment_prompt}]
    )
    return response.choices[0].message.content

def document_analysis(summary: str, keywords: List[str], sentiment: str) -> dict:
    """Combine all analyses."""
    return {"summary": summary, "keywords": keywords, "sentiment": sentiment}

# Result: 3 LLM calls happen concurrently, ~3x faster!
```

## Caching LLM Calls

**Save API costs with caching:**

```python
"""Cache expensive LLM calls."""
from hamilton.function_modifiers import cache
import openai

@cache(behavior="default")  # Cache LLM responses
async def document_summary(document_text: str, llm_client: openai.AsyncOpenAI) -> str:
    """Generate summary (cached).

    First call: Makes API request, caches result
    Subsequent calls: Retrieves from cache (free & instant!)
    """
    response = await llm_client.chat.completions.create(
        model="gpt-4",
        messages=[{
            "role": "user",
            "content": f"Summarize this document:\n\n{document_text}"
        }]
    )
    return response.choices[0].message.content

# First run: Costs $0.01
# Second run: $0.00, instant retrieval
# Savings on 1000 documents: $10!
```

## Prompt Engineering Patterns

**Modular prompts:**

```python
"""Build complex prompts from components."""
def system_message(task_type: str) -> str:
    """System message based on task."""
    templates = {
        "summarize": "You are an expert at creating concise summaries.",
        "extract": "You are an expert at extracting structured information.",
        "analyze": "You are an expert at analyzing content and providing insights."
    }
    return templates[task_type]

def user_context(document: str, max_length: int = 2000) -> str:
    """Truncate document if needed."""
    return document[:max_length] if len(document) > max_length else document

def instruction(task_type: str) -> str:
    """Task-specific instruction."""
    instructions = {
        "summarize": "Provide a 3-sentence summary.",
        "extract": "Extract key entities and dates.",
        "analyze": "Analyze the main themes and sentiment."
    }
    return instructions[task_type]

def messages(system_message: str, user_context: str, instruction: str) -> List[dict]:
    """Combine into message list."""
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"{user_context}\n\n{instruction}"}
    ]

async def llm_result(llm_client: openai.AsyncOpenAI, messages: List[dict]) -> str:
    """Execute LLM call."""
    response = await llm_client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )
    return response.choices[0].message.content
```

## Structured Output with Pydantic

**Parse LLM output into structured data:**

```python
"""Structured extraction with validation."""
from pydantic import BaseModel, Field
from typing import List
import openai

class ExtractedEntity(BaseModel):
    """Structured entity."""
    name: str = Field(description="Entity name")
    type: str = Field(description="Entity type (person, org, location)")
    relevance: float = Field(description="Relevance score 0-1", ge=0, le=1)

class ExtractionResult(BaseModel):
    """Complete extraction result."""
    entities: List[ExtractedEntity]
    summary: str

async def structured_extraction(
    document: str,
    llm_client: openai.AsyncOpenAI
) -> ExtractionResult:
    """Extract structured data from document."""
    response = await llm_client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[{
            "role": "user",
            "content": f"Extract entities from:\n\n{document}"
        }],
        response_format=ExtractionResult
    )
    return response.choices[0].message.parsed
```

## Agent Patterns

**Multi-step agent with Hamilton:**

```python
"""Agent with tool use."""
from typing import Literal

def agent_prompt(query: str, available_tools: List[str]) -> str:
    """Create agent prompt with tools."""
    tools_desc = "\n".join(f"- {tool}" for tool in available_tools)
    return f"""You have access to these tools:
{tools_desc}

User query: {query}

What tool should be used? Respond with just the tool name."""

async def tool_selection(
    llm_client: openai.AsyncOpenAI,
    agent_prompt: str
) -> Literal["search", "calculate", "summarize"]:
    """LLM selects which tool to use."""
    response = await llm_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": agent_prompt}]
    )
    return response.choices[0].message.content.strip().lower()

@config.when_in(tool_selection=["search"])
async def tool_result__search(query: str) -> str:
    """Execute search tool."""
    # Implement search logic
    return "Search results..."

@config.when_in(tool_selection=["calculate"])
def tool_result__calculate(query: str) -> str:
    """Execute calculation tool."""
    # Implement calculation logic
    return "Calculation result..."

async def final_response(
    llm_client: openai.AsyncOpenAI,
    query: str,
    tool_result: str
) -> str:
    """Generate final response with tool result."""
    response = await llm_client.chat.completions.create(
        model="gpt-4",
        messages=[{
            "role": "user",
            "content": f"User asked: {query}\nTool returned: {tool_result}\n\nProvide final answer:"
        }]
    )
    return response.choices[0].message.content
```

## Testing LLM Workflows

**Unit test prompts and logic:**

```python
"""Test LLM components."""
import pytest

def test_prompt_construction():
    """Test prompt building logic."""
    from llm_module import rag_prompt

    query = "What is Hamilton?"
    chunks = ["Hamilton is a framework", "It builds DAGs"]

    prompt = rag_prompt(query, chunks)

    assert "Hamilton is a framework" in prompt
    assert "What is Hamilton?" in prompt
    assert "Context:" in prompt

async def test_retrieval():
    """Test retrieval logic (mock vector store)."""
    # Mock vector store responses
    # Test retrieval function
    pass

def test_structured_output():
    """Test Pydantic parsing."""
    from llm_module import ExtractionResult, ExtractedEntity

    result = ExtractionResult(
        entities=[
            ExtractedEntity(name="Hamilton", type="product", relevance=0.9)
        ],
        summary="A framework for building DAGs"
    )

    assert len(result.entities) == 1
    assert result.entities[0].name == "Hamilton"
```

## Best Practices

1. **Modularize prompts** - Each component is a testable function
2. **Cache aggressively** - LLM calls are expensive
3. **Use async** - Parallelize independent LLM calls
4. **Structure outputs** - Use Pydantic for parsing
5. **Handle failures** - Add retry logic and fallbacks
6. **Track costs** - Monitor token usage
7. **Version prompts** - Use config for prompt variants

## Additional Resources

- For async patterns, use `/hamilton-scale`
- For observability, use `/hamilton-observability`
- Apache Hamilton LLM examples: github.com/apache/hamilton/tree/main/examples/LLM_Workflows
