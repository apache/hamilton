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

import matplotlib
import matplotlib.pyplot as plt
import pytest

from hamilton.io.utils import FILE_METADATA
from hamilton.plugins.matplotlib_extensions import MatplotlibWriter


def figure1():
    fig = plt.figure()
    plt.scatter([0, 1, 3], [0, 2.2, 2])
    return fig


def figure2():
    fig, ax = plt.subplots()
    ax.scatter([0, 1, 3], [0, 2.2, 2])
    return fig


@pytest.mark.parametrize("figure", [figure1(), figure2()])
def test_plotly_static_writer(figure: matplotlib.figure.Figure, tmp_path: pathlib.Path) -> None:
    file_path = tmp_path / "figure.png"

    writer = MatplotlibWriter(path=file_path)
    metadata = writer.save_data(figure)

    assert file_path.exists()
    assert metadata[FILE_METADATA]["path"] == str(file_path)
