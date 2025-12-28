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

import numpy as np
import numpy.typing as npt
from sklearn import svm
from sklearn.utils._bunch import Bunch

from hamilton.function_modifiers import pipe_output, source, step, value


# TODO: add another model or two and use `.when` to showcase that this can be customizable @execution
def _OneClassSVM_model(
    training_set: npt.NDArray[np.float64], nu: float, kernel: str, gamma: float
) -> svm.OneClassSVM:
    clf = svm.OneClassSVM(nu=nu, kernel=kernel, gamma=gamma)
    clf.fit(training_set)
    return clf


def _decision_function(
    model: svm.OneClassSVM,
    underlying_data: npt.NDArray[np.float64],
    mean: npt.NDArray[np.float64],
    std: npt.NDArray[np.float64],
) -> npt.NDArray[np.float64]:
    return model.decision_function((underlying_data - mean) / std)


def _prediction_step(
    decision: npt.NDArray[np.float64], idx: npt.NDArray[np.float64], data: Bunch
) -> npt.NDArray[np.float64]:
    Z = decision.min() * np.ones((data.Ny, data.Nx), dtype=np.float64)
    Z[idx[0], idx[1]] = decision
    return Z


@pipe_output(
    step(_OneClassSVM_model, nu=value(0.1), kernel=value("rbf"), gamma=value(0.5)),
    step(
        _decision_function,
        underlying_data=source("coverages_land"),
        mean=source("mean"),
        std=source("std"),
    ),
    step(_prediction_step, idx=source("idx"), data=source("data")),
)
def prediction_train(train_cover_std: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    return train_cover_std


@pipe_output(
    step(_OneClassSVM_model, nu=value(0.1), kernel=value("rbf"), gamma=value(0.5)),
    step(
        _decision_function,
        underlying_data=source("test_cover_std"),
        mean=source("mean"),
        std=source("std"),
    ),
)
def prediction_test(train_cover_std: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    return train_cover_std
