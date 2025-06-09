============
Loading Data
============

In Apache Hamilton, data loaders are just the same as other functions in the DAG. They take in configuration parameters, and
output datasets in the desired form. Following up on the marketing spend dataset, you might write a data loader that
reads a dataframe saved in csv format on s3 like this:

.. code-block:: python

    import boto3
    import urllib
    import pandas as pd

    from hamilton.function_modifiers import extract_columns

    client = boto3.client("s3")

    @extract_columns('col1', 'col2', 'col3', ...)
    def marketing_spend(marketing_spend_data_path: str) -> pd.DataFrame:
        """Loads marketing spend from specified path on s3
        """
        if not marketing_spend_data_path.startswith("s3://"):
            raise ValueError(f"Invalid s3 URI {marketing_spend_data_path}")
        return pd.read_csv(
            marketing_spend_data_path,
            storage_options = {...}) # See https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html#pandas-read-csv for more info

Loading data is as easy as that! Run your driver with ``marketing_spend_data_path`` as a parameter, and you're good to
go.  However, there are a few considerations you might have prior to productionalizing this dataflow...

Plugging in new Data Sources
----------------------------

An advantage of Apache Hamilton is that it allows for rapid plug-and play for various components of your pipeline. This is
particularly important for data loading, where you might want to load your data from different sources depending on some
context. For instance -- if you're running your pipeline in production, you may want to use the production data sources.
If you're running it in QA, you might want to use the staging data sources. Or, if you're running it locally, you might
want to use abbreviated, in-memory data sources for testing. While Apache Hamilton is not opinionated on exactly _how_ you make
this switch, it presents a variety of tooling that can make it more manageable. Some options. To demonstrate some
techniques, let's continue on the example of loading marketing spend...

Modules as Interfaces
=====================

Say you have multiple data-loading nodes in your DAG. One strategy is to put them all in a single module. That way, if you want to load them up from different sources, you can simply switch the module your driver utilizes. Taking the example from above, you might have the following modules:

.. code-block:: python

    @extract_columns('col1', 'col2', 'col3', ...)
    def marketing_spend(marketing_spend_data_path: str) -> pd.DataFrame:
        """Loads marketing spend from specified path on s3
        """
        if not marketing_spend_data_path.startswith("s3://"):
            raise ValueError(f"Invalid s3 URI {marketing_spend_data_path}")
        return pd.read_csv(
            marketing_spend_data_path,
            storage_options = {...}) # See https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html#pandas-read-csv for more info

.. code-block:: python

    @extract_columns('col1', 'col2', 'col3', ...)
    def marketing_spend(marketing_spend_data_path: str) -> pd.DataFrame:
        """Loads marketing spend from specified path on s3
        """
        if not marketing_spend_data_path.endswith("csv"):
            raise ValueError(f"Invalid local data loading target {marketing_spend_data_path}")
        if not os.path.exists(marketing_spend_data_path):
            raise ValueError(f"Path does not exists")
        return pd.read_csv(marketing_spend_data_path)

Then, in your driver, you can choose between which module you want to use:

.. code-block:: python

    local_data_driver = Driver(config, local_data_loaders, ...)
    prod_data_driver = Driver(config, prod_data_loaders, ...)

Using the Config to Decide Sources
==================================

Note that we can utilize the config to determine where the data comes from as well. By using ``config.when`` you can
arrive at the same effect as above, while making it entirely config driven. If you combine the two functions into the
same module with `@config.when` it will look as follows:

.. code-block:: python

    @config.when(data_source='local')
    @extract_columns('col1', 'col2', 'col3', ...)
    def marketing_spend__local(marketing_spend_data_path: str) -> pd.DataFrame:
        ...

    @config.when(data_source='prod')
    @extract_columns('col1', 'col2', 'col3', ...)
    def marketing_spend__prod(marketing_spend_data_path: str) -> pd.DataFrame:
        ...

Then you can invoke your driver but set the config differently:

.. code-block:: python

    driver = Driver(
        {'data_source' : 'prod', 'marketing_spend_data_path' : 's3://...'},
        data_loaders, ...)

Note that there are a variety of other ways you can organize your code -- at this point its entirely use-case dependent.
Apache Hamilton is a language for declaring dataflows that's applicable towards a multitude of use-cases. It's not going to
dictate how to write your functions or where you put them.
