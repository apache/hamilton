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

import dataclasses
import io
import json
import logging
from typing import Any, Collection, Dict, Type
from urllib import parse

import boto3
import requests
from PIL import Image

from hamilton.io.data_adapters import DataSaver
from hamilton.registry import register_adapter

client = boto3.client("s3")

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class JSONS3DataSaver(DataSaver):
    bucket: str
    key: str

    def save_data(self, data: dict) -> Dict[str, Any]:
        data = json.dumps(data).encode()
        client.put_object(Body=data, Bucket=self.bucket, Key=self.key)

    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [dict]

    @classmethod
    def name(cls) -> str:
        return "json_s3"


def _load_image(uri: str, format: str) -> Image:
    parsed = parse.urlparse(uri)
    if parsed.scheme.strip() == "":  # local file to upload
        with open(uri, "rb") as f:
            data = f.read()
    elif parsed.scheme.strip() in ("https", "http"):  # URL to copy over
        response = requests.get(uri)
        data = response.content
    image = Image.open(io.BytesIO(data))
    if format in ("jpeg", "jpg"):  # TODO -- add more formats if they don't support it
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
    return image


@dataclasses.dataclass
class ImageS3DataSaver(DataSaver):
    bucket: str
    key: str
    format: str
    # image_convert_params: Optional[Dict[str, Any]] = None

    def save_data(self, data: str) -> Dict[str, Any]:
        image = _load_image(data, self.format)
        in_mem_file = io.BytesIO()
        image.save(in_mem_file, format=self.format)
        in_mem_file.seek(0)
        client.put_object(Body=in_mem_file, Bucket=self.bucket, Key=self.key)
        return {"key": self.key, "bucket": self.bucket}

    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [str]  # URL or local path

    @classmethod
    def name(cls) -> str:
        return "image_s3"


@dataclasses.dataclass
class LocalImageSaver(DataSaver):
    path: str
    format: str
    # image_convert_params: Optional[Dict[str, Any]] = dataclasses.field(default_factory=dict)

    def save_data(self, data: str) -> Dict[str, Any]:
        image = _load_image(data, self.format)
        image.save(self.path, format=self.format)
        return {"path": self.path}

    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [str]  # URL or local path

    @classmethod
    def name(cls) -> str:
        return "image"


adapters = [JSONS3DataSaver, ImageS3DataSaver, LocalImageSaver]

for adapter in adapters:
    register_adapter(adapter)
