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

from __future__ import annotations

import importlib
import logging
from typing import TYPE_CHECKING, Any, Dict, List

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.utils.validation import check_array, check_is_fitted

from hamilton import base, driver, log_setup

if TYPE_CHECKING:
    from types import ModuleType


class HamiltonTransformer(BaseEstimator, TransformerMixin):
    """Scikit-learn compatible Transformer implementing Hamilton behavior"""

    def __init__(
        self,
        config: dict = None,
        modules: List[ModuleType] = None,
        adapter: base.HamiltonGraphAdapter = None,
        final_vars: List[str] = None,
    ):
        self.config = {} if config is None else config
        self.modules = [] if modules is None else modules
        self.adapter = adapter
        self.final_vars = [] if final_vars is None else final_vars

    def get_params(self) -> dict:
        """Get parameters for this estimator.

        :return: Current parameters of the estimator
        """
        return {
            "config": self.config,
            "modules": self.modules,
            "adapter": self.adapter,
            "final_vars": self.final_vars,
        }

    def set_params(self, **parameters) -> HamiltonTransformer:
        """Get parameters for this estimator.

        :param parameters: Estimator parameters.
        :return: self
        """
        for parameter, value in parameters.items():
            setattr(self, parameter, value)
        return self

    def get_features_names_out(self):
        """"""
        if self.feature_names_out_:
            return self.feature_names_out_

    def _get_tags(self) -> dict:
        """Get scikit-learn compatible estimator tags for introspection

        ref: https://scikit-learn.org/stable/developers/develop.html#estimator-tags
        """
        return {"requires_fit": True, "requires_y": False}

    def fit(self, X, y=None, overrides: Dict[str, Any] = None) -> HamiltonTransformer:
        """Instantiate Hamilton driver.Driver object

        :param X: Input 2D array
        :param overrides: dictionary of override values passed to driver.execute() during .transform()
        :return: self
        """

        check_array(X, accept_sparse=True)
        self.overrides_ = {} if overrides is None else overrides

        self.driver_ = driver.Driver(self.config, *self.modules, adapter=self.adapter)
        self.n_features_in_: int = X.shape[1]

        return self

    def transform(self, X, y=None, **kwargs) -> pd.DataFrame:
        """Execute Hamilton Driver on X with optional parameters fit_params and returns a
        transformed version of X. Requires prior call to .fit() to instantiate Hamilton Driver

        :param X: Input 2D array
        :return: Hamilton Driver output 2D array
        """

        check_is_fitted(self, "n_features_in_")

        if isinstance(X, pd.DataFrame):
            check_array(X, accept_sparse=True)
            if X.shape[1] != self.n_features_in_:
                raise ValueError("Shape of input is different from what was seen in `fit`")

            X = X.to_dict(orient="series")

        X_t = self.driver_.execute(final_vars=self.final_vars, overrides=self.overrides_, inputs=X)
        # self.driver_.visualize_execution(final_vars=self.final_vars,
        #                                  output_file_path="./scikit_transformer",
        #                                  render_kwargs={"format": "png"},
        #                                  inputs=X)
        self.n_features_out_ = len(self.final_vars)
        self.feature_names_out_ = X_t.columns.to_list()
        return X_t

    def fit_transform(self, X, y=None, **fit_params) -> pd.DataFrame:
        """Execute Hamilton Driver on X with optional parameters fit_params and returns a
        transformed version of X.

        :param X: Input 2D array
        :return: Hamilton Driver output 2D array
        """
        return self.fit(X, **fit_params).transform(X)


logger = logging.getLogger(__name__)
if __name__ == "__main__":
    log_setup.setup_logging()

    module_names = ["my_functions_a", "my_functions_b"]
    modules = [importlib.import_module(m) for m in module_names]

    initial_df = pd.DataFrame(
        {"signups": [1, 10, 50, 100, 200, 400], "spend": [10, 10, 20, 40, 40, 50]}
    )

    output_columns = [
        "spend",
        "signups",
        "avg_3wk_spend",
        "spend_per_signup",
        "spend_zero_mean_unit_variance",
    ]

    # Check 1: output of `vanilla driver` == `custom transformer`
    dr = driver.Driver({}, *modules)
    hamilton_df = dr.execute(final_vars=output_columns, inputs=initial_df.to_dict(orient="series"))

    custom_transformer = HamiltonTransformer(config={}, modules=modules, final_vars=output_columns)
    sklearn_df = custom_transformer.fit_transform(initial_df)

    try:
        pd.testing.assert_frame_equal(sklearn_df, hamilton_df)

    except ValueError as e:
        logger.warning("Check 1 failed; `sklearn_df` and `hamilton_df` are unequal")
        raise e

    # Check 2: output of `vanilla driver > transformation` == `scikit-learn pipeline`
    scaler = StandardScaler()

    hamilton_df = dr.execute(final_vars=output_columns, inputs=initial_df.to_dict(orient="series"))
    hamilton_then_sklearn = scaler.fit_transform(hamilton_df)

    pipeline1 = Pipeline(steps=[("hamilton", custom_transformer), ("scaler", scaler)])
    pipe_custom_then_sklearn = pipeline1.fit_transform(initial_df)
    try:
        assert isinstance(hamilton_then_sklearn, np.ndarray)
        assert isinstance(pipe_custom_then_sklearn, np.ndarray)

        np.testing.assert_equal(pipe_custom_then_sklearn, hamilton_then_sklearn)

    except ValueError as e:
        logger.warning(
            "Check 2 failed; `pipe_custom_then_sklearn` and `hamilton_then_sklearn` are unequal"
        )
        raise e

    # Check 3: output of `transformation > vanilla driver` == `scikit-learn pipeline`
    # The custom transformer requires a DataFrame, we leverage the `.set_output` from scikit-learn v1.2
    # ref: https://scikit-learn-enhancement-proposals.readthedocs.io/en/latest/slep018/proposal.html
    scaler = StandardScaler().set_output(transform="pandas")

    scaled_df = scaler.fit_transform(initial_df)
    sklearn_then_hamilton = dr.execute(
        final_vars=output_columns, inputs=scaled_df.to_dict(orient="series")
    )

    pipeline2 = Pipeline(steps=[("scaler", scaler), ("hamilton", custom_transformer)])
    pipe_sklearn_then_custom = pipeline2.fit_transform(initial_df)

    try:
        assert isinstance(sklearn_then_hamilton, pd.DataFrame)
        assert isinstance(pipe_sklearn_then_custom, pd.DataFrame)

        pd.testing.assert_frame_equal(pipe_sklearn_then_custom, sklearn_then_hamilton)
    except ValueError as e:
        logger.warning(
            "Check 3 failed; `pipe_sklearn_then_custom` and `sklearn_then_hamilton` are unequal"
        )
        raise e

    logger.info("All checks passed. `HamiltonTransformer` behaves properly")
