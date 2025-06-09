=======================
Caching logic
=======================

Caching Behavior
----------------

.. autoclass:: hamilton.caching.adapter.CachingBehavior
   :exclude-members: __init__, from_string
   :members:

   .. automethod:: from_string


``@cache`` decorator
----------------------

.. autoclass:: hamilton.function_modifiers.metadata.cache
   :special-members: __init__
   :private-members:
   :members:
   :exclude-members: BEHAVIOR_KEY, FORMAT_KEY

   .. autoattribute:: BEHAVIOR_KEY

   .. autoattribute:: FORMAT_KEY


Logging
-----------

.. autoclass:: hamilton.caching.adapter.CachingEvent
   :special-members: __init__
   :members:
   :inherited-members:


.. autoclass:: hamilton.caching.adapter.CachingEventType
   :special-members: __init__
   :members:
   :inherited-members:


Adapter
--------

.. autoclass:: hamilton.caching.adapter.HamiltonCacheAdapter
   :special-members: __init__
   :members:
   :inherited-members:


Quirks and limitations
----------------------

Caching is a large and complex feature. This section is an attempt to list quirks and limitations, known and theoretical, to help debugging and guide feature development

- The standard library includes a lot of types which are not primitives. Thus, Apache Hamilton might not be supporting them explicitly. It should be simple to add, so ping us if you need it.
- The ``ResultStore`` could be architectured better to support custom formats. Right now, we use a ``DataSaver`` to produce the ``.parquet`` file and we pickle the ``DataLoader`` for later retrieval. Then, the metadata and result stores are completely unaware of the ``.parquet`` file making it difficult to handle cache eviction.
- When a function with default parameter values passes through lifecycle hooks, the default values are not part of the ``node_kwargs``. They need to be retrieved manually from the ``node.Node`` object.
- supporting the Apache Hamilton ``AsyncDriver`` would require making the adapter async, but also the stores. A potential challenge is ensuring that you can use the same cache (i.e., same SQLite db and filesystem) for both sync and async drivers.
- If the ``@cache`` allows to specify the ``format`` (e.g., ``json``, ``parquet``), we probably want ``.with_cache()`` to support the same feature.
- Apache Hamilton allows a single ``do_node_execute()`` hook. Since the caching feature uses it, it is currently incompatible with other adapters leveraging it (``PDBDebugger``, ``CacheAdapter`` (deprecated), ``GracefulErrorAdapter`` (somewhat redundant with caching), ``DiskCacheAdapter`` (deprecated), ``NarwhalsAdapter`` (could be refactored))
- the presence of MD5 hashing can be seen as a security risk and prevent adoption. `read more in DVC issues <https://github.com/iterative/dvc/issues/3069>`_
- when hitting the base case of ``fingerprinting.hash_value()`` we return the constant ``UNHASHABLE_VALUE``. If the adapter receives this value, it will append a random UUID to it. This is to prevent collision between unhashable types. This ``data_version`` is no longer deterministic, but the value can still be retrieved or be part of another node's ``cache_key``.
- having ``@functools.singledispatch(object)`` allows to override the base case of ``hash_value()`` because it will catch all types.
