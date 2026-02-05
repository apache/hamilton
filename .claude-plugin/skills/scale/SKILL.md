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

---
name: hamilton-scale
description: Performance and parallelization patterns for Hamilton including async I/O, Spark, Ray, Dask, caching, and multithreading. Use for scaling Hamilton workflows.
allowed-tools: Read, Grep, Glob, Bash(python:*), Bash(pytest:*)
user-invocable: true
disable-model-invocation: false
---

# Hamilton Scaling & Performance

This skill covers parallelization strategies and performance optimization for Apache Hamilton workflows.

## When to Scale

Choose your scaling strategy based on workload:
- **Async**: I/O-bound operations (API calls, database queries)
- **MultiThreading**: Synchronous I/O (legacy APIs without async support)
- **Spark**: Large datasets (multi-GB to multi-TB) on clusters
- **Ray/Dask**: Distributed Python computation
- **Caching**: Avoid redundant expensive computations

## Async Execution for I/O-Bound Workflows

**When to Use:**
- API calls (LLM providers, REST APIs, GraphQL)
- Database queries (async ORM operations)
- Dependent chains of I/O-bound calls
- Multiple parallel external service calls

**Key Benefits:**
- Automatic parallelization of independent async operations
- Natural expression of dependent chains
- Mix async and sync functions in the same DAG
- Significantly faster than sequential execution

**Basic Async Pattern:**
```python
from hamilton import async_driver
import aiohttp
from typing import List

# Mix async and sync functions
async def api_data(user_id: str) -> dict:
    """Fetch from API (async I/O)."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.example.com/users/{user_id}") as resp:
            return await resp.json()

def transform_data(api_data: dict) -> dict:
    """Transform data (sync CPU)."""
    return {k: v.upper() if isinstance(v, str) else v for k, v in api_data.items()}

async def save_data(transform_data: dict) -> str:
    """Save to database (async I/O)."""
    async with db_pool.acquire() as conn:
        await conn.execute("INSERT INTO data VALUES ($1)", transform_data)
    return "success"

# Use AsyncDriver
import my_async_module
dr = await async_driver.Builder().with_modules(my_async_module).build()
result = await dr.execute(['save_data'], inputs={'user_id': '123'})
```

**Parallel I/O Operations:**
```python
# These three operations execute in parallel automatically!
async def user_data(user_id: str) -> dict:
    """Fetch user data."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.example.com/users/{user_id}") as resp:
            return await resp.json()

async def user_orders(user_id: str) -> List[dict]:
    """Fetch user orders (parallel with user_data)."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.example.com/orders?user={user_id}") as resp:
            return await resp.json()

async def user_preferences(user_id: str) -> dict:
    """Fetch preferences (parallel with both above)."""
    async with db_pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM preferences WHERE user_id=$1", user_id)

def user_profile(user_data: dict, user_orders: List[dict], user_preferences: dict) -> dict:
    """Combine all data (waits for all three to complete)."""
    return {"data": user_data, "orders": user_orders, "preferences": user_preferences}
```

## MultiThreading for Sync I/O

For synchronous I/O-bound code (legacy APIs, blocking libraries):

```python
from hamilton import driver
from hamilton.execution import executors

# Use multithreading for sync I/O operations
dr = driver.Builder()\
    .with_modules(my_functions)\
    .with_local_executor(executors.MultiThreadingExecutor(max_tasks=10))\
    .build()

# Sync functions that do I/O will run concurrently
results = dr.execute(['final_output'], inputs={...})
```

**When to Use:**
- Synchronous I/O code (requests library, blocking DB drivers)
- Legacy APIs without async support
- Simple parallelization without code rewrite

## Scaling with Apache Spark

**When to Use Spark:**
- Dataset size exceeds single-machine memory (multi-GB to multi-TB)
- You have access to a Spark cluster
- Need distributed data processing

**Basic PySpark Pattern:**
```python
from pyspark.sql import DataFrame as SparkDataFrame, SparkSession
from hamilton.plugins import h_spark

def raw_data(spark_session: SparkSession) -> SparkDataFrame:
    """Load data into Spark."""
    return spark_session.read.csv("data.csv", header=True)

def filtered_data(raw_data: SparkDataFrame) -> SparkDataFrame:
    """Filter using Spark operations."""
    return raw_data.filter(raw_data.age > 18)

def aggregated_stats(filtered_data: SparkDataFrame) -> SparkDataFrame:
    """Aggregate using Spark."""
    return filtered_data.groupBy("country").count()

# Driver Setup
dr = driver.Builder()\
    .with_modules(my_spark_functions)\
    .with_adapters(h_spark.SPARK_INPUT_CHECK)\
    .build()

result = dr.execute(['aggregated_stats'], inputs={'spark_session': spark})
```

**Column-Level Transformations with @with_columns:**
```python
from hamilton.plugins.h_spark import with_columns
import pandas as pd

# File: map_transforms.py
def normalized_amount(amount: pd.Series) -> pd.Series:
    """Pandas UDF for normalization."""
    return (amount - amount.mean()) / amount.std()

def amount_category(normalized_amount: pd.Series) -> pd.Series:
    """Categorize based on normalized amount."""
    return pd.cut(normalized_amount, bins=[-float('inf'), -1, 1, float('inf')],
                  labels=['low', 'medium', 'high'])

# Main dataflow
@with_columns(
    map_transforms,
    columns_to_pass=["amount"]
)
def enriched_data(raw_data: SparkDataFrame) -> SparkDataFrame:
    """Apply pandas UDFs to Spark DataFrame."""
    return raw_data
```

**Spark Best Practices:**
1. Keep transformations lazy - Don't call `.collect()` until final nodes
2. Use `@with_columns` for map operations
3. Partition wisely between major operations
4. Cache DataFrames accessed multiple times
5. Test with small data first (`.limit(1000)`)

## Ray for Distributed Python

**When to Use Ray:**
- Distributed Python computation
- Machine learning workloads
- Custom parallelization logic

```python
from hamilton.plugins import h_ray
import ray

ray.init()

ray_executor = h_ray.RayGraphAdapter(result_builder={"base": dict})

dr = driver.Driver({}, my_functions, adapter=ray_executor)
results = dr.execute(['large_computation'], inputs={...})
```

## Dask for Parallel Computing

**When to Use Dask:**
- Pandas-like operations on larger-than-memory datasets
- Parallel computation on single machine or cluster
- Incremental migration from pandas

```python
from hamilton.plugins import h_dask
from dask import distributed

cluster = distributed.LocalCluster()
client = distributed.Client(cluster)

dask_executor = h_dask.DaskExecutor(client=client)

dr = driver.Builder()\
    .with_remote_executor(dask_executor)\
    .with_modules(my_functions)\
    .build()
```

## Caching for Performance

**When to Use Caching:**
- Expensive API calls (LLM inference, external services)
- Time-consuming data processing
- Iterative development in notebooks
- Shared preprocessing between pipelines

**Basic Caching Setup:**
```python
from hamilton import driver

# Enable caching
dr = driver.Builder()\
    .with_modules(my_functions)\
    .with_cache()\
    .build()

# First execution: computes and caches
result1 = dr.execute(['final_output'], inputs={'data_path': 'data.csv'})

# Second execution: retrieves from cache (instant!)
result2 = dr.execute(['final_output'], inputs={'data_path': 'data.csv'})
```

**Controlling Cache Behavior:**
```python
from hamilton.function_modifiers import cache

# Always recompute (for data loaders)
@cache(behavior="recompute")
def live_api_data(api_key: str) -> dict:
    """Always fetch fresh data."""
    import requests
    response = requests.get("https://api.example.com/data",
                          headers={"Authorization": api_key})
    return response.json()

# Never cache (for non-deterministic operations)
@cache(behavior="disable")
def random_sample(data: pd.DataFrame) -> pd.DataFrame:
    """Random sampling should not be cached."""
    return data.sample(frac=0.1)

# Custom format for efficiency
@cache(format="parquet")
def large_dataframe(processed_data: pd.DataFrame) -> pd.DataFrame:
    """Store as parquet for efficiency."""
    return processed_data
```

**Driver-Level Cache Control:**
```python
dr = driver.Builder()\
    .with_modules(my_functions)\
    .with_cache(
        recompute=['raw_data'],  # Always recompute these
        disable=['random_sample'],  # Never cache these
        path="./my_cache"  # Custom location
    )\
    .build()

# Force complete refresh
dr = driver.Builder()\
    .with_modules(my_functions)\
    .with_cache(recompute=True)\
    .build()
```

**Cache Inspection:**
```python
# Visualize what was cached vs executed
dr.cache.view_run()  # Green = cache hit, Orange = executed

# Access cached results
run_id = dr.cache.last_run_id
data_version = dr.cache.data_versions[run_id]['my_node']
cached_result = dr.cache.result_store.get(data_version)
```

## Choosing the Right Scaling Strategy

**Decision Matrix:**

| Workload Type | Strategy | Use When |
|--------------|----------|----------|
| I/O-bound (async-capable) | AsyncDriver | Multiple API calls, async libraries available |
| I/O-bound (sync only) | MultiThreading | Legacy APIs, blocking I/O |
| Large datasets | Spark | Multi-GB/TB data, cluster available |
| Python computation | Ray/Dask | Custom parallel logic, ML workloads |
| Expensive operations | Caching | Repeated computations, LLM calls |

**Combining Strategies:**
- Cache + Async = Cache expensive API calls, parallelize independent calls
- Spark + Caching = Cache intermediate Spark results
- Ray + Caching = Distribute computation, cache results

## Performance Tips

1. **Profile first** - Identify bottlenecks before optimizing
2. **Start simple** - Begin with caching, add parallelization if needed
3. **Measure impact** - Benchmark before and after changes
4. **Consider costs** - Serialization overhead can negate parallelization benefits
5. **Test at scale** - Small data may hide parallelization overhead

## Additional Resources

- For basic Hamilton patterns, use `/hamilton-core`
- For LLM-specific workflows, use `/hamilton-llm`
- Apache Hamilton docs: hamilton.apache.org/concepts/parallel-task
