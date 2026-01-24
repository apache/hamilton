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

import sys

from hamilton import telemetry

# disable telemetry for all tests!
telemetry.disable_telemetry()

# Skip tests that require packages not yet available on Python 3.14
collect_ignore = []
if sys.version_info >= (3, 14):
    collect_ignore.extend(
        [
            # polars - no Python 3.14 support yet
            "plugins/test_polars_extensions.py",
            "plugins/test_polars_lazyframe_extensions.py",
            "resources/narwhals_example.py",
            # plotly - no Python 3.14 support yet
            "plugins/test_plotly_extensions.py",
            # xgboost - no Python 3.14 support yet
            "plugins/test_xgboost_extensions.py",
            # lightgbm - no Python 3.14 support yet
            "plugins/test_lightgbm_extensions.py",
            # mlflow - no Python 3.14 support yet
            "plugins/test_mlflow_extension.py",
            # kedro - no Python 3.14 support yet
            "plugins/test_h_kedro.py",
            "plugins/test_kedro_extensions.py",
            # lancedb - no Python 3.14 support yet
            "plugins/test_huggingface_extensions.py",
        ]
    )
