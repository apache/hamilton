Wrapping the Driver
------------------------------

The APIs that the Hamilton Driver is built on, are considered internal. So it is possible for you to define your own
driver in place of the stock Hamilton Driver, we suggest the following path if you don't like how the current Apache Hamilton
Driver interface is designed:

`Write a "Wrapper" class that delegates to the Hamilton Driver.`

i.e.

.. code-block:: python

    from hamilton import driver

    class MyCustomDriver(object):
        def __init__(self, constructor_arg, ...):
           self.constructor_arg = constructor_arg
           ...
        # some internal functions specific to your context
        # ...

        def my_execute_function(self, arg1, arg2, ...):
            """What actually calls the Hamilton"""
            dr = driver.Driver(self.constructor_arg, ...)
            df = dr.execute(self.outputs)
            return self.augmetn(df)

That way, you can create the right API constructs to invoke Hamilton in your context, and then delegate to the stock
Hamilton Driver. By doing so, it will ensure that your code continues to work, since we intend to honor the Hamilton
Driver APIs with backwards compatibility as much as possible.
