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

import pathlib
import sys

import plotly.graph_objects as go
import pytest

from hamilton.io.utils import FILE_METADATA
from hamilton.plugins.plotly_extensions import PlotlyInteractiveWriter, PlotlyStaticWriter


@pytest.fixture
def figure():
    yield go.Figure(data=go.Scatter(x=[1, 2, 3, 4, 5], y=[10, 14, 18, 24, 30], mode="markers"))


@pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="Windows does not currently support plotly static image export",
)
def test_plotly_static_writer(figure: go.Figure, tmp_path: pathlib.Path) -> None:
    file_path = tmp_path / "figure.png"

    writer = PlotlyStaticWriter(path=file_path)
    metadata = writer.save_data(figure)

    assert file_path.exists()
    assert metadata[FILE_METADATA]["path"] == str(file_path)


def test_plotly_interactive_writer(figure: go.Figure, tmp_path: pathlib.Path) -> None:
    file_path = tmp_path / "figure.html"

    writer = PlotlyInteractiveWriter(path=file_path, auto_open=False)
    metadata = writer.save_data(figure)

    assert file_path.exists()
    assert metadata[FILE_METADATA]["path"] == str(file_path)
