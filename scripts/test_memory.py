"""
Script to test memory.
Run with mprof:
    pip install memory_profiler
    mprof run test_memory.py
    mprof plot
See https://github.com/DAGWorks-Inc/hamilton/pull/374 for more details.
"""

from hamilton import driver
from hamilton.ad_hoc_utils import create_temporary_module
from hamilton.function_modifiers import parameterize, source

NUM_ITERS = 100

import numpy as np
import pandas as pd


def foo_0(memory_size: int = 100_000_000) -> pd.DataFrame:
    """
    Generates a large DataFrame with memory size close to the specified memory_size_gb.

    Parameters:
    memory_size_gb (float): Desired memory size of the DataFrame in GB. Default is 1 GB.

    Returns:
    pd.DataFrame: Generated DataFrame with approximate memory usage of memory_size_gb.
    """
    # Number of rows in the DataFrame
    num_rows = 10**6

    # Calculate the number of columns required to make a DataFrame close to memory_size_gb
    # Assuming float64 type which takes 8 bytes
    bytes_per_row = 8 * num_rows
    target_bytes = memory_size
    num_cols = target_bytes // bytes_per_row

    # Create a DataFrame with random data
    data = {f"col_{i}": np.random.random(num_rows) for i in range(int(num_cols))}
    df = pd.DataFrame(data)

    # Print DataFrame info, including memory usage
    print(df.info(memory_usage="deep"))
    return df


count = 0


@parameterize(
    **{f"foo_{i}": {"foo_i_minus_one": source(f"foo_{i - 1}")} for i in range(1, NUM_ITERS)}
)
def foo_i(foo_i_minus_one: pd.DataFrame) -> pd.DataFrame:
    global count
    count += 1
    print(f"foo_{count}")
    return foo_i_minus_one * 1.01


if __name__ == "__main__":
    mod = create_temporary_module(foo_i, foo_0)
    dr = driver.Builder().with_modules(mod).build()
    output = dr.execute([f"foo_{NUM_ITERS - 1}"], inputs=dict(memory_size=100_000_000))
