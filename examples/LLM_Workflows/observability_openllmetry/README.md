# Monitor Apache Hamilton with OpenTelemetry, OpenLLMetry and Traceloop

In this simple example, you'll learn how to use the `OpenTelemetryTracer` to emit traces of your Apache Hamilton code using the OpenTelemetry format, in particular LLM applications.

![Traceloop screenshot](screenshot.png)

[OpenTelemetry](https://opentelemetry.io/) is an open-source cross-language tool that allows to instrument, generate, collect, and export telemetry data (metrics, logs, traces), and constitute an industry-recognized standard. Learn more about it in this [Awesome OpenTelemetry repository](https://github.com/magsther/awesome-opentelemetry)

[OpenLLMetry](https://github.com/traceloop/openllmetry) is an open-source Python library that automatically instruments with OpenTelemetry components of your LLM stack including LLM providers (OpenAI, Anthropic, HuggingFace, Cohere, etc.), vector databases (Weaviate, Qdrant, Chroma, etc.), and frameworks ([Burr](https://github.com/apache/burr), Haystack, LangChain, LlamaIndex). In concrete terms, it means you automatically get detailed traces of API calls, retrieval operations, or text transformations for example.

One thing to note, OpenTelemetry is a middleware; it doesn't provide a destination to store data nor a dashboard. For this example, we'll use the tool [Traceloop](https://www.traceloop.com/), which is built by the developers of OpenLLMetry. It has a generous free-tier and can be conveniently set up in a few lines of code for this demo.

## Set up
Having access to a [Traceloop account](https://www.traceloop.com/) and an API key is a pre-requisite.

1. Create a virtual environment and activate it
    ```bash
    python -m venv venv && . venv/bin/active
    ```

2. Install requirements.
    ```bash
    pip install -r requirements.txt
    ```

3. Set environment variables for your API keys `OPENAI_API_KEY` and `TRACELOOP_API_KEY`

4. Execute the code
    ```bash
    python run.py
    ```

5. Explore results on Traceloop (or your OpenTelemetry destination).

### Without Traceloop

For this example to work without Traceloop, you will need to set up your own [OpenTelemetry destination](https://opentelemetry.io/ecosystem/vendors/). We suggest using [Jaeger](https://www.jaegertracing.io/docs/1.47/getting-started/) and included Python code to route telemetry to it in `run.py`.

## Should I still use the Apache Hamilton UI?

Absolutely! OpenTelemetry focsues on collecting telemetry about the internals of code and external API calls. It's a standard amongst web services. There's no conflict between the OpenTelemetry tracer and the tracking for the Apache Hamilton UI. In fact, the Apache Hamilton UI captures a superset of what OpenTelemetry allows, tailored to the Apache Hamilton framework such as:  visualizations, data lineage, summary statistics, and more utilities to improve your development experience. In the not too distant future, the Apache Hamilton UI could ingest OpenTelemetry data 😉 (contributions welcomed!)
