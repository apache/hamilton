#!/usr/bin/env bash
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

# Create the final (non-RC) release tag(s) for a voted Apache Hamilton release.
#
# During the RC build, apache_release_helper.py creates a tag like
#   <package>-v<version>-incubating-RC<rc>
# pointing at the commit the artifacts were built from. That RC commit often
# lives only on the release branch. After the vote passes and the release
# branch is squash-merged to main, the canonical release should be tagged
# with a clean, RC-less name on the merge commit so:
#   - the tag is reachable from main
#   - GitHub release pages / archives resolve to a sensible name
#     (ASF mentors flag RC-suffixed tags as poor release names)
#
# This script creates (and optionally pushes) an annotated tag
#   <package>-v<version>-incubating
# on a target commit (default: current HEAD, expected to be main at the
# squash-merge commit). The original -RC tag is left intact as the record
# of exactly what was voted on.
#
# Usage:
#   scripts/tag_release.sh [--commit <sha>] [--remote <name>] [--push] \
#       <package> <version>
#
#   package : one of apache-hamilton, apache-hamilton-sdk,
#             apache-hamilton-lsp, apache-hamilton-ui, apache-hamilton-contrib
#   version : e.g. 0.9.0
#
# Examples:
#   # dry: create the tag locally on current HEAD, don't push
#   scripts/tag_release.sh apache-hamilton-sdk 0.9.0
#
#   # create on a specific commit and push to origin
#   scripts/tag_release.sh --commit 1a2b3c4 --push apache-hamilton-sdk 0.9.0

set -eu

REMOTE="origin"
COMMIT="HEAD"
PUSH="false"

while [ $# -gt 0 ]; do
  case "$1" in
    --commit) COMMIT="$2"; shift 2 ;;
    --remote) REMOTE="$2"; shift 2 ;;
    --push)   PUSH="true"; shift ;;
    --) shift; break ;;
    -*) echo "Unknown option: $1" >&2; exit 1 ;;
    *) break ;;
  esac
done

if [ $# -ne 2 ]; then
  echo "Usage: $0 [--commit <sha>] [--remote <name>] [--push] <package> <version>" >&2
  echo "  package: apache-hamilton | apache-hamilton-sdk | apache-hamilton-lsp | apache-hamilton-ui | apache-hamilton-contrib" >&2
  exit 1
fi

PACKAGE="$1"
VERSION="$2"

case "$PACKAGE" in
  apache-hamilton|apache-hamilton-sdk|apache-hamilton-lsp|apache-hamilton-ui|apache-hamilton-contrib) ;;
  *) echo "ERROR: unknown package '$PACKAGE'" >&2; exit 1 ;;
esac

TAG="${PACKAGE}-v${VERSION}-incubating"
RC_TAG_GLOB="${PACKAGE}-v${VERSION}-incubating-RC*"

# Resolve target commit
TARGET_SHA="$(git rev-parse --verify "${COMMIT}^{commit}")"

echo "Package:      ${PACKAGE}"
echo "Version:      ${VERSION}"
echo "Release tag:  ${TAG}"
echo "Target commit ${TARGET_SHA}"
echo

# Sanity: warn if the target commit is not on main
if git rev-parse --verify main >/dev/null 2>&1; then
  if git merge-base --is-ancestor "${TARGET_SHA}" main; then
    echo "  OK: target commit is reachable from main."
  else
    echo "  WARNING: target commit is NOT reachable from 'main'."
    echo "           The final release tag should point at the squash-merge"
    echo "           commit on main. Continue only if you know what you're doing."
  fi
fi

# Show the RC tag(s) for reference (what was voted on)
RC_TAGS="$(git tag -l "${RC_TAG_GLOB}" || true)"
if [ -n "${RC_TAGS}" ]; then
  echo "  RC tag(s) for this release (kept as-is):"
  for t in ${RC_TAGS}; do
    echo "    ${t} -> $(git rev-list -n1 "$t")"
  done
fi
echo

# Refuse to clobber an existing final tag
if git rev-parse --verify "refs/tags/${TAG}" >/dev/null 2>&1; then
  echo "ERROR: tag '${TAG}' already exists (-> $(git rev-list -n1 "${TAG}"))." >&2
  echo "       Delete it first if you intend to move it: git tag -d ${TAG}" >&2
  exit 1
fi

# Create the annotated tag
git tag -a "${TAG}" "${TARGET_SHA}" -m "Apache ${PACKAGE} ${VERSION}-incubating"
echo "Created annotated tag ${TAG} -> ${TARGET_SHA}"

if [ "${PUSH}" = "true" ]; then
  echo "Pushing ${TAG} to ${REMOTE}..."
  git push "${REMOTE}" "refs/tags/${TAG}"
  echo "Pushed."
else
  echo
  echo "Tag created locally. To push:"
  echo "  git push ${REMOTE} refs/tags/${TAG}"
fi
