# Purpose of this module

The purpose of this module is to take Sphinx Furo themed documentation, pull the pages, and chunk the text
for further processing, e.g. creating embeddings. This is fairly generic code that is easy to change
and extend for your purposes. It runs anywhere that python runs, and can be extended to run on Ray, Dask,
and even PySpark.

```python
# import sphinx_doc_chunking via the means that you want. See above code.

from hamilton import driver

from hamilton.execution import executors

dr = (
    driver.Builder()
    .with_modules(sphinx_doc_chunking)
    .enable_dynamic_execution(allow_experimental_mode=True)
    .with_config({})
    # defaults to multi-threading -- and tasks control max concurrency
    .with_remote_executor(executors.MultiThreadingExecutor(max_tasks=25))
    .build()
)
```

## What you should modify

You'll likely want to:

1. play with what does the chunking and settings for that.
2. change how URLs are sourced.
3. change how text is extracted from a page.
4. extend the code to hit an API to get embeddings.
5. extend the code to push data to a vector database.

# Configuration Options
There is no configuration required for this module.

# Limitations

You general multiprocessing caveats apply if you choose an executor other than MultiThreading. For example:

1. Serialization -- objects need to be serializable between processes.
2. Concurrency/parallelism -- you're in control of this.
3. Failures -- you'll need to make your code do the right thing here.
4. Memory requirements -- the "collect" (or reduce) step pulls things into memory. If you hit this, this just
means you need to redesign your code a little, e.g. write large things to a store and pass pointers.

To extend this to [PySpark see the examples folder](https://github.com/apache/hamilton/tree/main/examples/LLM_Workflows/scraping_and_chunking/spark)
for the changes required to adjust the code to handle PySpark.
