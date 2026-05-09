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

"""Generate release announcement emails for Apache Hamilton packages.

Produces two emails:
  1. [RESULT][VOTE] email for dev@hamilton.apache.org (vote result)
  2. [ANNOUNCE] email for user@hamilton.apache.org (release announcement)

Usage:
    python generate_announce_email.py --package hamilton --version 1.90.0 --rc 0 --tag apache-hamilton-v1.90.0-incubating-RC0
    python generate_announce_email.py --package sdk --version 0.9.0 --rc 0 --tag apache-hamilton-sdk-v0.9.0-incubating-RC0
"""

import argparse
import re
import subprocess
import sys

PACKAGE_DISPLAY_NAMES = {
    "hamilton": "apache-hamilton",
    "sdk": "apache-hamilton-sdk",
    "lsp": "apache-hamilton-lsp",
    "contrib": "apache-hamilton-contrib",
    "ui": "apache-hamilton-ui",
}

PYPI_NAMES = {
    "hamilton": "apache-hamilton",
    "sdk": "apache-hamilton-sdk",
    "lsp": "apache-hamilton-lsp",
    "contrib": "apache-hamilton-contrib",
    "ui": "apache-hamilton-ui",
}

PROJECT = "hamilton"

PACKAGE_PATHS = {
    "hamilton": ["hamilton/", "plugin_tests/", "tests/", "pyproject.toml"],
    "sdk": ["ui/sdk/"],
    "lsp": ["dev_tools/language_server/"],
    "contrib": ["contrib/"],
    "ui": ["ui/backend/", "ui/frontend/"],
}


def linkify_prs(text: str) -> str:
    """Replace (#1234) references with full GitHub PR links."""
    return re.sub(
        r"\(#(\d+)\)",
        rf"(https://github.com/apache/{PROJECT}/pull/\1)",
        text,
    )


def get_commit_hash(tag: str) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", tag]).decode().strip()
    except subprocess.CalledProcessError:
        return "[INSERT COMMIT HASH]"


def get_new_contributors(tag: str, package_key: str) -> list[str]:
    """Find authors who contributed to this release but have no commits before the previous tag."""
    try:
        all_tags = (
            subprocess.check_output(["git", "tag", "--sort=-creatordate"]).decode().strip().split()
        )
        package_name = PACKAGE_DISPLAY_NAMES[package_key]
        matching = [t for t in all_tags if t.startswith(package_name)]
        if package_key == "hamilton":
            matching += [t for t in all_tags if t.startswith("sf-hamilton-")]
        if len(matching) < 2:
            return []
        prev_tag = matching[1]

        paths = PACKAGE_PATHS.get(package_key, [])

        def authors_in_range(rev_range):
            cmd = ["git", "log", "--format=%aN", rev_range, "--"]
            cmd.extend(paths)
            output = subprocess.check_output(cmd).decode().strip()
            return set(output.split("\n")) if output else set()

        current_authors = authors_in_range(f"{prev_tag}..{tag}")
        historical_authors = authors_in_range(prev_tag)
        return sorted(current_authors - historical_authors)
    except subprocess.CalledProcessError:
        return []


def get_changes_since_last_tag(tag: str, package_key: str) -> list[str]:
    """Get notable commits between the previous tag and this one, filtered to package paths."""
    try:
        all_tags = (
            subprocess.check_output(["git", "tag", "--sort=-creatordate"]).decode().strip().split()
        )
        package_name = PACKAGE_DISPLAY_NAMES[package_key]
        matching = [t for t in all_tags if t.startswith(package_name)]
        if package_key == "hamilton":
            matching += [t for t in all_tags if t.startswith("sf-hamilton-")]
        if len(matching) >= 2:
            prev_tag = matching[1]
        else:
            return ["[List key changes here]"]

        paths = PACKAGE_PATHS.get(package_key, [])
        cmd = ["git", "log", "--oneline", "--no-merges", f"{prev_tag}..{tag}", "--"]
        cmd.extend(paths)

        lines = subprocess.check_output(cmd).decode().strip().split("\n")
        notable = []
        for line in lines:
            if not line.strip():
                continue
            lower = line.lower()
            if any(skip in lower for skip in ["bump ", "bumps ", "bump-", "dependabot"]):
                continue
            if any(
                skip in lower
                for skip in [
                    "adds missing license",
                    "adds header",
                    "license header",
                    "linting",
                    ".rat-excludes",
                ]
            ):
                continue
            msg = line.split(" ", 1)[1] if " " in line else line
            notable.append(msg)
        return notable[:20] if notable else ["[List key changes here]"]
    except subprocess.CalledProcessError:
        return ["[List key changes here]"]


def generate_vote_result_email(
    package_key: str, version: str, rc: str, binding: int, nonbinding: int
) -> str:
    package_name = PACKAGE_DISPLAY_NAMES[package_key]
    version_incubating = f"{version}-incubating"

    return f"""\
Subject: [RESULT][VOTE] Release Apache {PROJECT} - {package_name} {version_incubating} (RC{rc})

Hi all,

The vote to release Apache Hamilton {package_name} {version_incubating} (RC{rc})
has passed with the following results:

+1 (binding): {binding}
+1 (non-binding): {nonbinding}
+0: 0
-1: 0

The vote thread is here:
[INSERT LINK TO VOTE THREAD]

Thank you to everyone who voted and helped verify this release!

We will proceed with finalizing the release.

On behalf of the Apache Hamilton PPMC,
[Your Name]
"""


def generate_announce_email(
    package_key: str, version: str, tag: str, changes: list[str], new_contributors: list[str]
) -> str:
    package_name = PACKAGE_DISPLAY_NAMES[package_key]
    pypi_name = PYPI_NAMES[package_key]
    version_incubating = f"{version}-incubating"
    commit_hash = get_commit_hash(tag)

    changes_str = "\n".join(f"  - {linkify_prs(c)}" for c in changes)
    contributors_str = ""
    if new_contributors:
        contributors_str = "\n\nWelcome to our new contributors:\n" + "\n".join(
            f"  - {c}" for c in new_contributors
        )

    return f"""\
Subject: [ANNOUNCE] Apache Hamilton {package_name} {version_incubating} released

Hi everyone,

The Apache Hamilton community is pleased to announce the release of
Apache Hamilton {package_name} {version_incubating}.

Apache Hamilton is a lightweight framework for describing dataflows
in Python. You write regular Python functions, and Hamilton builds a
directed acyclic graph (DAG) that it can execute, validate, and
visualize for you.

Notable changes in this release:
{changes_str}

Install or upgrade via pip:

    pip install {pypi_name}=={version}

The release is available at:
  - PyPI: https://pypi.org/project/{pypi_name}/{version}/
  - Source: https://dist.apache.org/repos/dist/release/incubator/{PROJECT}/{package_name}/{version}/
  - Git tag: {tag} ({commit_hash})
  - GitHub: https://github.com/apache/{PROJECT}/releases/tag/{tag}

The KEYS file is available at:
https://downloads.apache.org/incubator/{PROJECT}/KEYS

For documentation and getting started, see:
  - https://hamilton.apache.org/
  - https://github.com/apache/{PROJECT}

Thank you to everyone who contributed to this release!{contributors_str}

On behalf of the Apache Hamilton community,
[Your Name]

---
DISCLAIMER: Apache Hamilton is an effort undergoing incubation at
The Apache Software Foundation (ASF), sponsored by the Apache
Incubator. Incubation is required of all newly accepted projects
until a further review indicates that the infrastructure,
communications, and decision making process have stabilized in a
manner consistent with other successful ASF projects. While
incubation status is not necessarily a reflection of the
completeness or stability of the code, it does indicate that the
project has yet to be fully endorsed by the ASF.
"""


def generate_slack_message(
    package_key: str, version: str, tag: str, changes: list[str], new_contributors: list[str]
) -> str:
    package_name = PACKAGE_DISPLAY_NAMES[package_key]
    pypi_name = PYPI_NAMES[package_key]
    version_incubating = f"{version}-incubating"

    changes_str = "\n".join(f"• {linkify_prs(c)}" for c in changes)

    slack_contributors = ""
    if new_contributors:
        slack_contributors = f"\n:wave: *Welcome new contributors:* {', '.join(new_contributors)}\n"

    return f"""\
:tada: *Apache Hamilton `{package_name}` {version_incubating} released!*

{changes_str}

*Install:* `pip install {pypi_name}=={version}`
*PyPI:* https://pypi.org/project/{pypi_name}/{version}/
*GitHub:* https://github.com/apache/{PROJECT}/releases/tag/{tag}
*Docs:* https://hamilton.apache.org/
{slack_contributors}"""


def main():
    parser = argparse.ArgumentParser(
        description="Generate release announcement emails for Apache Hamilton."
    )
    parser.add_argument(
        "--package",
        required=True,
        choices=list(PACKAGE_DISPLAY_NAMES.keys()),
        help="Which package (hamilton, sdk, lsp, contrib, ui)",
    )
    parser.add_argument("--version", required=True, help="Release version (e.g., 1.90.0)")
    parser.add_argument("--rc", required=True, help="RC number that passed (e.g., 0)")
    parser.add_argument("--tag", required=True, help="Git tag for the release")
    parser.add_argument(
        "--binding-votes",
        type=int,
        default=3,
        help="Number of binding +1 votes (default: 3)",
    )
    parser.add_argument(
        "--nonbinding-votes",
        type=int,
        default=0,
        help="Number of non-binding +1 votes (default: 0)",
    )
    args = parser.parse_args()

    # Validate the tag exists
    try:
        subprocess.check_output(["git", "rev-parse", args.tag], stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print(f"Error: Git tag '{args.tag}' not found.")
        sys.exit(1)

    # Warn if tag is reachable from main (it shouldn't include un-voted commits)
    is_on_main = subprocess.run(
        ["git", "merge-base", "--is-ancestor", args.tag, "main"],
        capture_output=True,
    )
    if is_on_main.returncode != 0:
        print(
            f"Note: Tag '{args.tag}' is not on main (expected for a release branch).\n"
            f"      Changelog will only include commits reachable from the tag.\n"
        )

    changes = get_changes_since_last_tag(args.tag, args.package)
    new_contributors = get_new_contributors(args.tag, args.package)

    separator = "=" * 80

    print(f"\n{separator}")
    print("  EMAIL 1: Vote Result (send to dev@hamilton.apache.org)")
    print(f"{separator}\n")
    print(
        generate_vote_result_email(
            args.package, args.version, args.rc, args.binding_votes, args.nonbinding_votes
        )
    )

    print(f"\n{separator}")
    print("  EMAIL 2: Release Announcement (send to user@hamilton.apache.org)")
    print(f"{separator}\n")
    print(generate_announce_email(args.package, args.version, args.tag, changes, new_contributors))

    print(f"\n{separator}")
    print("  SLACK: Release Announcement (copy-paste to Slack)")
    print(f"{separator}\n")
    print(generate_slack_message(args.package, args.version, args.tag, changes, new_contributors))


if __name__ == "__main__":
    main()
