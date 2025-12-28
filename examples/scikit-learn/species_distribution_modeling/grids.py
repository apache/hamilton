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

from typing import Tuple

import numpy as np
import numpy.typing as npt
from original_script import construct_grids
from sklearn.utils._bunch import Bunch

from hamilton.function_modifiers import pipe_input, step


def _construct_grids(batch: Bunch) -> Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    """Our wrapper around and external function to integrate it as a node in the DAG."""
    return construct_grids(batch=batch)


@pipe_input(step(_construct_grids))
def data_grid_(
    data: Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]],
) -> Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    return data


def meshgrid(
    data_grid_: Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]],
) -> Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    return np.meshgrid(data_grid_[0], data_grid_[1][::-1])


def land_reference(data: Bunch) -> npt.NDArray[np.float64]:
    return data.coverages[6]


def idx(land_reference: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    return np.where(land_reference > -9999)


def coverages_land(data: Bunch, idx: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    return data.coverages[:, idx[0], idx[1]].T


def background_points(data: Bunch) -> npt.NDArray[np.float64]:
    np.random.seed(13)
    return np.c_[
        np.random.randint(low=0, high=data.Ny, size=10000),
        np.random.randint(low=0, high=data.Nx, size=10000),
    ].T
