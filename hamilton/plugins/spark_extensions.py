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

import abc
import dataclasses
from typing import Any, Collection, Dict, Tuple, Type

try:
    import pyspark.sql as ps
except ImportError as e:
    raise NotImplementedError("Pyspark is not installed.") from e

from pandas import DataFrame
from pyspark.sql import SparkSession

from hamilton import registry
from hamilton.io import utils
from hamilton.io.data_adapters import DataLoader


@dataclasses.dataclass
class SparkDataFrameDataLoader(DataLoader):
    """Base class for data loaders that load pyspark dataframes.
    We are not yet including data savers, but that will be added to this most likely..
    """

    spark: SparkSession

    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [ps.DataFrame]

    @abc.abstractmethod
    def load_data(self, type_: Type[DataFrame]) -> Tuple[ps.DataFrame, Dict[str, Any]]:
        pass


@dataclasses.dataclass
class CSVDataLoader(SparkDataFrameDataLoader):
    path: str  # It supports multiple but for now we're going to have a single one
    # We can always make that a list of strings, or make a multiple reader (.multicsv)
    header: bool = True
    sep: str = ","

    def load_data(self, type_: Type[DataFrame]) -> Tuple[ps.DataFrame, Dict[str, Any]]:
        return (
            self.spark.read.csv(self.path, header=self.header, sep=self.sep, inferSchema=True),
            utils.get_file_metadata(self.path),
        )

    @classmethod
    def name(cls) -> str:
        return "csv"


@dataclasses.dataclass
class ParquetDataLoader(SparkDataFrameDataLoader):
    path: str  # It supports multiple but for now we're going to have a single one

    # We can always make that a list of strings, or make a multiple reader (.multicsv)

    def load_data(self, type_: Type[DataFrame]) -> Tuple[ps.DataFrame, Dict[str, Any]]:
        return self.spark.read.parquet(self.path), utils.get_file_metadata(self.path)

    @classmethod
    def name(cls) -> str:
        return "parquet"


def register_data_loaders():
    """Function to register the data loaders for this extension."""
    for loader in [CSVDataLoader, ParquetDataLoader]:
        registry.register_adapter(loader)


COLUMN_FRIENDLY_DF_TYPE = False

register_data_loaders()


DATAFRAME_TYPE = ps.DataFrame
COLUMN_TYPE = None


def register_types():
    """Function to register the types for this extension."""
    registry.register_types("spark", DATAFRAME_TYPE, COLUMN_TYPE)


register_types()
