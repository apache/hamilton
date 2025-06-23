===================
Output Immutability
===================

In Apache Hamilton, functions are only called once!

Immutability means, that once a "data structure", e.g. a column is created, and output by a function, the values in the
column are not changeable.

When Apache Hamilton figures out the execution call path, it walks it and calls functions only once. This means, that if the
output of a function is immutable, then there's only one place it was created; it's not modified anywhere else. This
provides a great debugging experience if there are ever issues in your dataflow. We believe that by default, one should
always strive for immutability of outputs.

However, it is up to you, the Hamilton function writer, to ensure that immutability is something that is adhered to.

Best practice:
--------------

#. To preserve “immutability” of outputs, don’t mutate passed in data structures. e.g. if you get passed in a pandas series, don’t mutate it.

   #. Test for this in your unit tests if this is something important to you!

#. Otherwise YMMV with debugging:

   #. Clearly document mutating inputs in your function documentation if you do mutate inputs provided. That will make debugging your code that much simpler!
