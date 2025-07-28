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

import pathlib
from typing import Union

import lightgbm
import numpy as np
import pytest

from hamilton.io.utils import FILE_METADATA
from hamilton.plugins.lightgbm_extensions import LightGBMFileReader, LightGBMFileWriter


def fitted_lightgbm_model() -> lightgbm.LGBMModel:
    model = lightgbm.LGBMRegressor()
    model.fit([[0], [1]], [0, 1])
    return model


def fitted_lightgbm_booster() -> lightgbm.Booster:
    train = lightgbm.Dataset(np.asarray([[0], [1], [0], [1], [1]]), label=[0, 0, 0, 0, 0])
    booster = lightgbm.train({"objective": "regression"}, train, 1)
    return booster


def fitted_lightgbm_cvbooster() -> lightgbm.CVBooster:
    train = lightgbm.Dataset(np.asarray([[0], [1], [0], [1], [1]]), label=[0, 0, 0, 0, 0])
    results = lightgbm.cv({"objective": "regression"}, train, 1, return_cvbooster=True)
    return results["cvbooster"]


@pytest.mark.parametrize(
    "fitted_lightgbm",
    [fitted_lightgbm_model(), fitted_lightgbm_booster(), fitted_lightgbm_cvbooster()],
)
def test_lightgbm_file_writer(
    fitted_lightgbm: Union[lightgbm.LGBMModel, lightgbm.Booster, lightgbm.CVBooster],
    tmp_path: pathlib.Path,
) -> None:
    model_path = tmp_path / "model.lgbm"
    writer = LightGBMFileWriter(path=model_path)

    metadata = writer.save_data(fitted_lightgbm)

    assert model_path.exists()
    assert metadata[FILE_METADATA]["path"] == str(model_path)


@pytest.mark.parametrize(
    "fitted_lightgbm",
    [fitted_lightgbm_model(), fitted_lightgbm_booster(), fitted_lightgbm_cvbooster()],
)
def test_xgboost_model_file_reader(
    fitted_lightgbm: Union[lightgbm.LGBMModel, lightgbm.Booster, lightgbm.CVBooster],
    tmp_path: pathlib.Path,
) -> None:
    model_path = tmp_path / "model.lgbm"
    if isinstance(fitted_lightgbm, lightgbm.LGBMModel):
        fitted_lightgbm.booster_.save_model(filename=model_path)
    else:
        fitted_lightgbm.save_model(filename=model_path)
    reader = LightGBMFileReader(path=model_path)

    model, metadata = reader.load_data(type(fitted_lightgbm))

    assert LightGBMFileReader.applicable_types() == [
        lightgbm.LGBMModel,
        lightgbm.Booster,
        lightgbm.CVBooster,
    ]
    if isinstance(model, lightgbm.Booster):
        assert model.num_trees() > 0
    elif isinstance(model, lightgbm.CVBooster):
        assert len(model.boosters) > 0
    elif isinstance(model, lightgbm.LGBMModel):
        assert model.get_params().get("model_file", False)
    else:
        raise TypeError(f"LightGBMFileReader loaded model of type {type(model)}.")
