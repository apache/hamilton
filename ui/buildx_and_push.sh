#!/bin/bash
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


export DOCKER_CLI_EXPERIMENTAL=enabled

# check if Docker Buildx is installed
check_buildx_installed() {
    if ! docker buildx version &> /dev/null; then
        echo "Error: Docker Buildx is not installed. Please install Docker Buildx to proceed."
        exit 1
    fi
}

# check if jq is installed
check_jq_installed() {
    if ! jq --version &> /dev/null; then
        echo "Error: jq is not installed. Please install jq to proceed."
        exit 1
    fi
}

# fetches the latest version of sf-hamilton-ui from PyPI
get_latest_version() {
    response=$(curl -s https://pypi.org/pypi/sf-hamilton-ui/json)

    # check if curl succeeded and the response is not empty
    if [ $? -ne 0 ] || [ -z "$response" ]; then
        echo "Error: Failed to fetch data from PyPI. Please check your internet connection or the URL."
        exit 1
    fi

    # extract version using jq and handle potential errors
    version=$(echo "$response" | jq -r '.info.version')
    if [ "$version" == "null" ]; then
        echo "Error: Unable to extract version from the response."
        exit 1
    fi

    echo "$version"
}

# check if Docker Buildx and jq are installed
check_buildx_installed
check_jq_installed

VERSION=$(get_latest_version)

echo "Using sf-hamilton-ui version: $VERSION"

# check if Buildx is already enabled; create a builder instance if not
docker buildx inspect hamilton-builder > /dev/null 2>&1 || \
    docker buildx create --use --name hamilton-builder

FRONTEND_IMAGE="dagworks/ui-frontend"
BACKEND_IMAGE="dagworks/ui-backend"

# define common platforms/architectures
PLATFORMS="linux/amd64,linux/arm64"

cd "$(dirname "$0")" # cd into the directory where this script is present(i.e. ui)

docker buildx build --platform $PLATFORMS \
    -t $BACKEND_IMAGE:$VERSION -t $BACKEND_IMAGE:latest \
    --push -f backend/Dockerfile.backend-prod backend/

docker buildx build --platform $PLATFORMS \
    -t $FRONTEND_IMAGE:$VERSION -t $FRONTEND_IMAGE:latest \
    --push -f frontend/Dockerfile.frontend-prod frontend/ \
    --build-arg REACT_APP_AUTH_MODE=local \
    --build-arg REACT_APP_USE_POSTHOG=false \
