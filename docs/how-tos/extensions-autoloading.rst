=====================
Extension autoloading
=====================

Under ``hamilton.plugins``, there are many modules named ``*_extensions`` (e.g., ``hamilton.plugins.pandas_extensions``, ``hamilton.plugins.mlflow_extensions``). They implement Apache Hamilton features for 3rd party libraries, including ``@extract_columns``, materializers (``to.parquet``, ``from_.mlflow``), and more.


Autoloading behavior
--------------------

By default, Apache Hamilton attempts to load all extensions one-by-one. This means that as you have more Python packages in your environment (e.g., ``pandas``, ``pyspark``, ``mlflow``, ``xgboost``), importing Apache Hamilton appears to become slower because it actually imports many packages.

This behavior can be less desirable when your Apache Hamilton dataflow doesn't use any of these packages, but you need them in your Python environment nonetheless. For example, if only ``pandas`` is needed for your dataflow, but you have ``mlflow`` and ``xgboost`` in your environment their respective extensions will be loaded each time.


Disable autoloading
--------------------

Disabling extension autoloading allows to import Apache Hamilton without any extensions, which can reduce import time from 2-3 sec to less than 0.5 sec. This speedup is welcomed when you need to restart a notebook's kernel often or you're operating in a low RAM environment (some Python packages are larger than 50Mbs).

There are three ways to opt-out: programmatically, environment variables, configuration file. You must opt-out before having any other ``hamilton`` import.

1. Programmatically
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from hamilton import registry
    registry.disable_autoload()

2. Environment variables
~~~~~~~~~~~~~~~~~~~~~~~~

From the console

.. code-block:: console

    export HAMILTON_AUTOLOAD_EXTENSIONS=0

Programmatically via Python ``os.environ``.

.. code-block:: python

    import os
    os.environ["HAMILTON_AUTOLOAD_EXTENSIONS"] = "0"

Programmatically in Jupyter notebooks

.. code-block:: python

    %env HAMILTON_AUTOLOAD_EXTENSIONS=0

3. Configuration file
~~~~~~~~~~~~~~~~~~~~~

Using the following command disables autoloading via the configuration file ``./hamilton.conf``. Apache Hamilton won't autoload extensions anymore (i.e., you won't need to use approach 1 or 2 each time).

.. code-block:: console

    hamilton-disable-autoload-extensions

To revert this configuration use the following command

.. code-block:: console

    hamilton-enable-autoload-extensions

To reenable autoloading in specific files, you can delete the environment variable or use ``registry.enable_autoload()`` before calling ``registry.initialize()``

.. code-block:: python

    from hamilton import registry
    registry.enable_autoload()
    registry.initialize()


Manually loading extensions
----------------------------

If you disabled autoloading, extensions need to be loaded manually. You should load them before having any other ``hamilton`` import to avoid hard-to-track bugs. There are two ways.

1. Importing the extension
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from hamilton.plugins import pandas_extensions, mlflow_extensions

2. Registering the extension
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This approach has good IDE support via ``typing.Literal``

.. code-block:: python

    from hamilton import registry
    registry.load_extensions("mlflow")
