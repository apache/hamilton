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

from hamilton.plugins import h_ray


def test_parse_ray_remote_options_from_tags():
    tags = {
        f"{h_ray.RAY_REMOTE_TAG_NAMESPACE}.resources": '{"GPU": 1}',
        "another_tag": "another_value",
    }

    ray_options = h_ray.parse_ray_remote_options_from_tags(tags)

    assert len(ray_options) == 1
    assert "resources" in ray_options
    assert ray_options["resources"] == {"GPU": 1}
