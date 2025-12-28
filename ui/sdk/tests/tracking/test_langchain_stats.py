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

from hamilton_sdk.tracking import langchain_stats
from langchain_core import documents as lc_documents
from langchain_core import messages as lc_messages


def test_compute_stats_lc_docs():
    result = lc_documents.Document(page_content="Hello, World!", metadata={"source": "local_dir"})
    node_name = "test_node"
    node_tags = {}
    actual = langchain_stats.compute_stats_lc_docs(result, node_name, node_tags)
    expected = {
        "observability_schema_version": "0.0.2",
        "observability_type": "dict",
        "observability_value": {"content": "Hello, World!", "metadata": {"source": "local_dir"}},
    }
    assert actual == expected


def test_compute_stats_lc_messages():
    result = lc_messages.AIMessage(content="Hello, World!")
    node_name = "test_node"
    node_tags = {}
    actual = langchain_stats.compute_stats_lc_messages(result, node_name, node_tags)
    expected = {
        "observability_schema_version": "0.0.2",
        "observability_type": "dict",
        "observability_value": {"type": "ai", "value": "Hello, World!"},
    }
    assert actual == expected
