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

import dataclasses
import pickle
from typing import Any, Collection, Dict, Type

import numpy as np
from sklearn import base

from hamilton import registry
from hamilton.io import utils
from hamilton.io.data_adapters import DataSaver

# TODO -- put this back in the standard library


@dataclasses.dataclass
class NumpyMatrixToCSV(DataSaver):
    path: str
    sep: str = ","

    def __post_init__(self):
        if not self.path.endswith(".csv"):
            raise ValueError(f"CSV files must end with .csv, got {self.path}")

    def save_data(self, data: np.ndarray) -> Dict[str, Any]:
        np.savetxt(self.path, data, delimiter=self.sep)
        return utils.get_file_metadata(self.path)

    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [np.ndarray]

    @classmethod
    def name(cls) -> str:
        return "csv"


@dataclasses.dataclass
class SKLearnPickler(DataSaver):
    path: str

    def save_data(self, data: base.ClassifierMixin) -> Dict[str, Any]:
        pickle.dump(data, open(self.path, "wb"))
        return utils.get_file_metadata(self.path)

    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [base.ClassifierMixin]

    @classmethod
    def name(cls) -> str:
        return "pickle"


for adapter in [NumpyMatrixToCSV, SKLearnPickler]:
    registry.register_adapter(adapter)
