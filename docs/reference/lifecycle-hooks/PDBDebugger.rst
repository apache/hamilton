=====================
lifecycle.PDBDebugger
=====================


.. autoclass:: hamilton.lifecycle.default.PDBDebugger
   :special-members: __init__
   :members:
   :inherited-members:

Using PDBDebugger with Parallelizable
-------------------------------------

``PDBDebugger`` is not a good fit for parallel or multithreaded task-based
execution. Task-based execution is turned on with
``enable_dynamic_execution(allow_experimental_mode=True)``. See
:doc:`/concepts/parallel-task`. If you do not set a remote executor, the
builder defaults to ``MultiThreadingExecutor(max_tasks=10)``. Concurrent
mapped tasks then enter ``pdb`` at the same time and share one terminal:
prompts and command output interleave, a command can be consumed by a
different task than the one you intended, and the ``(Pdb)`` prompt itself
can be split by other tasks' logs.

``MultiProcessingExecutor`` is not usable with ``PDBDebugger``: worker
processes leave the debugger immediately and the run fails with
``bdb.BdbQuit``.

To debug a dataflow that uses ``Parallelizable`` and ``Collect``, set the
remote executor to ``SynchronousLocalTaskExecutor`` so each mapped task
finishes its debugger session before the next one starts:

.. code-block:: python

    # my_dataflow.py
    from hamilton.htypes import Collect, Parallelizable


    def items() -> Parallelizable[int]:
        for value in range(3):
            yield value


    def work(items: int) -> int:
        return items * 2


    def total(work: Collect[int]) -> int:
        return sum(work)

.. code-block:: python

    # run.py
    import my_dataflow
    from hamilton import driver
    from hamilton.execution.executors import SynchronousLocalTaskExecutor
    from hamilton.lifecycle import PDBDebugger

    dr = (
        driver.Builder()
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_modules(my_dataflow)
        .with_adapters(PDBDebugger(node_filter="work", before=True))
        .with_remote_executor(SynchronousLocalTaskExecutor())
        .build()
    )

    dr.execute(["total"])

``node_filter`` selects which nodes drop into the debugger. At least one of
``before``, ``during``, or ``after`` must be ``True``, or the adapter will
not open a ``pdb`` session.
