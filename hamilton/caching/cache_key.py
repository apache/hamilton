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

import base64
import zlib
from typing import Dict, Mapping


def _compress_string(string: str) -> str:
    return base64.b64encode(zlib.compress(string.encode(), level=3)).decode()


def _decompress_string(string: str) -> str:
    return zlib.decompress(base64.b64decode(string.encode())).decode()


def _encode_str_dict(d: Mapping) -> str:
    interleaved_tuple = tuple(item for pair in sorted(d.items()) for item in pair)
    return ",".join(interleaved_tuple)


def _decode_str_dict(s: str) -> Mapping:
    interleaved_tuple = tuple(s.split(","))
    d = {}
    for i in range(0, len(interleaved_tuple), 2):
        d[interleaved_tuple[i]] = interleaved_tuple[i + 1]
    return d


def decode_key(cache_key: str) -> dict:
    node_name, _, code_and_data_string = cache_key.partition("-")
    code_version, _, dep_encoded = code_and_data_string.partition("-")
    data_stringified = _decompress_string(dep_encoded)

    if data_stringified == "<none>":
        dependencies_data_versions = {}
    else:
        dependencies_data_versions = _decode_str_dict(data_stringified)
    return dict(
        node_name=node_name,
        code_version=code_version,
        dependencies_data_versions=dependencies_data_versions,
    )


def create_cache_key(
    node_name: str, code_version: str, dependencies_data_versions: Dict[str, str]
) -> str:
    if len(dependencies_data_versions.keys()) > 0:
        dependencies_stringified = _encode_str_dict(dependencies_data_versions)
    else:
        dependencies_stringified = "<none>"

    safe_node_name = "".join(c for c in node_name if c.isalnum() or c in ("_",)).rstrip()

    return f"{safe_node_name}-{code_version}-{_compress_string(dependencies_stringified)}"
