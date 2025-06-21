import os
import re
import subprocess
import sys

# required to get reference documentation to be built
sys.path.insert(0, os.path.abspath(".."))

project = "Hamilton"

html_theme = "furo"
html_title = "Hamilton"
html_theme_options = {
    "source_repository": "https://github.com/apache/hamilton",
    "source_branch": "main",
    "source_directory": "docs/",
    "announcement": "📢 Announcing the "
    + '<a target="_blank" href="https://www.meetup.com/global-hamilton-open-source-user-group-meetup/">Hamilton Meetup Group</a>. Sign up to attend events! 📢',
    "light_css_variables": {
        "color-announcement-background": "#ffba00",
        "color-announcement-text": "#091E42",
    },
    "dark_css_variables": {
        "color-announcement-background": "#ffba00",
        "color-announcement-text": "#091E42",
    },
}
html_static_path = ["_static"]
templates_path = ['_templates']

html_css_files = [
    "testimonials.css",
]
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "myst_nb",
    "sphinx_sitemap",
    "docs.data_adapters_extension",
]

nb_execution_mode = "off"

# this is required to get simplepdf to work
nb_mime_priority_overrides = [
    ["simplepdf", "application/vnd.jupyter.widget-view+json", 10],
    ["simplepdf", "application/javascript", 20],
    ["simplepdf", "text/html", 30],
    ["simplepdf", "image/svg+xml", 40],
    ["simplepdf", "image/png", 50],
    ["simplepdf", "image/gif", 60],
    ["simplepdf", "image/jpeg", 70],
    ["simplepdf", "text/markdown", 80],
    ["simplepdf", "text/latex", 90],
    ["simplepdf", "text/plain", 100],
]


# for the sitemap extension ---
# check if the current commit is tagged as a release (vX.Y.Z) and set the version
GIT_TAG_OUTPUT = subprocess.check_output(["git", "tag", "--points-at", "HEAD"])
current_tag = GIT_TAG_OUTPUT.decode().strip()
if re.match(r"^sf-hamilton-(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$", current_tag):
    version = current_tag
else:
    version = "latest"
language = "en"
GIT_BRANCH_OUTPUT = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
current_branch = GIT_BRANCH_OUTPUT.decode().strip()
if current_branch == "main":
    html_baseurl = "https://hamilton.apache.org/"
else:
    html_baseurl = "https://hamilton.staged.apache.org/"
html_extra_path = ["robots.txt"]
# ---
