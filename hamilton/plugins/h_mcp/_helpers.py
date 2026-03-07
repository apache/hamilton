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

import linecache
import sys
import traceback
from typing import TYPE_CHECKING
from uuid import uuid4

from hamilton import ad_hoc_utils, driver

if TYPE_CHECKING:
    from types import ModuleType


def build_driver_from_code(
    code: str, config: dict | None = None
) -> tuple[driver.Driver, ModuleType]:
    """Build a Hamilton Driver from a code string.

    Uses ad_hoc_utils.module_from_source to create a temp module,
    then builds the Driver with dynamic execution enabled.

    :param code: Python source code defining Hamilton functions.
    :param config: Optional Hamilton config dict.
    :return: Tuple of (Driver, temp_module). Caller must clean up the module.
    """
    module_name = f"mcp_temp_{uuid4().hex}"
    module = ad_hoc_utils.module_from_source(code, module_name=module_name)
    dr = (
        driver.Builder()
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_modules(module)
        .with_config(config or {})
        .build()
    )
    return dr, module


def cleanup_temp_module(module: ModuleType) -> None:
    """Remove a temporary module from sys.modules and linecache."""
    name = module.__name__
    sys.modules.pop(name, None)
    linecache.cache.pop(name, None)


def format_validation_errors(exc: Exception) -> list[dict]:
    """Parse a Hamilton or Python exception into structured error dicts.

    Returns a list of ``{"type": ..., "message": ..., "detail": ...}`` dicts.
    """
    error_type = type(exc).__name__
    message = str(exc)

    if isinstance(exc, SyntaxError):
        return [
            {
                "type": error_type,
                "message": message,
                "detail": f"line {exc.lineno}" if exc.lineno else None,
            }
        ]

    return [{"type": error_type, "message": message, "detail": None}]


def format_exception_chain(exc: Exception) -> list[dict]:
    """Format an exception including its full traceback as structured errors."""
    errors = format_validation_errors(exc)
    tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
    errors[0]["traceback"] = "".join(tb)
    return errors


def serialize_results(results: dict) -> dict[str, str]:
    """Convert Hamilton execution results to JSON-safe string representations.

    Handles pandas DataFrames/Series via .to_dict(), falls back to str().
    """
    serialized = {}
    for key, val in results.items():
        try:
            import pandas as pd

            if isinstance(val, pd.DataFrame):
                serialized[key] = val.to_dict()
                continue
            if isinstance(val, pd.Series):
                serialized[key] = val.to_dict()
                continue
        except ImportError:
            pass
        try:
            import numpy as np

            if isinstance(val, np.ndarray):
                serialized[key] = val.tolist()
                continue
        except ImportError:
            pass
        try:
            import polars as pl

            if isinstance(val, pl.DataFrame):
                serialized[key] = val.to_dicts()
                continue
            if isinstance(val, pl.Series):
                serialized[key] = val.to_list()
                continue
        except ImportError:
            pass
        serialized[key] = str(val)
    return serialized
