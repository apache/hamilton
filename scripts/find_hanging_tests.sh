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

# Finds tests that prevent pytest from shutting down cleanly.
# Runs each test file individually with a timeout and reports any that hang.
#
# Usage:
#   ./find_hanging_tests.sh [timeout_seconds] [test_directory]
#   ./find_hanging_tests.sh              # defaults: 30s, tests/
#   ./find_hanging_tests.sh 60 tests/plugins

set -uo pipefail

TIMEOUT="${1:-30}"
TEST_DIR="${2:-tests/}"
HANGING=()
FAILED=()
PASSED=()

echo "Finding test files in ${TEST_DIR}..."
TEST_FILES=$(find "$TEST_DIR" -name "test_*.py" -type f | sort)
TOTAL=$(echo "$TEST_FILES" | wc -l | tr -d ' ')

echo "Found ${TOTAL} test files. Timeout per file: ${TIMEOUT}s"
echo ""

i=0
for test_file in $TEST_FILES; do
    i=$((i + 1))
    printf "[%3d/%d] %-70s " "$i" "$TOTAL" "$test_file"

    timeout "$TIMEOUT" uv run pytest "$test_file" -x -q 2>&1 > /tmp/hanging_test_output.txt
    exit_code=$?

    if [ $exit_code -eq 124 ]; then
        echo "HANG (killed after ${TIMEOUT}s)"
        HANGING+=("$test_file")
    elif [ $exit_code -ne 0 ]; then
        echo "FAIL (exit $exit_code)"
        FAILED+=("$test_file")
    else
        echo "OK"
        PASSED+=("$test_file")
    fi
done

echo ""
echo "================================================================"
echo "  Results"
echo "================================================================"
echo ""
echo "Passed: ${#PASSED[@]}"
echo "Failed: ${#FAILED[@]}"
echo "Hanging: ${#HANGING[@]}"

if [ ${#FAILED[@]} -gt 0 ]; then
    echo ""
    echo "--- Failed tests ---"
    for f in "${FAILED[@]}"; do
        echo "  $f"
    done
fi

if [ ${#HANGING[@]} -gt 0 ]; then
    echo ""
    echo "--- Hanging tests (did not exit within ${TIMEOUT}s) ---"
    for f in "${HANGING[@]}"; do
        echo "  $f"
    done
fi
