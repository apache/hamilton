# Purpose of this module

This module shows a simple retrieval augmented generation (RAG) example using
Apache Hamilton. It shows you how you might structure your code with Apache Hamilton to
create a simple RAG pipeline.

This example uses [FAISS](https://engineering.fb.com/2017/03/29/data-infrastructure/faiss-a-library-for-efficient-similarity-search/) + and in memory vector store and the OpenAI LLM provider.
The implementation of the FAISS vector store uses the LangChain wrapper around it.
That's because this was the simplest way to get this example up without requiring
someone having to host and manage a proper vector store.

## Example Usage

### Inputs
These are the defined inputs.

 - *input_texts*: A list of strings. Each string will be encoded into a vector and stored in the vector store.
 - *question*: A string. This is the question you want to ask the LLM, and vector store which will provide context.
 - *top_k*: An integer. This is the number of vectors to retrieve from the vector store. Defaults to 5.

### Overrides
With Apache Hamilton you can easily override a function and provide a value for it. For example if you're
iterating you might just want to override these two values before modifying the functions:

 - *context*: if you want to skip going to the vector store and provide the context directly, you can do so by providing this override.
 - *rag_prompt*: if you want to provide the prompt to pass to the LLM, pass it in as an override.

### Execution
You can ask to get back any result of an intermediate function by providing the function name in the `execute` call.
Here we just ask for the final result, but if you wanted to, you could ask for outputs of any of the functions, which
you can then introspect or log for debugging/evaluation purposes. Note if you want more platform integrations,
you can add adapters that will do this automatically for you, e.g. like we have the `PrintLn` adapter here.
```python
# import the module
from hamilton import driver
from hamilton import lifecycle
dr = (
    driver.Builder()
    .with_modules(faiss_rag)
    .with_config({})
    # this prints the inputs and outputs of each step.
    .with_adapters(lifecycle.PrintLn(verbosity=2))
    .build()
)
result = dr.execute(
    ["rag_response"],
    inputs={
        "input_texts": [
            "harrison worked at kensho",
            "stefan worked at Stitch Fix",
        ],
        "question": "where did stefan work?",
    },
)
print(result)
```

# How to extend this module
What you'd most likely want to do is:

1. Change the vector store (and how embeddings are generated).
2. Change the LLM provider.
3. Change the context and prompt.

With (1) you can import any vector store/library that you want. You should draw out
the process you would like, and that should then map to Apache Hamilton functions.
With (2) you can import any LLM provider that you want, just use `@config.when` if you
want to switch between multiple providers.
With (3) you can add more functions that create parts of the prompt.

# Configuration Options
There is no configuration needed for this module.

# Limitations

You need to have the OPENAI_API_KEY in your environment.
It should be accessible from your code by doing `os.environ["OPENAI_API_KEY"]`.

The code does not check the context length, so it may fail if the context passed is too long
for the LLM you send it to.
