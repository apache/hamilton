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
from typing import Any, Collection, Dict, Tuple, Type, Union

from hamilton.io.data_adapters import DataLoader, DataSaver


@dataclasses.dataclass
class MockDataLoader(DataLoader):
    required_param: int
    default_param: int = 1

    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [bool]

    def load_data(self, type_: Type) -> Tuple[int, Dict[str, Any]]:
        pass

    @classmethod
    def name(cls) -> str:
        pass


@dataclasses.dataclass
class MockDataLoader2(DataLoader):
    required_param: int
    default_param: int = 1

    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [int]

    def load_data(self, type_: Type) -> Tuple[int, Dict[str, Any]]:
        pass

    @classmethod
    def name(cls) -> str:
        pass


@dataclasses.dataclass
class MockDataSaver(DataSaver):
    required_param: int
    default_param: int = 1

    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [bool]

    def save_data(self, type_: Type) -> Tuple[int, Dict[str, Any]]:
        pass

    @classmethod
    def name(cls) -> str:
        pass


@dataclasses.dataclass
class MockDataSaver2(DataSaver):
    required_param: int
    default_param: int = 1

    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [int]

    def save_data(self, type_: Type) -> Tuple[int, Dict[str, Any]]:
        pass

    @classmethod
    def name(cls) -> str:
        pass


@dataclasses.dataclass
class MockDataSaver3(DataSaver):
    required_param: int
    default_param: int = 1

    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [int, float]

    def save_data(self, type_: Type) -> Tuple[int, Dict[str, Any]]:
        pass

    @classmethod
    def name(cls) -> str:
        pass


def test_data_loader_get_required_params():
    assert MockDataLoader.get_required_arguments() == {"required_param": int}
    assert MockDataLoader.get_optional_arguments() == {"default_param": int}


def test_loader_applies_to():
    """Tests applies to is doing the right thing for a loader. i.e. A->B where A is the loader."""
    loader = MockDataLoader(1, 2)
    # bool -> int   -- bool is a subclass of int.
    assert loader.applies_to(int) is True
    # bool -> bool   -- bool is a subclass of itself
    assert loader.applies_to(bool) is True

    loader2 = MockDataLoader2(1, 2)
    # int -> int   -- int is a subclass of int.
    assert loader2.applies_to(int) is True
    # int -> bool   -- bool is not a subclass of int
    assert loader2.applies_to(bool) is False


def test_saver_applies_to():
    """Tests applies to is doing the right thing for a saver. i.e. A->B where B is the saver."""
    saver = MockDataSaver(1, 2)
    # int -> bool -- int is not a subclass of bool
    assert saver.applies_to(int) is False
    # bool -> bool  -- bool is a subclas of itself
    assert saver.applies_to(bool) is True

    saver2 = MockDataSaver2(1, 2)
    # int -> int -- int is a subclass of itself
    assert saver2.applies_to(int) is True
    # bool -> int -- bool is a subclass of int
    assert saver2.applies_to(bool) is True
    # [int, float] -> int -- can't handle union type here correctly
    assert saver2.applies_to(Union[int, float]) is False


def test_saver_applies_to_union_of_all_types():
    """If a saver supports saving multiple things, then we need to take the union of that type.

    Why? well if there's a type that outputs a union, then we will not match it when
    we should. So the only way to do that is to take the union of all types if there's
    more than 1 and simply match it.
    """
    saver = MockDataSaver3(1, 3)
    assert saver.applies_to(Union[float, int]) is True
    # order shouldn't matter
    assert saver.applies_to(Union[int, float]) is True
    assert saver.applies_to(int) is True
    assert saver.applies_to(float) is True
