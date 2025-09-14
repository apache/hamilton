import argparse
import glob
import hashlib
import os
import shutil
import subprocess
import sys

# --- Configuration ---
# You need to fill these in for your project.
# The name of your project's short name (e.g., 'myproject').
PROJECT_SHORT_NAME = "hamilton"
# Your Apache ID (the one you use to log in to svn and people.apache.org).
APACHE_ID = "skrawcz"

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
            version += "." + rc
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


def create_release_artifacts(version, rc_num):
    """Creates the source tarball, GPG signature, and checksums using `python -m build`."""
    print("Creating release artifacts with 'python -m build'...")
    version_with_incubating = f"{version}-incubating"

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
    tarball_path = glob.glob(
        f"dist/{PROJECT_SHORT_NAME.replace('-', '_')}-{version_with_incubating}.tar.gz"
    )

    if not tarball_path:
        print("Error: Could not find the generated source tarball in the 'dist' directory.")
        return None

    archive_name = tarball_path[0]

    print(f"Found source tarball: {archive_name}")

    # Sign the tarball with GPG. The user must have a key configured.
    try:
        subprocess.run(
            ["gpg", "--armor", "--output", f"{archive_name}.asc", "--detach-sig", archive_name],
            check=True,
        )
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

    return archive_name


def svn_upload(version, rc_num, archive_name):
    """Uploads the artifacts to the ASF dev distribution repository."""
    print("Uploading artifacts to ASF SVN...")
    svn_path = f"https://dist.apache.org/repos/dist/dev/incubator/{PROJECT_SHORT_NAME}/{version}-incubating-rc{rc_num}"

    try:
        # Create a new directory for the release candidate.
        subprocess.run(
            [
                "svn",
                "mkdir",
                "-m",
                f"Creating directory for {version}-incubating-rc{rc_num}",
                svn_path,
            ],
            check=True,
        )

        # Get the files to import (tarball, asc, sha512).
        files_to_import = [archive_name, f"{archive_name}.asc", f"{archive_name}.sha512"]

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
                    APACHE_ID,
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

The Nexus staging repository is:
[Insert Nexus staging repository URL here if applicable]

Release artifacts are signed with the following key:
[Insert your GPG key ID here]
The KEYS file is available at:
https://downloads.apache.org/incubator/{PROJECT_SHORT_NAME}/KEYS

Please download, verify, and test the release candidate.

The vote will run for a minimum of 72 hours.
Please vote:

[ ] +1 Release this package as Apache {PROJECT_SHORT_NAME} {version_with_incubating}
[ ] +0 No opinion
[ ] -1 Do not release this package because... (Please provide a reason)

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
        * `APACHE_ID`
        * `VERSION_FILE` and `VERSION_PATTERN`
    3.  **Prerequisites**:
        * You must have `git`, `gpg`, `svn`, and the `build` Python module installed.
        * Your GPG key and SVN access must be configured for your Apache ID.
    4.  **Run the Script**:
        Open your terminal, navigate to the root of your project directory, and run the script with the desired version and release candidate number.


    python apache_release_helper.py 1.2.3 0
    """
    parser = argparse.ArgumentParser(description="Automates parts of the Apache release process.")
    parser.add_argument("version", help="The new release version (e.g., '1.0.0').")
    parser.add_argument("rc_num", help="The release candidate number (e.g., '0' for RC0).")
    args = parser.parse_args()

    version = args.version
    rc_num = args.rc_num

    check_prerequisites()

    current_version = get_version_from_file(VERSION_FILE)
    print(current_version)
    expected_version = version
    if rc_num != "-":
        expected_version = f"{version}.RC{rc_num}"
    if current_version != expected_version:
        print("Update the version in the version file to match the expected version.")
        sys.exit(1)

    print(f"\nCreating git tag 'v{expected_version}'...")
    try:
        # subprocess.run(["git", "add", VERSION_FILE], check=True)
        # subprocess.run(
        #     ["git", "commit", "-m", f"Set version to {version} for RC{rc_num}"], check=True
        # )
        subprocess.run(["git", "tag", f"v{version}"], check=True)
        print(f"Git tag v{version} created.")
    except subprocess.CalledProcessError as e:
        print(f"Error creating Git tag: {e}")
        sys.exit(1)

    # Create artifacts
    archive_name = create_release_artifacts(version, rc_num)
    if not archive_name:
        sys.exit(1)

    # Upload artifacts
    # NOTE: You MUST have your SVN client configured to use your Apache ID and have permissions.
    svn_url = svn_upload(version, rc_num, archive_name)
    if not svn_url:
        sys.exit(1)

    # Generate email
    generate_email_template(version, rc_num, svn_url)

    print("\nProcess complete. Please copy the email template to your mailing list.")


if __name__ == "__main__":
    main()
