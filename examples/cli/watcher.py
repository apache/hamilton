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

import sys

from watchdog.events import FileModifiedEvent
from watchdog.observers import Observer
from watchdog.tricks import ShellCommandTrick

if __name__ == "__main__":
    cmd = sys.argv[1:]

    event_handler = ShellCommandTrick(
        shell_command=" ".join(cmd),
        patterns=["*.py"],
    )
    observer = Observer()
    observer.schedule(
        event_handler,
        path=".",
        event_filter=[FileModifiedEvent],
    )
    observer.start()
    print(f"Watching with {cmd}")
    try:
        while observer.is_alive():
            observer.join(1)
    finally:
        observer.stop()
        observer.join()
