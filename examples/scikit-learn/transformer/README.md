# Classic Apache Hamilton Hello World

In this example we show you a custom scikit-learn `Transformer` class. This class should be compliant with [scikit-learn transformers specifications](https://scikit-learn.org/stable/developers/develop.html). This class is meant to be used as part of broader scikit-learn pipelines. Scikit-learn estimators and pipelines allow for stateful objects, which are helpful when applying transformations on train-test splits notably. Also, all pipeline, estimator, and transformer objects should be picklable, enabling reproducible pipelines.

File organization:

* `my_functions_a.py` and `my_functions_b.py` house the logic that we want to compute.
* `run.py` runs the DAG and asserts the properties of the output for basic use cases.

To run things:
```bash
> python run.py
```
You can even run this example in Google Colab:
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)
](https://colab.research.google.com/github/dagworks-inc/hamilton/blob/main/examples/scikit-learn/hamilton_notebook.ipynb)



# DAG Visualization:
Here is the visualization of the execution that the transformer currently performs if you run `run.py`:

![scikit_transformer](scikit_transformer.png)

# Limitations and TODOs
- The current implementation relies on Apache Hamilton defaults' `base.HamiltonGraphAdapter` and `base.PandasDataFrameResult` which limits the compatibility with other computation engines supported by Apache Hamilton
- The current implementation could be improved for deeper object inspection. A particular challenge is that the Apache Hamilton driver alters the number of columns / features of the input array, and does so by specifying the *output columns*. In contrast, scikit-learn typically reads columns / features of the *input array* and passes it down. It would be worth looking at [the output feature naming convention](https://scikit-learn.org/stable/developers/develop.html#developer-api-for-set-output) and the [`ColumnTransformer` class](https://scikit-learn.org/stable/modules/generated/sklearn.compose.ColumnTransformer.html#sklearn.compose.ColumnTransformer) which aims to fulfill a similar objective to Apache Hamilton.
- The current implementation allows little direct access to the `Apache Hamilton driver`. Currently, the driver accessible via the `.driver_` attribute after calling `.fit()` or `.fit_transform()` which seems to be coherent with typical scikit-learn behavior.
- The current implementation could be slightly modified to have no dependencies on scikit-learn itself. However, having inheriting from `BaseEstimator` and `TransformerMixin` provides some clarity about the class's purpose.
