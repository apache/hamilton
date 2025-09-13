# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import logging
from typing import Any, Callable, Iterable, Optional, Union

logger = logging.getLogger(__name__)

from hamilton import contrib

with contrib.catch_import_errors(__name__, __file__, logger):
    import matplotlib
    import pandas as pd
    from mlforecast import MLForecast
    from mlforecast.target_transforms import BaseTargetTransform
    from numba import njit
    from sklearn.base import BaseEstimator
    from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
    from utilsforecast.evaluation import evaluate
    from utilsforecast.losses import mse
    from utilsforecast.plotting import plot_series
    from window_ops.expanding import expanding_mean
    from window_ops.rolling import rolling_mean


# sklearn compliant models (including XGBoost and LightGBM) subclass BaseEstimator
MODELS_TYPE = Union[
    BaseEstimator, list[BaseEstimator], dict[str, BaseEstimator]
]  # equivalent to mlforecast.core.Models
LAG_TRANSFORMS_TYPE = dict[int, list[Union[Callable, tuple[Callable, Any]]]]
DATE_FEATURES_TYPE = Iterable[Union[str, Callable]]
CONFIDENCE_INTERVAL_TYPE = Optional[list[Union[int, float]]]


def base_models() -> MODELS_TYPE:
    """ML models to fit and evaluate
    Override with your own models at the Hamilton Driver level.
    """
    return [
        RandomForestRegressor(),
        HistGradientBoostingRegressor(),
    ]


@njit
def _rolling_mean_48(x) -> Callable:
    """Example lag transform defined in a function"""
    return rolling_mean(x, window_size=48)


def lag_transforms() -> LAG_TRANSFORMS_TYPE:
    """Use operations from `window_ops` (packaged with mlforecast)"""
    return {
        1: [expanding_mean],  # function without arguments
        24: [(rolling_mean, 24)],  # function with arguments as tuple
        48: [_rolling_mean_48],  # function returning a parameterized function (wrapped)
    }


def _hour_index(times):
    return times % 24


def date_features() -> DATE_FEATURES_TYPE:
    return [_hour_index]


def forecaster(
    base_models: MODELS_TYPE,
    freq: Union[int, str] = "M",
    lags: Optional[list[int]] = None,
    lag_transforms: Optional[LAG_TRANSFORMS_TYPE] = None,
    date_features: Optional[DATE_FEATURES_TYPE] = None,
    target_transforms: Optional[list[BaseTargetTransform]] = None,
    num_threads: int = 1,
) -> MLForecast:
    """Create the forecasting harness with data and models
    :param freq: frequency of the data, see pandas ref: https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases
    :param n_jobs: number of cores to use; -1 will use all available cores
    """
    return MLForecast(
        models=base_models,
        freq=freq,
        lags=lags,
        lag_transforms=lag_transforms,
        date_features=date_features,
        target_transforms=target_transforms,
        num_threads=num_threads,
    )


def cross_validation_predictions(
    forecaster: MLForecast,
    dataset: pd.DataFrame,
    static_features: Optional[list[str]] = None,
    dropna: bool = True,
    keep_last_n_inputs: Optional[int] = None,
    train_models_for_n_horizons: Optional[int] = None,
    confidence_percentile: CONFIDENCE_INTERVAL_TYPE = None,
    cv_n_windows: int = 2,
    cv_forecast_horizon: int = 12,
    cv_step_size: Optional[int] = None,
    cv_input_size: Optional[int] = None,
    cv_refit: bool = True,
    cv_save_train_predictions: bool = True,
) -> pd.DataFrame:
    """Fit models and predict over `cv_n_windows` time windows

    :param cv_n_windows: number of cross-validation windows
    :param cv_forecast_horizon: number of steps in the future to predict
    :param cv_step_size: step between cv windows; if None equal to cv_forecast_horizon
    :param cv_input_size: maximum number of training sample per cv window; if None use expanding window
    :param keep_last_n_inputs: keep that many record for inference
    :param refit: Train a new model on each cv window; If False train on the first cv window and evaluate on others
    """
    return forecaster.cross_validation(
        df=dataset,
        n_windows=cv_n_windows,
        h=cv_forecast_horizon,
        step_size=cv_step_size,
        input_size=cv_input_size,
        keep_last_n=keep_last_n_inputs,
        max_horizon=train_models_for_n_horizons,
        static_features=static_features,
        level=confidence_percentile,
        dropna=dropna,
        refit=cv_refit,
        fitted=cv_save_train_predictions,
    )


def evaluation_metrics() -> list[Callable]:
    """List of metrics to use with `utilsforecast.evaluation.evaluate` in `cross_validation_evaluation`
    The metric function should receive as arguments at least:
        df: pd.DataFrame
        models: list[str]
        id_col: str = "unique_id"
        target_col: str = "y"
    See examples: https://github.com/Nixtla/utilsforecast/blob/main/utilsforecast/losses.py
    """
    return [mse]


def cross_validation_evaluation(
    cross_validation_predictions: pd.DataFrame,
    evaluation_metrics: list[Callable],
) -> pd.DataFrame:
    """Evaluate the crossvalidation predictions and aggregate the performances by series"""
    df = cross_validation_predictions.reset_index()
    evals = []
    for cutoff in df.cutoff.unique():
        eval_ = evaluate(
            df=df.loc[df.cutoff == cutoff],
            metrics=evaluation_metrics,
        )
        evals.append(eval_)

    evaluation_df = pd.concat(evals)
    evaluation_df = evaluation_df.groupby("unique_id").mean(numeric_only=True)
    return evaluation_df


def best_model_per_series(cross_validation_evaluation: pd.DataFrame) -> pd.Series:
    """Return the best model for each series"""
    return cross_validation_evaluation.idxmin(axis=1)


def fitted_forecaster(
    forecaster: MLForecast,
    dataset: pd.DataFrame,
    static_features: Optional[list[str]] = None,
    dropna: bool = True,
    keep_last_n: Optional[int] = None,
    train_models_for_n_horizons: Optional[int] = None,
    save_train_predictions: bool = True,
) -> MLForecast:
    """Fit models over full dataset"""
    return forecaster.fit(
        df=dataset,
        static_features=static_features,
        dropna=dropna,
        keep_last_n=keep_last_n,
        max_horizon=train_models_for_n_horizons,
        fitted=save_train_predictions,
    )


def inference_predictions(
    fitted_forecaster: MLForecast,
    inference_forecast_horizon: int = 12,
    inference_uids: Optional[list[str]] = None,
    inference_dataset: Optional[pd.DataFrame] = None,
    inference_exogenous: Optional[pd.DataFrame] = None,
    confidence_percentile: CONFIDENCE_INTERVAL_TYPE = None,
) -> pd.DataFrame:
    """Infer values using the trained models
    :param inference_forecast_horizon: number of steps in the future to forecast
    """
    return fitted_forecaster.predict(
        h=inference_forecast_horizon,
        ids=inference_uids,
        new_df=inference_dataset,
        X_df=inference_exogenous,
        level=confidence_percentile,
    )


def plotting_config(
    plot_max_n_series: int = 4,
    plot_uids: Optional[list[str]] = None,
    plot_models: Optional[list[str]] = None,
    plot_anomalies: bool = False,
    plot_confidence_percentile: CONFIDENCE_INTERVAL_TYPE = None,
    plot_engine: str = "matplotlib",
) -> dict:
    """Configuration for plotting functions"""
    return dict(
        max_ids=plot_max_n_series,
        ids=plot_uids,
        models=plot_models,
        plot_anomalies=plot_anomalies,
        level=plot_confidence_percentile,
        engine=plot_engine,
    )


def dataset_plot(dataset: pd.DataFrame, plotting_config: dict) -> matplotlib.figure.Figure:
    """Plot series from the dataset"""
    return plot_series(df=dataset, **plotting_config)


def inference_plot(
    dataset: pd.DataFrame,
    inference_predictions: pd.DataFrame,
    plotting_config: dict,
) -> matplotlib.figure.Figure:
    """Plot forecast values"""
    return plot_series(df=dataset, forecasts_df=inference_predictions, **plotting_config)


if __name__ == "__main__":
    import __init__ as nixtla_mlforecast

    from hamilton import driver

    dr = driver.Builder().with_modules(nixtla_mlforecast).build()

    # create the DAG image
    dr.display_all_functions("dag", {"format": "png", "view": False})
