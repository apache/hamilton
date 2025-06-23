# Apache Hamilton + Feast

In this example, we're going to show you how Apache Hamilton can help you structure your Feast repository and bring tighter coupling between your feature transformations (code) and feature store (data).
- **Feast** is a feature store, which is an ML-specific stack component, that helps store and serve features (offline vs. online, batch vs. stream). It keeps a registry of features scattered across storage sources (database, data warehouse, streaming, etc.) and facilitates data retrieval and joining. Features need to be computed separately, typically in an SQL pipeline or a Python dataframe library and then be pushed to the Feast feature store([Feast FAQ](https://feast.dev/)).
- **Apache Hamilton** is a data transformation micro-framework. It helps one write Python code that is modular and reusable, and that expresses a [DAG](https://en.wikipedia.org/wiki/Directed_acyclic_graph) of execution. It was initially developed for large dataframes with hundreds of columns for machine learning while preserving strong lineage capabilities ([high-level comparison](https://hamilton.apache.org/)).


## File organization
- `/default_feature_store` is the quickstart example you can generate by calling `feast init default`. It is presented here as a reference point to compare with Apache Hamilton + Feast alternatives.
- `/simple_feature_store` is a 1-to-1 reimplementation of `/default_feature_store`. You will notice that adding Apache Hamilton helps make explicit the dependencies between Feast objects therefore increasing readability and maintainability.
- `/integration_feature_store` extends the `/simple_feature_store` example by adding the feature transformation  code using Apache Hamilton and directly integrating with Feast.
- `retrieval.ipynb` in `/integration_feature_store/feature_repo` shows how to retrieve features from Feast and highlights the benefits of end-to-end visibility with Apache Hamilton.

## Learn more about Feast
- Hands-on workshop: https://github.com/feast-dev/feast-workshop
