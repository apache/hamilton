=====================
dbt
=====================

If you're familiar with DBT, you likely noticed that it can fill a similar role to Apache Hamilton. What DBT does for SQL
files (organizing functions, providing lineage capabilities, making testing easier), Apache Hamilton does for python functions.

Many projects span the gap between SQL and python, and Apache Hamilton is a natural next step for an ML workflow after extracting data from DBT.

This example shows how you can use DBT's `new python capabilities <https://docs.getdbt.com/docs/build/python-models>`_ to integrate a Apache Hamilton dataflow
with a DBT pipeline.

Find the full, working dbt project `here <https://github.com/apache/hamilton/tree/main/examples/dbt>`_.
