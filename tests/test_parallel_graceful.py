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

import pytest

from hamilton import driver
from hamilton.execution.executors import SynchronousLocalTaskExecutor
from hamilton.lifecycle.default import GracefulErrorAdapter

from .resources import graceful_parallel


def _make_driver(
    test_state: str,
    try_parallel=True,
    fail_first=False,
    allow_injection=True,
):
    local_executor = SynchronousLocalTaskExecutor()
    dr = (
        driver.Builder()
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_modules(graceful_parallel)
        .with_remote_executor(local_executor)
        .with_adapters(
            GracefulErrorAdapter(
                error_to_catch=Exception,
                sentinel_value=None,
                try_all_parallel=try_parallel,
                allow_injection=allow_injection,
            )
        )
        .with_config(
            {
                "test_state": test_state,
                "test_front": "bad" if fail_first else "good",
            },
        )
        .build()
    )
    return dr


@pytest.mark.parametrize(
    "test_state, try_parallel, fail_first, expected_value",
    [
        ("early", True, False, [None]),
        ("middle", True, False, [0.0, 6.0, 12.0, 18.0, 24.0, None]),
        ("middle", False, False, [None]),
        ("pass", True, False, [0.0, 6.0, 12.0, 18.0, 24.0, 30.0, None, None, None, None]),
        ("pass", False, True, [None]),
    ],
    ids=[
        "test_early_parallel_fail",
        "test_middle_parallel_fail",
        "test_middle_parallel_as_single",
        "test_inside_block_errors",
        "test_pre_parallel_fail",
    ],
)
def test_parallel_graceful_simple(test_state, try_parallel, fail_first, expected_value) -> None:
    # Fail before the anything is yielded: should get 1 failure and skip all
    dr = _make_driver(
        test_state,
        try_parallel,
        fail_first,
    )
    ans = dr.execute(
        ["distro_gather"],
        inputs={"n": 10},
    )
    assert ans["distro_gather"] == expected_value


def test_parallel_gather_injection() -> None:
    dr = _make_driver(
        "pass",
        try_parallel=True,
        fail_first=False,
    )
    ans = dr.execute(
        ["distro_end"],
        inputs={"n": 10},
    )
    assert ans["distro_end"] == [
        [0.0, None],
        [6.0, None],
        [12.0, None],
        [18.0, None],
        [24.0, 13],
        [30.0, 16],
        [None, 19],
        [None, 22],
        [None, 25],
        [None, 28],
    ]

    # show that disallowing injection skips over the gathering step
    dr = _make_driver(
        "pass",
        try_parallel=True,
        fail_first=False,
        allow_injection=False,
    )
    ans = dr.execute(
        ["distro_end"],
        inputs={"n": 10},
    )
    assert ans["distro_end"] == [
        None,
        None,
        None,
        None,
        [24.0, 13],
        [30.0, 16],
        None,
        None,
        None,
        None,
    ]
