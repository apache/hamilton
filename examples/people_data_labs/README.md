# People Data Labs

[People Data Labs](https://www.peopledatalabs.com/) is a data provider that offers several data APIs for person enrichment & search, company enrichment & search, and IP enrichment.

This example showcases how Apache Hamilton can help you write modular data transformations.

![](all_functions.png)
> Dataflow visualization generated directly from the Apache Hamilton code.

## Content
- `notebook.ipynb` is a step-by-step introduction to Apache Hamilton. Start there.
- `analysis.py` contains data transformations used by `run.py`. They're the same as the ones defined in `notebook.ipynb`.
- `run.py` contains code to execute the analysis.


## Set up
1. Create a virtual environment and activate it
    ```console
    python -m venv venv && . venv/bin/active
    ```

2. Install requirements
    ```console
    pip install -r requirements.txt
    ```

3. Download the data with this command (it should take ~3mins)
    ```console
    python download_data.py
    ```

4. Visit the notebook or execute the script
    ```console
    python run.py
    ```

You can even run this example in Google Colab:
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)
](https://colab.research.google.com/github/dagworks-inc/hamilton/blob/main/examples/people_data_labs/notebook.ipynb)



## Resources
- [PDL Blog](https://blog.peopledatalabs.com/) and [PDL Recipes](https://docs.peopledatalabs.com/recipes)
- [Interactive Apache Hamilton training](https://www.tryhamilton.dev/hamilton-basics/jumping-in)
- [Apache Hamilton documentation](https://hamilton.apache.org/concepts/node/)
- more [Apache Hamilton code examples](https://github.com/apache/hamilton/tree/main/examples) and integrations with Python tools.
