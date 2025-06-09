=======
License
=======

Apache Hamilton is released under the `Apache 2.0 License <https://github.com/apache/hamilton/blob/main/LICENSE>`_.



Usage analytics & data privacy
-----------------------------------
By default, when using Apache Hamilton, it collects anonymous usage data to help improve Apache Hamilton and know where to apply development
efforts.

We capture three types of events: one when the `Driver` object is instantiated, one when the `execute()` call on the \
`Driver` object completes, and one for most `Driver` object function invocations.
No user data or potentially sensitive information is or ever will be collected. The captured data is limited to:

* Operating System and Python version
* A persistent UUID to indentify the session, stored in ~/.hamilton.conf.
* Error stack trace limited to Apache Hamilton code, if one occurs.
* Information on what features you're using from Apache Hamilton: decorators, adapters, result builders.
* How Apache Hamilton is being used: number of final nodes in DAG, number of modules, size of objects passed to `execute()`, \
  the name of the Driver function being invoked.


Else see :doc:`/reference/disabling-telemetry` for how to disable telemetry.

Otherwise we invite you to inspect telemetry.py for details.
