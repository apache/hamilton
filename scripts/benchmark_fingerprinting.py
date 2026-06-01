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

"""Corroborating benchmark for the pandas fingerprinting speedup.

Compares the new vectorized :func:`hamilton.caching.fingerprinting.hash_pandas_obj`
(single buffer hash over ``hash_pandas_object(...).values``) against the old
per-row approach (``hash_pandas_object(...).to_dict()`` fed through an ordered
``hash_mapping``, which loops over rows in Python).

The structural "no per-row loop" assertion in the test suite is the hard gate;
this script is corroborating evidence with a generous 5x floor to avoid the
flakiness of an absolute-time threshold. Run directly:

    python scripts/benchmark_fingerprinting.py
"""

import time

import pandas as pd

from hamilton.caching import fingerprinting as fp

N_ROWS = 500_000
MIN_SPEEDUP = 5.0


def _old_hash_pandas_obj(obj) -> str:
    """The pre-change per-row implementation, kept here only for comparison."""
    from pandas.util import hash_pandas_object

    hash_per_row = hash_pandas_object(obj)
    return fp.hash_mapping(hash_per_row.to_dict(), ignore_order=False, depth=1)


def _time(fn, obj, repeats: int = 3) -> float:
    best = float("inf")
    for _ in range(repeats):
        start = time.perf_counter()
        fn(obj)
        best = min(best, time.perf_counter() - start)
    return best


def main() -> None:
    df = pd.DataFrame(
        {
            "a": range(N_ROWS),
            "b": [float(i) for i in range(N_ROWS)],
            "c": [f"row-{i}" for i in range(N_ROWS)],
        }
    )

    old = _time(_old_hash_pandas_obj, df)
    new = _time(fp.hash_pandas_obj, df)
    speedup = old / new

    print(f"rows={N_ROWS}")
    print(f"old per-row loop : {old * 1000:.1f} ms")
    print(f"new vectorized   : {new * 1000:.1f} ms")
    print(f"speedup          : {speedup:.1f}x")

    assert speedup >= MIN_SPEEDUP, (
        f"expected >= {MIN_SPEEDUP}x speedup, measured {speedup:.1f}x "
        f"(old={old * 1000:.1f} ms, new={new * 1000:.1f} ms)"
    )
    print(f"OK: vectorized pandas hashing is {speedup:.1f}x faster (>= {MIN_SPEEDUP}x floor)")


if __name__ == "__main__":
    main()
