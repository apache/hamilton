# OpenLineage Adapter

This is an example of how to use the OpenLineage adapter that can be used to send metadata to an OpenLineage server.

## Motivation
OpenLineage is an open standard for data lineage.
With Apache Hamilton you can read and write data, and with OpenLineage you can track the lineage of that data.

## Steps
1. Build your project with Apache Hamilton.
2. Use one of the [materialization approaches](https://hamilton.apache.org/concepts/materialization/) to surface metadata about what is loaded and saved.
3. Use the OpenLineage adapter to send metadata to an OpenLineage server.

## To run this example:

1. Install the requirements:
```bash
pip install -r requirements.txt
```
2. Run the example:
```bash
python run.py
```
Or run the example in a notebook:
```bash
jupyter notebook
```
