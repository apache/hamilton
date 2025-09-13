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

# --- START LICENSE (optional)
# --- END LICENSE
# --- START IMPORT SECTION
import logging

from hamilton import contrib

logger = logging.getLogger(__name__)

with contrib.catch_import_errors(__name__, __file__, logger):
    # non-hamilton imports go here
    pass

# hamilton imports go here; check for required version if need be.

# --- END IMPORT SECTION

# --- START HAMILTON DATAFLOW


# --- END HAMILTON DATAFLOW
# --- START MAIN CODE
if __name__ == "__main__":
    # Code to create an imaging showing on DAG workflow.
    # run as a script to test Hamilton's execution
    import __init__ as MODULE_NAME

    from hamilton import base, driver

    dr = driver.Driver(
        {},  # CONFIG: fill as appropriate
        MODULE_NAME,
        adapter=base.DefaultAdapter(),
    )
    # saves to current working directory creating dag.png.
    dr.display_all_functions("dag", {"format": "png", "view": False})
# --- END MAIN CODE
