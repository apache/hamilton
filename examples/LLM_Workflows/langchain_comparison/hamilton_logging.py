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

# run.py
import hamilton_anthropic
from hamilton import driver, lifecycle

dr = (
    driver.Builder()
    .with_modules(hamilton_anthropic)
    .with_config({"provider": "anthropic"})
    # we just need to add this line to get things printing
    # to the console; see DAGWorks for a more off-the-shelf
    # solution.
    .with_adapters(lifecycle.PrintLn(verbosity=2))
    .build()
)
print(dr.execute(["joke_response"], inputs={"topic": "ice cream"}))
