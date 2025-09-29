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

# This script helps new Apache committers set up their GPG keys for releases.
# It guides you through creating a new key, exports the public key, and
# provides instructions on how to add it to your project's KEYS file.

echo "========================================================"
echo "      Apache GPG Key Setup Script"
echo "========================================================"
echo " "
echo "Step 1: Generating a new GPG key."
echo " "
echo "Please be aware of Apache's best practices for GPG keys:"
echo "- **Key Type:** Select **(1) RSA and RSA**."
echo "- **Key Size:** Enter **4096**."
echo "- **Email Address:** Use your official **@apache.org** email address."
echo "- **Passphrase:** Use a strong, secure passphrase."
echo " "
read -p "Press [Enter] to start the GPG key generation..."

# Generate a new GPG key
# The --batch and --passphrase-fd 0 options are used for automation,
# but the script will still require interactive input.
gpg --full-gen-key

if [ $? -ne 0 ]; then
  echo "Error: GPG key generation failed. Please check your GPG installation."
  exit 1
fi

echo " "
echo "Step 2: Listing your GPG keys to find the new key ID."
echo "Your new key is listed under 'pub' with a string of 8 or 16 characters after the '/'."

# List all GPG keys
gpg --list-keys

echo " "
read -p "Please copy and paste your new key ID here (e.g., A1B2C3D4 or 1234ABCD5678EF01): " KEY_ID

if [ -z "$KEY_ID" ]; then
  echo "Error: Key ID cannot be empty. Exiting."
  exit 1
fi

echo " "
echo "Step 3: Exporting your public key to a file."

# Export the public key in ASCII armored format
gpg --armor --export "$KEY_ID" > "$KEY_ID.asc"

if [ $? -ne 0 ]; then
  echo "Error: Public key export failed. Please ensure the Key ID is correct."
  rm -f "$KEY_ID.asc"
  exit 1
fi

echo "Checking out dist repository to update KEYS file"
svn checkout --depth immediates https://dist.apache.org/repos/dist dist
cd dist/release
svn checkout https://dist.apache.org/repos/dist/release/incubator/hamilton incubator/hamilton

cd ../../
gpg --list-keys "$KEY_ID" >> dist/release/incubator/hamilton/KEYS
cat "$KEY_ID.asc" >> dist/release/incubator/hamilton/KEYS
cd dist/release/incubator/hamilton

echo " "
echo "========================================================"
echo "      Setup Complete!"
echo "========================================================"
echo "Your public key has been saved to: $KEY_ID.asc"
echo " "
echo "NEXT STEPS (VERY IMPORTANT):"
echo "1. Please inspect the KEYS file to ensure the new key is added correctly. It should be in the current directory."
echo "2. If all good run: svn update KEYS && svn commit -m \"Adds new key $KEY_ID for YOUR NAME\""
echo "3. Inform the mailing list that you've updated the KEYS file."
echo "   The updated KEYS file is essential for others to verify your release signatures."
echo " "
