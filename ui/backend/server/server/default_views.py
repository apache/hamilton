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

from django.http import HttpResponse


def root_index(request) -> HttpResponse:
    """Showing how we can render some HTML from django."""
    return HttpResponse(
        """
    <html>
      <header></header>
      <body>
        <h1><center>Welcome to the backend server!</center></h1>
        <p><center>Did you mean to visit the <a href="http://localhost:8242">frontend</a>? Note this sometimes takes a bit of time to start up.</center> </p>
      </body>
    </html>
    """
    )
