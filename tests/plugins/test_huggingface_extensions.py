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
import sys

import lancedb
import numpy as np
import pytest
from datasets import Dataset, DatasetDict

from hamilton.plugins import huggingface_extensions


def test_hfds_loader():
    path_to_test = "tests/resources/hf_datasets"
    reader = huggingface_extensions.HuggingFaceDSLoader(path_to_test)
    ds, metadata = reader.load_data(DatasetDict)

    assert huggingface_extensions.HuggingFaceDSLoader.applicable_types() == list(
        huggingface_extensions.HF_types
    )
    assert reader.applies_to(DatasetDict)
    assert reader.applies_to(Dataset)
    assert ds.shape == {"train": (1, 3)}


def test_hfds_parquet_saver(tmp_path: pathlib.Path):
    file_path = tmp_path / "testhf.parquet"
    saver = huggingface_extensions.HuggingFaceDSParquetSaver(file_path)
    ds = Dataset.from_dict({"a": [1, 2, 3]})
    metadata = saver.save_data(ds)
    assert file_path.exists()
    assert metadata["dataset_metadata"] == {
        "columns": ["a"],
        "features": {"a": {"_type": "Value", "dtype": "int64"}},
        "rows": 3,
        "size_in_bytes": None,
    }
    assert "file_metadata" in metadata
    assert huggingface_extensions.HuggingFaceDSParquetSaver.applicable_types() == list(
        huggingface_extensions.HF_types
    )
    assert saver.applies_to(DatasetDict)
    assert saver.applies_to(Dataset)


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires Python 3.9 or higher")
def test_hfds_lancedb_saver(tmp_path: pathlib.Path):
    db_client = lancedb.connect(tmp_path / "lancedb")
    saver = huggingface_extensions.HuggingFaceDSLanceDBSaver(db_client, "test_table")
    ds = Dataset.from_dict({"vector": [np.array([1.0, 2.0, 3.0])], "named_entities": ["a"]})
    metadata = saver.save_data(ds)
    assert metadata == {
        "dataset_metadata": {
            "columns": ["vector", "named_entities"],
            "features": {
                "named_entities": {"_type": "Value", "dtype": "string"},
                "vector": {"_type": "List", "feature": {"_type": "Value", "dtype": "float64"}},
            },
            "rows": 1,
            "size_in_bytes": None,
        },
        "db_meta": {"table_name": "test_table"},
    }
    assert db_client.open_table("test_table").search().to_list() == [
        {"named_entities": "a", "vector": [1.0, 2.0, 3.0]}
    ]
