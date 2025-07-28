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

from hamilton import registry


@pytest.mark.parametrize("entrypoint", ["config_disable_autoload", "config_enable_autoload"])
def test_command_entrypoints_arent_renamed(entrypoint: str):
    """Ensures that functions associated with an entrypoint in
    pyproject.toml aren't renamed.

    This doesn't prevent the entrypoints from being renamed
    """
    assert hasattr(registry, entrypoint)
