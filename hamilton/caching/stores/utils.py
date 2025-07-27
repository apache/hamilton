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


def get_directory_size(directory: str) -> float:
    """Get the size of the content of a directory in bytes."""
    total_size = 0
    for p in pathlib.Path(directory).rglob("*"):
        if p.is_file():
            total_size += p.stat().st_size

    return total_size


def readable_bytes_size(n_bytes: float) -> str:
    """Convert a number of bytes to a human-readable unit."""
    labels = ["B", "KB", "MB", "GB", "TB"]
    exponent = 0

    while n_bytes > 1024.0:
        n_bytes /= 1024.0
        exponent += 1

    return f"{n_bytes:.2f} {labels[exponent]}"
