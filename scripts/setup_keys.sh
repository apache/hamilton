#!/bin/bash

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

echo " "
echo "========================================================"
echo "      Setup Complete!"
echo "========================================================"
echo "Your public key has been saved to: $KEY_ID.asc"
echo " "
echo "NEXT STEPS (VERY IMPORTANT):"
echo "1. Find your project's KEYS file in its SVN repository."
echo "   e.g., svn checkout https://dist.apache.org/repos/dist/release/incubator/your-podling/KEYS"
echo "2. Append the contents of $KEY_ID.asc to the KEYS file."
echo "3. Commit and push the updated KEYS file to the SVN repository."
echo "4. Inform the mailing list that you've updated the KEYS file."
echo "   The updated KEYS file is essential for others to verify your release signatures."
echo " "
