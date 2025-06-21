# DiskCache Adapter
This adapter uses [diskcache](https://grantjenks.com/docs/diskcache/tutorial.html) to cache node execution on disk. The cache key is a tuple of the function's
`(source code, input a, ..., input n)`. This means, a function will only be executed once for a given set of inputs,
and source code hash. The cache is stored in a directory of your choice, and it can be shared across different runs of your
code. That way as you develop, if the inputs and the code haven't changed, the function will not be executed again and
instead the result will be retrieved from the cache.

> 💡 This can be a great tool for developing inside a Jupyter notebook or other interactive environments.

Disk cache has great features to:
- set maximum cache size
- set automated eviction policy once maximum size is reached
- allow custom `Disk` implementations to change the serialization protocol (e.g., pickle, JSON)

> ⚠ The default `Disk` serializes objects using the `pickle` module. Changing Python or library versions could break your
> cache (both keys and values). Learn more about [caveats](https://grantjenks.com/docs/diskcache/tutorial.html#caveats).

> ❓ To store artifacts robustly, please use Apache Hamilton materializers or the
> [CachingGraphAdapter](https://github.com/apache/hamilton/tree/main/examples/caching_nodes/caching_graph_adatper) instead.
> The `CachingGraphAdapter` stores tagged nodes directly on the file system using common formats (JSON, CSV, Parquet, etc.).
> However, it isn't aware of your function version and requires you to manually manage your disk space.


# How to use it
## Use the hook
Find it under plugins at `hamilton.plugins.h_diskcache` and add it to your Driver definition.

```python
from hamilton import driver
from hamilton.plugins import h_diskcache
import functions

dr = (
    driver.Builder()
    .with_modules(functions)
    .with_adapters(h_diskcache.DiskCacheAdapter())
    .build()
)
```

## Inspect the hook
To inspect the caching behavior in real-time, you can get the logger:

```python
logger = logging.getLogger("hamilton.plugins.h_diskcache")
logger.setLevel(logging.DEBUG)  # or logging.INFO
logger.addHandler(logging.StreamHandler())
```
- INFO will only return the total cache after executing the Driver
- DEBUG will return inputs for each node and specify if the value is `from cache` or `executed`

## Clear cache
The utility function `h_diskcache.evict_all_except_driver` allows you to clear cached values for all nodes except those in the passed driver.
This is an efficient tool to clear old artifacts as your project evolves.

```python
from hamilton import driver
from hamilton.plugins import h_diskcache
import functions

dr = (
    driver.Builder()
    .with_modules(functions)
    .with_adapters(h_diskcache.DiskCacheAdapter())
    .build()
)
h_diskcache.evict_all_except_driver(dr)
```

## Cache settings
Find all the cache settings in the [diskcache docs](https://grantjenks.com/docs/diskcache/api.html#constants).
