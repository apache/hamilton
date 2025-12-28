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

import boto3


def main():
    """Simple script to download data files locally"""

    BUCKET = "hamilton-pdl-demo"

    s3 = boto3.client("s3")

    print("Starting data download. It should take a total of ~3min.")
    print("Downloading `pdl_data.json`")
    s3.download_file(Bucket=BUCKET, Key="pdl_data.json", Filename="data/pdl_data.json")
    print("Downloading `stock_data.json`")
    s3.download_file(Bucket=BUCKET, Key="stock_data.json", Filename="data/stock_data.json")

    print("Data successfully downloaded.")


if __name__ == "__main__":
    main()
