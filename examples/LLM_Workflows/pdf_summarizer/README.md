# (Yet another) LLM PDF Summarizer 📝
Here's an extensible and production-ready PDF summarizer that you can run anywhere! The frontend uses streamlit, which communicates with a FastAPI backend powered by Apache Hamilton. You give it a PDF file via the browser app and it returns you a text summary using the OpenAI API. If you want, you skip the browser inteface and directly access the `/summarize` endpoint with your document! Everything is containerized using Docker, so you should be able to run it where you please 🏃.

## Why build this project?
This project shows how easy it is to productionize Apache Hamilton. Its function-centric declarative approach makes the code easy to read and extend. We invite you to clone the repo and customize to your needs! We are happy to help you via [Slack](https://hamilton-opensource.slack.com/join/shared_invite/zt-1bjs72asx-wcUTgH7q7QX1igiQ5bbdcg) and are excited to see what you build 😁

Here are a few ideas:
- Modify the streamlit `file_uploader` to allow sending batches of files through the UI
- Add PDF parsing and preprocessing to reduce number of tokens sent to OpenAI
- Add Apache Hamilton functions to gather metadata (file length, number of tokens, language, etc.) and return it via `SummaryResponse`
- Support other file formats; use the `@config.when()` decorator to add alternatives to the `raw_text()` function for PDFs
- Extract structured data from PDFs using open source models from the HuggingFace Hub.


![](./backend/summarization_module.png)
*The Apache Hamilton execution DAG powering the backend*


# Setup
1. Clone this repository `git clone https://github.com/apache/hamilton.git`
2. Move to the directory `cd hamilton/examples/LLM_Workflows/pdf_summarizer`
3. Create a `.env` (next to `README.md` and `docker-compose.yaml`) and add your OpenAI API key in  such that `OPENAI_API_KEY=YOUR_API_KEY`
4. Build docker images `docker compose build`
5. Create docker containers `docker compose up -d`
6. Go to [http://localhost:8080/docs](http://localhost:8080/docs) to see if the FastAPI server is running
7. Go to [http://localhost:8081/](http://localhost:8081/) to view the Streamlit app
8. If you make changes, you need to rebuild the docker images, so do `docker compose up -d --build`.
9. To stop the containers do `docker compose down`.
10. To look at the logs, your docker application should allow you to view them,
or you can do `docker compose logs -f` to tail the logs (ctrl+c to stop tailing the logs).

## Connecting to DAGWorks
1. Create a DAGWorks account at www.dagworks.io - follow the instructions to set up a project.
2. Add your DAGWorks API Key to the `.env` file. E.g. `DAGWORKS_API_KEY=YOUR_API_KEY`
3. Uncomment dagworks-sdk in `requirements.txt`.
4. Uncomment the lines in server.py to replace `sync_dr` with the DAGWorks Driver.
5. Rebuild the docker images `docker compose up -d --build`.

# Running on Spark!
Yes, that's right, you can also run the exact same code on spark! It's just a oneline
code change. See the [run_on_spark README](run_on_spark/README.md) for more details.
