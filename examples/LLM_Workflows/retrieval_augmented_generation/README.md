# Retrieval Augmented Generation app with Apache Hamilton
This application allows you to search arXiv for PDFs or import arbitrary PDF files and search over them using LLMs. For each file, the text is divided in chunks that are embedded with OpenAI and stored in Weaviate. When you query the system, the most relevant chunks are retrieved and a summary answer is generated using OpenAI.

The ingestion and retrieval steps are implemented as dataflows with Apache Hamilton and are exposed via FastAPI endpoints. The frontend is built with Streamlit and exposes the different functionalities via a simple web UI. Everything is packaged as containers with docker compose.

This example draws from previous simpler examples ([Knowledge Retrieval](https://github.com/apache/hamilton/tree/main/examples/LLM_Workflows/knowledge_retrieval), [Modular LLM Stack](https://github.com/apache/hamilton/tree/main/examples/LLM_Workflows/modular_llm_stack), [PDF Summarizer](https://github.com/apache/hamilton/tree/main/examples/LLM_Workflows/pdf_summarizer)).

> Find below a list of references for the technical concepts found in this example

# Setup
## Setup script
1. Give executable permissions to the script: `chmod +x build_app.sh`
2. To build and launch the app the first time, specify where to download the app and your OpenAI API key: `./build_app.sh DOWNLOAD_DIRECTORY YOUR_OPENAI_API_KEY`
- To rebuild and launch `docker compose up -d --build`
- To shutdown the app `docker compose down`
- To view app logs `docker compose logs -f`

## Manual setup
1. Clone this repository `git clone https://github.com/apache/hamilton.git`
2. Move to the directory `cd hamilton/examples/LLM_Workflows/retrieval_augmented_generation`
3. Create a copy of `.env.template` with `cp .env.template .env`
4. Replace the placeholder in `.env` with your OpenAI API key such that `OPENAI_API_KEY=YOUR_API_KEY`
5. Create and build docker images `docker compose up -d --build`
6. Go to [http://localhost:8080/](http://localhost:8080/) to view the Streamlit app. If it's running, it means the FastAPI server started and was able to connect to Weaviate. You can manually verify FastAPI at [http://localhost:8082/docs](http://localhost:8082/docs) and Weaviate at [http://localhost:8080/docs](http://localhost:8083/v1)
- If you make changes, you need to rebuild the docker images, so do `docker compose up -d --build`.
- To stop the containers do `docker compose down`.
- To look at the logs, your docker application should allow you to view them,
or you can do `docker compose logs -f` to tail the logs (ctrl+c to stop tailing the logs).

# Technical References:
- [Docker Compose Networking](https://docs.docker.com/compose/networking/)
- [FastAPI /docs metadata](https://fastapi.tiangolo.com/tutorial/metadata/)
- [FastAPI lifespan events](https://fastapi.tiangolo.com/advanced/events/)
- [Apache Hamilton Interactive online demo](https://www.tryhamilton.dev/)
- [Apache Hamilton Parallelizable/Collect](https://hamilton.apache.org/concepts/customizing-execution/#dynamic-dags-parallel-execution)
- [OpenAI API docs](https://platform.openai.com/docs/introduction)
- [RAG sample architecture by Amazon](https://docs.aws.amazon.com/sagemaker/latest/dg/jumpstart-foundation-models-customize-rag.html)
- [Streamlit API documentation](https://docs.streamlit.io/library/api-reference)
- [Streamlit Include PDF as HTML within Markdown](https://discuss.streamlit.io/t/rendering-pdf-on-ui/13505)
- [Weaviate 101](https://weaviate.io/developers/weaviate/tutorials)
- [Weaviate GraphQL Retrieval API](https://weaviate.io/developers/weaviate/api/graphql#graphql)
- [Weaviate Python Client](https://weaviate-python-client.readthedocs.io/en/stable/index.html)
- [Weaviate Hybrid Search](https://weaviate.io/developers/academy/zero_to_mvp/queries_2/hybrid)
