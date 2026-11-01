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

import subprocess
from unittest import mock

from hamilton import driver
from hamilton.cli import logic

from tests.cli.resources import module_v1, module_v2


def test_git_directory_exists():
    completed_process = subprocess.CompletedProcess(
        args=["git", "rev-parse", "--show-toplevel"],
        returncode=0,
        stdout="/tmp/fake-repo\n",
        stderr="",
    )

    with mock.patch("subprocess.run", return_value=completed_process) as run_mock:
        git_base_dir = logic.get_git_base_directory()

    assert git_base_dir == "/tmp/fake-repo"
    run_mock.assert_called_once_with(
        ["git", "rev-parse", "--show-toplevel"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def test_map_nodes_to_origins():
    expected_mapping = {
        "customers_path": "customers_df",
        "customers_df": "customers_df",
        "orders_path": "orders_df",
        "orders_df": "orders_df",
        "customers_orders_df": "customers_orders_df",
        "amount": "customers_orders_df",
        "age": "customers_orders_df",
        "country": "customers_orders_df",
        "orders_per_customer": "orders_per_customer",
        "average_order_by_customer": "average_order_by_customer",
        "customer_summary_table": "customer_summary_table",
    }

    dr = driver.Builder().with_modules(module_v1).build()
    node_to_origin = logic.map_nodes_to_functions(dr)

    assert node_to_origin == expected_mapping


def test_diff_versions():
    reference_versions = {
        "average_order_by_customer": "b58a6",
        "customer_summary_table": "6bf52",
        "customers_df": "480be",
        "customers_orders_df": "883f0",
        "orders_df": "58e65",
        "orders_per_customer": "6af6d",
    }
    current_versions = {
        "average_order_by_customer": "5296f",
        "customer_summary_table": "6bf52",
        "customers_df": "480be",
        "customers_orders_df": "883f0",
        "orders_df": "58e65",
        "orders_per_distributor": "6d64l",
    }

    diff = logic.diff_versions(
        current_map=current_versions,
        reference_map=reference_versions,
    )

    assert diff["reference_only"] == ["orders_per_customer"]
    assert diff["current_only"] == ["orders_per_distributor"]
    assert diff["edit"] == ["average_order_by_customer"]


def test_diff_node_versions():
    current_dr = driver.Builder().with_modules(module_v2).build()
    reference_dr = driver.Builder().with_modules(module_v1).build()

    current_nodes = logic.hash_hamilton_nodes(current_dr)
    reference_nodes = logic.hash_hamilton_nodes(reference_dr)

    diff = logic.diff_versions(
        current_map=current_nodes,
        reference_map=reference_nodes,
    )

    assert diff["reference_only"] == ["orders_per_customer"]
    assert diff["current_only"] == ["orders_per_distributor"]
    assert diff["edit"] == ["average_order_by_customer", "customer_summary_table"]


HAMILTON_MODULE_SOURCE = """import pandas as pd


def spend_per_signup(spend: pd.Series, signups: pd.Series) -> pd.Series:
    \"\"\"The cost per signup in relation to spend.\"\"\"
    return spend / signups


def total(spend: pd.Series) -> float:
    \"\"\"Total spend.\"\"\"
    return spend.sum()
"""


def test_create_test_stubs_generates_stubs(tmp_path):
    module_file = tmp_path / "business_logic.py"
    module_file.write_text(HAMILTON_MODULE_SOURCE)

    out_file, created, skipped = logic.create_test_stubs(module_file)

    assert out_file == tmp_path / "test_business_logic.py"
    assert created == ["test_spend_per_signup", "test_total"]
    assert skipped == []

    text = out_file.read_text()
    assert "import pandas as pd" in text
    assert "import business_logic" in text
    assert "def test_spend_per_signup():" in text
    assert "spend: pd.Series = pd.Series([])  # TODO: fill in" in text
    assert "actual = business_logic.spend_per_signup(spend, signups)" in text
    assert "pd.testing.assert_series_equal(actual, expected)" in text
    assert "def test_total():" in text
    # total() returns float, so it gets a plain assert even though its param is pandas
    total_stub = text.split("def test_total():")[1]
    assert "assert actual == expected" in total_stub
    assert "pd.testing" not in total_stub


def test_create_test_stubs_skips_existing_and_appends(tmp_path):
    module_file = tmp_path / "business_logic.py"
    module_file.write_text(HAMILTON_MODULE_SOURCE)
    existing = tmp_path / "test_business_logic.py"
    existing.write_text(
        "import business_logic\n\n\ndef test_spend_per_signup():\n    assert True\n"
    )

    out_file, created, skipped = logic.create_test_stubs(module_file)

    assert out_file == existing
    assert created == ["test_total"]
    assert skipped == ["test_spend_per_signup"]

    text = existing.read_text()
    assert text.count("def test_spend_per_signup():") == 1
    assert "def test_total():" in text
    # original content preserved at the top
    assert text.startswith("import business_logic")


def test_create_test_stubs_custom_output_path(tmp_path):
    module_file = tmp_path / "business_logic.py"
    module_file.write_text(HAMILTON_MODULE_SOURCE)
    custom_out = tmp_path / "custom_tests.py"

    out_file, created, skipped = logic.create_test_stubs(module_file, output_file=custom_out)

    assert out_file == custom_out
    assert custom_out.exists()
    assert created == ["test_spend_per_signup", "test_total"]


def test_create_test_stubs_non_pandas_functions_use_plain_assert(tmp_path):
    module_file = tmp_path / "strings.py"
    module_file.write_text(
        "def shout(word: str) -> str:\n    return word.upper()\n"
    )

    out_file, created, _ = logic.create_test_stubs(module_file)

    text = out_file.read_text()
    assert "import pandas" not in text
    assert "word: str = None  # TODO: fill in" in text
    assert "assert actual == expected" in text


def test_create_test_stubs_resolves_sibling_imports(tmp_path):
    (tmp_path / "helpers.py").write_text("def double(x):\n    return x * 2\n")
    module_file = tmp_path / "uses_sibling.py"
    module_file.write_text(
        "from helpers import double\n\n\ndef doubled_value(x: int) -> int:\n    return double(x)\n"
    )

    out_file, created, skipped = logic.create_test_stubs(module_file)

    assert created == ["test_doubled_value"]
    text = out_file.read_text()
    assert "def test_doubled_value():" in text
