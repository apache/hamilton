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
from sklearn import datasets, utils

from hamilton.function_modifiers import config

"""
Module to load digit data.
"""


@config.when(data_loader="iris")
def data__iris() -> utils.Bunch:
    return datasets.load_digits()


@config.when(data_loader="digits")
def data__digits() -> utils.Bunch:
    return datasets.load_digits()


def target(data: utils.Bunch) -> np.ndarray:
    return data.target


def target_names(data: utils.Bunch) -> np.ndarray:
    return data.target_names


def feature_matrix(data: utils.Bunch) -> np.ndarray:
    return data.data
