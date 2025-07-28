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

from kedro.io import DataCatalog
from kedro.io.memory_dataset import MemoryDataset

from hamilton.plugins import kedro_extensions


def test_kedro_saver():
    dataset_name = "in_memory"
    data = 37
    catalog = DataCatalog({dataset_name: MemoryDataset()})

    saver = kedro_extensions.KedroSaver(dataset_name=dataset_name, catalog=catalog)
    saver.save_data(data)
    loaded_data = catalog.load(dataset_name)

    assert loaded_data == data


def test_kedro_loader():
    dataset_name = "in_memory"
    data = 37
    catalog = DataCatalog({dataset_name: MemoryDataset(data=data)})

    loader = kedro_extensions.KedroLoader(dataset_name=dataset_name, catalog=catalog)
    loaded_data, metadata = loader.load_data(int)

    assert loaded_data == data
