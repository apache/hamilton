# /usr/bin/env python

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

# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import find_packages, setup

REQUIREMENTS_FILES = ["requirements.txt"]


def load_requirements():
    # TODO -- confirm below works/delete this
    requirements = {"click", "loguru", "requests", "typer"}
    with open("hamilton_ui/requirements-mini.txt") as f:
        requirements.update(line.strip() for line in f)
    return list(requirements)


setup(
    name="sf-hamilton-ui",  # there's already a hamilton in pypi
    version="0.0.17",
    description="Hamilton, the micro-framework for creating dataframes.",
    long_description="""Hamilton tracking server, see [the docs for more](https://github.com/apache/hamilton/tree/main/ui/)""",
    long_description_content_type="text/markdown",
    author="Stefan Krawczyk, Elijah ben Izzy",
    author_email="stefank@cs.stanford.edu,elijah@dagworks.io",
    url="https://github.com/apache/hamilton",
    packages=find_packages(exclude=["tests"], include=["hamilton_ui", "hamilton_ui.*"]),
    include_package_data=True,
    install_requires=load_requirements(),
    zip_safe=False,
    keywords="hamilton",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    # Note that this feature requires pep8 >= v9 and a version of setup tools greater than the
    # default version installed with virtualenv. Make sure to update your tools!
    python_requires=">=3.6, <4",
    # adding this to slim the package down, since these dependencies are only used in certain contexts.
    # Relevant project URLs
    project_urls={  # Optional
        "Bug Reports": "https://github.com/apache/hamilton/issues",
        "Source": "https://github.com/apache/hamilton",
    },
)
