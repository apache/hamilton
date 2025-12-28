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

import time


def node_5s() -> float:
    start = time.time()
    time.sleep(5)
    return time.time() - start


def add_1_to_previous(node_5s: float) -> float:
    start = time.time()
    time.sleep(1)
    return node_5s + (time.time() - start)


def node_1s_error(node_5s: float) -> float:
    time.sleep(1)
    raise ValueError("Does not break telemetry if executed through ray")
