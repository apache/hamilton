# @datasaver and @dataloader example

This example shows you can use the
`@datasaver()` and `@dataloader()` decorators to
annotated functions that save and load data so that they
can also return metadata.

This metadata is then exposed in the Apache Hamilton UI / inspectable
by other adapters.

To run this example, you can use the following command:

1. Install the requirements:
```bash
pip install -r requirements.txt
```
2. Have the Apache Hamilton UI set up. See [UI docs](https://hamilton.apache.org/hamilton-ui/) for instructions.
3. You have modified the run.py / notebook to log to the right Apache Hamilton UI project.
4. Run the example:

```bash
python run.py
```
or via the notebook.
