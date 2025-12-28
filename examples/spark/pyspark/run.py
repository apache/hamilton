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

import dataflow
import map_transforms

from hamilton import driver


def main():
    dr = driver.Builder().with_modules(dataflow, map_transforms).build()
    dr.visualize_execution(["final_result"], "./out.png", {"format": "png"})
    final_result = dr.execute(["final_result"])
    print(final_result)


if __name__ == "__main__":
    main()
