<!--
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
-->

# Documentation

Instructions for managing documentation on read the docs.

# Build locally

To build locally, you need to run the following -- make sure you're in the root of the repo:

```bash
pip install --group docs
```
and then one of the following to build and view the documents:
```bash
sphinx-build -b dirhtml -W -E -T -a docs /tmp/mydocs
python -m http.server --directory /tmp/mydocs
```
or for auto rebuilding do:
```bash
sphinx-autobuild -b dirhtml -W -E -T  --watch hamilton/ -a docs /tmp/mydocs
```
Then it'll be running on port 8000.

Note: readthedocs builds will fail if there are ANY WARNINGs in the build.
So make sure to check the build log for any warnings, and fix them, else you'll waste time debugging readthedocs
build failures.

# SimplePDF
To create a PDF, you can run the following:
```bash
sphinx-build -b simplepdf  -W -E -T  -a docs /tmp/mydocs
# or if you want to auto-rebuild:
sphinx-autobuild -b simplepdf  -W -E -T  --watch hamilton/ -a docs /tmp/mydocs
```
The PDF will be in `/tmp/mydocs` in a few minutes.

# reST vs myST
We use both! The general breakdown of when to use which is:
1. For documentation that we want to be viewable in github, use myST.
2. Otherwise default to using reST.
