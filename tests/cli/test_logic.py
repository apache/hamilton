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

import pytest

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
    module_file.write_text("def shout(word: str) -> str:\n    return word.upper()\n")

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


def _import_file(path, tmp_path):
    """Import a generated test file for real, so a NameError at import time fails the test."""
    import importlib.util
    import sys

    sys.path.insert(0, str(tmp_path))
    try:
        spec = importlib.util.spec_from_file_location(f"generated_{path.stem}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(tmp_path))
    return module


def test_create_test_stubs_does_not_execute_the_module(tmp_path):
    marker = tmp_path / "imported.marker"
    module_file = tmp_path / "side_effects.py"
    module_file.write_text(
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('the module ran')\n"
        "raise RuntimeError('importing this module is not safe')\n"
        "\n"
        "\n"
        "def value(x: int) -> int:\n"
        "    return x + 1\n"
    )

    out_file, created, skipped = logic.create_test_stubs(module_file)

    assert created == ["test_value"]
    assert skipped == []
    assert not marker.exists()
    assert "def test_value():" in out_file.read_text()


def test_create_test_stubs_handles_package_relative_imports(tmp_path):
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "__init__.py").write_text("")
    (package / "helpers.py").write_text("def double(x: int) -> int:\n    return x * 2\n")
    module_file = package / "logic_mod.py"
    module_file.write_text(
        "from .helpers import double\n\n\ndef doubled(x: int) -> int:\n    return double(x)\n"
    )

    out_file, created, skipped = logic.create_test_stubs(module_file)

    assert out_file == package / "test_logic_mod.py"
    assert created == ["test_doubled"]
    text = out_file.read_text()
    assert "import pkg.logic_mod" in text
    assert "actual = pkg.logic_mod.doubled(x)" in text
    compile(text, str(out_file), "exec")


def test_create_test_stubs_with_postponed_annotations(tmp_path):
    module_file = tmp_path / "postponed.py"
    module_file.write_text(
        "from __future__ import annotations\n"
        "\n"
        "import pandas as pd\n"
        "\n"
        "\n"
        "def scaled(spend: pd.Series, factor: float = 1.0) -> pd.Series:\n"
        "    return spend * factor\n"
    )

    out_file, created, skipped = logic.create_test_stubs(module_file)

    assert created == ["test_scaled"]
    text = out_file.read_text()
    assert "spend: pd.Series = pd.Series([])  # TODO: fill in" in text
    assert "factor: float = 1.0  # TODO: fill in" in text
    assert "pd.testing.assert_series_equal(actual, expected)" in text
    compile(text, str(out_file), "exec")


def test_create_test_stubs_preserves_parameter_kinds_and_defaults(tmp_path):
    module_file = tmp_path / "kinds.py"
    module_file.write_text(
        "def mixed(a, /, b, c=1, *args, flag=False, **kwargs):\n"
        '    """Every parameter kind."""\n'
        "    return a\n"
    )

    out_file, created, skipped = logic.create_test_stubs(module_file)

    assert created == ["test_mixed"]
    text = out_file.read_text()
    assert "a = None  # TODO: fill in" in text
    assert "b = None  # TODO: fill in" in text
    assert "c = 1  # TODO: fill in" in text
    assert "args = ()  # TODO: fill in" in text
    assert "flag = False  # TODO: fill in" in text
    assert "kwargs = {}  # TODO: fill in" in text
    assert "actual = kinds.mixed(a, b, c, *args, flag=flag, **kwargs)" in text
    compile(text, str(out_file), "exec")


def test_create_test_stubs_append_adds_missing_imports(tmp_path):
    module_file = tmp_path / "business_logic.py"
    module_file.write_text(HAMILTON_MODULE_SOURCE)
    existing = tmp_path / "test_business_logic.py"
    existing.write_text("def test_spend_per_signup():\n    assert True\n")

    out_file, created, skipped = logic.create_test_stubs(module_file)

    assert out_file == existing
    assert created == ["test_total"]
    assert skipped == ["test_spend_per_signup"]
    text = existing.read_text()
    assert "import pandas as pd" in text
    assert "import business_logic" in text
    # the imports land above the code that was already there
    assert text.index("import pandas as pd") < text.index("def test_spend_per_signup():")
    compile(text, str(existing), "exec")


def test_create_test_stubs_append_keeps_the_header_first_and_does_not_duplicate_imports(tmp_path):
    module_file = tmp_path / "business_logic.py"
    module_file.write_text(HAMILTON_MODULE_SOURCE)
    existing = tmp_path / "test_business_logic.py"
    existing.write_text(
        "# Licensed to the Apache Software Foundation (ASF)\n"
        "import business_logic\n"
        "\n"
        "\n"
        "def test_spend_per_signup():\n"
        "    assert True\n"
    )

    _, created, _ = logic.create_test_stubs(module_file)

    text = existing.read_text()
    assert created == ["test_total"]
    assert text.startswith("# Licensed to the Apache Software Foundation (ASF)")
    assert text.count("import business_logic") == 1
    assert text.count("import pandas as pd") == 1
    assert (
        text.index("import business_logic")
        < text.index("import pandas as pd")
        < text.index("def test_total():")
    )
    compile(text, str(existing), "exec")


def test_create_test_stubs_rejects_a_module_it_cannot_parse(tmp_path):
    module_file = tmp_path / "broken.py"
    module_file.write_text("def broken(:\n")

    with pytest.raises(ValueError, match="Could not parse"):
        logic.create_test_stubs(module_file)


def test_create_test_stubs_uses_a_placeholder_for_defaults_that_reference_names(tmp_path):
    module_file = tmp_path / "bumped.py"
    module_file.write_text(
        "DEFAULT_LEVEL = 3\n\n\ndef bump(level=DEFAULT_LEVEL, *args, **kwargs):\n    return level\n"
    )

    out_file, created, skipped = logic.create_test_stubs(module_file)

    assert created == ["test_bump"]
    text = out_file.read_text()
    # DEFAULT_LEVEL is not imported by the generated file, so it must not be written raw
    assert "level = None  # TODO: fill in (default is DEFAULT_LEVEL)" in text
    assert "actual = bumped.bump(level, *args, **kwargs)" in text
    compile(text, str(out_file), "exec")
    _import_file(out_file, tmp_path)


def test_create_test_stubs_drops_annotations_the_generated_file_cannot_resolve(tmp_path):
    module_file = tmp_path / "annotated.py"
    module_file.write_text(
        "from __future__ import annotations\n"
        "\n"
        "from typing import Optional\n"
        "\n"
        "\n"
        "def label(value: Optional[str] = None, counts: dict[str, int] = {}) -> Optional[str]:\n"
        "    return value\n"
    )

    out_file, created, skipped = logic.create_test_stubs(module_file)

    text = out_file.read_text()
    # Optional is typing, which the generated file does not import: keep it in the comment
    assert "value = None  # TODO: fill in (declared as Optional[str])" in text
    # dict and str are builtins, so that annotation is safe to keep
    assert "counts: dict[str, int] = {}  # TODO: fill in" in text
    compile(text, str(out_file), "exec")
    _import_file(out_file, tmp_path)


def test_create_test_stubs_skips_async_functions(tmp_path):
    module_file = tmp_path / "mixed_async.py"
    module_file.write_text(
        "async def fetch(url: str) -> str:\n"
        "    return url\n"
        "\n"
        "\n"
        "def parse(url: str) -> str:\n"
        "    return url.strip()\n"
    )

    out_file, created, skipped = logic.create_test_stubs(module_file)

    assert created == ["test_parse"]
    assert "test_fetch" not in out_file.read_text()


def test_create_test_stubs_does_not_run_decorators(tmp_path):
    marker = tmp_path / "decorated.marker"
    (tmp_path / "decorators.py").write_text(
        "from pathlib import Path\n"
        "\n"
        "\n"
        "def counted(fn):\n"
        f"    Path({str(marker)!r}).write_text('a decorator ran')\n"
        "    return fn\n"
    )
    module_file = tmp_path / "decorated.py"
    module_file.write_text(
        "from decorators import counted\n\n\n@counted\ndef value(x: int) -> int:\n    return x\n"
    )

    out_file, created, skipped = logic.create_test_stubs(module_file)

    assert created == ["test_value"]
    assert not marker.exists()
    assert "def test_value():" in out_file.read_text()


def test_create_test_stubs_keeps_the_line_endings_of_an_existing_file(tmp_path):
    module_file = tmp_path / "business_logic.py"
    module_file.write_text(HAMILTON_MODULE_SOURCE)
    existing = tmp_path / "test_business_logic.py"
    existing.write_bytes(
        b"import business_logic\r\n\r\n\r\ndef test_spend_per_signup():\r\n    assert True\r\n"
    )

    _, created, _ = logic.create_test_stubs(module_file)

    raw = existing.read_bytes()
    assert created == ["test_total"]
    assert b"import pandas as pd\r\n" in raw
    assert b"\n" not in raw.replace(b"\r\n", b"")
    assert b"\r\n    assert actual == expected\r\n" in raw


def test_create_test_stubs_leaves_an_unparsable_test_file_alone(tmp_path):
    module_file = tmp_path / "business_logic.py"
    module_file.write_text(HAMILTON_MODULE_SOURCE)
    existing = tmp_path / "test_business_logic.py"
    existing.write_text("def broken(:\n")

    with pytest.raises(ValueError, match="Refusing to append"):
        logic.create_test_stubs(module_file)

    assert existing.read_text() == "def broken(:\n"


def test_create_test_stubs_does_not_duplicate_equivalent_imports(tmp_path):
    module_file = tmp_path / "business_logic.py"
    module_file.write_text(HAMILTON_MODULE_SOURCE)
    existing = tmp_path / "test_business_logic.py"
    existing.write_text(
        "from pandas import Series\n"
        "import pandas as pandas_alias\n"
        "import business_logic\n"
        "\n"
        "\n"
        "def test_spend_per_signup():\n"
        "    assert True\n"
    )

    _, created, _ = logic.create_test_stubs(module_file)

    text = existing.read_text()
    assert created == ["test_total"]
    # the new stubs call pd.*, so exactly one `import pandas as pd` has to be there
    assert text.count("import pandas as pd") == 1
    assert text.count("import business_logic") == 1
    assert text.count("from pandas import Series") == 1
    compile(text, str(existing), "exec")
    _import_file(existing, tmp_path)


def test_create_test_stubs_inserts_imports_above_executable_code(tmp_path):
    module_file = tmp_path / "business_logic.py"
    module_file.write_text(HAMILTON_MODULE_SOURCE)
    existing = tmp_path / "test_business_logic.py"
    existing.write_text(
        "def helper():\n"
        "    return 1\n"
        "\n"
        "\n"
        "HELPER = helper()\n"
        "import business_logic\n"
        "\n"
        "\n"
        "def test_spend_per_signup():\n"
        "    assert True\n"
    )

    _, created, _ = logic.create_test_stubs(module_file)

    text = existing.read_text()
    assert created == ["test_total"]
    # HELPER = helper() runs before the existing import, so the new imports must go above it
    assert text.index("import pandas as pd") < text.index("HELPER = helper()")
    assert text.index("import pandas as pd") < text.index("import business_logic")
    compile(text, str(existing), "exec")
