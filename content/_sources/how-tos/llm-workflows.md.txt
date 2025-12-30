# LLM workflows

Apache Hamilton is great for describing dataflows, and a lot of "actions" you want
an "agent" to perform can be described as one, e.g. create an embedding
of some passed in text, query a vector database, find the nearest documents, etc.

The benefit of using Apache Hamilton within an LLM Powered app is that:
1. you can visualize the dataflow.
2. you can easily test, modify, compose, and reuse dataflows. For example,
   you can easily test the dataflow that creates an embedding of some text
   without having to worry about the rest of the dataflow.
3. you can easily swap out the implementation details of components surgically. For example,
   you can swap out the vector database client based on configuration, this helps in ensuring
   you can quickly and easily modify/update your dataflow and have confidence around the impact of that change.
4. you can use functionality like runtime data quality checks/extend Apache Hamilton's capabilities with your own needs to inject/augment
   your dataflow with additional functionality, e.g. caching, logging, etc.
5. you can request the intermediate outputs of a dataflow by requesting it as output without any surgery required to
any of your code to do so. This is useful for debugging.

The following examples show how to use Apache Hamilton for LLM workflows:

* [How to use "OpenAI functions" with a Knowledge Base](https://github.com/apache/hamilton/tree/main/examples/LLM_Workflows/knowledge_retrieval/)
* [Modular LLM Stack](https://github.com/apache/hamilton/tree/main/examples/LLM_Workflows/modular_llm_stack) with [blog post](https://blog.dagworks.io/p/building-a-maintainable-and-modular)
* [PDF Summarizer](https://github.com/apache/hamilton/tree/main/examples/LLM_Workflows/pdf_summarizer) which shows
a partial RAG workflow (just missing going to a vector store to get the PDF/content) that runs inside FastAPI with a Streamlit frontend.
