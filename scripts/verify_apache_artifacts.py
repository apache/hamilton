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
Apache Artifacts Verification Script

Comprehensive verification tool for Apache release artifacts.
Checks signatures, checksums, licenses, and archive integrity.

Usage:
    # List contents of an artifact
    uv run python scripts/verify_apache_artifacts.py list-contents dist/apache-hamilton-0.41.0-incubating-src.tar.gz

    # Verify signatures and checksums
    uv run python scripts/verify_apache_artifacts.py signatures

    # Verify licenses with Apache RAT
    uv run python scripts/verify_apache_artifacts.py licenses --rat-jar path/to/apache-rat.jar

    # Verify everything
    uv run python scripts/verify_apache_artifacts.py all --rat-jar path/to/apache-rat.jar

    # Specify custom artifacts directory
    uv run python scripts/verify_apache_artifacts.py signatures --artifacts-dir /path/to/dist
"""

import argparse
import glob
import hashlib
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import xml.etree.ElementTree as ET
import zipfile

# Configuration
PROJECT_SHORT_NAME = "hamilton"


def _fail(message: str) -> None:
    """Print error message and exit."""
    print(f"\n❌ {message}")
    sys.exit(1)


def _print_section(title: str) -> None:
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


# ============================================================================
# Signature and Checksum Verification
# ============================================================================


def _verify_artifact_signature(artifact_path: str, signature_path: str) -> bool:
    """Verify GPG signature of artifact."""
    print(f"  Verifying GPG signature: {os.path.basename(signature_path)}")

    if not os.path.exists(signature_path):
        print("    ✗ Signature file not found")
        return False

    try:
        result = subprocess.run(
            ["gpg", "--verify", signature_path, artifact_path],
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            print("    ✓ GPG signature is valid")
            return True
        else:
            print("    ✗ GPG signature verification failed")
            if result.stderr:
                print(f"    Error: {result.stderr.decode()}")
            return False
    except subprocess.CalledProcessError:
        print("    ✗ Error running GPG")
        return False


def _verify_artifact_checksum(artifact_path: str, checksum_path: str) -> bool:
    """Verify SHA512 checksum of artifact."""
    print(f"  Verifying SHA512 checksum: {os.path.basename(checksum_path)}")

    if not os.path.exists(checksum_path):
        print("    ✗ Checksum file not found")
        return False

    # Read expected checksum
    with open(checksum_path, "r", encoding="utf-8") as f:
        expected_checksum = f.read().strip().split()[0]

    # Calculate actual checksum
    sha512_hash = hashlib.sha512()
    with open(artifact_path, "rb") as f:
        while chunk := f.read(65536):
            sha512_hash.update(chunk)

    actual_checksum = sha512_hash.hexdigest()

    if actual_checksum == expected_checksum:
        print("    ✓ SHA512 checksum is valid")
        return True
    else:
        print("    ✗ SHA512 checksum mismatch!")
        print(f"    Expected: {expected_checksum}")
        print(f"    Actual:   {actual_checksum}")
        return False


def _verify_tar_gz_readable(artifact_path: str) -> bool:
    """Verify tar.gz archive can be read and contains files."""
    print(f"  Checking archive readability: {os.path.basename(artifact_path)}")

    try:
        with tarfile.open(artifact_path, "r:gz") as tar:
            members = tar.getmembers()

            if len(members) == 0:
                print("    ✗ Archive is empty (no files)")
                return False

            print(f"    ✓ Archive is readable and contains {len(members)} files")
            return True
    except tarfile.TarError as e:
        print(f"    ✗ Archive is corrupted or unreadable: {e}")
        return False
    except Exception as e:
        print(f"    ✗ Error reading archive: {e}")
        return False


def _verify_wheel_readable(wheel_path: str) -> bool:
    """Verify wheel can be read and contains expected structure."""
    print(f"  Checking wheel readability: {os.path.basename(wheel_path)}")

    try:
        with zipfile.ZipFile(wheel_path, "r") as whl:
            file_list = whl.namelist()

            if len(file_list) == 0:
                print("    ✗ Wheel is empty (no files)")
                return False

            # Check for metadata
            metadata_files = [f for f in file_list if "METADATA" in f or "WHEEL" in f]
            if not metadata_files:
                print("    ✗ Wheel missing required metadata files")
                return False

            print(f"    ✓ Wheel is readable and contains {len(file_list)} files")
            return True
    except zipfile.BadZipFile:
        print("    ✗ Wheel is corrupted or not a valid ZIP file")
        return False
    except Exception as e:
        print(f"    ✗ Error reading wheel: {e}")
        return False


def _verify_artifact_exists(artifact_path: str, min_size: int = 1000) -> bool:
    """Verify artifact exists and has reasonable size."""
    if not os.path.exists(artifact_path):
        print(f"  ✗ Artifact not found: {os.path.basename(artifact_path)}")
        return False

    file_size = os.path.getsize(artifact_path)
    if file_size < min_size:
        print(
            f"  ✗ Artifact is suspiciously small ({file_size} bytes): {os.path.basename(artifact_path)}"
        )
        return False

    print(f"  ✓ Artifact exists: {os.path.basename(artifact_path)} ({file_size:,} bytes)")
    return True


def verify_signatures(artifacts_dir: str) -> bool:
    """Verify all signatures and checksums in artifacts directory."""
    _print_section("Verifying Signatures and Checksums")

    if not os.path.exists(artifacts_dir):
        _fail(f"Artifacts directory not found: {artifacts_dir}")

    # Find all artifacts (exclude .asc and .sha512 files)
    all_files = [
        f for f in os.listdir(artifacts_dir) if os.path.isfile(os.path.join(artifacts_dir, f))
    ]
    artifacts = [f for f in all_files if not f.endswith((".asc", ".sha512"))]

    if not artifacts:
        print(f"⚠️  No artifacts found in {artifacts_dir}")
        return False

    print(f"Found {len(artifacts)} artifact(s) to verify:\n")

    all_valid = True
    for artifact_name in artifacts:
        artifact_path = os.path.join(artifacts_dir, artifact_name)

        print(f"Verifying: {artifact_name}")
        print("-" * 80)

        # Check existence and size
        if not _verify_artifact_exists(artifact_path):
            all_valid = False
            continue

        # Verify signature
        signature_path = f"{artifact_path}.asc"
        if not _verify_artifact_signature(artifact_path, signature_path):
            all_valid = False

        # Verify checksum
        checksum_path = f"{artifact_path}.sha512"
        if not _verify_artifact_checksum(artifact_path, checksum_path):
            all_valid = False

        # Verify archive/wheel structure
        if artifact_name.endswith(".tar.gz"):
            if not _verify_tar_gz_readable(artifact_path):
                all_valid = False
        elif artifact_name.endswith(".whl"):
            if not _verify_wheel_readable(artifact_path):
                all_valid = False

        print()

    return all_valid


# ============================================================================
# License Verification (Apache RAT)
# ============================================================================


def _check_licenses_with_rat(
    artifact_path: str,
    rat_jar_path: str,
    report_name: str,
    report_only: bool = False,
) -> bool:
    """Run Apache RAT license checker on artifact."""
    print(f"\nRunning Apache RAT on: {os.path.basename(artifact_path)}")
    print("-" * 80)

    # Create reports directory
    report_dir = "dist"
    os.makedirs(report_dir, exist_ok=True)

    rat_report_xml = os.path.join(report_dir, f"rat-report-{report_name}.xml")
    rat_report_txt = os.path.join(report_dir, f"rat-report-{report_name}.txt")

    # Extract archive to temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        extract_dir = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_dir)

        print("  Extracting archive...")
        try:
            with tarfile.open(artifact_path, "r:gz") as tar:
                # Use data filter for Python 3.12+ to avoid deprecation warning
                tar.extractall(extract_dir, filter="data")
            print("    ✓ Extracted to temp directory")
        except Exception as e:
            print(f"    ✗ Error extracting archive: {e}")
            return False

        # Locate .rat-excludes file
        rat_excludes = ".rat-excludes"
        if not os.path.exists(rat_excludes):
            print(f"    ⚠️  Warning: {rat_excludes} not found, running without excludes")
            rat_excludes = None

        # Run RAT with XML output
        print("  Running Apache RAT (XML format for parsing)...")
        rat_cmd_xml = [
            "java",
            "-jar",
            rat_jar_path,
            "-x",  # XML output
            "-d",
            extract_dir,
        ]
        if rat_excludes:
            rat_cmd_xml.extend(["-E", rat_excludes])

        try:
            with open(rat_report_xml, "w", encoding="utf-8") as report_file:
                result = subprocess.run(
                    rat_cmd_xml,
                    stdout=report_file,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                )

            if result.returncode != 0:
                print(f"    ⚠️  RAT exited with code {result.returncode}")

            print(f"    ✓ RAT XML report: {rat_report_xml}")
        except Exception as e:
            print(f"    ✗ Error running RAT (XML): {e}")
            return False

        # Run RAT with plain text output
        print("  Running Apache RAT (text format for review)...")
        rat_cmd_txt = [
            "java",
            "-jar",
            rat_jar_path,
            "-d",
            extract_dir,
        ]
        if rat_excludes:
            rat_cmd_txt.extend(["-E", rat_excludes])

        try:
            with open(rat_report_txt, "w", encoding="utf-8") as report_file:
                subprocess.run(
                    rat_cmd_txt,
                    stdout=report_file,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                )
            print(f"    ✓ RAT text report: {rat_report_txt}")
        except Exception as e:
            print(f"    ⚠️  Warning: Could not generate text report: {e}")

        # Parse XML report
        print("  Parsing RAT report...")
        try:
            tree = ET.parse(rat_report_xml)
            root = tree.getroot()

            # Find license issues
            unapproved_licenses = []
            unknown_licenses = []

            for resource in root.findall(".//resource"):
                name = resource.get("name", "unknown")

                # Get license approval and family from child elements
                license_approval_elem = resource.find("license-approval")
                license_family_elem = resource.find("license-family")

                license_approval = (
                    license_approval_elem.get("name", "true")
                    if license_approval_elem is not None
                    else "true"
                )
                license_family = (
                    license_family_elem.get("name", "") if license_family_elem is not None else ""
                )

                if license_approval == "false" or license_family == "Unknown license":
                    if license_family == "Unknown license" or not license_family:
                        unknown_licenses.append(name)
                    else:
                        unapproved_licenses.append(name)

            # Report findings
            total_files = len(root.findall(".//resource"))
            issues_count = len(unapproved_licenses) + len(unknown_licenses)

            print(f"    ✓ Scanned {total_files} files")
            print(f"    ✓ Found {issues_count} files with license issues")

            if issues_count > 0:
                print("\n  ⚠️  License Issues Found:")

                if unknown_licenses:
                    print(f"\n    Unknown/Missing Licenses ({len(unknown_licenses)} files):")
                    for file in unknown_licenses[:10]:
                        print(f"      - {file}")
                    if len(unknown_licenses) > 10:
                        print(f"      ... and {len(unknown_licenses) - 10} more")

                if unapproved_licenses:
                    print(f"\n    Unapproved Licenses ({len(unapproved_licenses)} files):")
                    for file in unapproved_licenses[:10]:
                        print(f"      - {file}")
                    if len(unapproved_licenses) > 10:
                        print(f"      ... and {len(unapproved_licenses) - 10} more")

                print("\n    📄 Reports saved:")
                print(f"       - {rat_report_xml} (structured)")
                print(f"       - {rat_report_txt} (human-readable)")

                if report_only:
                    print("\n  ℹ️  Report-only mode: continuing despite license issues")
                    return True
                else:
                    print("\n  ❌ License check failed!")
                    return False
            else:
                print("    ✅ All files have approved licenses")
                print("\n    📄 Reports saved:")
                print(f"       - {rat_report_xml} (structured)")
                print(f"       - {rat_report_txt} (human-readable)")
                return True

        except Exception as e:
            print(f"    ✗ Error parsing RAT report: {e}")
            if report_only:
                print("    ℹ️  Report-only mode: continuing despite parse error")
                return True
            return False


def verify_licenses(artifacts_dir: str, rat_jar_path: str, report_only: bool = False) -> bool:
    """Verify licenses in all tar.gz artifacts using Apache RAT."""
    _print_section("Verifying Licenses with Apache RAT")

    if not os.path.exists(artifacts_dir):
        _fail(f"Artifacts directory not found: {artifacts_dir}")

    if not rat_jar_path or not os.path.exists(rat_jar_path):
        _fail(
            f"Apache RAT JAR not found: {rat_jar_path}\nDownload from: https://creadur.apache.org/rat/download_rat.cgi"
        )

    # Check for java
    if shutil.which("java") is None:
        _fail("Java not found. Required for Apache RAT.")

    # Find all tar.gz artifacts (not wheels)
    all_files = [
        f for f in os.listdir(artifacts_dir) if os.path.isfile(os.path.join(artifacts_dir, f))
    ]
    tar_artifacts = [f for f in all_files if f.endswith(".tar.gz")]

    if not tar_artifacts:
        print(f"⚠️  No tar.gz artifacts found in {artifacts_dir}")
        return False

    print(f"Found {len(tar_artifacts)} tar.gz artifact(s) to check:\n")

    all_valid = True
    for artifact_name in tar_artifacts:
        artifact_path = os.path.join(artifacts_dir, artifact_name)

        # Generate report name from artifact name
        report_name = artifact_name.replace(".tar.gz", "").replace(".", "-")

        if not _check_licenses_with_rat(artifact_path, rat_jar_path, report_name, report_only):
            all_valid = False

    return all_valid


# ============================================================================
# List Contents
# ============================================================================


def _list_tar_gz_contents(artifact_path: str) -> None:
    """List contents of a tar.gz archive."""
    print(f"\nContents of: {os.path.basename(artifact_path)}")
    print("=" * 80)

    try:
        with tarfile.open(artifact_path, "r:gz") as tar:
            members = tar.getmembers()

            print(f"Total files: {len(members)}\n")

            # Group by type
            files = [m for m in members if m.isfile()]
            dirs = [m for m in members if m.isdir()]
            symlinks = [m for m in members if m.issym() or m.islnk()]

            print(f"Files: {len(files)}, Directories: {len(dirs)}, Symlinks: {len(symlinks)}\n")

            # Show all files
            print("Files:\n")

            for member in members:
                size = f"{member.size:>12,}" if member.isfile() else "        <dir>"
                prefix = "  "
                if member.issym() or member.islnk():
                    prefix = "→ "
                    if member.linkname:
                        print(f"{prefix}{member.name} -> {member.linkname}")
                        continue
                print(f"{prefix}{member.name:<70} {size}")

    except Exception as e:
        print(f"Error reading archive: {e}")


def _list_wheel_contents(wheel_path: str) -> None:
    """List contents of a wheel file."""
    print(f"\nContents of: {os.path.basename(wheel_path)}")
    print("=" * 80)

    try:
        with zipfile.ZipFile(wheel_path, "r") as whl:
            file_list = whl.namelist()

            print(f"Total files: {len(file_list)}\n")

            # Group by directory
            top_level_dirs = {}
            for file in file_list:
                top_dir = file.split("/")[0]
                top_level_dirs[top_dir] = top_level_dirs.get(top_dir, 0) + 1

            print("Top-level structure:")
            for dir_name, count in sorted(top_level_dirs.items()):
                print(f"  {dir_name:<50} ({count} files)")

            # Show all files
            print("\nFiles:\n")

            for filename in sorted(file_list):
                info = whl.getinfo(filename)
                size = f"{info.file_size:>12,}" if not filename.endswith("/") else "        <dir>"
                print(f"  {filename:<70} {size}")

    except Exception as e:
        print(f"Error reading wheel: {e}")


def list_contents(artifact_path: str) -> None:
    """List contents of a specific artifact."""
    _print_section("Listing Artifact Contents")

    if not os.path.exists(artifact_path):
        _fail(f"Artifact not found: {artifact_path}")

    if artifact_path.endswith(".tar.gz"):
        _list_tar_gz_contents(artifact_path)
    elif artifact_path.endswith(".whl"):
        _list_wheel_contents(artifact_path)
    else:
        _fail(f"Unsupported file type: {artifact_path}\nSupported: .tar.gz, .whl")


# ============================================================================
# Command Handlers
# ============================================================================


def cmd_signatures(args) -> bool:
    """Verify signatures and checksums."""
    return verify_signatures(args.artifacts_dir)


def cmd_licenses(args) -> bool:
    """Verify licenses with Apache RAT."""
    if not args.rat_jar:
        _fail("--rat-jar is required for license verification")

    return verify_licenses(args.artifacts_dir, args.rat_jar, args.report_only)


def cmd_all(args) -> bool:
    """Verify everything: signatures, checksums, and licenses."""
    _print_section("Complete Apache Artifacts Verification")

    # Step 1: Verify signatures
    print("\n[1/2] Verifying signatures and checksums...")
    signatures_ok = verify_signatures(args.artifacts_dir)

    # Step 2: Verify licenses
    if args.rat_jar:
        print("\n[2/2] Verifying licenses with Apache RAT...")
        licenses_ok = verify_licenses(args.artifacts_dir, args.rat_jar, args.report_only)
    else:
        print("\n[2/2] Skipping license verification (no --rat-jar provided)")
        licenses_ok = True

    # Summary
    _print_section("Verification Summary")

    print("Results:")
    print(f"  Signatures & Checksums: {'✅ PASS' if signatures_ok else '❌ FAIL'}")
    print(
        f"  License Compliance:     {'✅ PASS' if licenses_ok else '❌ FAIL' if args.rat_jar else '⊘ SKIPPED'}"
    )

    return signatures_ok and licenses_ok


def cmd_list_contents(args) -> None:
    """List contents of a specific artifact."""
    list_contents(args.artifact)


def cmd_twine_check(args) -> bool:
    """Verify wheel metadata with twine."""
    _print_section("Verifying Wheel Metadata with Twine")

    wheel_pattern = f"{args.artifacts_dir}/apache_hamilton-*.whl"
    wheel_files = glob.glob(wheel_pattern)

    if not wheel_files:
        print(f"❌ No wheel found matching: {wheel_pattern}")
        return False

    for wheel_path in wheel_files:
        print(f"\nChecking {os.path.basename(wheel_path)}...")
        try:
            subprocess.run(
                ["twine", "check", wheel_path],
                check=True,
                capture_output=True,
                text=True,
            )
            print(f"  ✓ {os.path.basename(wheel_path)} metadata is valid")
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Twine check failed: {e.stderr}")
            return False

    print("\n✅ All wheels passed twine validation")
    return True


# ============================================================================
# CLI Entry Point
# ============================================================================


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Apache Artifacts Verification Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List contents of a specific artifact
  uv run python scripts/verify_apache_artifacts.py list-contents dist/apache-hamilton-0.41.0-incubating-src.tar.gz
  uv run python scripts/verify_apache_artifacts.py list-contents dist/apache_hamilton-0.41.0-py3-none-any.whl

  # Verify signatures and checksums only
  uv run python scripts/verify_apache_artifacts.py signatures

  # Verify licenses with Apache RAT
  uv run python scripts/verify_apache_artifacts.py licenses --rat-jar /path/to/apache-rat.jar

  # Verify everything
  uv run python scripts/verify_apache_artifacts.py all --rat-jar /path/to/apache-rat.jar

  # Report-only mode (don't fail on license issues)
  uv run python scripts/verify_apache_artifacts.py licenses --rat-jar /path/to/apache-rat.jar --report-only

  # Custom artifacts directory
  uv run python scripts/verify_apache_artifacts.py all --artifacts-dir /path/to/artifacts --rat-jar /path/to/rat.jar
        """,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # list-contents subcommand
    list_parser = subparsers.add_parser(
        "list-contents", help="List contents of a specific artifact"
    )
    list_parser.add_argument("artifact", help="Path to artifact file (.tar.gz or .whl)")

    # signatures subcommand
    sig_parser = subparsers.add_parser(
        "signatures", help="Verify GPG signatures and SHA512 checksums"
    )
    sig_parser.add_argument(
        "--artifacts-dir",
        default="dist",
        help="Directory containing artifacts (default: dist)",
    )

    # licenses subcommand
    lic_parser = subparsers.add_parser("licenses", help="Verify licenses with Apache RAT")
    lic_parser.add_argument(
        "--artifacts-dir",
        default="dist",
        help="Directory containing artifacts (default: dist)",
    )
    lic_parser.add_argument("--rat-jar", required=True, help="Path to Apache RAT JAR file")
    lic_parser.add_argument(
        "--report-only",
        action="store_true",
        help="Generate report but don't fail on issues",
    )

    # all subcommand
    all_parser = subparsers.add_parser("all", help="Verify everything (signatures + licenses)")
    all_parser.add_argument(
        "--artifacts-dir",
        default="dist",
        help="Directory containing artifacts (default: dist)",
    )
    all_parser.add_argument(
        "--rat-jar", help="Path to Apache RAT JAR file (optional for signatures-only)"
    )
    all_parser.add_argument(
        "--report-only",
        action="store_true",
        help="Generate report but don't fail on license issues",
    )

    # twine-check subcommand
    twine_parser = subparsers.add_parser("twine-check", help="Verify wheel metadata with twine")
    twine_parser.add_argument(
        "--artifacts-dir",
        default="dist",
        help="Directory containing artifacts (default: dist)",
    )

    args = parser.parse_args()

    # Dispatch to command handler
    success = False
    try:
        if args.command == "list-contents":
            cmd_list_contents(args)
            sys.exit(0)
        elif args.command == "signatures":
            success = cmd_signatures(args)
        elif args.command == "licenses":
            success = cmd_licenses(args)
        elif args.command == "all":
            success = cmd_all(args)
        elif args.command == "twine-check":
            success = cmd_twine_check(args)
        else:
            _fail(f"Unknown command: {args.command}")
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    if success:
        print("\n✅ Verification completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Verification failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
