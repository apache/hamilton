=======================
config.when*
=======================

``@config.when`` allows you to specify different implementations depending on configuration parameters.

Note the following:

* The function cannot have the same name in the same file (or python gets unhappy), so we name it with a \_\_ (dunderscore) as a suffix. The dunderscore is removed before it goes into the DAG.

* There is currently no ``@config.otherwise(...)`` decorator, so make sure to have ``config.when`` specify set of configuration possibilities. Any missing cases will not have that output column (and subsequent downstream nodes may error out if they ask for it). To make this easier, we have a few more ``@config`` decorators:

  * ``@config.when_not(param=value)`` Will be included if the parameter is _not_ equal to the value specified.

  * ``@config.when_in(param=[value1, value2, ...])`` Will be included if the parameter is equal to one of the specified values.

  * ``@config.when_not_in(param=[value1, value2, ...])`` Will be included if the parameter is not equal to any of the specified values.

  * ``@config`` If you're feeling adventurous, you can pass in a lambda function that takes in the entire configuration and resolves to ``True`` or ``False``. You probably don't want to do this.

* To always exclude a function (such as helper functions) from the DAG the most straightforward and preferred pattern is to prefix it with "_", but you can also use ``@hamilton_exclude``.

----

**Reference Documentation**

.. autoclass:: hamilton.function_modifiers.config
   :special-members: __init__

.. autoclass:: hamilton.function_modifiers.configuration.hamilton_exclude
