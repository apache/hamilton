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
from collections.abc import Collection
from pathlib import Path
from typing import Any, Literal, Union

try:
    import lightgbm
except ImportError as e:
    raise NotImplementedError("LightGBM is not installed.") from e


from hamilton import registry
from hamilton.io import utils
from hamilton.io.data_adapters import DataLoader, DataSaver

LIGHTGBM_MODEL_TYPES = [lightgbm.LGBMModel, lightgbm.Booster, lightgbm.CVBooster]
LIGHTGBM_MODEL_TYPES_ANNOTATION = Union[lightgbm.LGBMModel, lightgbm.Booster, lightgbm.CVBooster]


@dataclasses.dataclass
class LightGBMFileWriter(DataSaver):
    """Write LighGBM models and boosters to a file"""

    path: str | Path
    num_iteration: int | None = None
    start_iteration: int = 0
    importance_type: Literal["split", "gain"] = "split"

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return LIGHTGBM_MODEL_TYPES

    def save_data(self, data: LIGHTGBM_MODEL_TYPES_ANNOTATION) -> dict[str, Any]:
        if isinstance(data, lightgbm.LGBMModel):
            data = data.booster_

        data.save_model(
            filename=self.path,
            num_iteration=self.num_iteration,
            start_iteration=self.start_iteration,
            importance_type=self.importance_type,
        )
        return utils.get_file_metadata(self.path)

    @classmethod
    def name(cls) -> str:
        return "file"


@dataclasses.dataclass
class LightGBMFileReader(DataLoader):
    """Load LighGBM models and boosters from a file"""

    path: str | Path

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return LIGHTGBM_MODEL_TYPES

    def load_data(
        self, type_: type
    ) -> tuple[lightgbm.Booster | lightgbm.CVBooster, dict[str, Any]]:
        model = type_(model_file=self.path)
        metadata = utils.get_file_metadata(self.path)
        return model, metadata

    @classmethod
    def name(cls) -> str:
        return "file"


def register_data_loaders():
    for loader in [
        LightGBMFileReader,
        LightGBMFileWriter,
    ]:
        registry.register_adapter(loader)


register_data_loaders()

COLUMN_FRIENDLY_DF_TYPE = False
