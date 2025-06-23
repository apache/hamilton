=============
Visualization
=============

After assembling the dataflow, several visualization features become available to the Driver. Apache Hamilton dataflow visualizations are great for documentation because they are directly derived from the code.

On this page, you'll learn:

- the available visualization functions
- how to answer lineage questions
- how to apply a custom style to your visualization

For this page, we'll assume we have the following dataflow and Driver:

.. code-block:: python

    # my_dataflow.py
    def A() -> int:
        """Constant value 35"""
        return 35

    def B(A: int) -> float:
        """Divide A by 3"""
        return A / 3

    def C(A: int, B: float) -> float:
        """Square A and multiply by B"""
        return A**2 * B

    def D(A: int) -> str:
        """Say `hello` A times"""
        return "hello "

    def E(D: str) -> str:
        """Say hello*A world"""
        return D + "world"

    # run.py
    from hamilton import driver
    import my_dataflow

    dr = driver.Builder().with_modules(my_dataflow).build()


Available visualizations
------------------------

View full dataflow
~~~~~~~~~~~~~~~~~~

During development and for documentation, it's most useful to view the full dataflow and all nodes.

.. code-block:: python

    dr.display_all_functions(...)

.. image:: _visualization/display_all.png
    :height: 200px

View executed dataflow
~~~~~~~~~~~~~~~~~~~~~~

Visualizing exactly which nodes were executed is more helpful than viewing the full dataflow when logging driver execution (e.g., ML experiments).

You should produce the visualization before executing the dataflow. Otherwise, the figure won't be generated if the execution fails first.

.. code-block:: python

    # pull variables to ensure .execute() and
    # .visualize_execution() receive the same
    # arguments
    final_vars = ["A", "C", "E"]
    inputs = dict()
    overrides = dict(B=36.1)

    dr.visualize_execution(
        final_vars=final_vars,
        inputs=inputs,
        overrides=overrides,
    )
    dr.execute(
        final_vars=final_vars,
        inputs=inputs,
        overrides=overrides,
    )

.. image:: _visualization/execution.png
    :height: 250px

An equivalent method is available if you're using materialization.

.. code-block:: python

    materializer =  to.json(
        path="./out.json",
        dependencies=["C", "E"],
        combine=base.DictResult(),
        id="results_to_json",
    )
    additional_vars = ["A"]
    inputs = dict()
    overrides = dict(B=36.1)

    dr.visualize_materialization(
        materializer,
        additional_vars=additional_vars,
        inputs=inputs,
        overrides=dict(B=36.1),
        output_file_path="dag.png"
    )
    dr.materialize(
        materializer,
        additional_vars=additional_vars,
        inputs=inputs,
        overrides=dict(B=36.1),
    )

.. image:: _visualization/materialization.png
    :height: 250px


Learn more about :doc:`materialization`.

View node dependencies
----------------------

Representing data pipelines, ML experiments, or LLM applications as a dataflow helps reason about the dependencies between operations. The Hamilton Driver has the following utilities to select and return a list of nodes (to learn more :doc:`../how-tos/use-hamilton-for-lineage`):

- ``.what_is_upstream_of(*node_names: str)``
- ``.what_is_downstream_of(*node_names: str)``
- ``.what_is_the_path_between(upstream_node_name: str, downstream_node_name: str)``

These functions are wrapped into their visualization counterparts:

Display ancestors of ``B``:

.. code-block:: python

    dr.display_upstream(["B"])

.. image:: _visualization/upstream.png
    :height: 200px

Display descendants of ``D`` and its immediate parents (``A`` only).

.. code-block:: python

    dr.display_downstream(["D"])

.. image:: _visualization/downstream.png
    :height: 200px

Filter nodes to the necessary path:

.. code-block:: python

    dr.visualize_path-between("A", "C")
    # dr.visualize_path-between("C", "D") would return
    # ValueError: No path found between C and D.

.. image:: _visualization/between.png
    :height: 200px

Configure your visualization
----------------------------

All of the above visualization functions share parameters to customize the visualization (e.g., hide legend, hide inputs). Learn more by reviewing the API reference for `Driver.display_all_functions() <https://hamilton.apache.org/reference/drivers/Driver/#hamilton.driver.Driver.display_all_functions>`_; parameters should apply to all other visualizations.

.. _custom-visualization-style:

Apply custom style
~~~~~~~~~~~~~~~~~~

By default, each node is labeled with name and type, and stylized (shape, color, outline, etc.). By passing a function to the parameter ``custom_style_function``, you can customize the node style based on its attributes. This pairs nicely with the ``@tag`` function modifier (learn more :ref:`tag-decorators`)

Your own custom style function must:

1. Use only keyword arguments, taking in ``node`` and ``node_class``.
2. Return a tuple ``(style, node_class, legend_name)`` where:
    - ``style``: dictionary of valid graphviz node style attributes.
    - ``node_class``: class used to style the default visualization - we recommend returning the input ``node_class``
    - ``legend_name``: text to display in the legend. Return ``None`` for no legend entry.
3. For the execution-focused visualizations, your custom styles are applied before the modifiers for outputs and overrides are applied.

If you need more customization, we suggest getting the graphviz object produced, and modifying it directly.

This `online graphviz editor <https://edotor.net/>`_ can help you get started!

.. code-block:: python

    def custom_style(
        *, node: graph_types.HamiltonNode, node_class: str
    ) -> Tuple[dict, Optional[str], Optional[str]]:
        """Custom style function for the visualization.

        :param node: node that Apache Hamilton is styling.
        :param node_class: class used to style the default visualization
        :return: a triple of (style, node_class, legend_name)
        """
        if node.type in [float, int]:
            style = ({"fillcolor": "aquamarine"}, node_class, "numbers")

        else:
            style = ({}, node_class, None)

        return style

    dr.display_all_functions(custom_style_function=custom_style)


.. image:: _visualization/custom_style.png
    :height: 250px


See the `full code example <https://github.com/apache/hamilton/tree/main/examples/styling_visualization>`_ for more details.
