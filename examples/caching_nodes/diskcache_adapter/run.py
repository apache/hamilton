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

import logging

import functions

from hamilton import driver
from hamilton.plugins import h_diskcache


def main():
    dr = (
        driver.Builder()
        .with_modules(functions)
        .with_adapters(h_diskcache.DiskCacheAdapter())
        .build()
    )
    results = dr.execute(["C"], inputs=dict(external=10))
    print(results)
    results = dr.execute(["C"], inputs=dict(external=10))
    print(results)


if __name__ == "__main__":
    logger = logging.getLogger("hamilton.plugins.h_diskcache")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    main()
