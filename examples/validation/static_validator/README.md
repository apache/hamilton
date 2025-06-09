# Example showing graph validation

This uses the StaticValidator class to validate a graph.

This specifically show how, for example, you can validate tags on functions.

 - run.py shows the validator and how to wire it in
 - good_module.py shows a node with the correct tags
 - bad_module.py shows a node with the wrong tags
 - notebook.ipynb shows how to run the same code in a notebook

To run the example, run `python run.py` and you should see the following output:

```
# good_module.py ran
{'foo': 'Hello, world!'}

# bad_module.py didn't have the right tags so graph building errored out
...
Apache Hamilton.lifecycle.base.ValidationException: Node validation failed! 1 errors encountered:
  foo: Node bad_module.foo is an output node, but does not have a table_name tag.
```

Alternatively you can run this all via the notebook.ipynb.
