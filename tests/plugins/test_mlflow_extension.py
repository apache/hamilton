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

import sys
from pathlib import Path

import pytest

PY38_OR_BELOW = sys.version_info < (3, 9)
pytestmark = pytest.mark.skipif(
    PY38_OR_BELOW, reason="Breaks for python 3.8 and below due to backports dependency."
)

if not PY38_OR_BELOW:
    import mlflow

    from hamilton.plugins.mlflow_extensions import MLFlowModelLoader, MLFlowModelSaver

import numpy as np
import pytest
from sklearn.base import BaseEstimator
from sklearn.linear_model import LinearRegression

from hamilton.io.materialization import from_, to

# TODO move these tests to `plugin_tests` because the required read-writes can get
# complicated and tests are time consuming.


@pytest.fixture
def fitted_sklearn_model() -> BaseEstimator:
    model = LinearRegression()
    model.fit([[0]], [[0]])
    return model


def coefficients_are_equal(model1, model2) -> bool:
    """Check if two linear models have the same coefficients"""
    return np.allclose(model1.coef_, model2.coef_) and np.allclose(
        model1.intercept_, model2.intercept_
    )


def test_mlflow_log_model_to_active_run(fitted_sklearn_model: BaseEstimator, tmp_path: Path):
    model_path = tmp_path / "sklearn_model"
    saver = MLFlowModelSaver(flavor="sklearn")

    mlflow.set_tracking_uri(model_path.as_uri())
    with mlflow.start_run():
        # save model
        metadata = saver.save_data(fitted_sklearn_model)
    # reload model
    loaded_model = mlflow.sklearn.load_model(metadata["model_uri"])

    assert coefficients_are_equal(fitted_sklearn_model, loaded_model)


def test_mlflow_log_model_to_specific_run(fitted_sklearn_model: BaseEstimator, tmp_path: Path):
    model_path = tmp_path / "sklearn_model"
    # create a "previous run"
    mlflow.set_tracking_uri(model_path.as_uri())
    mlflow.start_run()
    run_id = mlflow.active_run().info.run_id
    mlflow.end_run()
    saver = MLFlowModelSaver(flavor="sklearn", run_id=run_id)

    # save model
    metadata = saver.save_data(fitted_sklearn_model)
    # reload model
    loaded_model = mlflow.sklearn.load_model(metadata["model_uri"])

    assert coefficients_are_equal(fitted_sklearn_model, loaded_model)


def test_mlflow_log_model_active_and_specific_run_ids_are_equal(
    fitted_sklearn_model: BaseEstimator, tmp_path: Path
):
    model_path = tmp_path / "sklearn_model"

    mlflow.set_tracking_uri(model_path.as_uri())
    with mlflow.start_run():
        run_id = mlflow.active_run().info.run_id
        saver = MLFlowModelSaver(flavor="sklearn", run_id=run_id)
        # save model
        metadata = saver.save_data(fitted_sklearn_model)
    # reload model
    loaded_model = mlflow.sklearn.load_model(metadata["model_uri"])

    assert coefficients_are_equal(fitted_sklearn_model, loaded_model)


def test_mlflow_log_model_active_and_specific_run_ids_are_unequal(
    fitted_sklearn_model: BaseEstimator, tmp_path: Path
):
    model_path = tmp_path / "sklearn_model"
    mlflow.set_tracking_uri(model_path.as_uri())
    mlflow.start_run()
    run_id = mlflow.active_run().info.run_id
    mlflow.end_run()
    saver = MLFlowModelSaver(flavor="sklearn", run_id=run_id)

    with mlflow.start_run():
        # save model
        with pytest.raises(RuntimeError):
            saver.save_data(fitted_sklearn_model)


def test_mlflow_load_runs_model(fitted_sklearn_model: BaseEstimator, tmp_path: Path):
    mlflow_path = tmp_path / "mlflow_path"
    artifact_path = "model"
    mlflow.set_tracking_uri(mlflow_path.as_uri())
    with mlflow.start_run():
        run_id = mlflow.active_run().info.run_id
        mlflow.sklearn.log_model(fitted_sklearn_model, artifact_path=artifact_path)

    # specify run via model_uri
    loader = MLFlowModelLoader(model_uri=f"runs:/{run_id}/{artifact_path}", flavor="sklearn")
    loaded_model, _ = loader.load_data(LinearRegression)
    assert coefficients_are_equal(fitted_sklearn_model, loaded_model)

    # specify run via arguments
    loader = MLFlowModelLoader(mode="tracking", path=artifact_path, run_id=run_id, flavor="sklearn")
    loaded_model, _ = loader.load_data(LinearRegression)
    assert coefficients_are_equal(fitted_sklearn_model, loaded_model)


def test_mlflow_load_registry_model(fitted_sklearn_model: BaseEstimator, tmp_path: Path):
    mlflow_path = tmp_path / "mlflow_path"
    artifact_path = "model"
    model_name = "my_registered_model"
    version = 1
    # track a model
    mlflow.set_tracking_uri(mlflow_path.as_uri())
    with mlflow.start_run():
        run_id = mlflow.active_run().info.run_id
        mlflow.sklearn.log_model(fitted_sklearn_model, artifact_path=artifact_path)
    # register the model
    run_model_uri = f"runs:/{run_id}/{artifact_path}"
    mlflow.register_model(run_model_uri, model_name)

    # specify via model_uri
    loader = MLFlowModelLoader(model_uri=f"models:/{model_name}/{version}", flavor="sklearn")
    loaded_model, _ = loader.load_data(LinearRegression)
    assert coefficients_are_equal(fitted_sklearn_model, loaded_model)

    # specify via arguments
    loader = MLFlowModelLoader(
        mode="registry", model_name=model_name, version=version, flavor="sklearn"
    )
    loaded_model, _ = loader.load_data(LinearRegression)
    assert coefficients_are_equal(fitted_sklearn_model, loaded_model)


def test_mlflow_infer_flavor(fitted_sklearn_model: BaseEstimator):
    saver = MLFlowModelSaver(path="model")

    metadata = saver.save_data(fitted_sklearn_model)

    assert "sklearn" in metadata["flavors"].keys()


def test_mlflow_specify_flavor_using_module(fitted_sklearn_model: BaseEstimator, tmp_path):
    model_path = tmp_path / "sklearn_model"
    saver = MLFlowModelSaver(flavor=mlflow.sklearn)

    mlflow.set_tracking_uri(model_path.as_uri())
    with mlflow.start_run():
        # save model
        metadata = saver.save_data(fitted_sklearn_model)
    # reload model
    loaded_model = mlflow.sklearn.load_model(metadata["model_uri"])

    assert coefficients_are_equal(fitted_sklearn_model, loaded_model)


def test_mlflow_handle_saver_kwargs():
    path = "tmp/path"
    flavor = "sklearn"
    saver = MLFlowModelSaver(path=path, flavor=flavor, mlflow_kwargs=dict(unknown_kwarg=True))

    assert saver.path == path
    assert saver.flavor == flavor
    assert saver.mlflow_kwargs.get("unknown_kwarg") is True


def test_io_to_mlflow_handle_saver_kwargs():
    path = "tmp/path"
    flavor = "sklearn"
    id = "saver_id"
    dependencies = ["tmp_node"]
    saver = to.mlflow(
        path=path,
        flavor=flavor,
        id=id,
        dependencies=dependencies,
        mlflow_kwargs=dict(unknown_kwarg=True),
    )
    mlflow_saver = vars(saver)["data_saver_kwargs"]

    assert mlflow_saver["path"].value == path
    assert mlflow_saver["flavor"].value == flavor
    assert mlflow_saver["mlflow_kwargs"].value.get("unknown_kwarg") is True


def test_io_to_mlflow_handle_loader_kwargs():
    path = "tmp/path"
    flavor = "sklearn"
    loader = from_.mlflow(
        target="test_node",
        model_uri=path,
        flavor=flavor,
        mlflow_kwargs=dict(unknown_kwarg=True),
    )
    mlflow_loader = vars(loader)["data_loader_kwargs"]

    assert mlflow_loader["model_uri"].value == path
    assert mlflow_loader["flavor"].value == flavor
    assert mlflow_loader["mlflow_kwargs"].value.get("unknown_kwarg") is True


def test_mlflow_registered_model_metadata(fitted_sklearn_model: BaseEstimator, tmp_path: Path):
    """When registering a model through materializers, the metadata must contain the
    key `registered_model` because the `hamilton.plugins.h_mlflow.MLFlowTracker` is expecting it.
    """
    model_path = tmp_path / "sklearn_model"
    saver = MLFlowModelSaver(flavor="sklearn", register_as="my_model")

    mlflow.set_tracking_uri(model_path.as_uri())
    with mlflow.start_run():
        metadata = saver.save_data(fitted_sklearn_model)

    assert metadata.get("registered_model")
