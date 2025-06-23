# MLFLow plugin for Apache Hamilton

[MLFlow](https://mlflow.org/) is an open-source Python framework for experiment tracking. It allows data science teams to store results, artifacts (machine learning models, figures, tables), and metadata in a principled way when executing data pipelines.

The MLFlow plugin for Apache Hamilton includes two sets of features:
- Save and load machine learning models with the `MLFlowModelSaver` and `MLFlowModelLoader` materializers
- Automatically track data pipeline results in MLFlow with the `MLFlowTracker`.

This pairs nicely with the `HamiltonTracker` and the [Apache Hamilton UI](https://hamilton.apache.org/hamilton-ui/ui/) which gives you a way to explore your pipeline code, attributes of the artifacts produced, and execution observability.

We're working on better linking Apache Hamilton "projects" with MLFlow "experiments" and runs from both projects.

## Instructions
1. Create a virtual environment and activate it
    ```console
    python -m venv venv && . venv/bin/active
    ```

2. Install requirements for the Apache Hamilton code
    ```console
    pip install -r requirements.txt
    ```

3. Explore the notebook `tutorial.ipynb`


4. Launch the MLFlow user interface to explore results
    ```console
    mlflow ui
    ```

## Going further
- Learn the basics of Apache Hamilton via the `Concepts/` [documentation section](https://hamilton.apache.org/concepts/node/)
- Visit [tryhamilton.dev](tryhamilton.dev) for an interactive tutorial in your browser
- Visit the [DAGWorks blog](https://blog.dagworks.io/) for more detailed guides
