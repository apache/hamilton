#!/usr/bin/env python3
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

"""
Test script to validate Hamilton UI tracking functionality.

This script creates a simple Hamilton DAG, executes it with tracking enabled,
and sends the execution data to the Hamilton UI server.

Usage:
    # Start the UI server first (in another terminal):
    hamilton ui

    # Then run this script:
    python ui/test_tracking.py
"""

import sys

import pandas as pd

from hamilton import driver
from hamilton_sdk import adapters

print("=" * 60)
print("Hamilton UI Tracking Test")
print("=" * 60)
print()


# Define simple Hamilton functions
def input_data() -> pd.DataFrame:
    """Create sample input data."""
    return pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [2, 4, 6, 8, 10]})


def x_squared(input_data: pd.DataFrame) -> pd.Series:
    """Square the x column."""
    return input_data["x"] ** 2


def y_doubled(input_data: pd.DataFrame) -> pd.Series:
    """Double the y column."""
    return input_data["y"] * 2


def sum_all(x_squared: pd.Series, y_doubled: pd.Series) -> float:
    """Sum all values."""
    return x_squared.sum() + y_doubled.sum()


def average(sum_all: float, input_data: pd.DataFrame) -> float:
    """Calculate average."""
    total_elements = len(input_data) * 2  # x and y columns
    return sum_all / total_elements


print("📊 Creating Hamilton DAG...")
print()

# Create tracker adapter
tracker = adapters.HamiltonTracker(
    project_id=1,  # Using default project ID
    username="test-user",
    dag_name="test_tracking_dag",
    tags={"test": "mini-mode", "environment": "local"},
    hamilton_api_url="http://localhost:8241",
    hamilton_ui_url="http://localhost:8241",
    api_key="test-key",  # Using permissive mode key
)

# Build driver with tracker
dr = driver.Builder().with_modules(sys.modules[__name__]).with_adapters(tracker).build()

print("✅ DAG created with tracker adapter")
print("   Project ID: 1")
print("   DAG Name: test_tracking_dag")
print("   API URL: http://localhost:8241")
print()

# Visualize the DAG
print("📈 DAG Structure:")
dr.display_all_functions()
print()

# Execute the DAG
print("▶️  Executing DAG...")
result = dr.execute(["average", "sum_all", "x_squared", "y_doubled"])

print()
print("=" * 60)
print("Results:")
print("=" * 60)
for key, value in result.items():
    if isinstance(value, pd.Series):
        print(f"\n{key}:")
        print(value)
    else:
        print(f"{key}: {value}")

print()
print("=" * 60)
print("✅ Execution Complete!")
print("=" * 60)
print()
print("🌐 View results in the UI:")
print("   http://localhost:8241")
print()
print("💡 Tips:")
print("   - Check the 'Projects' page to see your test project")
print("   - Click on the project to see execution runs")
print("   - Explore the DAG visualization and execution details")
print()
