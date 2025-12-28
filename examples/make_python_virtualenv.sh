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

# This script is used to create separate python virtual environments for individual examples
# A python virtual environment named "hamilton-env" is created in every directory containing requirements.txt file

# USAGE (inside hamilton/examples directory): bash make_python_virtualenv.sh

# Get a list of all the folders containing "requirements.txt" file
export folders=$(find . -name 'requirements.txt' -printf '%h\n');

echo "List of all folders containing requirements.txt";
echo $folders;

for folder in $folders; do
    # Change directory
    pushd $folder;

    # Remove previous hamilton python virtual environment
    rm -rf ./hamilton-env;

    # Create a new python virtual environment named "hamilton"
    python3 -m venv hamilton-env;

    # Change to that virtual environment
    source ./hamilton-env/bin/activate;

    # Install the requirements listed in hamilton virtual environment
    pip install -r requirements.txt;

    # Deactivate the virtual environment
    deactivate;

    # Return to the examples folder
    popd;
done
