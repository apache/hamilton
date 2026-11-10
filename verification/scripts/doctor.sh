#!/bin/sh
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

# verify doctor: says whether this machine runs the recipes on a Python CI tests. Run it from the
# repository root, as `scripts/verify doctor` does.
set -u

uv --version || exit 1
if [ -f uv.lock ]; then
  echo 'uv.lock pins the versions drives install, while CI resolves the newest releases: delete it to resolve as CI does'
fi
# The Pythons the workflow's test job runs, read by the parser recipes-match-ci compares with.
ci=$(uv run --quiet --script verification/scripts/check_recipes_match_ci.py --root . --pythons) || exit 1
if [ ! -x .venv/bin/python ]; then
  echo "no .venv yet: the first scenario creates it with the newest Python uv finds, which CI may not test ($ci); uv sync --python <one of those> picks one it does"
  exit 0
fi
v=$(.venv/bin/python -c 'import sys; print("%d.%d" % sys.version_info[:2])') || exit 1
case " $ci " in
  *" $v "*) echo ".venv runs Python $v, one CI tests ($ci)" ;;
  *) echo ".venv runs Python $v, which CI does not test ($ci): uv sync --python <one of those> gives it one" >&2; exit 1 ;;
esac
