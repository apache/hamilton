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

import os
import sys
import uuid

import pytest

# Skip tests that require packages not yet available on Python 3.14+
collect_ignore = []
if sys.version_info >= (3, 14):
    collect_ignore.extend(
        [
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


@pytest.fixture
def postgres_schema():
    """A throwaway schema on the PostgreSQL server named by ``HAMILTON_TEST_POSTGRES_URL``.

    Yields ``(engine, schema_name)``; skips when the variable is unset. Only that schema is
    created and it is dropped afterwards, so any server the variable points at stays clean.
    """
    url = os.environ.get("HAMILTON_TEST_POSTGRES_URL")
    if not url:
        pytest.skip("HAMILTON_TEST_POSTGRES_URL not set")
    sqlalchemy = pytest.importorskip("sqlalchemy")
    engine = sqlalchemy.create_engine(url)
    schema = f"lineage_{uuid.uuid4().hex[:8]}"
    with engine.begin() as conn:
        conn.execute(sqlalchemy.text(f"CREATE SCHEMA {schema}"))
    try:
        yield engine, schema
    finally:
        with engine.begin() as conn:
            conn.execute(sqlalchemy.text(f"DROP SCHEMA {schema} CASCADE"))
        engine.dispose()
