========
Glossary
========

Before we dive into the concepts, let's clarify the terminology we'll be using:

.. list-table::
   :header-rows: 0

   * - Directed Acyclic Graph (DAG)
     - A `directed acyclic graph <https://en.wikipedia.org/wiki/Directed\_acyclic\_graph>`_ is a computer \
       science/mathematics term for representing the world with "nodes" and "edges", where "edges" only flow in one \
       direction. It is called a graph because it can be drawn and visualized.
   * - Dataflow
     - The organization of functions and dependencies. This is a DAG -- it's directed (one function is running before \
       the other), acyclic, (there are no cycles, i.e., no function runs before itself), and a graph (it is easily \
       naturally represented by nodes and edges) and can be represented visually. See :doc:`node`.
   * - Node |
       Hamilton node |
       Transform
     - A single step in the dataflow DAG representing a computation -- usually 1:1 with functions but decorators break that \
       pattern -- in which case multiple transforms trace back to a single function. See :doc:`node`.
   * - Function |
       Python function |
       Hamilton function |
       Node definition
     - A Python function written by a user to create a single node (in the standard case) or \
       many (using function modifiers). See :doc:`node`.
   * - Module |
       Python module
     - Python code organized into a ``.py`` file. These are natural groupings of functions that turn to a set of nodes. See :doc:`best-practices/code-organization` for more details.
   * - Driver |
       Hamilton Driver
     - An object that loads Python modules to build a dataflow. It is responsible for visualizing and executing the \
       dataflow. See :doc:`driver`.
   * - script |
       runner |
       driver code
     - The piece of code where you create the Driver and execute the dataflow to get results.
   * - Config
     - Data that dictates the way the DAG is constructed. See :doc:`driver`.
   * - Function modifiers |
       Decorators
     - A function that modifies how your Hamilton function is compiled into a Hamilton node. See :doc:`function-modifiers`.
