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

import argparse
import glob
import hashlib
import os
import shutil
import subprocess
import sys
from typing import Optional

# --- Configuration ---
# You need to fill these in for your project.
# The name of your project's short name (e.g., 'myproject').
PROJECT_SHORT_NAME = "hamilton"
# The file where you want to update the version number.
# Common options are setup.py, __init__.py, or a dedicated VERSION file.
# For example: "src/main/python/myproject/__init__.py"
VERSION_FILE = "hamilton/version.py"
# A regular expression pattern to find the version string in the VERSION_FILE.
# For example: r"__version__ = \"(\d+\.\d+\.\d+)\""
# The capture group (parentheses) should capture the version number.
VERSION_PATTERN = r"VERSION = \((\d+), (\d+), (\d+)(, \"(\w+)\")?\)"


def get_version_from_file(file_path: str) -> str:
    """Get the version from a file."""
    import re

    with open(file_path) as f:
        content = f.read()
    match = re.search(VERSION_PATTERN, content)
    if match:
        major, minor, patch, rc_group, rc = match.groups()
        version = f"{major}.{minor}.{patch}"
        if rc:
            raise ValueError("Do not commit RC to the version file.")
        return version
    raise ValueError(f"Could not find version in {file_path}")


def check_prerequisites():
    """Checks for necessary command-line tools and Python modules."""
    print("Checking for required tools...")
    required_tools = ["git", "gpg", "svn"]
    for tool in required_tools:
        if shutil.which(tool) is None:
            print(f"Error: '{tool}' not found. Please install it and ensure it's in your PATH.")
            sys.exit(1)

    try:
        import build  # noqa:F401

        print("Python 'build' module found.")
    except ImportError:
        print(
            "Error: The 'build' module is not installed. Please install it with 'pip install build'."
        )
        sys.exit(1)

    print("All required tools found.")


def update_version(version, rc_num):
    """Updates the version number in the specified file."""
    import re

    print(f"Updating version in {VERSION_FILE} to {version} RC{rc_num}...")
    try:
        with open(VERSION_FILE, "r") as f:
            content = f.read()
        major, minor, patch = version.split(".")
        if int(rc_num) >= 0:
            new_version_tuple = f'VERSION = ({major}, {minor}, {patch}, "RC{rc_num}")'
        else:
            new_version_tuple = f"VERSION = ({major}, {minor}, {patch})"
        new_content = re.sub(VERSION_PATTERN, new_version_tuple, content)
        if new_content == content:
            print("Error: Could not find or replace version string. Check your VERSION_PATTERN.")
            return False

        with open(VERSION_FILE, "w") as f:
            f.write(new_content)

        print("Version updated successfully.")
        return True

    except FileNotFoundError:
        print(f"Error: {VERSION_FILE} not found.")
        return False
    except Exception as e:
        print(f"An error occurred while updating the version: {e}")
        return False


def sign_artifacts(archive_name: str) -> Optional[list[str]]:
    """Creates signed files for the designated artifact."""
    files = []
    # Sign the tarball with GPG. The user must have a key configured.
    try:
        subprocess.run(
            ["gpg", "--armor", "--output", f"{archive_name}.asc", "--detach-sig", archive_name],
            check=True,
        )
        files.append(f"{archive_name}.asc")
        print(f"Created GPG signature: {archive_name}.asc")
    except subprocess.CalledProcessError as e:
        print(f"Error signing tarball: {e}")
        return None

    # Generate SHA512 checksum.
    sha512_hash = hashlib.sha512()
    with open(archive_name, "rb") as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            sha512_hash.update(data)

    with open(f"{archive_name}.sha512", "w") as f:
        f.write(f"{sha512_hash.hexdigest()}\n")
    print(f"Created SHA512 checksum: {archive_name}.sha512")
    files.append(f"{archive_name}.sha512")
    return files


def create_release_artifacts(version) -> tuple[list[str], list[str]]:
    """Creates the source tarball, GPG signature, and checksums using `python -m build`."""
    print("Creating release artifacts with 'python -m build'...")

    # Clean the dist directory before building.
    if os.path.exists("dist"):
        shutil.rmtree("dist")

    # Use python -m build to create the source distribution.
    try:
        subprocess.run(["python", "-m", "build", "--sdist", "."], check=True)
        print("Source distribution created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error creating source distribution: {e}")
        return None

    # Find the created tarball in the dist directory.
    expected_tar_ball = f"dist/sf_hamilton-{version.lower()}.tar.gz"
    tarball_path = glob.glob(expected_tar_ball)

    if not tarball_path:
        print(
            f"Error: Could not find {expected_tar_ball} the generated source tarball in the 'dist' directory."
        )
        if os.path.exists("dist"):
            print("Contents of 'dist' directory:")
            for item in os.listdir("dist"):
                print(f"- {item}")
        else:
            print("'dist' directory not found.")
        raise ValueError("Could not find the generated source tarball in the 'dist' directory.")

    # copy the tarball to be apache-hamilton-{version.lower()}-incubating.tar.gz
    new_tar_ball = f"dist/apache-hamilton-{version.lower()}-incubating.tar.gz"
    shutil.copy(tarball_path[0], new_tar_ball)
    archive_name = new_tar_ball
    print(f"Found source tarball: {archive_name}")
    main_signed_files = sign_artifacts(archive_name)
    if main_signed_files is None:
        raise ValueError("Could not sign the main release artifacts.")
    # create sf-hamilton release artifacts
    sf_hamilton_signed_files = sign_artifacts(expected_tar_ball)
    return [new_tar_ball] + main_signed_files, [expected_tar_ball] + sf_hamilton_signed_files


def svn_upload(version, rc_num, archive_files, sf_hamilton_archive_files, apache_id):
    """Uploads the artifacts to the ASF dev distribution repository."""
    print("Uploading artifacts to ASF SVN...")
    svn_path = f"https://dist.apache.org/repos/dist/dev/incubator/{PROJECT_SHORT_NAME}/apache-hamilton/{version}-incubating-RC{rc_num}"

    try:
        # Create a new directory for the release candidate.
        subprocess.run(
            [
                "svn",
                "mkdir",
                "-m",
                f"Creating directory for {version}-incubating-RC{rc_num}",
                svn_path,
            ],
            check=True,
        )

        # Get the files to import (tarball, asc, sha512).
        files_to_import = archive_files + sf_hamilton_archive_files

        # Use svn import for the new directory.
        for file_path in files_to_import:
            subprocess.run(
                [
                    "svn",
                    "import",
                    file_path,
                    f"{svn_path}/{os.path.basename(file_path)}",
                    "-m",
                    f"Adding {os.path.basename(file_path)}",
                    "--username",
                    apache_id,
                ],
                check=True,
            )

        print(f"Artifacts successfully uploaded to: {svn_path}")
        return svn_path

    except subprocess.CalledProcessError as e:
        print(f"Error during SVN upload: {e}")
        print("Make sure you have svn access configured for your Apache ID.")
        return None


def generate_email_template(version, rc_num, svn_url):
    """Generates the content for the [VOTE] email."""
    print("Generating email template...")
    version_with_incubating = f"{version}-incubating"
    tag = f"v{version}"

    email_content = f"""[VOTE] Release Apache {PROJECT_SHORT_NAME} {version_with_incubating} (release candidate {rc_num})

Hi all,

This is a call for a vote on releasing Apache {PROJECT_SHORT_NAME} {version_with_incubating},
release candidate {rc_num}.

This release includes the following changes (see CHANGELOG for details):
- [List key changes here]

The artifacts for this release candidate can be found at:
{svn_url}

The Git tag to be voted upon is:
{tag}

The release hash is:
[Insert git commit hash here]


Release artifacts are signed with the following key:
[Insert your GPG key ID here]
The KEYS file is available at:
https://downloads.apache.org/incubator/{PROJECT_SHORT_NAME}/KEYS

Please download, verify, and test the release candidate.

For testing, please run some of the examples, scripts/qualify.sh has
a sampling of them to run.

The vote will run for a minimum of 72 hours.
Please vote:

[ ] +1 Release this package as Apache {PROJECT_SHORT_NAME} {version_with_incubating}
[ ] +0 No opinion
[ ] -1 Do not release this package because... (Please provide a reason)

Checklist for reference:
[ ] Download links are valid.
[ ] Checksums and signatures.
[ ] LICENSE/NOTICE files exist
[ ] No unexpected binary files
[ ] All source files have ASF headers
[ ] Can compile from source

On behalf of the Apache {PROJECT_SHORT_NAME} PPMC,
[Your Name]
"""
    print("\n" + "=" * 80)
    print("EMAIL TEMPLATE (COPY AND PASTE TO YOUR MAILING LIST)")
    print("=" * 80)
    print(email_content)
    print("=" * 80)


def main():
    """
    ### How to Use the Updated Script

    1.  **Install the `build` module**:
        ```bash
        pip install build
        ```
    2.  **Configure the Script**: Open `apache_release_helper.py` in a text editor and update the three variables at the top of the file with your project's details:
        * `PROJECT_SHORT_NAME`
        * `VERSION_FILE` and `VERSION_PATTERN`
    3.  **Prerequisites**:
        * You must have `git`, `gpg`, `svn`, and the `build` Python module installed.
        * Your GPG key and SVN access must be configured for your Apache ID.
    4.  **Run the Script**:
        Open your terminal, navigate to the root of your project directory, and run the script with the desired version, release candidate number, and Apache ID.


    python apache_release_helper.py 1.2.3 0 your_apache_id
    """
    parser = argparse.ArgumentParser(description="Automates parts of the Apache release process.")
    parser.add_argument("version", help="The new release version (e.g., '1.0.0').")
    parser.add_argument("rc_num", help="The release candidate number (e.g., '0' for RC0).")
    parser.add_argument("apache_id", help="Your apache user ID.")
    args = parser.parse_args()

    version = args.version
    rc_num = args.rc_num
    apache_id = args.apache_id

    check_prerequisites()

    current_version = get_version_from_file(VERSION_FILE)
    print(current_version)
    if current_version != version:
        print("Update the version in the version file to match the expected version.")
        sys.exit(1)

    tag_name = f"v{version}-incubating-RC{rc_num}"
    print(f"\nChecking for git tag '{tag_name}'...")
    try:
        # Check if the tag already exists
        existing_tag = subprocess.check_output(["git", "tag", "-l", tag_name]).decode().strip()
        if existing_tag == tag_name:
            print(f"Git tag '{tag_name}' already exists.")
            response = input("Do you want to continue without creating a new tag? (y/n): ").lower()
            if response != "y":
                print("Aborting.")
                sys.exit(1)
        else:
            # Tag does not exist, create it
            print(f"Creating git tag '{tag_name}'...")
            subprocess.run(["git", "tag", tag_name], check=True)
            print(f"Git tag {tag_name} created.")
    except subprocess.CalledProcessError as e:
        print(f"Error checking or creating Git tag: {e}")
        sys.exit(1)

    # Create artifacts
    main_archive_files, sf_hamilton_archive_files = create_release_artifacts(version)
    if not main_archive_files:
        sys.exit(1)

    # Upload artifacts
    # NOTE: You MUST have your SVN client configured to use your Apache ID and have permissions.
    svn_url = svn_upload(version, rc_num, main_archive_files, sf_hamilton_archive_files, apache_id)
    if not svn_url:
        sys.exit(1)

    # Generate email
    generate_email_template(version, rc_num, svn_url)

    print("\nProcess complete. Please copy the email template to your mailing list.")


if __name__ == "__main__":
    main()
