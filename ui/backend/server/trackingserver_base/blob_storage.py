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

import abc
import json
import logging
import os
import uuid
from typing import Optional

try:
    import aiobotocore.session
except ImportError:
    logging.info(
        "aiobotocore is not installed. Please install aiobotocore to use S3BlobStore -- "
        "if you're using the normal (local) blob store ignore this."
    )
import aiofiles
from django.conf import settings

""""File for managing blob stores. TODO -- use more of django's configuration/settings to do this.
I just want to get something done quickly, and we can easily wire in the settings later.
"""


class BlobStore(abc.ABC):
    """Abstract base class for blob stores"""

    @abc.abstractmethod
    async def write_obj(self, namespace: str, contents: dict) -> str:
        """Serializes/writes an object to the blob store

        @param contents: Contents of the object (dictionary)
        @return: The URL of the object
        """

    @abc.abstractmethod
    async def read_obj(self, url: str) -> dict:
        """Reads an object from the blob store

        @param url: URL of the object
        @return: The deserialized object
        """

    @classmethod
    @abc.abstractmethod
    def store(cls) -> str:
        """Gets the store name, E.G. s3. This allow these classes to register themselves,
        in case we have multiple stores present at once that we need to read/write from."""
        pass

    @classmethod
    def create(cls):
        """Creates a blob store from the environment. This is useful for configuring
        in case we need to change the s3 bucket, etc...
        """
        return cls(**settings.HAMILTON_BLOB_STORE_PARAMS)


class LocalTextFileBlobStore(BlobStore):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    async def write_obj(self, namespace: str, contents: dict) -> str:
        # Generate a unique filename for the new blob
        filename = str(uuid.uuid4()) + ".json"
        filepath = os.path.join(self.base_dir, namespace, filename)
        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath))

        # Serialize dictionary to JSON and write to file
        async with aiofiles.open(filepath, "w") as f:
            await f.write(json.dumps(contents))

        return filepath  # Return local file URL

    async def read_obj(self, url: str) -> dict:
        # Read file and deserialize JSON to dictionary
        async with aiofiles.open(url, "r") as f:
            contents_str = await f.read()
            contents = json.loads(contents_str)

        return contents

    @classmethod
    def store(cls) -> str:
        return "local"


class S3BlobStore(BlobStore):
    def __init__(
        self,
        bucket_name: str,
        global_prefix: str,
        region_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
    ):
        self.bucket_name = bucket_name
        self.region_name = region_name
        self.global_prefix = global_prefix
        if endpoint_url is None and region_name is None:
            raise ValueError("Must provide either region_name or endpoint_url")
        self.endpoint_url = endpoint_url
        self.region_name = region_name

    @property
    def client(self):
        session = aiobotocore.session.get_session()
        kwargs = {}
        if self.region_name is not None:
            kwargs["region_name"] = self.region_name
        if self.endpoint_url is not None:
            kwargs["endpoint_url"] = self.endpoint_url
        return session.create_client("s3", **kwargs)

    async def write_obj(self, namespace: str, contents: dict) -> str:
        # Generate a unique filename for the new blob
        filename = str(uuid.uuid4()) + ".json"
        key = f"{self.global_prefix}/{namespace}/{filename}"

        serialized_contents = json.dumps(contents)

        async with self.client as client:
            await client.put_object(Bucket=self.bucket_name, Key=key, Body=serialized_contents)

        # Construct the object URL using s3:// scheme
        url = f"s3://{self.bucket_name}/{key}"
        return url

    async def read_obj(self, url: str) -> dict:
        # Extract bucket and key from the provided s3:// URL
        if not url.startswith("s3://"):
            raise ValueError("Invalid S3 URL format")
        parts = url[len("s3://") :].split("/", 1)
        if len(parts) != 2:
            raise ValueError("Invalid S3 URL format")
        bucket, key = parts

        async with self.client as client:
            response = await client.get_object(Bucket=bucket, Key=key)
            async with response["Body"] as stream:
                contents_str = await stream.read()
                contents = json.loads(contents_str)

        return contents

    @classmethod
    def store(cls) -> str:
        return "s3"


def get_blob_store() -> BlobStore:
    blob_store_classes = {
        "local": LocalTextFileBlobStore,
        "s3": S3BlobStore,
    }
    which_blob_store = settings.HAMILTON_BLOB_STORE
    if which_blob_store not in blob_store_classes:
        raise ValueError(f"Invalid blob store {which_blob_store}")
    return blob_store_classes[which_blob_store].create()
