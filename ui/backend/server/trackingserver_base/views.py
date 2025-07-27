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

# this file is not needed and superseded by api.py
# # Create your views here.
# from django.http import HttpResponse, JsonResponse
# from django.shortcuts import render
#
# # from ninja import NinjaAPI
# from ninja import Router
#
# router = Router()
#
#
# @router.get("")
# def index(request):
#     return HttpResponse("Hello, world. You're at the gitserver index.")
#
# @router.get("code")
# def code(request):
#     data = {"repo": "foobar", "files": "Finland", "is_active": True, "count": 28}
#     # return JsonResponse(data)
#     return data
import os

from django.conf import settings
from django.http import HttpResponse


def serve_frontend(request):
    """
    Serves the index.html file or other static files directly from the build folder.
    """
    path = request.path.strip("/")
    if not path:
        path = "index.html"
    file_path = os.path.join(settings.BASE_DIR, "build", path)
    if os.path.exists(file_path):
        with open(file_path, "rb") as file:
            return HttpResponse(file.read(), content_type="text/html")
    return HttpResponse("File not found", status=404)
