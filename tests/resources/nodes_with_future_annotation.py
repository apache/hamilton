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

from __future__ import annotations

from hamilton.function_modifiers import dataloader
from hamilton.htypes import Collect, Parallelizable

"""Tests future annotations with common node types"""


def parallelized() -> Parallelizable[int]:
    yield 1
    yield 2
    yield 3


def standard(parallelized: int) -> int:
    return parallelized + 1


def collected(standard: Collect[int]) -> int:
    return sum(standard)


@dataloader()
def sample_dataloader() -> tuple[list[str], dict]:
    """Grouping here as the rest test annotations"""
    return ["a", "b", "c"], {}
