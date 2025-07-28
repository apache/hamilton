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

from hamilton_lsp.server import HamiltonLanguageServer, register_server_features


# TODO use argparse to allow
#   - io, tcp, websocket modes
#   - select host and port
def main():
    language_server = HamiltonLanguageServer()
    language_server = register_server_features(language_server)

    language_server.start_io()
    # tcp is good for debugging
    # server.start_tcp("127.0.0.1", 8087)


if __name__ == "__main__":
    main()
