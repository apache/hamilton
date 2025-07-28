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

import pandas as pd

from hamilton.experimental import h_databackends


def test_isinstance_dataframe():
    value = pd.DataFrame()
    assert isinstance(value, h_databackends.DATAFRAME_TYPES)


def test_issubclass_dataframe():
    class_ = pd.DataFrame
    assert issubclass(class_, h_databackends.DATAFRAME_TYPES)


def test_not_isinstance_dataframe():
    value = 6
    assert not isinstance(value, h_databackends.DATAFRAME_TYPES)


def test_not_issubclass_dataframe():
    class_ = int
    assert not issubclass(class_, h_databackends.DATAFRAME_TYPES)


def test_isinstance_column():
    value = pd.Series()
    assert isinstance(value, h_databackends.COLUMN_TYPES)


def test_issubclass_column():
    class_ = pd.Series
    assert issubclass(class_, h_databackends.COLUMN_TYPES)


def test_not_isinstance_column():
    value = 6
    assert not isinstance(value, h_databackends.COLUMN_TYPES)


def test_not_issubclass_column():
    class_ = int
    assert not issubclass(class_, h_databackends.COLUMN_TYPES)
