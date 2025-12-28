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

import json
import subprocess


def main():
    # equivalent to using your command line with
    # `hamilton --verbose --json-out version ./module_v1.py`
    result = subprocess.run(
        ["hamilton", "--verbose", "--json-out", "version", "./module_v1.py"],
        stdout=subprocess.PIPE,
        text=True,
    )

    # `--json-out` outputs the result as JSON string on a single line
    # `--verbose` outputs intermediary commands on separate lines
    responses = []
    for line in result.stdout.splitlines():
        command_response = json.loads(line)
        responses.append(command_response)

    print(responses)


if __name__ == "__main__":
    main()
