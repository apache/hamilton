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

# This script moves a release candidate from the dev repository to the release repository.

set -e

DRY_RUN=false
POSITIONAL_ARGS=()

while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run)
      DRY_RUN=true
      shift # past argument
      ;;
    *)
      POSITIONAL_ARGS+=("$1") # save positional arg
      shift # past argument
      ;;
  esac
done

set -- "${POSITIONAL_ARGS[@]}" # restore positional parameters

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 [--dry-run] <version> <rc_num>"
    echo "Example: $0 --dry-run 1.2.3 0"
    exit 1
fi

VERSION=$1
RC_NUM=$2
PROJECT_SHORT_NAME="hamilton"

# Source and destination URLs
SOURCE_URL="https://dist.apache.org/repos/dist/dev/incubator/${PROJECT_SHORT_NAME}/${VERSION}-RC${RC_NUM}"
DEST_URL="https://dist.apache.org/repos/dist/release/incubator/${PROJECT_SHORT_NAME}/${VERSION}"

if [ "$DRY_RUN" = true ]; then
    echo "Performing a dry run. No changes will be made."
else
    echo "This script will copy the release candidate from dev to release."
    echo "Source: ${SOURCE_URL}"
    echo "Destination: ${DEST_URL}"
    echo " "

    read -p "Are you sure you want to continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]
    then
        echo "Aborting."
        exit 1
    fi
fi

# Create the release directory
if [ "$DRY_RUN" = true ]; then
    echo "DRY RUN: svn mkdir --parents -m \"Creating directory for Apache ${PROJECT_SHORT_NAME} ${VERSION}\" \"${DEST_URL}\""
else
    svn mkdir --parents -m "Creating directory for Apache ${PROJECT_SHORT_NAME} ${VERSION}" "${DEST_URL}"
fi

# Get the list of files in the source directory
FILES=$(svn list "${SOURCE_URL}")

for FILE in $FILES; do
    if [[ "$FILE" == apache-hamilton* ]]; then
        SOURCE_FILE_URL="${SOURCE_URL}/${FILE}"
        DEST_FILE_URL="${DEST_URL}/${DEST_FILE_NAME}"

        if [ "$DRY_RUN" = true ]; then
            echo "DRY RUN: svn cp \"${SOURCE_FILE_URL}\" \"${DEST_FILE_URL}\" -m \"Promote Apache ${PROJECT_SHORT_NAME} ${VERSION}: ${DEST_FILE_NAME}\""
        else
            echo "Copying ${FILE} to ${DEST_FILE_URL}"
            svn cp "${SOURCE_FILE_URL}" "${DEST_FILE_URL}" -m "Promote Apache ${PROJECT_SHORT_NAME} ${VERSION}: ${DEST_FILE_NAME}"
        fi
    fi
done


if [ $? -eq 0 ]; then
    if [ "$DRY_RUN" = true ]; then
        echo "Dry run complete."
    else
        echo "Successfully copied release artifacts to: ${DEST_URL}"
        echo "The release is now live."
    fi
else
    echo "Error: Failed to copy release artifacts. Please check the SVN URLs and your credentials."
    exit 1
fi
