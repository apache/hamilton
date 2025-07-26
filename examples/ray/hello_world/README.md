# Apache Hamilton on Ray

Here we have a hello world example showing how you can
take some Apache Hamilton functions and then easily run them
in a distributed setting via ray.

`pip install sf-hamilton[ray]`  or `pip install sf-hamilton ray` to for the right dependencies to run this example.

File organization:

* `business_logic.py` houses logic that should be invariant to how hamilton is executed.
* `data_loaders.py` houses logic to load data for the business_logic.py module. The
idea is that you'd swap this module out for other ways of loading data.
* `run.py` is the script that ties everything together that uses vanilla Ray.

# Running the code:
For the vanilla Ray implementation use:

> python run.py

Here is the visualization of the execution:

![ray_dag](ray_dag.png)
