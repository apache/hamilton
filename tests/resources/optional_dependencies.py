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

from typing import Any, Dict

# Defaults
_A = 2
_B = 3
_D = 5
_F = 7


def c(b: int = _B, a: int = _A) -> int:
    """a+b"""
    return a + b


def e(c: int, d: int = _D) -> int:
    """a+b+d"""
    return c + d


def g(e: int, f: int = _F) -> int:
    """a+b+d+f"""
    return e + f


def i(h: int, f: int = _F) -> int:
    """we will pass None to e and so don't want the code to break for the unit test."""
    if h is None:
        h = 10
    return h + f


def none_result() -> int:
    """Function to show that we don't filter out the result."""
    return None


def j(none_result: int, f: int = _F) -> int:
    # dont use f.
    return none_result


def _do_all(a_val: int = _A, b_val: int = _B, d_val: int = _D, f_val: int = _F) -> Dict[str, Any]:
    c_val = c(a_val, b_val)
    e_val = e(c_val, d_val)
    g_val = g(e_val, f_val)
    return {"a": a_val, "b": b_val, "c": c_val, "d": d_val, "e": e_val, "f": f_val, "g": g_val}
