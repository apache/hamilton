# Streamlit + Apache Hamilton

> This example accompanies the documentation page for [Streamlit](https://hamilton.apache.org/integrations/streamlit/) integration.

Streamlit is an open-source Python library to create web applications with minimal effort. It's an effective solution to create simple dashboards, interactive data visualizations, and proof-of-concepts for data science, machine learning, and LLM applications.

In this example, We will build a simple financial dashboard based on the Kaggle [Bank Marketing Dataset](https://www.kaggle.com/datasets/janiobachmann/bank-marketing-dataset).

## How to run
1. Create virtual environment: `python -m venv ./venv`
2. Activate virtual environment: `. venv/bin/activate` (or `source venv/bin/Scripts` on Windows)
3. Install requirements: `pip install -r requirements.txt`
4. Launch Streamlit application: `streamlit run app.py`


## File organization
Adding Apache Hamilton to your Streamlit application can provide a better separation between the dataflow and the UI logic. They pair nicely together because Apache Hamilton is also stateless. Once defined, each call to `Driver.execute()` is independent. Therefore, on each Streamlit rerun, you use `Driver.execute()` to complete computations. Using Apache Hamilton this way allows you to write your dataflow into Python modules and outside of the Streamlit.

### logic.py
Apache Hamilton transformations are defined in the module `logic.py`. This includes downloading the data from the web, getting unique values for `job`, conducting groupby aggregates, and creating `plotly` figures.

### app.py
The Streamlit UI is defined in `app.py`. Notice a few things:
- `app.py` doesn't have to depend on `pandas` and `plotly`.
- `@cache_resource` allows to create the `Driver` only once.
- `@cache_data` on `_execute()` will automatically cache any Apache Hamilton result based on the combination of arguments (`final_vars`, `inputs`, and `overrides`)
- `get_state_inputs()` and `get_state_overrides()` will collect values from user inputs.
- `execute()` parses the inputs and overrides from the state and call `_execute()`.


## Benefits
- **Clearer scope**: the decoupling between `app.py` and `logic.py` makes it easier to add data transformations or extend UI, and debug errors associated with either.
- **Reusable code**: the module `logic.py` can be reused elsewhere with Apache Hamilton.
    - If you are building a proof-of-concept with Streamlit, your Apache Hamilton module will be able to grow with your project and be useful for your production pipelines.
    - If you are already building dataflows with Apache Hamilton, using it with Streamlit ensures your dashboard metrics have the same implementation with your production pipeline (i.e., prevent [implementation skew](https://building.nubank.com.br/dealing-with-train-serve-skew-in-real-time-ml-models-a-short-guide/))
- **Performance boost**: by caching the Apache Hamilton Driver and its execution call, we are able to effectively cache all data operations in a few lines of code. Furthermore, Apache Hamilton can scale further by using a remote task executor on a separate machine from the Streamlit application.
