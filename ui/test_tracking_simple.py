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
Simple test script to validate Hamilton UI tracking.

This script will:
1. Check if the Hamilton UI is running
2. Guide you through creating a project if needed
3. Run a simple DAG with tracking enabled
4. Display the results and links to view in the UI

Usage:
    # Make sure the UI server is running:
    hamilton ui

    # Then run this script (optionally with a user name for API calls):
    python ui/test_tracking_simple.py
    python ui/test_tracking_simple.py --user my-username
    python ui/test_tracking_simple.py --dag dataframe   # DataFrame-based DAG
"""

import argparse
import sys

import pandas as pd
import requests

from hamilton import driver


def _parse_args():
    parser = argparse.ArgumentParser(description="Hamilton UI Tracking Test")
    parser.add_argument(
        "--user",
        default="test-user",
        help="User name to use for API calls (x-api-user and tracker username)",
    )
    parser.add_argument(
        "--dag",
        choices=["simple", "dataframe"],
        default="simple",
        help="DAG to run: 'simple' (default) or 'dataframe' (DataFrame-based)",
    )
    return parser.parse_args()


args = _parse_args()
USER_NAME = args.user

print("=" * 70)
print("Hamilton UI Tracking Test")
print("=" * 70)
print(f"User: {USER_NAME}")
print()

# Step 1: Check if UI is running
print("🔍 Checking Hamilton UI connection...")
try:
    response = requests.get("http://localhost:8241/", timeout=5)
    if response.status_code == 200:
        print("✅ Hamilton UI is running at http://localhost:8241")
    else:
        print(f"⚠️  Unexpected response: {response.status_code}")
except requests.exceptions.RequestException as e:
    print("❌ Cannot connect to Hamilton UI at http://localhost:8241")
    print(f"   Error: {e}")
    print()
    print("Please start the Hamilton UI server first:")
    print("  hamilton ui")
    sys.exit(1)

print()

# Step 2: Check for projects
print("📋 Checking for existing projects...")
try:
    response = requests.get(
        "http://localhost:8241/api/v1/projects",
        headers={"x-api-user": USER_NAME, "x-api-key": "test-key"},
        timeout=5,
    )
    projects = response.json()

    if not projects:
        print("⚠️  No projects found.")
        print()
        print("   The user name must match the one used in the UI; otherwise no")
        print("   projects are returned for this user. (Current user: --user " + USER_NAME + ")")
        print()
        print("📝 Please create a project in the UI first:")
        print()
        print("   1. Open: http://localhost:8241/dashboard/projects")
        print("   2. Click 'Create Project'")
        print("   3. Fill in:")
        print("      - Name: Test Project")
        print("      - Description: Testing Hamilton tracking")
        print("      - Visibility: Public")
        print("   4. Note the Project ID (should be 1)")
        print()
        print("Then run this script again (with the same user name if needed).")
        print()

        # Try to open browser
        try:
            import webbrowser

            webbrowser.open("http://localhost:8241/dashboard/projects")
            print("✅ Opened browser to create project")
        except Exception:
            pass

        sys.exit(0)
    else:
        print(f"✅ Found {len(projects)} project(s):")
        for proj in projects[:3]:  # Show first 3
            print(f"   - Project {proj['id']}: {proj['name']}")
        project_id = projects[0]["id"]
        print()
        print(f"📦 Using Project ID: {project_id}")

except Exception as e:
    print(f"❌ Error checking projects: {e}")
    sys.exit(1)

print()

# Step 3: Create and run a Hamilton DAG
if args.dag == "dataframe":
    DAG_OUTPUTS = ["average", "sum_all", "x_squared", "y_doubled"]
    DAG_NAME = "test_tracking_dag"
else:
    DAG_OUTPUTS = ["average_squared", "sum_squared"]
    DAG_NAME = "simple_test_dag"

print("🚀 Creating Hamilton DAG (" + args.dag + ")...")


# Define simple Hamilton functions inline
def input_numbers() -> pd.Series:
    """Generate input numbers."""
    return pd.Series([1, 2, 3, 4, 5])


def squared(input_numbers: pd.Series) -> pd.Series:
    """Square the numbers."""
    return input_numbers**2


def sum_squared(squared: pd.Series) -> float:
    """Sum of squared numbers."""
    return squared.sum()


def average_squared(sum_squared: float, input_numbers: pd.Series) -> float:
    """Average of squared numbers."""
    return sum_squared / len(input_numbers)


# DataFrame-based DAG (--dag dataframe)
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


# Build driver WITHOUT tracking first (to test basic functionality)
print("   Building DAG...")
dr = driver.Builder().with_modules(sys.modules[__name__]).build()

print("   DAG created successfully!")
if args.dag == "dataframe":
    print()
    print("📈 DAG structure:")
    dr.display_all_functions()
print()

# Step 4: Execute without tracking
print("▶️  Executing DAG (without tracking)...")
result = dr.execute(DAG_OUTPUTS)

print()
print("Results:")
if args.dag == "dataframe":
    for key, value in result.items():
        if isinstance(value, pd.Series):
            print(f"  {key}:")
            print(value.to_string())
        else:
            print(f"  {key}: {value}")
else:
    print(f"  - sum_squared: {result['sum_squared']}")
    print(f"  - average_squared: {result['average_squared']}")
print()

# Step 5: Now execute WITH tracking
print("🔄 Executing with Hamilton UI tracking...")
try:
    from hamilton_sdk import adapters

    tracker = adapters.HamiltonTracker(
        project_id=project_id,
        username=USER_NAME,
        dag_name=DAG_NAME,
        tags={"test": "true", "environment": "local"},
        hamilton_api_url="http://localhost:8241",
        hamilton_ui_url="http://localhost:8241",
        api_key="test-key",
    )

    # Rebuild driver with tracker
    dr_tracked = driver.Builder().with_modules(sys.modules[__name__]).with_adapters(tracker).build()

    # Execute
    result_tracked = dr_tracked.execute(DAG_OUTPUTS)

    print("✅ Execution tracked successfully!")
    print()
    print("=" * 70)
    print("🎉 Success! View your results:")
    print("=" * 70)
    print()
    print(f"📊 Dashboard:  http://localhost:8241/dashboard/projects/{project_id}")
    print(f"📈 Project:    http://localhost:8241/dashboard/project/{project_id}")
    print()
    print("You should see:")
    print("  - Your DAG execution in the project dashboard")
    print("  - Execution details including node values")
    print("  - DAG visualization")
    print()

except ImportError:
    print("❌ hamilton-sdk not installed")
    print("   Install with: pip install apache-hamilton-sdk")
except Exception as e:
    print(f"❌ Error during tracked execution: {e}")
    import traceback

    traceback.print_exc()
