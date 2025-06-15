# Purpose of this module

This module implements a dataflow to train an XGBoost model with hyperparameter tuning using Optuna.

You give it a 2D arrays for `X_train`, `y_train`, `X_test`, `y_test` and you are good to go!

# Configuration Options
The Apache Hamilton driver can be configured with the following options:
 - {"task":  "classification"} to use xgboost.XGBClassifier.
 - {"task":  "regression"} to use xgboost.XGBRegressor.

There are several relevant inputs and override points.

**Inputs**:
 - `model_config_override`: Pass a dictionary to override the XGBoost default config. **Warning** passing a `model_config_override = {"objective": "binary:logistic}` to an `XGBRegressor` effectively changes it to an `XGBClassifier`
 - `optuna_distributions_override`: Pass a dictionary of optuna distributions to define the hyperparameter search space.

**Overrides**:
 - `base_model`: can change it to the type `xgboost.XGBRanker` for a ranking task or `xgboost.dask.DaskXGBClassifier` to support Dask
 - `scoring_func`: can be any `sklearn.metrics` function that accepts `y_true` and `y_pred` as arguments. Remember to set accordingly `higher_is_better` for the optimization task
 - `cross_validation_folds`: can be any sequence of tuples that define (`train_index`, `validation_index`) to train the model with cross-validation over `X_train`

# Limitations

- It is difficult to adapt for distributed Optuna hyperparameter search.
- The current structure makes it difficult to add custom training callbacks to the XGBoost model (can be done to some extent via `model_config_override`).
