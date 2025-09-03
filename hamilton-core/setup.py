
import tomllib
import pathlib
import re
import os
import shutil
import sys
from setuptools import setup

# ensure the right current working directory
os.chdir(os.path.abspath(os.path.dirname(__file__)))

def copy_hamilton_library():
    setup_dir = pathlib.Path(__file__).resolve().parent
    source_dir = (setup_dir.parent / 'hamilton').resolve()
    dest_dir = (setup_dir / 'hamilton' / '_hamilton').resolve()

    # Safety checks
    if not source_dir.is_dir():
        print(f"Error: Source directory does not exist: {source_dir}")
        sys.exit(1)

    if not str(dest_dir).startswith(str(setup_dir)):
        print(f"Error: Destination directory {dest_dir} is outside the setup directory {setup_dir}")
        sys.exit(1)

    # Remove destination if it exists to avoid errors or stale files
    if dest_dir.exists():
        print("delete: ", dest_dir)
        shutil.rmtree(dest_dir)

    # Copy entire directory tree from source to destination
    print(f"copy from: {source_dir}; to {dest_dir}")
    shutil.copytree(source_dir, dest_dir)


def get_version():
    version_path = pathlib.Path(__file__).parent / "hamilton" / "_hamilton" / "version.py"
    content = version_path.read_text()
    match = re.search(r'^VERSION\s*=\s*\(([^)]+)\)', content, re.MULTILINE)
    if match:
        version_tuple_str = match.group(1)  # "1, 88, 0"
        # Parse tuple string into list of integers
        version_parts = [part.strip() for part in version_tuple_str.split(",")]
        version_str = ".".join(version_parts)
        return version_str

copy_hamilton_library()

pyproject_path = pathlib.Path(__file__).parents[1] / "pyproject.toml"
pyproject = tomllib.loads(pyproject_path.read_text())
project = pyproject["project"]

readme_file = project.get("readme", None)
console_scripts = [
    f"{name}={target}" for name, target in project.get("entry-points", {}).get("console_scripts", {}).items()
]
install_requires = list(
    set(project.get("dependencies", [])).difference(set(["pandas", "numpy"]))
)
extras_require = {
    **project.get("optional-dependencies", {}),
    **{"visualization": ["graphviz"]},  # drop networkx
}

setup(
    name="sf-hamilton-core",
    version=get_version(),
    description=project.get("description", ""),
    long_description=pathlib.Path(readme_file).read_text() if readme_file else "",
    long_description_content_type="text/markdown" if readme_file else None,
    python_requires=project.get("requires-python", None),
    license=project.get("license", {}).get("text", None),
    keywords=project.get("keywords", []),
    author=", ".join(a["name"] for a in project.get("authors", [])),
    author_email=", ".join(a["email"] for a in project.get("authors", [])),
    classifiers=project.get("classifiers", []),
    install_requires=install_requires,
    extras_require=extras_require,
    entry_points={"console_scripts": console_scripts},
    project_urls=project.get("urls", {}),
    packages=["hamilton"],
    package_data={"hamilton": ["*.json", "*.md", "*.txt"]},
)
