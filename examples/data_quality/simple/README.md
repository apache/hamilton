# Data Quality Example
Here we show how one can define some transformation logic that uses the new data quality feature.
In addition, we also show how you can manage execution on top of Ray, Pandas on Spark.

Note: at this current time - release 1.9.0 - _Dask data types_ + default validators with `@check_output` do not work well together.
Using Dask for multiprocessing using non-dask types works fine. That said, if you need to use Dask data types, we recommend using the pandera integration. See data_quality/pandera folder for this same code, but using
the pandera integration instead to validate outputs -- see examples/data_quality/pandera for examples.

# The task
We want to create some features for input to training a model. The task is to try to predict absenteeism at work.
Inspiration comes from [here](https://ieeexplore.ieee.org/document/6263151) and [here](https://github.com/outerbounds/hamilton-metaflow).

## Parts:
There are three parts to this task.

1. Write data loading logic.
2. Write feature transform logic.
3. Writing logic to materialize a dataframe from the above two parts.

These three parts map to the files laid out below -- with part (3) having multiple possible files.

We will be adding `@check_output` decorators to step (2). You could add them to step (1) if you like, but we omit that
here as an exercise for the reader.

## Example file set up
* Absenteeism_at_work.csv  - the raw data set. [Source](https://ieeexplore.ieee.org/document/6263151).
* data_loaders.py - a module that says how the data should be loaded. If we want to use native data types (e.g. dask data types)
this is where we would make that happen.
* feature_logic.py - this module contains some feature transformation code. It is annotated with `@check_output` and also
shows how one might support running the same code on Spark, Dask, and Ray, if you need to change how some code works.
* run.py - this is the default Apache Hamilton way of materializing features.
* run_dask.py - this shows how one would materialize features using Dask.
* run_ray.py - this shows how one would materialize features using Ray.
* run_spark.py - this shows how one would materialize features using Pandas on Spark.

Each file should have some documentation at the top to help identify what it is and how you can use it.

## How to run
Running the code involves installing the right python dependencies, and then executing the code.
It is best practice to create a python virtual environment for each project/example; we omit showing that step here.

The DAG created for each way of executing is logically the same, though it might involve different functions
being executed in the case of `spark` and `dask`; the `@config.when*` decorators are used for this purpose.

Note: `importance` is not specified in the `@check_output`decorators found in feature_logic.py. The default
behavior is therefore invoked, which is to log a "warning" and not stop execution. If stopping execution is desired,
`importance="fail"` should then be added to the decorators; more centralized control is going to be added in future releases.

### Normal Apache Hamilton

> pip install -r requirements.txt
> python run.py

### Apache Hamilton on Dask
It is best practice to create a python virtual environment for each project/example. We omit showing that step here.
> pip install -r requirements-dask.txt
> python run_dask.py

### Apache Hamilton on Ray
It is best practice to create a python virtual environment for each project/example. We omit showing that step here.
> pip install -r requirements-ray.txt
> python run_ray.py

### Apache Hamilton on Pandas on Spark
It is best practice to create a python virtual environment for each project/example. We omit showing that step here.
> pip install -r requirements-spark.txt
> python run_spark.py


# Visualizing Execution
Again you'll see that the visualizations don't change much between the different ways of executing. But to help you
visualize what's going on, here is the output of `visualize_execution` for each of them.

## Vanilla Apache Hamilton
![run](./run.png)

## Dask
![run_dask](./run_dask.png)

## Ray
![run_ray](./run_ray.png)

## Pandas on Spark
![run_spark](./run_spark.png)
