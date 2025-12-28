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

from typing import Any, Dict, Tuple

import numpy as np
import numpy.typing as npt
from sklearn import metrics
from sklearn.utils._bunch import Bunch

from hamilton.function_modifiers import pipe_input, source, step


def _normalize(
    data: npt.NDArray[np.float64], land_reference: npt.NDArray[np.float64]
) -> npt.NDArray[np.float64]:
    data[land_reference == -9999] = -9999
    return data


@pipe_input(step(_normalize, land_reference=source("land_reference")))
def prediction_background(
    prediction_train: npt.NDArray[np.float64], background_points: npt.NDArray[np.float64]
) -> npt.NDArray[np.float64]:
    return prediction_train[background_points[0], background_points[1]]


def levels(prediction_train: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    return np.linspace(prediction_train.min(), prediction_train.max(), 25)


def area_under_curve(
    prediction_test: npt.NDArray[np.float64],
    prediction_background: npt.NDArray[np.float64],
) -> float:
    scores = np.r_[prediction_test, prediction_background]
    y = np.r_[np.ones(prediction_test.shape), np.zeros(prediction_background.shape)]
    fpr, tpr, thresholds = metrics.roc_curve(y, scores)
    roc_auc = metrics.auc(fpr, tpr)
    return roc_auc


def plot_species_distribution(
    meshgrid: Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]],
    prediction_train: npt.NDArray[np.float64],
    land_reference: npt.NDArray[np.float64],
    levels: npt.NDArray[np.float64],
    bunch: Bunch,
    area_under_curve: float,
) -> Dict[str, Any]:
    return {
        "X": meshgrid[0],
        "Y": meshgrid[1],
        "Z": prediction_train,
        "land_reference": land_reference,
        "levels": levels,
        "species": bunch,
        "roc_auc": area_under_curve,
    }
