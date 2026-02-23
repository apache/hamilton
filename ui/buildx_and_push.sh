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

set -e

export DOCKER_CLI_EXPERIMENTAL=enabled

# Apache-compliant Docker image naming
# TODO: Update to apache/hamilton-* namespace when project graduates from incubator
FRONTEND_IMAGE="apache/hamilton-ui-frontend"
BACKEND_IMAGE="apache/hamilton-ui-backend"

# Define common platforms/architectures
PLATFORMS="linux/amd64,linux/arm64"

# Usage information
usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Apache-compliant Docker image builder for Hamilton UI.

OPTIONS:
    --version VERSION       Specify version to build (required)
    --type TYPE            Build type: release, rc, snapshot, nightly (default: release)
    --rc-number NUM        Release candidate number (required if --type=rc)
    --tag-latest           Tag as :latest (ONLY for approved releases)
    --help                 Show this help message

EXAMPLES:
    # Official release (requires PMC approval)
    $0 --version 0.0.17 --type release --tag-latest

    # Release candidate
    $0 --version 0.0.18 --type rc --rc-number 1

    # Snapshot/development build
    $0 --version 0.0.18 --type snapshot

    # Nightly build
    $0 --version 0.0.18 --type nightly

IMPORTANT:
    - :latest tag should ONLY be used for PMC-approved releases
    - Release candidates must be tagged as VERSION-rcN
    - Snapshots must be tagged as VERSION-SNAPSHOT
    - Nightly builds must be tagged as VERSION-nightly-YYYYMMDD
EOF
    exit 1
}

# Check if Docker Buildx is installed
check_buildx_installed() {
    if ! docker buildx version &> /dev/null; then
        echo "Error: Docker Buildx is not installed. Please install Docker Buildx to proceed."
        exit 1
    fi
}

# Parse command line arguments
VERSION=""
BUILD_TYPE="release"
RC_NUMBER=""
TAG_LATEST=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --version)
            VERSION="$2"
            shift 2
            ;;
        --type)
            BUILD_TYPE="$2"
            shift 2
            ;;
        --rc-number)
            RC_NUMBER="$2"
            shift 2
            ;;
        --tag-latest)
            TAG_LATEST=true
            shift
            ;;
        --help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Validate required arguments
if [ -z "$VERSION" ]; then
    echo "Error: --version is required"
    usage
fi

# Validate build type
case $BUILD_TYPE in
    release|rc|snapshot|nightly)
        ;;
    *)
        echo "Error: Invalid build type '$BUILD_TYPE'. Must be: release, rc, snapshot, or nightly"
        exit 1
        ;;
esac

# Validate RC number for release candidates
if [ "$BUILD_TYPE" = "rc" ] && [ -z "$RC_NUMBER" ]; then
    echo "Error: --rc-number is required for release candidate builds"
    exit 1
fi

# Warn if trying to tag :latest for non-release builds
if [ "$TAG_LATEST" = true ] && [ "$BUILD_TYPE" != "release" ]; then
    echo "ERROR: :latest tag can ONLY be used for release builds (--type=release)"
    echo "This is required by Apache Software Foundation policy."
    echo "Release candidates, snapshots, and nightly builds must NOT use :latest tag."
    exit 1
fi

# Build version tag based on build type
case $BUILD_TYPE in
    release)
        VERSION_TAG="$VERSION"
        ;;
    rc)
        VERSION_TAG="${VERSION}-rc${RC_NUMBER}"
        ;;
    snapshot)
        VERSION_TAG="${VERSION}-SNAPSHOT"
        ;;
    nightly)
        DATE=$(date +%Y%m%d)
        VERSION_TAG="${VERSION}-nightly-${DATE}"
        ;;
esac

echo "=========================================="
echo "Apache Hamilton UI Docker Build"
echo "=========================================="
echo "Version Tag: $VERSION_TAG"
echo "Build Type: $BUILD_TYPE"
echo "Tag :latest: $TAG_LATEST"
echo "Platforms: $PLATFORMS"
echo "Backend Image: $BACKEND_IMAGE:$VERSION_TAG"
echo "Frontend Image: $FRONTEND_IMAGE:$VERSION_TAG"
echo "=========================================="

# Safety check for :latest tag
if [ "$TAG_LATEST" = true ]; then
    echo ""
    echo "WARNING: You are about to tag this build as :latest"
    echo "This should ONLY be done for PMC-approved releases."
    echo ""
    read -p "Has this release been approved by the Apache Hamilton PMC? (yes/no): " APPROVED

    if [ "$APPROVED" != "yes" ]; then
        echo "Aborting. Release must be approved before tagging as :latest"
        exit 1
    fi
fi

# Check prerequisites
check_buildx_installed

# Check if Buildx is already enabled; create a builder instance if not
docker buildx inspect hamilton-builder > /dev/null 2>&1 || \
    docker buildx create --use --name hamilton-builder

cd "$(dirname "$0")" # cd into the directory where this script is present (i.e. ui)

# Build backend image
echo ""
echo "Building backend image..."
if [ "$TAG_LATEST" = true ]; then
    docker buildx build --platform $PLATFORMS \
        -t $BACKEND_IMAGE:$VERSION_TAG \
        -t $BACKEND_IMAGE:latest \
        --push -f backend/Dockerfile.backend-prod backend/
else
    docker buildx build --platform $PLATFORMS \
        -t $BACKEND_IMAGE:$VERSION_TAG \
        --push -f backend/Dockerfile.backend-prod backend/
fi

# Build frontend image
echo ""
echo "Building frontend image..."
if [ "$TAG_LATEST" = true ]; then
    docker buildx build --platform $PLATFORMS \
        -t $FRONTEND_IMAGE:$VERSION_TAG \
        -t $FRONTEND_IMAGE:latest \
        --push -f frontend/Dockerfile.frontend-prod frontend/ \
        --build-arg REACT_APP_AUTH_MODE=local \
        --build-arg REACT_APP_USE_POSTHOG=false
else
    docker buildx build --platform $PLATFORMS \
        -t $FRONTEND_IMAGE:$VERSION_TAG \
        --push -f frontend/Dockerfile.frontend-prod frontend/ \
        --build-arg REACT_APP_AUTH_MODE=local \
        --build-arg REACT_APP_USE_POSTHOG=false
fi

echo ""
echo "=========================================="
echo "Build complete!"
echo "=========================================="
echo "Backend: $BACKEND_IMAGE:$VERSION_TAG"
echo "Frontend: $FRONTEND_IMAGE:$VERSION_TAG"
if [ "$TAG_LATEST" = true ]; then
    echo ""
    echo "Also tagged as :latest (approved release)"
fi
echo "=========================================="
