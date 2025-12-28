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

from typing import Dict, Tuple

import numpy as np
import numpy.typing as npt
from original_script import create_species_bunch
from sklearn.utils._bunch import Bunch

from hamilton.function_modifiers import extract_fields, pipe_input, source, step


def _create_species_bunch(
    species_name: str,
    data: Bunch,
    data_grid: Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]],
) -> npt.NDArray[np.float64]:
    """Our wrapper around and external function to integrate it as a node in the DAG."""
    return create_species_bunch(
        species_name, data.train, data.test, data.coverages, data_grid[0], data_grid[1]
    )


def _standardize_features(
    species_bunch: npt.NDArray[np.float64],
) -> Tuple[
    npt.NDArray[np.float64],
    npt.NDArray[np.float64],
    npt.NDArray[np.float64],
]:
    mean = species_bunch.cov_train.mean(axis=0)
    std = species_bunch.cov_train.std(axis=0)
    return species_bunch, mean, std


@extract_fields(
    {
        "bunch": Bunch,
        "mean": npt.NDArray[np.float64],
        "std": npt.NDArray[np.float64],
        "train_cover_std": npt.NDArray[np.float64],
        "test_cover_std": npt.NDArray[np.float64],
    }
)
@pipe_input(
    step(_create_species_bunch, data=source("data"), data_grid=source("data_grid_")),
    step(_standardize_features),
)
def species(
    chosen_species: Tuple[
        npt.NDArray[np.float64],
        npt.NDArray[np.float64],
        npt.NDArray[np.float64],
    ],
) -> Dict[str, npt.NDArray[np.float64]]:
    train_cover_std = (chosen_species[0].cov_train - chosen_species[1]) / chosen_species[2]
    return {
        "bunch": chosen_species[0],
        "mean": chosen_species[1],
        "std": chosen_species[2],
        "train_cover_std": train_cover_std,
        "test_cover_std": chosen_species[0].cov_test,
    }
