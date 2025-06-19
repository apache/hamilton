=====================
dbt
=====================

If you're familiar with DBT, you likely noticed that it can fill a similar role to Hamilton. What DBT does for SQL
files (organizing functions, providing lineage capabilities, making testing easier), Hamilton does for python functions.

Many projects span the gap between SQL and python, and Hamilton is a natural next step for an ML workflow after extracting data from DBT.

This example shows how you can use DBT's `new python capabilities <https://docs.getdbt.com/docs/build/python-models>`_ to integrate a Hamilton dataflow
with a DBT pipeline.

Find the full, working dbt project `here <https://github.com/DAGWorks-Inc/hamilton/tree/main/examples/dbt>`_.
