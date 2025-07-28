############################################################################
# Copyright(c) Open Law Library. All rights reserved.                      #
# See ThirdPartyNotices.txt in the project root for additional notices.    #
#                                                                          #
# Licensed under the Apache License, Version 2.0 (the "License")           #
# you may not use this file except in compliance with the License.         #
# You may obtain a copy of the License at                                  #
#                                                                          #
#     http: // www.apache.org/licenses/LICENSE-2.0                         #
#                                                                          #
# Unless required by applicable law or agreed to in writing, software      #
# distributed under the License is distributed on an "AS IS" BASIS,        #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. #
# See the License for the specific language governing permissions and      #
# limitations under the License.                                           #
############################################################################
import asyncio
import concurrent
import os
import threading

import pytest
from lsprotocol.types import EXIT, INITIALIZE, SHUTDOWN, ClientCapabilities, InitializeParams
from pygls.server import LanguageServer

RETRIES = 3
CALL_TIMEOUT = 3


def retry_stalled_init_fix_hack():
    if "DISABLE_TIMEOUT" in os.environ:
        return lambda f: f

    def decorator(func):
        def newfn(*args, **kwargs):
            attempt = 0
            while attempt < RETRIES:
                try:
                    return func(*args, **kwargs)
                except concurrent.futures._base.TimeoutError:
                    print(
                        "\n\nRetrying timeouted test server init " "%d of %d\n" % (attempt, RETRIES)
                    )
                    attempt += 1
            return func(*args, **kwargs)

        return newfn

    return decorator


class NativeClientServer:
    def __init__(self, LS=LanguageServer):
        # Client to Server pipe
        csr, csw = os.pipe()
        # Server to client pipe
        scr, scw = os.pipe()

        # Setup Server
        self.server = LS("server", "v1")
        self.server_thread = threading.Thread(
            name="Server Thread",
            target=self.server.start_io,
            args=(os.fdopen(csr, "rb"), os.fdopen(scw, "wb")),
        )
        self.server_thread.daemon = True

        # Setup client
        self.client = LS("client", "v1", asyncio.new_event_loop())
        self.client_thread = threading.Thread(
            name="Client Thread",
            target=self.client.start_io,
            args=(os.fdopen(scr, "rb"), os.fdopen(csw, "wb")),
        )
        self.client_thread.daemon = True

    @classmethod
    def decorate(cls):
        return pytest.mark.parametrize("client_server", [cls], indirect=True)

    def start(self):
        self.server_thread.start()
        self.server.thread_id = self.server_thread.ident
        self.client_thread.start()
        self.initialize()

    def stop(self):
        shutdown_response = self.client.lsp.send_request(SHUTDOWN).result()
        assert shutdown_response is None
        self.client.lsp.notify(EXIT)
        self.server_thread.join()
        self.client._stop_event.set()
        try:
            self.client.loop._signal_handlers.clear()  # HACK ?
        except AttributeError:
            pass
        self.client_thread.join()

    @retry_stalled_init_fix_hack()
    def initialize(self):
        timeout = None if "DISABLE_TIMEOUT" in os.environ else 1
        response = self.client.lsp.send_request(
            INITIALIZE,
            InitializeParams(
                process_id=12345, root_uri="file://", capabilities=ClientCapabilities()
            ),
        ).result(timeout=timeout)
        assert response.capabilities is not None

    def __iter__(self):
        yield self.client
        yield self.server
