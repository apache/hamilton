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
import tarfile
import tempfile
import zipfile

# --- Configuration ---
PROJECT_SHORT_NAME = "hamilton"

# Package configurations: each Hamilton package has its own settings
PACKAGE_CONFIGS = {
    "hamilton": {
        "name": "apache-hamilton",
        "working_dir": ".",
        "version_file": "hamilton/version.py",
        "version_pattern": r"VERSION = \((\d+), (\d+), (\d+)(, \"(\w+)\")?\)",
        "version_extractor": lambda match: f"{match.group(1)}.{match.group(2)}.{match.group(3)}",
    },
    "sdk": {
        "name": "apache-hamilton-sdk",
        "working_dir": "ui/sdk",
        "version_file": "ui/sdk/pyproject.toml",
        "version_pattern": r'version\s*=\s*"(\d+\.\d+\.\d+)"',
        "version_extractor": lambda match: match.group(1),
    },
    "lsp": {
        "name": "apache-hamilton-lsp",
        "working_dir": "dev_tools/language_server",
        "version_file": "dev_tools/language_server/pyproject.toml",
        "version_pattern": r'version\s*=\s*"(\d+\.\d+\.\d+)"',
        "version_extractor": lambda match: match.group(1),
    },
    "contrib": {
        "name": "apache-hamilton-contrib",
        "working_dir": "contrib",
        "version_file": "contrib/pyproject.toml",
        "version_pattern": r'version\s*=\s*"(\d+\.\d+\.\d+)"',
        "version_extractor": lambda match: match.group(1),
    },
    "ui": {
        "name": "apache-hamilton-ui",
        "working_dir": "ui/backend",
        "version_file": "ui/backend/pyproject.toml",
        "version_pattern": r'version\s*=\s*"(\d+\.\d+\.\d+)"',
        "version_extractor": lambda match: match.group(1),
    },
}

# Legacy configuration (kept for backward compatibility with single VERSION_FILE references)
VERSION_FILE = "hamilton/version.py"
VERSION_PATTERN = r"VERSION = \((\d+), (\d+), (\d+)(, \"(\w+)\")?\)"


def get_version_from_file(package_config: dict) -> str:
    """Get the version from a file using package-specific configuration."""
    import re

    file_path = package_config["version_file"]
    pattern = package_config["version_pattern"]
    extractor = package_config["version_extractor"]

    with open(file_path) as f:
        content = f.read()
    match = re.search(pattern, content)
    if match:
        # Check for RC in the match (only for main hamilton package)
        if len(match.groups()) >= 5 and match.group(5):
            raise ValueError("Do not commit RC to the version file.")
        version = extractor(match)
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


def update_version(package_config: dict, version, rc_num):
    """Updates the version number in the specified file."""
    import re

    version_file = package_config["version_file"]
    pattern = package_config["version_pattern"]

    print(f"Updating version in {version_file} to {version} RC{rc_num}...")
    try:
        with open(version_file, "r") as f:
            content = f.read()

        # Only the main hamilton package uses the tuple format with RC
        if package_config["name"] == "apache-hamilton":
            major, minor, patch = version.split(".")
            if int(rc_num) >= 0:
                new_version_tuple = f'VERSION = ({major}, {minor}, {patch}, "RC{rc_num}")'
            else:
                new_version_tuple = f"VERSION = ({major}, {minor}, {patch})"
            new_content = re.sub(pattern, new_version_tuple, content)
        else:
            # Other packages use pyproject.toml with simple version string
            # For now, we don't update these with RC numbers in pyproject.toml
            print(
                f"Note: Version updates for {package_config['name']} are manual in pyproject.toml"
            )
            return True

        if new_content == content:
            print("Error: Could not find or replace version string. Check your VERSION_PATTERN.")
            return False

        with open(version_file, "w") as f:
            f.write(new_content)

        print("Version updated successfully.")
        return True

    except FileNotFoundError:
        print(f"Error: {version_file} not found.")
        return False
    except Exception as e:
        print(f"An error occurred while updating the version: {e}")
        return False


def sign_artifacts(archive_name: str) -> list[str] | None:
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


def _modify_wheel_for_apache_release(original_wheel: str, new_wheel_path: str, package_name: str):
    """Helper to modify the wheel for apache release.

    # Flit somehow builds something incorrectly.
    # 1. change PKG-INFO's first line to be `Metadata-Version: 2.4`
    # 2. make sure the second line is `Name: {package_name}`
    # 3. remove the `Import-Name:` line from PKG-INFO.

    :param original_wheel: Path to the original wheel.
    :param new_wheel_path: Path to the new wheel to create.
    :param package_name: The Apache package name (e.g., 'apache-hamilton')
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Unzip the wheel
        with zipfile.ZipFile(original_wheel, "r") as zip_ref:
            zip_ref.extractall(tmpdir)

        # Find the .dist-info directory
        dist_info_dirs = glob.glob(os.path.join(tmpdir, "*.dist-info"))
        if not dist_info_dirs:
            raise ValueError(f"Could not find .dist-info directory in {original_wheel}")
        dist_info_dir = dist_info_dirs[0]
        pkg_info = os.path.join(dist_info_dir, "PKG-INFO")

        _modify_pkg_info_file(pkg_info, package_name)

        # Create the new wheel
        with zipfile.ZipFile(new_wheel_path, "w", zipfile.ZIP_DEFLATED) as zip_ref:
            for root, _, files in os.walk(tmpdir):
                for file in files:
                    zip_ref.write(
                        os.path.join(root, file), os.path.relpath(os.path.join(root, file), tmpdir)
                    )


def _modify_pkg_info_file(pkg_info_path: str, package_name: str):
    """
    Flit somehow builds something incorrectly.
    1. change PKG-INFO's first line to be `Metadata-Version: 2.4`
    2. make sure the second line is `Name: {package_name}`
    3. remove the `Import-Name:` line from PKG-INFO if present.
    """
    with open(pkg_info_path, "r") as f:
        lines = f.readlines()

    new_lines = []
    for i, line in enumerate(lines):
        if i == 0:
            new_lines.append("Metadata-Version: 2.4\n")
        elif i == 1:
            new_lines.append(f"Name: {package_name}\n")
        elif line.startswith("Import-Name:"):
            continue  # Skip this line
        else:
            new_lines.append(line)

    with open(pkg_info_path, "w") as f:
        f.writelines(new_lines)


def _modify_tarball_for_apache_release(
    original_tarball: str, new_tarball_path: str, package_name: str
):
    """Helper to modify the tarball for apache release.

    # Flit somehow builds something incorrectly.
    # 1. change PKG-INFO's first line to be `Metadata-Version: 2.4`
    # 2. make sure the second line is `Name: {package_name}`
    # 3. remove the `Import-Name:` line from PKG-INFO.

    :param original_tarball: Path to the original tarball.
    :param new_tarball_path: Path to the new tarball to create.
    :param package_name: The Apache package name (e.g., 'apache-hamilton')
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Extract the tarball
        with tarfile.open(original_tarball, "r:gz") as tar:
            tar.extractall(path=tmpdir)

        # Modify the PKG-INFO file
        # The extracted tarball has a single directory inside.
        extracted_dir = os.path.join(tmpdir, os.listdir(tmpdir)[0])
        pkg_info_path = os.path.join(extracted_dir, "PKG-INFO")

        _modify_pkg_info_file(pkg_info_path, package_name)

        # Create the new tarball
        with tarfile.open(new_tarball_path, "w:gz") as tar:
            tar.add(extracted_dir, arcname=os.path.basename(extracted_dir))


def create_release_artifacts(package_config: dict, version) -> list[str]:
    """Creates the source tarball, GPG signature, and checksums using flit build."""
    package_name = package_config["name"]
    working_dir = package_config["working_dir"]

    print(f"Creating release artifacts for {package_name} with 'flit build'...")

    # Save current directory and change to package working directory
    original_dir = os.getcwd()
    if working_dir != ".":
        os.chdir(working_dir)

    try:
        # Clean the dist directory before building.
        if os.path.exists("dist"):
            shutil.rmtree("dist")

        # Use flit build to create the source distribution.
        try:
            subprocess.run(
                [
                    "flit",
                    "build",
                    "--no-use-vcs",
                ],
                check=True,
            )
            print("Source distribution created successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error creating source distribution: {e}")
            return None

        # Find the created tarball in the dist directory.
        # Convert package name with underscores for file naming
        package_file_name = package_name.replace("-", "_")
        expected_tar_ball = f"dist/{package_file_name}-{version.lower()}.tar.gz"
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

        # Copy the tarball to be {package-name}-{version}-incubating.tar.gz
        new_tar_ball = f"dist/{package_name}-{version.lower()}-incubating.tar.gz"
        _modify_tarball_for_apache_release(tarball_path[0], new_tar_ball, package_name)
        archive_name = new_tar_ball
        print(f"Found source tarball: {archive_name}")
        new_tar_ball_singed = sign_artifacts(archive_name)
        if new_tar_ball_singed is None:
            raise ValueError("Could not sign the main release artifacts.")

        # Create wheel release artifacts
        expected_wheel = f"dist/{package_file_name}-{version.lower()}-py3-none-any.whl"
        wheel_path = glob.glob(expected_wheel)

        # Create incubator wheel release artifacts
        expected_incubator_wheel = (
            f"dist/{package_name}-{version.lower()}-incubating-py3-none-any.whl"
        )
        shutil.copy(wheel_path[0], expected_incubator_wheel)
        incubator_wheel_signed_files = sign_artifacts(expected_incubator_wheel)

        files_to_upload = (
            [new_tar_ball]
            + new_tar_ball_singed
            + [expected_incubator_wheel]
            + incubator_wheel_signed_files
        )
        return files_to_upload

    finally:
        # Always return to original directory
        os.chdir(original_dir)


def svn_upload(package_name: str, version, rc_num, files_to_import: list[str], apache_id):
    """Uploads the artifacts to the ASF dev distribution repository.

    files_to_import: Get the files to import (tarball, asc, sha512).
    """
    print("Uploading artifacts to ASF SVN...")
    # Include package name in SVN path for multi-package support
    svn_path = f"https://dist.apache.org/repos/dist/dev/incubator/{PROJECT_SHORT_NAME}/{package_name}/{version}-RC{rc_num}"

    try:
        # Create a new directory for the release candidate.
        print(
            f"Creating directory for {package_name} {version}-incubating-RC{rc_num}... at {svn_path}"
        )
        subprocess.run(
            [
                "svn",
                "mkdir",
                "--parents",
                "-m",
                f"Creating directory for {package_name} {version}-incubating-RC{rc_num}",
                svn_path,
            ],
            check=True,
        )

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
            print(f"Imported {file_path} to {svn_path}")

        print(f"Artifacts successfully uploaded to: {svn_path}")
        return svn_path

    except subprocess.CalledProcessError as e:
        print(f"Error during SVN upload: {e}")
        print("Make sure you have svn access configured for your Apache ID.")
        return None


def generate_email_template(package_name: str, version, rc_num, svn_url):
    """Generates the content for the [VOTE] email."""
    print("Generating email template...")
    version_with_incubating = f"{version}-incubating"
    tag = f"{package_name}-v{version}"

    email_content = f"""[VOTE] Release Apache {PROJECT_SHORT_NAME} - {package_name} {version_with_incubating} (release candidate {rc_num})

Hi all,

This is a call for a vote on releasing Apache {PROJECT_SHORT_NAME} {package_name} {version_with_incubating},
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

[ ] +1 Release this package as Apache {PROJECT_SHORT_NAME} {package_name} {version_with_incubating}
[ ] +0 No opinion
[ ] -1 Do not release this package because... (Please provide a reason)

Checklist for reference:
[ ] Incubating in name.
[ ] Download links are valid.
[ ] Checksums and signatures.
[ ] LICENSE/NOTICE/DISCLAIMER files exist
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

    1.  **Install the `flit` module**:
        ```bash
        pip install flit
        ```
    2.  **Configure the Script**: The script now supports multiple Hamilton packages.
        Available packages: hamilton, sdk, lsp, contrib, ui
    3.  **Prerequisites**:
        * You must have `git`, `gpg`, `svn`, and the `flit` Python module installed.
        * Your GPG key and SVN access must be configured for your Apache ID.
    4.  **Run the Script**:
        Open your terminal, navigate to the root of your project directory, and run the script
        with the desired package, version, release candidate number, and Apache ID.

    Note: if you have multiple gpg keys, specify the default in ~/.gnupg/gpg.conf add a line with `default-key <KEYID>`.

    Examples:
        python apache_release_helper.py --package hamilton 1.89.0 0 your_apache_id
        python apache_release_helper.py --package sdk 0.8.0 0 your_apache_id
        python apache_release_helper.py --package lsp 0.1.0 0 your_apache_id
        python apache_release_helper.py --package contrib 0.0.8 0 your_apache_id
        python apache_release_helper.py --package ui 0.0.17 0 your_apache_id
    """
    parser = argparse.ArgumentParser(
        description="Automates parts of the Apache release process for Hamilton packages."
    )
    parser.add_argument(
        "--package",
        required=True,
        choices=list(PACKAGE_CONFIGS.keys()),
        help="Which Hamilton package to release (hamilton, sdk, lsp, contrib, ui)",
    )
    parser.add_argument("version", help="The new release version (e.g., '1.0.0').")
    parser.add_argument("rc_num", help="The release candidate number (e.g., '0' for RC0).")
    parser.add_argument("apache_id", help="Your apache user ID.")
    args = parser.parse_args()

    package_key = args.package
    version = args.version
    rc_num = args.rc_num
    apache_id = args.apache_id

    # Get package configuration
    package_config = PACKAGE_CONFIGS[package_key]
    package_name = package_config["name"]

    print(f"\n{'=' * 80}")
    print(f"  Apache Hamilton Release Helper - {package_name}")
    print(f"{'=' * 80}\n")

    check_prerequisites()

    # Validate version matches what's in the version file
    current_version = get_version_from_file(package_config)
    print(f"Current version in {package_config['version_file']}: {current_version}")
    if current_version != version:
        print("Update the version in the version file to match the expected version.")
        sys.exit(1)

    # Create git tag (from repo root)
    tag_name = f"{package_name}-v{version}-incubating-RC{rc_num}"
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
    print(f"\n{'=' * 80}")
    print("  Building Release Artifacts")
    print(f"{'=' * 80}\n")
    files_to_upload = create_release_artifacts(package_config, version)
    if not files_to_upload:
        sys.exit(1)

    # Upload artifacts
    print(f"\n{'=' * 80}")
    print("  Uploading to Apache SVN")
    print(f"{'=' * 80}\n")
    # NOTE: You MUST have your SVN client configured to use your Apache ID and have permissions.
    svn_url = svn_upload(package_name, version, rc_num, files_to_upload, apache_id)
    if not svn_url:
        sys.exit(1)

    # Generate email
    print(f"\n{'=' * 80}")
    print("  Vote Email Template")
    print(f"{'=' * 80}\n")
    generate_email_template(package_name, version, rc_num, svn_url)

    print("\n" + "=" * 80)
    print("  Process Complete!")
    print("=" * 80)
    print("\nNext steps:")
    print(f"1. Push the git tag: git push origin {tag_name}")
    print("2. Copy the email template above and send to dev@hamilton.apache.org")
    print("3. Wait for votes (minimum 72 hours)")
    print("\n")


if __name__ == "__main__":
    main()
